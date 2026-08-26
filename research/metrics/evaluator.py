"""Unified evaluator for ssc-bench-v0.1.

Does not modify engine semantics. UNKNOWN is never success. Hidden fields
are stripped before any proposer-facing projection.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Optional

import sympy

from symbolic_compactification import (
    NONZERO,
    UNKNOWN,
    ZERO,
    parse_expression,
    structure_summary,
    verify_equivalent,
)
from symbolic_compactification.models import AdapterError

HIDDEN_FIELDS = (
    "human_reference",
    "target_compact",
    "expected_verdict",
    "mutation_type",
    "ladder_id",
    "notes",
)

BENCHMARK_VERSION = "ssc-bench-v0.1"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def proposer_view(item: dict) -> dict:
    """Strip hidden labels. Never pass this result's complement to a proposer."""
    allowed = {
        "id", "tier", "family", "task", "current", "symbols", "functions",
        "source_format", "source_file",
    }
    view = {k: item[k] for k in allowed if k in item}
    view["hidden_from_proposer"] = True
    return view


def assert_no_leakage(payload: Any) -> None:
    blob = json.dumps(payload, default=str)
    for key in HIDDEN_FIELDS:
        if f'"{key}"' in blob:
            raise RuntimeError(f"F_LEAK: hidden field {key} present in proposer payload")


def _parse(text: str, symbols: list, functions: list):
    return parse_expression(text, symbols, functions=functions or None)


def ast_depth(expr: sympy.Expr) -> int:
    depth = 1
    for child in expr.args:
        depth = max(depth, 1 + ast_depth(child))
    return depth


def repeated_subexpression_count(expr: sympy.Expr, *, cap: int = 4000) -> int:
    counts: Counter[str] = Counter()
    n = 0
    for sub in sympy.preorder_traversal(expr):
        n += 1
        if n > cap:
            break
        if sub.args:
            counts[sympy.srepr(sub)] += 1
    return sum(1 for c in counts.values() if c >= 2)


def distinct_repeated_kernels(expr: sympy.Expr) -> int:
    bodies: Counter[str] = Counter()
    for s in expr.atoms(sympy.Sum):
        bodies[sympy.srepr(s.args[0])] += 1
    for p in expr.atoms(sympy.Product):
        bodies[sympy.srepr(p.args[0])] += 1
    calls: Counter[str] = Counter()
    for sub in sympy.preorder_traversal(expr):
        if isinstance(sub, sympy.core.function.AppliedUndef):
            calls[type(sub).__name__] += 1
    return (
        sum(1 for c in bodies.values() if c >= 2)
        + sum(1 for c in calls.values() if c >= 2)
    )


def compactness(text: str, symbols: list, functions: list | None = None) -> dict:
    try:
        expr = _parse(text, symbols, functions or [])
    except AdapterError as exc:
        return {
            "ok": False,
            "error": exc.code,
            "count_ops": None,
            "char_len": len(text),
            "ast_depth": None,
            "n_sums": None,
            "n_products": None,
            "n_piecewise": None,
            "n_piecewise_branches": None,
            "n_indexed_calls": None,
            "n_indexed_names": None,
            "n_distinct_repeated_kernels": None,
            "repeated_subexpression_count": None,
        }
    summary = structure_summary(expr)
    return {
        "ok": True,
        "error": None,
        "count_ops": summary["count_ops"],
        "char_len": len(text),
        "ast_depth": ast_depth(expr),
        "n_sums": summary["sums"],
        "n_products": summary["products"],
        "n_piecewise": summary["piecewise"],
        "n_piecewise_branches": summary["piecewise_branches"],
        "n_indexed_calls": summary["indexed_calls"],
        "n_indexed_names": len(summary["indexed_names"]),
        "n_distinct_repeated_kernels": distinct_repeated_kernels(expr),
        "repeated_subexpression_count": repeated_subexpression_count(expr),
    }


def compactness_delta(before: dict, after: dict) -> dict:
    keys = [
        "count_ops", "char_len", "ast_depth", "n_sums", "n_products",
        "n_piecewise", "n_piecewise_branches", "n_indexed_calls",
        "n_distinct_repeated_kernels", "repeated_subexpression_count",
    ]
    out = {}
    for key in keys:
        b, a = before.get(key), after.get(key)
        out[f"delta_{key}"] = None if b is None or a is None else b - a
    return out


def classify_failure(verdict: str, evidence: list, promoted: bool,
                     claimed_proven: bool = False) -> list[str]:
    codes = []
    kinds = [e.get("kind") for e in evidence if isinstance(e, dict)]
    if "construction_or_parse_failed" in kinds:
        codes.append("F_PARSE")
    if "TIME_BUDGET_EXCEEDED" in kinds:
        codes.append("F_TIMEOUT")
    if claimed_proven and verdict != ZERO:
        codes.append("F_HALLUC")
    if promoted and verdict != ZERO:
        codes.append("F_HALLUC")
    if verdict == NONZERO:
        codes.append("F_INTUITION")
    if verdict == UNKNOWN and "TIME_BUDGET_EXCEEDED" not in kinds:
        codes.append("F_UNKNOWN")
    return codes


def adjudicate_item(item: dict) -> dict:
    """Tier A (and any adjudicate task): run the engine on current vs candidate."""
    if not item.get("candidate"):
        raise ValueError(f"{item['id']}: adjudicate requires candidate")
    result = verify_equivalent(
        item["current"], item["candidate"], item["symbols"],
        functions=item.get("functions") or None,
    )
    expected = item.get("expected_verdict")
    match = expected is None or result.verdict == expected
    false_zero = (
        result.verdict == ZERO
        and expected == NONZERO
    )
    missed_nonzero = (
        expected == NONZERO
        and result.verdict != NONZERO
    )
    unknown_as_success = False  # invariant
    return {
        "id": item["id"],
        "task": "adjudicate",
        "verdict": result.verdict,
        "expected_verdict": expected,
        "match": match,
        "certified_success": bool(expected == ZERO and result.verdict == ZERO),
        "false_promotion": bool(false_zero),
        "nonzero_detection": bool(expected == NONZERO and result.verdict == NONZERO),
        "unknown": result.verdict == UNKNOWN,
        "unknown_as_success": unknown_as_success,
        "missed_nonzero": missed_nonzero,
        "seconds": result.seconds,
        "probes_tried": result.probes_tried,
        "evidence_kinds": [e.get("kind") for e in result.evidence if isinstance(e, dict)],
        "counterexample": result.counterexample,
        "failure_codes": classify_failure(
            result.verdict, result.evidence, promoted=false_zero),
        "compactness_current": compactness(
            item["current"], item["symbols"], item.get("functions")),
        "compactness_candidate": compactness(
            item["candidate"], item["symbols"], item.get("functions")),
    }


def score_compactify_result(
    item: dict,
    *,
    certified_text: Optional[str],
    claimed_text: Optional[str],
    promotions: int,
    verifier_calls: int,
    candidates_proposed: int,
    llm_calls: Optional[int],
    wall_clock_s: float,
    time_to_first_zero_s: Optional[float],
    time_to_best_certified_s: Optional[float],
    claimed_proven: bool,
    ladder_level: Optional[int] = None,
    token_usage: Optional[int] = None,
) -> dict:
    """Score a compactification run. Certified metrics use certified_text only."""
    symbols = item["symbols"]
    functions = item.get("functions")
    before = compactness(item["current"], symbols, functions)
    certified = (
        compactness(certified_text, symbols, functions)
        if certified_text is not None else None
    )
    claimed = (
        compactness(claimed_text, symbols, functions)
        if claimed_text is not None else None
    )
    hidden = item.get("human_reference") or item.get("target_compact")
    distance = None
    if certified_text is not None and hidden:
        vr = verify_equivalent(
            certified_text, hidden, symbols, functions=functions or None)
        if vr.verdict == ZERO:
            distance = 0
        else:
            distance = 1000 if certified is None else (
                abs((certified.get("count_ops") or 0) - (before.get("count_ops") or 0))
                + 1000
            )
    false_promotion = False
    if certified_text is not None:
        vr = verify_equivalent(
            item["current"], certified_text, symbols,
            functions=functions or None)
        if vr.verdict != ZERO:
            false_promotion = True
    return {
        "id": item["id"],
        "task": "compactify",
        "certified_success": bool(certified_text is not None and not false_promotion),
        "false_promotion": false_promotion,
        "unknown_as_success": False,
        "promotions": promotions,
        "verifier_calls": verifier_calls,
        "candidates_proposed": candidates_proposed,
        "llm_calls": llm_calls,
        "token_usage": token_usage,
        "wall_clock_s": wall_clock_s,
        "time_to_first_zero_s": time_to_first_zero_s,
        "time_to_best_certified_s": time_to_best_certified_s,
        "certified_ladder_level": ladder_level,
        "distance_to_hidden_reference": distance,
        "claimed_proven": claimed_proven,
        "failure_codes": classify_failure(
            ZERO if certified_text and not false_promotion else UNKNOWN,
            [], promoted=false_promotion, claimed_proven=claimed_proven),
        "compactness_input": before,
        "compactness_certified": certified,
        "compactness_claimed": claimed,
        "delta_certified": compactness_delta(before, certified) if certified else None,
        "delta_claimed": compactness_delta(before, claimed) if claimed else None,
    }


def load_items(root: Path, *, split: Optional[str] = None,
               tier: Optional[str] = None) -> list[dict]:
    items = []
    for path in sorted(root.rglob("*.json")):
        if path.name in {"schema.json", "metadata.json"}:
            continue
        data = json.loads(path.read_text())
        if isinstance(data, dict) and "id" in data:
            bundle = [data]
        elif isinstance(data, list):
            bundle = data
        else:
            continue
        for item in bundle:
            if split and item.get("split") != split:
                continue
            if tier and item.get("tier") != tier:
                continue
            items.append(item)
    return items


def summarize(records: list[dict]) -> dict:
    def _mean(xs):
        xs = [x for x in xs if x is not None]
        return None if not xs else sum(xs) / len(xs)

    def _sd(xs):
        xs = [x for x in xs if isinstance(x, (int, float)) and not isinstance(x, bool)]
        if len(xs) < 2:
            return None
        m = sum(xs) / len(xs)
        var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
        return math.sqrt(var)

    binaries = [
        "certified_success", "false_promotion", "nonzero_detection",
        "unknown", "match",
    ]
    out: dict[str, Any] = {"n": len(records)}
    for key in binaries:
        vals = [int(bool(r[key])) for r in records if key in r]
        if not vals:
            continue
        out[key] = {
            "n": len(vals),
            "count": sum(vals),
            "mean": _mean(vals),
            "sd": _sd(vals),
        }
    secs = [r.get("seconds") or r.get("wall_clock_s") for r in records]
    out["seconds"] = {"mean": _mean(secs), "sd": _sd(secs)}
    return out


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
