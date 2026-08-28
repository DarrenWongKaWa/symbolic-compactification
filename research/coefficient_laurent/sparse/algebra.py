"""Sparse Laurent maps ``{power: expr}``.

Per-power rewrite is ``expand`` of that coefficient only, and only when
``count_ops`` is at most ``EXPAND_OPS_CAP``. Larger coefficients are left
unsimplified. This module never rebuilds the summed kernel and never
calls together on it.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping

import sympy

EXPAND_OPS_CAP = 250

LaurentMap = dict[int, sympy.Expr]


def count_ops_map(m: Mapping[Any, Any]) -> int:
    """Sum of ``count_ops`` over coefficient expressions. Fail-closed to 0."""
    total = 0
    for coeff in m.values():
        total += _count_ops(_as_expr(coeff), default=0)
    return total


def add_maps(*maps: Mapping[Any, Any], ops_cap: int = EXPAND_OPS_CAP) -> LaurentMap:
    """Add sparse Laurent maps powerwise. Empty input is the zero map."""
    buckets: dict[int, list[sympy.Expr]] = defaultdict(list)
    for m in maps:
        _collect(m, buckets, scale_by=None)
    return _finalize(buckets, ops_cap)


def convolve(
    left: Mapping[Any, Any],
    right: Mapping[Any, Any],
    *,
    ops_cap: int = EXPAND_OPS_CAP,
) -> LaurentMap:
    """Cauchy product of two sparse Laurent maps."""
    buckets: dict[int, list[sympy.Expr]] = defaultdict(list)
    right_terms = tuple((_as_power(q), _as_expr(cb)) for q, cb in right.items())
    for p, ca in left.items():
        pa = _as_power(p)
        ea = _as_expr(ca)
        if _is_zero(ea):
            continue
        for qb, eb in right_terms:
            if _is_zero(eb):
                continue
            buckets[pa + qb].append(ea * eb)
    return _finalize(buckets, ops_cap)


def scale(
    m: Mapping[Any, Any],
    coeff: Any,
    *,
    ops_cap: int = EXPAND_OPS_CAP,
) -> LaurentMap:
    """Multiply every coefficient of ``m`` by ``coeff``."""
    factor = _as_expr(coeff)
    if _is_zero(factor):
        return {}
    buckets: dict[int, list[sympy.Expr]] = defaultdict(list)
    _collect(m, buckets, scale_by=factor)
    return _finalize(buckets, ops_cap)


def _collect(
    m: Mapping[Any, Any],
    buckets: dict[int, list[sympy.Expr]],
    *,
    scale_by: sympy.Expr | None,
) -> None:
    for power, coeff in m.items():
        expr = _as_expr(coeff)
        if scale_by is not None:
            expr = scale_by * expr
        if _is_zero(expr):
            continue
        buckets[_as_power(power)].append(expr)


def _finalize(buckets: Mapping[int, list[sympy.Expr]], ops_cap: int) -> LaurentMap:
    out: LaurentMap = {}
    for power in sorted(buckets):
        terms = buckets[power]
        if not terms:
            continue
        coeff = terms[0] if len(terms) == 1 else sympy.Add(*terms)
        coeff = _expand_coeff(coeff, ops_cap)
        if not _is_zero(coeff):
            out[power] = coeff
    return out


def _expand_coeff(expr: sympy.Expr, ops_cap: int) -> sympy.Expr:
    ops = _count_ops(expr, default=ops_cap + 1)
    if ops > ops_cap:
        return expr
    try:
        return sympy.expand(expr)
    except Exception:
        return expr


def _count_ops(expr: sympy.Expr, *, default: int) -> int:
    try:
        return int(sympy.count_ops(expr, visual=False))
    except Exception:
        return default


def _as_power(power: Any) -> int:
    if isinstance(power, bool):
        raise TypeError(f"Laurent power must be an integer, got {type(power)!r}")
    if isinstance(power, int):
        return power
    if isinstance(power, sympy.Integer):
        return int(power)
    raise TypeError(f"Laurent power must be an integer, got {type(power)!r}")


def _as_expr(value: Any) -> sympy.Expr:
    if isinstance(value, sympy.Expr):
        return value
    if isinstance(value, bool):
        raise TypeError(f"unsupported coefficient type: {type(value)!r}")
    if isinstance(value, int):
        return sympy.Integer(value)
    raise TypeError(f"unsupported coefficient type: {type(value)!r}")


def _is_zero(expr: sympy.Expr) -> bool:
    return expr == 0
