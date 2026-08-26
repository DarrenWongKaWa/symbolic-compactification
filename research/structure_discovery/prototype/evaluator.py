"""Four-axis evaluator. UNKNOWN is never success. No single aggregate score."""
from __future__ import annotations

from typing import Any

D_ORDER = ["D0", "D1", "D2", "D3", "D4", "D5", "D6"]


def _rank(d: str | None) -> int:
    if not d:
        return -1
    return D_ORDER.index(d) if d in D_ORDER else -1


def _norm(s: str) -> str:
    return "".join(s.split())


def score_run(item: dict, run: dict) -> dict[str, Any]:
    gold_types = list(item.get("gold_types") or [])
    if item.get("gold_hypothesis_type") and item["gold_hypothesis_type"] not in gold_types:
        gold_types.append(item["gold_hypothesis_type"])
    forbidden_types = set(item.get("forbidden_types") or [])
    forbidden_recon = [_norm(x) for x in (item.get("forbidden_reconstructions") or [])]
    polarity = item.get("polarity") or "positive"
    proposed = run.get("hypothesis_types") or []
    proposed_set = set(proposed)

    type_hit = any(t in proposed_set for t in gold_types) if gold_types else False
    false_type = any(t in forbidden_types for t in proposed_set)
    closed_forms = []
    for node in (run.get("graph") or {}).get("nodes") or []:
        if node.get("closed"):
            closed_forms.append(node["closed"])
    unsafe_merge = False
    for c in closed_forms:
        if _norm(c) in forbidden_recon and any(
            n.get("verdict") == "ZERO" and _norm(n.get("closed") or "") == _norm(c)
            for n in (run.get("graph") or {}).get("nodes") or []
        ):
            unsafe_merge = True

    # hypothesis term overlap vs gold targets
    gold_subs = item.get("gold_target_subexpressions") or []
    hyp_subs = []
    for h in run.get("hypotheses") or []:
        hyp_subs.extend(h.get("target_subexpressions") or [])
    overlap = 0
    if gold_subs:
        gset = {_norm(s) for s in gold_subs}
        hset = {_norm(s) for s in hyp_subs}
        if gset:
            overlap = len(gset & hset) / len(gset)

    d_attempted = max((_rank(d) for d in run.get("d_attempted") or []), default=-1)
    d_certified = max((_rank(d) for d in run.get("d_certified") or []), default=-1)
    # certified type that matches gold
    gold_certified = False
    for n in (run.get("graph") or {}).get("nodes") or []:
        if n.get("state") == "ZERO_CERTIFIED" and n.get("hypothesis_type") in gold_types:
            gold_certified = True

    false_promotion = bool(run.get("false_promotion"))
    n_zero = int(run.get("n_zero") or 0)
    n_nz = int(run.get("n_nonzero") or 0)
    n_unk = int(run.get("n_unknown") or 0)

    # negative items: success is no ZERO on a forbidden reconstruction
    if polarity == "negative":
        discovery_success = (not unsafe_merge) and (not false_promotion)
        # claiming a forbidden type is a hypothesis error even if not certified
        hyp_quality = "false_type" if false_type else (
            "correct_abstain" if not type_hit else "type_hit_on_negative"
        )
    else:
        discovery_success = type_hit
        hyp_quality = (
            "type_exact" if type_hit else
            ("false_type" if false_type else "miss")
        )

    return {
        "id": item.get("id"),
        "split": item.get("split"),
        "tier": item.get("tier"),
        "polarity": polarity,
        "gold_types": gold_types,
        "gold_d": item.get("abstraction_level"),
        "axis_A_hypothesis_quality": hyp_quality,
        "axis_A_type_hit": type_hit,
        "axis_A_false_type": false_type,
        "axis_A_target_overlap": round(overlap, 4),
        "axis_B_n_hypotheses": run.get("n_hypotheses"),
        "axis_B_constructable": sum(
            1 for n in (run.get("graph") or {}).get("nodes") or []
            if n.get("state") == "CONSTRUCTABLE"
        ),
        "axis_C_n_zero": n_zero,
        "axis_C_n_nonzero": n_nz,
        "axis_C_n_unknown": n_unk,
        "axis_C_false_promotion": false_promotion,
        "axis_C_unsafe_merge": unsafe_merge,
        "axis_C_gold_type_certified": gold_certified,
        "axis_D_d_attempted": D_ORDER[d_attempted] if d_attempted >= 0 else None,
        "axis_D_d_certified": D_ORDER[d_certified] if d_certified >= 0 else None,
        "discovery_success": discovery_success,
        "certified_structured": run.get("certified_structured"),
        "hypothesis_types": proposed,
        "context_gold_name_hits": run.get("context_gold_name_hits") or [],
    }
