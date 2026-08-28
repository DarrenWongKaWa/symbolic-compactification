"""Size / complexity router for Track V.

Chooses a strategy from ``research.scalable_verification.api.STRATEGIES``.
Does not decide truth. Thresholds are frozen in THRESHOLDS.json.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

import sympy

from research.scalable_verification.api import STRATEGIES, route_name

THRESHOLDS_PATH = Path(__file__).resolve().parent / "THRESHOLDS.json"

MEASURE_KEYS = (
    "op_count",
    "tree_depth",
    "piecewise_count",
    "sum_count",
    "special_function_count",
    "n_free_symbols",
)

_REQUIRED_BOUNDS = (
    "direct_ops_max",
    "special_function_ops_max",
    "huge_ops",
    "huge_sum_ops",
)
_REQUIRED_MINS = ("piecewise", "sum", "special_function")


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
    for bucket in ("direct", "dd_certificate", "limit"):
        vals = kinds.get(bucket)
        if not isinstance(vals, list) or not all(isinstance(v, str) and v for v in vals):
            raise ValueError(f"THRESHOLDS.json kinds.{bucket} must be a string list")
    order = data.get("policy_order")
    if not isinstance(order, list) or not order:
        raise ValueError("THRESHOLDS.json policy_order must be a nonempty list")
    pw = data.get("piecewise_limit") or {}
    for label in ("with_sum", "without_sum"):
        raw = str(pw.get(label, "")).strip().upper()
        if raw not in STRATEGIES:
            raise ValueError(f"THRESHOLDS.json piecewise_limit.{label} is not a strategy")
    return data


THRESHOLDS = load_thresholds()


def measure(expr: Any) -> dict[str, int]:
    """Return frozen complexity measures for a SymPy expression.

    Counts ``Sum`` / ``Piecewise`` / special-function nodes by preorder
    traversal so a top-level node is included. ``op_count`` is
    ``sympy.count_ops(..., visual=False)``.
    """
    expr = _as_expr(expr)
    special_names = frozenset(THRESHOLDS["special_function_names"])
    piecewise_count = 0
    sum_count = 0
    special_function_count = 0
    for node in sympy.preorder_traversal(expr):
        if isinstance(node, sympy.Piecewise):
            piecewise_count += 1
        if isinstance(node, sympy.Sum):
            sum_count += 1
        name = getattr(getattr(node, "func", None), "__name__", "")
        if name in special_names:
            special_function_count += 1
    return {
        "op_count": int(sympy.count_ops(expr, visual=False)),
        "tree_depth": _tree_depth(expr),
        "piecewise_count": piecewise_count,
        "sum_count": sum_count,
        "special_function_count": special_function_count,
        "n_free_symbols": len(expr.free_symbols),
    }


def route(obligation_kind: Any, measures: Any) -> str:
    """Choose a strategy. Never returns a verification verdict."""
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


def _tree_depth(expr: sympy.Basic) -> int:
    max_d = 0
    stack: list[tuple[sympy.Basic, int]] = [(expr, 0)]
    while stack:
        node, depth = stack.pop()
        if depth > max_d:
            max_d = depth
        nxt = depth + 1
        for arg in node.args:
            stack.append((arg, nxt))
    return max_d


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
        return None
    if step == "SPECIAL_FUNCTION_LOCAL":
        if (
            m["special_function_count"] >= mins["special_function"]
            and ops < bounds["special_function_ops_max"]
        ):
            return "SPECIAL_FUNCTION_LOCAL"
        return None
    if step == "PIECEWISE_LIMIT":
        if m["piecewise_count"] >= mins["piecewise"] and kind in set(kinds["limit"]):
            pw = THRESHOLDS["piecewise_limit"]
            if m["sum_count"] >= mins["sum"]:
                return str(pw["with_sum"])
            return str(pw["without_sum"])
        return None
    if step == "SMALL_DD_CERTIFICATE":
        if ops < bounds["direct_ops_max"] and kind in set(kinds["dd_certificate"]):
            return "DD_CERTIFICATE"
        return None
    if step == "SMALL_DIRECT":
        if ops < bounds["direct_ops_max"] and kind in set(kinds["direct"]):
            return "DIRECT"
        return None
    if step == "DEFAULT_UNKNOWN":
        return "UNKNOWN"
    return None
