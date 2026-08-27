"""P1 propose. Same client/SOL as P0; catalog is the contract."""
from __future__ import annotations

from typing import Optional

from research.grounded_proposer.catalog import catalog_entries, catalog_ids, render_catalog
from research.grounded_proposer.parser import parse_p1
from research.grounded_proposer.prompts import SYSTEM_PROMPT, build_p1_user_prompt
from research.llm_abstraction.client import chat_complete
from research.llm_abstraction.config import CONFIG_ID, PRIMARY_MODEL, ProposerConfig
from research.llm_abstraction.packetizer import packets_for_item
from research.llm_abstraction.secrets import sanitize
from research.obligation_ir.source_index import SourceIndex, build_index
from research.structure_discovery.prototype.leakage import assert_no_leakage, proposer_view


def propose_p1(item: dict, index: SourceIndex, *, condition: str = "A2") -> dict:
    pub = proposer_view(item)
    extra = (
        "gold_types", "gold_members", "gold_latent", "gold_operator",
        "forbidden_types", "hidden_gold",
    )
    assert_no_leakage(pub, extra_forbidden=extra)
    entries = catalog_entries(index)
    cat_ids = catalog_ids(entries)
    cat_text = render_catalog(entries)
    packets_text = ""
    if condition.upper() in {"A2", "A3", "P1"}:
        _pk, _sm, packets_text = packets_for_item(
            {"current": pub["current"], "symbols": pub.get("symbols") or [],
             "functions": pub.get("functions") or []},
            cap=10,
            backends="relations",
            timeout_s=180.0 if item.get("id") == "guo-sigma-abc" else 12.0,
        )
    user = build_p1_user_prompt(
        expression=pub["current"] if condition.upper() != "A3" else "(omitted; use catalog)",
        catalog_text=cat_text,
        packets_text=packets_text if condition.upper() in {"A2", "P1"} else "",
        scientific_context=pub.get("scientific_context") or [],
        symbols=pub.get("symbols") or [],
        functions=pub.get("functions") or [],
    )
    cfg = ProposerConfig(model=PRIMARY_MODEL, condition="A2", sol_timeout_s=180.0)
    rec = chat_complete(
        [{"role": "system", "content": SYSTEM_PROMPT},
         {"role": "user", "content": user}],
        cfg,
    )
    parsed = parse_p1(rec.get("content") or "", cat_ids)
    hyps = parsed.get("hypotheses") or []
    return sanitize({
        "protocol": "grounded-proposer-v1",
        "config_id": CONFIG_ID,
        "condition": "P1_A2",
        "item_id": item.get("id"),
        "blocked": rec.get("blocked"),
        "error": rec.get("error"),
        "usage": rec.get("usage"),
        "latency_s": rec.get("latency_s"),
        "request_id": rec.get("request_id"),
        "parse_status": parsed.get("parse_status"),
        "n_ok": parsed.get("n_ok"),
        "n_parse_failure": parsed.get("n_parse_failure"),
        "n_catalog": len(entries),
        "hypotheses": [h.to_dict() if hasattr(h, "to_dict") else h for h in hyps],
        "raw_content": (rec.get("content") or "")[:8000],
        "catalog_ids": sorted(cat_ids),
    })
