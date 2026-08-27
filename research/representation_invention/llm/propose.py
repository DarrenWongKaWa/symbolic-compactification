"""P2/P3/P4 propose. Same client/SOL as P1; V2 catalog-id contract."""
from __future__ import annotations

from typing import Any, Optional

from research.llm_abstraction.client import chat_complete
from research.llm_abstraction.config import CONFIG_ID, PRIMARY_MODEL, ProposerConfig
from research.llm_abstraction.packetizer import packets_for_item
from research.llm_abstraction.secrets import sanitize
from research.representation_invention.llm.catalog_render import catalog_ids, render_catalog
from research.representation_invention.llm.parser import parse_p2
from research.representation_invention.llm.prompts import (
    SYSTEM_PROMPT,
    build_p2_user_prompt,
    include_sol_packets,
)
from research.representation_invention.schema import OK
from research.structure_discovery.prototype.leakage import assert_no_leakage, proposer_view

PROTOCOL_ID = "grounded-proposer-v2"
ALLOWED_CONDITIONS = {"P2", "P3", "P4"}
_LEAK_TOKENS = (
    "gold_types", "gold_members", "gold_latent", "gold_operator",
    "forbidden_types", "hidden_gold",
    "Phi_Gamma", "PhiGamma",
)


def _normalize_condition(condition: str) -> str:
    cond = (condition or "P2").upper()
    if cond not in ALLOWED_CONDITIONS:
        raise ValueError(f"condition must be one of {sorted(ALLOWED_CONDITIONS)}; got {condition!r}")
    return cond


def assert_prompt_clean(*parts: str) -> None:
    """Proposer-visible text must not contain gold field names or gold objects."""
    import re

    blob = "\n".join(parts)
    for tok in _LEAK_TOKENS:
        if tok in blob:
            raise RuntimeError(f"F_LEAK: {tok} in proposer prompt")
    if re.search(r"\bL[4-7]\b", blob):
        raise RuntimeError("F_LEAK: L4-L7 token in proposer prompt")


def _sol_timeout_s(item: dict, config: Optional[ProposerConfig]) -> float:
    if config is not None and config.sol_timeout_s:
        # ProposerConfig default is 12s; Guo live runs need the long budget.
        if item.get("id") == "guo-sigma-abc" and config.sol_timeout_s <= 12.0:
            return 180.0
        return float(config.sol_timeout_s)
    return 180.0 if item.get("id") == "guo-sigma-abc" else 12.0


def _hyp_dicts(parsed: dict) -> list[dict]:
    out = []
    for h in parsed.get("hypotheses") or []:
        out.append(h.to_dict() if hasattr(h, "to_dict") else h)
    return out


def propose_p2(
    item: dict,
    catalog_entries: list[dict],
    *,
    condition: str = "P2",
    packets_text: Optional[str] = None,
    seed: Optional[int] = None,
    config: Optional[ProposerConfig] = None,
) -> dict[str, Any]:
    """Propose V2 hypotheses. P3 = RAW (no SOL). P2/P4 include SOL packets.

    `packets_text` is computed via packets_for_item unless the caller supplies
    it (tests pass a string or empty to avoid the packetizer).
    """
    cond = _normalize_condition(condition)
    pub = proposer_view(item)
    extra = (
        "gold_types", "gold_members", "gold_latent", "gold_operator",
        "forbidden_types", "hidden_gold", "gold_auxiliaries",
        "prefer_abstain", "requires_new_head", "gold_mode",
    )
    assert_no_leakage(pub, extra_forbidden=extra)
    cat_ids = catalog_ids(catalog_entries)
    cat_text = render_catalog(catalog_entries)

    cfg = config or ProposerConfig(
        model=PRIMARY_MODEL,
        condition=cond,
        sol_timeout_s=_sol_timeout_s(item, None),
    )
    if include_sol_packets(cond) and packets_text is None:
        _pk, _sm, packets_text = packets_for_item(
            {
                "current": pub["current"],
                "symbols": pub.get("symbols") or [],
                "functions": pub.get("functions") or [],
            },
            cap=cfg.packet_cap,
            backends="relations",
            timeout_s=_sol_timeout_s(item, cfg),
        )
    if not include_sol_packets(cond):
        packets_text = ""

    user = build_p2_user_prompt(
        condition=cond,
        expression=pub.get("current") or "",
        catalog_text=cat_text,
        packets_text=packets_text or "",
        scientific_context=pub.get("scientific_context") or [],
        symbols=pub.get("symbols") or [],
        functions=pub.get("functions") or [],
    )
    assert_prompt_clean(SYSTEM_PROMPT, user)

    rec = chat_complete(
        [{"role": "system", "content": SYSTEM_PROMPT},
         {"role": "user", "content": user}],
        cfg,
    )
    parsed = parse_p2(rec.get("content") or "", cat_ids)
    hyps = _hyp_dicts(parsed)
    n_ok = int(parsed.get("n_ok") or 0)
    n_grounded = sum(
        1
        for h in hyps
        if h.get("parse_status") == OK
        and h.get("member_ids")
        and all(m in cat_ids for m in h.get("member_ids") or [])
    )
    usage = rec.get("usage") or {}
    out = {
        "protocol": PROTOCOL_ID,
        "config_id": CONFIG_ID,
        "condition": cond,
        "item_id": item.get("id") or pub.get("id"),
        "seed": seed,
        "blocked": rec.get("blocked"),
        "error": rec.get("error"),
        "model": rec.get("model") or cfg.model,
        "usage": usage,
        "reasoning_tokens": (usage or {}).get("reasoning_tokens") if isinstance(usage, dict) else None,
        "latency_s": rec.get("latency_s"),
        "request_id": rec.get("request_id"),
        "reasoning_len": rec.get("reasoning_len"),
        "reasoning_sha": rec.get("reasoning_sha"),
        "parse_status": parsed.get("parse_status"),
        "parse_error": parsed.get("parse_error"),
        "n_ok": n_ok,
        "n_parse_failure": parsed.get("n_parse_failure"),
        "n_hypotheses": len(hyps),
        "n_grounded": n_grounded,
        "n_catalog": len(catalog_entries or []),
        "hypotheses": hyps,
        "raw_content": (rec.get("content") or "")[:8000],
        "catalog_ids": sorted(cat_ids),
        "abstain": parsed.get("abstain"),
    }
    return sanitize(out)
