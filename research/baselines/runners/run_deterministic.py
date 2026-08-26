#!/usr/bin/env python3
"""Deterministic arms B0, B1, B6, B7-det, and engine Tier-A adjudication.

    .venv/bin/python research/baselines/runners/run_deterministic.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import sympy  # noqa: E402

from symbolic_compactification import (  # noqa: E402
    ZERO,
    collect_common_factor,
    combine_identical_sums,
    parse_expression,
    verify_equivalent,
)
from symbolic_compactification.budgets import BudgetExceeded, run_symbolic_operation  # noqa: E402
from symbolic_compactification.models import AdapterError  # noqa: E402
from research.metrics.evaluator import (  # noqa: E402
    adjudicate_item,
    compactness,
    load_items,
    score_compactify_result,
    summarize,
    write_json,
)

OUT = ROOT / "research" / "runs" / "protocol_v0"
BENCH = ROOT / "benchmark"


def _parse(item):
    return parse_expression(
        item["current"], item["symbols"], functions=item.get("functions") or None)


def _srepr_or_str(expr):
    return str(expr)


def arm_b0(item: dict) -> dict:
    t0 = time.time()
    return score_compactify_result(
        item,
        certified_text=item["current"],
        claimed_text=item["current"],
        promotions=0,
        verifier_calls=0,
        candidates_proposed=0,
        llm_calls=0,
        wall_clock_s=time.time() - t0,
        time_to_first_zero_s=None,
        time_to_best_certified_s=None,
        claimed_proven=False,
        ladder_level=0 if item["tier"] == "C" else None,
    )


_BUDGET_KEY = {
    "simplify": "simplify_seconds",
    "factor": "factor_seconds",
    "cancel": "cancel_seconds",
    "together": "together_seconds",
    "factor_terms": "factor_terms_seconds",
}


def _has_structure(expr) -> bool:
    return bool(expr.atoms(sympy.Sum, sympy.Product, sympy.Piecewise))


def _try_transform(name, expr):
    if name == "combine_identical_sums":
        r = combine_identical_sums(expr)
        return r.after if r.applied else expr
    if name == "collect_common_factor":
        r = collect_common_factor(expr)
        return r.after if r.applied else expr
    # Global simplify on Sum/Piecewise is the eager-expansion anti-pattern
    # and is the hang we just observed; skip it for structured input.
    if name == "simplify" and _has_structure(expr):
        return expr
    fn = {
        "simplify": sympy.simplify,
        "factor": sympy.factor,
        "cancel": sympy.cancel,
        "together": sympy.together,
        "factor_terms": sympy.factor_terms,
    }.get(name)
    if fn is None:
        return expr
    try:
        return run_symbolic_operation(
            name, fn, (expr,), budget_key=_BUDGET_KEY.get(name, "simplify_seconds"))
    except (BudgetExceeded, Exception):
        return expr


def arm_b1(item: dict, *, certify: bool) -> dict:
    t0 = time.time()
    try:
        expr = _parse(item)
    except AdapterError as exc:
        rec = score_compactify_result(
            item, certified_text=None, claimed_text=None,
            promotions=0, verifier_calls=0, candidates_proposed=0,
            llm_calls=0, wall_clock_s=time.time() - t0,
            time_to_first_zero_s=None, time_to_best_certified_s=None,
            claimed_proven=False)
        rec["failure_codes"] = ["F_PARSE"]
        rec["parse_error"] = exc.code
        return rec
    claimed = expr
    applied = []
    if _has_structure(expr):
        # Conventional global CAS on Sum/Piecewise hangs and is the
        # eager-expansion anti-pattern. B1 therefore leaves structured
        # input unchanged. Named structural transforms belong to B7-det.
        pass
    else:
        for name in ("simplify", "factor", "cancel", "together"):
            nxt = _try_transform(name, claimed)
            if nxt != claimed:
                applied.append(name)
            claimed = nxt
    claimed_text = _srepr_or_str(claimed)
    if not certify:
        rec = score_compactify_result(
            item, certified_text=None, claimed_text=claimed_text,
            promotions=0, verifier_calls=0, candidates_proposed=len(applied),
            llm_calls=0, wall_clock_s=time.time() - t0,
            time_to_first_zero_s=None, time_to_best_certified_s=None,
            claimed_proven=True)
        rec["b1_applied"] = applied
        rec["b1_structured_skipped"] = _has_structure(expr)
        return rec
    vr = verify_equivalent(
        item["current"], claimed_text, item["symbols"],
        functions=item.get("functions") or None)
    t1 = time.time() - t0
    certified = claimed_text if vr.verdict == ZERO else None
    rec = score_compactify_result(
        item, certified_text=certified, claimed_text=claimed_text,
        promotions=int(vr.verdict == ZERO), verifier_calls=1,
        candidates_proposed=max(len(applied), 1), llm_calls=0,
        wall_clock_s=t1,
        time_to_first_zero_s=t1 if certified else None,
        time_to_best_certified_s=t1 if certified else None,
        claimed_proven=False)
    rec["b1_applied"] = applied
    rec["b1_structured_skipped"] = _has_structure(expr)
    rec["b1_verdict"] = vr.verdict
    return rec


# --- restricted e-graph (B6): not egg ------------------------------------ #

def _children(expr):
    return list(expr.args)


def saturate_small(expr: sympy.Expr, *, steps: int = 8) -> sympy.Expr:
    """Tiny rewrite saturator. Soundness via later verify, not by itself."""
    def _b(name, fn, key):
        def inner(e):
            return run_symbolic_operation(name, fn, (e,), budget_key=key)
        return inner

    rules = [
        _b("expand", sympy.expand, "expand_seconds"),
        _b("factor", sympy.factor, "factor_seconds"),
        _b("cancel", sympy.cancel, "cancel_seconds"),
        _b("together", sympy.together, "together_seconds"),
        _b("powsimp", sympy.powsimp, "simplify_seconds"),
    ]
    best = expr
    best_ops = int(sympy.count_ops(expr, visual=False))
    seen = {sympy.srepr(expr)}
    frontier = [expr]
    for _ in range(steps):
        nxt = []
        for cur in frontier:
            for rule in rules:
                try:
                    cand = rule(cur)
                except (BudgetExceeded, Exception):
                    continue
                key = sympy.srepr(cand)
                if key in seen:
                    continue
                seen.add(key)
                ops = int(sympy.count_ops(cand, visual=False))
                if ops < best_ops:
                    best, best_ops = cand, ops
                nxt.append(cand)
            if len(seen) > 80:
                break
        frontier = nxt
        if not frontier or len(seen) > 80:
            break
    return best


def arm_b6(item: dict) -> dict:
    t0 = time.time()
    try:
        expr = _parse(item)
    except AdapterError as exc:
        rec = score_compactify_result(
            item, certified_text=None, claimed_text=None,
            promotions=0, verifier_calls=0, candidates_proposed=0,
            llm_calls=0, wall_clock_s=time.time() - t0,
            time_to_first_zero_s=None, time_to_best_certified_s=None,
            claimed_proven=False)
        rec["failure_codes"] = ["F_PARSE"]
        rec["parse_error"] = exc.code
        rec["b6_status"] = "skipped_unsupported"
        return rec
    if _has_structure(expr):
        rec = score_compactify_result(
            item, certified_text=item["current"], claimed_text=item["current"],
            promotions=0, verifier_calls=0, candidates_proposed=0,
            llm_calls=0, wall_clock_s=time.time() - t0,
            time_to_first_zero_s=None, time_to_best_certified_s=None,
            claimed_proven=False)
        rec["b6_status"] = "skipped_structured"
        return rec
    cand = saturate_small(expr)
    text = str(cand)
    vr = verify_equivalent(
        item["current"], text, item["symbols"],
        functions=item.get("functions") or None)
    certified = text if vr.verdict == ZERO else None
    return score_compactify_result(
        item, certified_text=certified, claimed_text=text,
        promotions=int(vr.verdict == ZERO), verifier_calls=1,
        candidates_proposed=1, llm_calls=0,
        wall_clock_s=time.time() - t0,
        time_to_first_zero_s=(time.time() - t0) if certified else None,
        time_to_best_certified_s=(time.time() - t0) if certified else None,
        claimed_proven=False)


def arm_b7_det(item: dict) -> dict:
    """Greedy named structural transforms + exact verify. No LLM."""
    t0 = time.time()
    try:
        expr = _parse(item)
    except AdapterError as exc:
        rec = score_compactify_result(
            item, certified_text=None, claimed_text=None,
            promotions=0, verifier_calls=0, candidates_proposed=0,
            llm_calls=0, wall_clock_s=time.time() - t0,
            time_to_first_zero_s=None, time_to_best_certified_s=None,
            claimed_proven=False)
        rec["failure_codes"] = ["F_PARSE"]
        rec["parse_error"] = exc.code
        return rec
    current_text = item["current"]
    certified = current_text
    promotions = 0
    calls = 0
    t_zero = None
    for fn in (combine_identical_sums, collect_common_factor):
        r = fn(expr)
        calls += 1
        if not r.applied:
            continue
        text = str(r.after)
        vr = verify_equivalent(
            current_text, text, item["symbols"],
            functions=item.get("functions") or None)
        if vr.verdict == ZERO:
            expr = r.after
            current_text = text
            certified = text
            promotions += 1
            if t_zero is None:
                t_zero = time.time() - t0
    return score_compactify_result(
        item, certified_text=certified, claimed_text=str(expr),
        promotions=promotions, verifier_calls=max(calls, 1),
        candidates_proposed=2, llm_calls=0,
        wall_clock_s=time.time() - t0,
        time_to_first_zero_s=t_zero,
        time_to_best_certified_s=t_zero,
        claimed_proven=False)


def run_tier_a(split: str) -> dict:
    items = load_items(BENCH, split=split, tier="A")
    records = []
    for item in items:
        if item["task"] != "adjudicate":
            continue
        if item["id"].startswith("C-guo"):
            continue
        records.append(adjudicate_item(item))
    return {"split": split, "n": len(records), "summary": summarize(records),
            "records": records}


def run_compactify(split: str, arm_name: str, fn, tiers=("B", "C")) -> dict:
    records = []
    for tier in tiers:
        for item in load_items(BENCH, split=split, tier=tier):
            if item["task"] != "compactify":
                continue
            if item.get("source_format") == "wolfram":
                rec = score_compactify_result(
                    item, certified_text=None, claimed_text=None,
                    promotions=0, verifier_calls=0, candidates_proposed=0,
                    llm_calls=0, wall_clock_s=0, time_to_first_zero_s=None,
                    time_to_best_certified_s=None, claimed_proven=False)
                rec["skipped"] = "wolfram_source_not_in_this_runner"
                records.append(rec)
                continue
            records.append(fn(item))
    return {"arm": arm_name, "split": split, "n": len(records),
            "summary": summarize(records), "records": records}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for split in ("dev", "test"):
        adj = run_tier_a(split)
        write_json(OUT / f"engine_adjudicate_{split}.json", adj)
        print(f"engine {split}: {json.dumps(adj['summary'], default=str)}")
        for name, fn in [
            ("B0", arm_b0),
            ("B1-cert", lambda it: arm_b1(it, certify=True)),
            ("B1-raw", lambda it: arm_b1(it, certify=False)),
            ("B6", arm_b6),
            ("B7-det", arm_b7_det),
        ]:
            payload = run_compactify(split, name, fn)
            write_json(OUT / f"{name}_{split}.json", payload)
            print(f"{name} {split}: {json.dumps(payload['summary'], default=str)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
