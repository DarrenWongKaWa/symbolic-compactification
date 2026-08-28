"""Size / structure router for Track V2 obligations.

Chooses a strategy. Does not decide truth. Thresholds are frozen in
THRESHOLDS.json.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

import sympy

THRESHOLDS_PATH = Path(__file__).resolve().parent / "THRESHOLDS.json"

STRATEGIES = (
    "DIRECT",
    "FACTOR",
    "SERIES",
    "DD_RECURRENCE",
    "HERMITE_RECURRENCE",
    "SPECIAL_FUNCTION",
    "UNKNOWN",
)

VERDICTS = (
    "ZERO",
    "NONZERO",
    "FAMILY_ZERO",
    "FAMILY_NONZERO",
    "FAMILY_UNKNOWN",
)

MEASURE_KEYS = (
    "op_count",
    "branch_count",
    "sum_count",
    "n_free_symbols",
    "special_function_count",
    "denom_complexity",
    "multiplicity",
)

_REQUIRED_BOUNDS = (
    "direct_ops_max",
    "special_function_ops_max",
    "recurrence_ops_max",
    "huge_ops",
    "huge_sum_ops",
    "huge_denom",
    "direct_symbols_max",
    "factor_denom_min",
)
_REQUIRED_MINS = ("branch", "sum", "special_function", "hermite_multiplicity")
_REQUIRED_KIND_BUCKETS = (
    "direct",
    "factor_series",
    "dd_recurrence",
    "hermite_recurrence",
)


def route_name(name: str) -> str:
    """Map a label onto STRATEGIES. Verdicts become UNKNOWN."""
    n = (name or "UNKNOWN").strip().upper()
    if n in VERDICTS or n not in STRATEGIES:
        return "UNKNOWN"
    return n


def load_thresholds() -> dict[str, Any]:
    """Load frozen THRESHOLDS.json. Missing or malformed files raise."""
    data = json.loads(THRESHOLDS_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("THRESHOLDS.json must be an object")
    if data.get("does_not_decide_truth") is not True:
        raise ValueError("THRESHOLDS.json must freeze does_not_decide_truth=true")
    bounds = data.get("bounds")
    mins = data.get("mins")
    kinds = data.get("kinds")
    if not isinstance(bounds, dict) or not isinstance(mins, dict) or not isinstance(kinds, dict):
        raise ValueError("THRESHOLDS.json missing bounds/mins/kinds")
    for key in _REQUIRED_BOUNDS:
        if not isinstance(bounds.get(key), int) or isinstance(bounds.get(key), bool):
            raise ValueError(f"THRESHOLDS.json bounds.{key} must be int")
    for key in _REQUIRED_MINS:
        if not isinstance(mins.get(key), int) or isinstance(mins.get(key), bool):
            raise ValueError(f"THRESHOLDS.json mins.{key} must be int")
    names = data.get("special_function_names")
    if not isinstance(names, list) or not all(isinstance(n, str) and n for n in names):
        raise ValueError("THRESHOLDS.json special_function_names must be nonempty strings")
    if "polygamma" not in names:
        raise ValueError("THRESHOLDS.json must include polygamma")
    for bucket in _REQUIRED_KIND_BUCKETS:
        vals = kinds.get(bucket)
        if not isinstance(vals, list) or not all(isinstance(v, str) and v for v in vals):
            raise ValueError(f"THRESHOLDS.json kinds.{bucket} must be a string list")
    order = data.get("policy_order")
    if not isinstance(order, list) or not order:
        raise ValueError("THRESHOLDS.json policy_order must be a nonempty list")
    pw = data.get("branch_limit") or {}
    for label in ("with_sum", "without_sum"):
        raw = str(pw.get(label, "")).strip().upper()
        if raw not in STRATEGIES or raw in VERDICTS:
            raise ValueError(f"THRESHOLDS.json branch_limit.{label} is not a strategy")
    denom_factor = str(data.get("denom_factor", "")).strip().upper()
    if denom_factor not in STRATEGIES or denom_factor in VERDICTS:
        raise ValueError("THRESHOLDS.json denom_factor is not a strategy")
    return data


THRESHOLDS = load_thresholds()


def measure(expr: Any) -> dict[str, int]:
    """Return frozen complexity measures for a SymPy expression.

    Structural counts use preorder traversal (top-level ``Sum`` /
    ``Piecewise`` included). ``op_count`` is
    ``sympy.count_ops(..., visual=False)``. ``branch_count`` is the number
    of Piecewise arms, not the number of Piecewise nodes.
    ``denom_complexity`` is ``count_ops`` of the together-denominator.
    ``multiplicity`` is ``1 + max derivative order`` when a Derivative is
    present, else 0.
    """
    expr = _as_expr(expr)
    special_names = frozenset(THRESHOLDS["special_function_names"])
    branch_count = 0
    sum_count = 0
    special_function_count = 0
    for node in sympy.preorder_traversal(expr):
        if isinstance(node, sympy.Piecewise):
            branch_count += len(node.args)
        if isinstance(node, sympy.Sum):
            sum_count += 1
        name = getattr(getattr(node, "func", None), "__name__", "")
        if name in special_names:
            special_function_count += 1
    return {
        "op_count": int(sympy.count_ops(expr, visual=False)),
        "branch_count": branch_count,
        "sum_count": sum_count,
        "n_free_symbols": len(expr.free_symbols),
        "special_function_count": special_function_count,
        "denom_complexity": _denom_complexity(expr),
        "multiplicity": _multiplicity(expr),
    }


def route(obligation_kind: Any, measures: Any) -> str:
    """Choose a strategy. Never returns a verification or family verdict."""
    parsed = _normalize_measures(measures)
    if parsed is None:
        return route_name("UNKNOWN")
    kind = str(obligation_kind or "").strip().upper()
    for step in THRESHOLDS["policy_order"]:
        hit = _apply_step(step, kind, parsed)
        if hit is not None:
            return route_name(hit)
    return route_name("UNKNOWN")


def _as_expr(expr: Any) -> sympy.Basic:
    if isinstance(expr, sympy.Basic):
        return expr
    if isinstance(expr, bool) or not isinstance(expr, int):
        raise TypeError("measure expects a sympy expression")
    return sympy.Integer(expr)


def _as_int(value: Any) -> Optional[int]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_measures(measures: Any) -> Optional[dict[str, int]]:
    if not isinstance(measures, Mapping):
        return None
    out: dict[str, int] = {}
    for key in MEASURE_KEYS:
        if key not in measures:
            out[key] = 0
            continue
        parsed = _as_int(measures[key])
        if parsed is None or parsed < 0:
            return None
        out[key] = parsed
    return out


def _denom_complexity(expr: sympy.Basic) -> int:
    try:
        if isinstance(expr, sympy.Piecewise):
            vals = [_denom_complexity(arg[0]) for arg in expr.args]
            return max(vals) if vals else 0
        if isinstance(expr, sympy.Sum):
            return _denom_complexity(expr.function)
        _num, den = sympy.fraction(sympy.together(expr))
        if den == 1:
            return 0
        return int(sympy.count_ops(den, visual=False))
    except Exception:
        return 0


def _multiplicity(expr: sympy.Basic) -> int:
    max_m = 0
    for node in sympy.preorder_traversal(expr):
        if not isinstance(node, sympy.Derivative):
            continue
        order = 0
        for _var, n in node.variable_count:
            order += int(n)
        cand = order + 1
        if cand > max_m:
            max_m = cand
    return max_m


def _apply_step(step: str, kind: str, m: dict[str, int]) -> Optional[str]:
    bounds = THRESHOLDS["bounds"]
    mins = THRESHOLDS["mins"]
    kinds = THRESHOLDS["kinds"]
    ops = m["op_count"]
    if step == "HUGE_UNKNOWN":
        if ops > bounds["huge_ops"]:
            return "UNKNOWN"
        if m["sum_count"] >= mins["sum"] and ops > bounds["huge_sum_ops"]:
            return "UNKNOWN"
        if m["denom_complexity"] > bounds["huge_denom"]:
            return "UNKNOWN"
        return None
    if step == "SPECIAL_FUNCTION":
        if (
            m["special_function_count"] >= mins["special_function"]
            and ops < bounds["special_function_ops_max"]
        ):
            return "SPECIAL_FUNCTION"
        return None
    if step == "HERMITE_RECURRENCE":
        if ops >= bounds["recurrence_ops_max"]:
            return None
        if kind in set(kinds["hermite_recurrence"]):
            return "HERMITE_RECURRENCE"
        if (
            m["multiplicity"] >= mins["hermite_multiplicity"]
            and kind in set(kinds["dd_recurrence"])
        ):
            return "HERMITE_RECURRENCE"
        return None
    if step == "DD_RECURRENCE":
        if ops < bounds["recurrence_ops_max"] and kind in set(kinds["dd_recurrence"]):
            return "DD_RECURRENCE"
        return None
    if step == "BRANCH_FACTOR_OR_SERIES":
        if m["branch_count"] >= mins["branch"] and kind in set(kinds["factor_series"]):
            pw = THRESHOLDS["branch_limit"]
            if m["sum_count"] >= mins["sum"]:
                return str(pw["with_sum"])
            return str(pw["without_sum"])
        return None
    if step == "DENOM_FACTOR":
        if (
            m["denom_complexity"] >= bounds["factor_denom_min"]
            and ops < bounds["special_function_ops_max"]
            and kind in set(kinds["direct"]) | set(kinds["factor_series"])
        ):
            return str(THRESHOLDS["denom_factor"])
        return None
    if step == "SMALL_DIRECT":
        if (
            ops < bounds["direct_ops_max"]
            and m["n_free_symbols"] <= bounds["direct_symbols_max"]
            and kind in set(kinds["direct"])
        ):
            return "DIRECT"
        return None
    if step == "DEFAULT_UNKNOWN":
        return "UNKNOWN"
    return None
