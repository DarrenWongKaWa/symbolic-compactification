"""propose_abstraction: experimental DeepSeek proposer. Does not modify SOL."""
from __future__ import annotations

from typing import Any, Optional, Sequence, Union

from research.llm_abstraction.client import chat_complete
from research.llm_abstraction.config import CONFIG_ID, PROTOCOL_ID, ProposerConfig
from research.llm_abstraction.packetizer import basic_summary, packets_for_item
from research.llm_abstraction.parser import parse_model_output
from research.llm_abstraction.prompts import SYSTEM_PROMPT, build_user_prompt
from research.llm_abstraction.schema import BLOCKED, ProposeResult
from research.structure_discovery.prototype.leakage import (
    assert_no_leakage,
    proposer_view,
)


def _as_item(expression: Union[str, dict], item: Optional[dict]) -> tuple[str, dict]:
    if isinstance(expression, dict):
        item = expression
    item = dict(item or {})
    if "current" in item:
        pub = proposer_view(item)
        extra = (
            "gold_types", "gold_members", "gold_latent", "gold_operator",
            "forbidden_types", "hidden_gold", "gold_auxiliaries",
            "prefer_abstain", "requires_new_head", "gold_mode",
        )
        assert_no_leakage(pub, extra_forbidden=extra)
        return pub.get("current") or "", pub
    return str(expression), item


def propose_abstraction(
    expression: Union[str, dict],
    observation_bundle=None,
    scientific_context: Optional[Sequence[str]] = None,
    config: Optional[ProposerConfig] = None,
    *,
    item: Optional[dict] = None,
    packets_text: Optional[str] = None,
    basic: Optional[dict] = None,
) -> ProposeResult:
    config = config or ProposerConfig()
    expr, pub = _as_item(expression, item)
    symbols = pub.get("symbols") or []
    functions = pub.get("functions") or []
    assumptions = pub.get("assumptions") or []
    ctx = list(scientific_context or pub.get("scientific_context") or [])
    cond = (config.condition or "A0").upper()
    need_packets = cond in {"A2", "A3", "L2", "L3", "G2", "G3"}
    need_summary = cond in {"A1", "A2", "L1", "L2", "G1", "G2"}
    if need_packets and packets_text is None:
        if observation_bundle is not None:
            from research.llm_abstraction.packetizer import packetize, render_packets
            data = observation_bundle.to_dict() if hasattr(observation_bundle, "to_dict") else observation_bundle
            packets = packetize(data, cap=config.packet_cap)
            packets_text = render_packets(packets)
        else:
            _pk, _sm, packets_text = packets_for_item(
                {"current": expr, "symbols": symbols, "functions": functions,
                 "hidden_gold": pub.get("hidden_gold") or {}},
                cap=config.packet_cap,
                backends=config.sol_backends,
                timeout_s=config.sol_timeout_s,
            )
            basic = basic or _sm
    if need_summary and basic is None:
        basic = basic_summary(expr, symbols, functions)
    user = build_user_prompt(
        condition=cond,
        expression=expr,
        symbols=symbols,
        functions=functions,
        assumptions=assumptions,
        scientific_context=ctx,
        basic_summary=basic if need_summary else None,
        packets_text=packets_text if need_packets else None,
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
    rec = chat_complete(messages, config)
    if rec.get("blocked"):
        return ProposeResult(
            hypotheses=[],
            parse_status=BLOCKED,
            parse_error=str(rec.get("error") or "BLOCKED"),
            raw_content="",
            meta={
                "model": rec.get("model"),
                "config_id": CONFIG_ID,
                "protocol_id": PROTOCOL_ID,
                "condition": cond,
                "blocked": True,
                "error": rec.get("error"),
            },
        )
    result = parse_model_output(rec.get("content") or "")
    result.meta = {
        "model": rec.get("model"),
        "config_id": CONFIG_ID,
        "protocol_id": PROTOCOL_ID,
        "condition": cond,
        "packet_cap": config.packet_cap,
        "usage": rec.get("usage") or {},
        "latency_s": rec.get("latency_s"),
        "request_id": rec.get("request_id"),
        "reasoning_len": rec.get("reasoning_len"),
        "reasoning_sha": rec.get("reasoning_sha"),
        "blocked": False,
        "error": rec.get("error"),
        "n_ok": len([h for h in result.hypotheses if h.parse_status == "OK"]),
    }
    return result
