"""Laurent series of a rational prefactor in ``t = var - point``.

Each multiplicative factor is expanded on its own and combined by a
sparse Cauchy product. Coefficients are per-power ``expand`` only.
This module never rebuilds a summed kernel and never calls together.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Optional

import sympy

INF_VAL = 10**9

LaurentMap = dict[int, sympy.Expr]


def pole_order(expr: Any, var: Any, point: Any) -> int:
    """Most negative power of ``expr`` in ``t = var - point``, or 0."""
    series = expand_rational(expr, var, point, 0)
    if not series:
        return 0
    return min(0, min(series))


def expand_rational(expr: Any, var: Any, point: Any, pmax: Any) -> LaurentMap:
    """Sparse Laurent map ``{power: coeff}`` of a rational in ``t = var - point``.

    Powers above ``pmax`` are omitted. Zero coefficients are omitted.
    """
    expr_e = _as_expr(expr)
    var_e = _as_expr(var)
    point_e = _as_expr(point)
    pmax_i = _as_int(pmax, name="pmax")
    t = sympy.Dummy("t")
    substituted = expr_e.xreplace({var_e: point_e + t})
    return _expand_in_t(substituted, t, pmax_i)


def convolve(
    left: Mapping[Any, Any],
    right: Mapping[Any, Any],
    pmax: Optional[int] = None,
) -> LaurentMap:
    """Cauchy product of two sparse Laurent maps, truncated at ``pmax``."""
    buckets: dict[int, list[sympy.Expr]] = defaultdict(list)
    pmax_i = None if pmax is None else _as_int(pmax, name="pmax")
    right_terms = tuple((_as_power(q), _as_expr(cb)) for q, cb in right.items())
    for p, ca in left.items():
        pa = _as_power(p)
        ea = _as_expr(ca)
        if _is_zero(ea):
            continue
        for qb, eb in right_terms:
            if _is_zero(eb):
                continue
            power = pa + qb
            if pmax_i is not None and power > pmax_i:
                continue
            buckets[power].append(ea * eb)
    return _finalize(buckets)


def _expand_in_t(expr: sympy.Expr, t: sympy.Expr, pmax: int) -> LaurentMap:
    if _is_zero(expr):
        return {}
    if not expr.has(t):
        return {0: expr} if pmax >= 0 else {}

    if isinstance(expr, sympy.Add):
        acc: LaurentMap = {}
        for term in expr.args:
            acc = _add_maps(acc, _expand_in_t(term, t, pmax))
        return {p: acc[p] for p in sorted(acc) if p <= pmax}

    if isinstance(expr, sympy.Pow):
        n = _as_int_power(expr.exp)
        base = expr.base
        if isinstance(base, sympy.Mul):
            split = sympy.Mul(*(sympy.Pow(arg, n) for arg in base.args))
            return _expand_in_t(split, t, pmax)
        return _expand_power(base, n, t, pmax)

    if isinstance(expr, sympy.Mul):
        return _expand_product(expr.args, t, pmax)

    return _expand_power(expr, 1, t, pmax)


def _expand_product(
    factors: tuple[sympy.Expr, ...],
    t: sympy.Expr,
    pmax: int,
) -> LaurentMap:
    vals = [_safe_val(f, t) for f in factors]
    if any(v >= INF_VAL for v in vals):
        for f, v in zip(factors, vals):
            if v >= INF_VAL and isinstance(f, sympy.Pow) and _as_int_power(f.exp) < 0:
                raise ValueError("division by zero")
        return {}
    total = sum(vals)
    acc: LaurentMap = {0: sympy.Integer(1)}
    remaining = total
    for f, v in zip(factors, vals):
        remaining -= v
        fm = _expand_in_t(f, t, pmax - total + v)
        if not fm:
            return {}
        acc = convolve(acc, fm, pmax=pmax - remaining)
        if not acc:
            return {}
    return acc


def _expand_power(base: sympy.Expr, n: int, t: sympy.Expr, pmax: int) -> LaurentMap:
    if n == 0:
        return {0: sympy.Integer(1)} if pmax >= 0 else {}
    poly = _as_poly(base, t)
    if poly is None:
        raise ValueError("not a rational function of t")
    if poly.is_zero:
        if n > 0:
            return {}
        raise ValueError("division by zero")
    terms = _poly_terms(poly)
    if not terms:
        if n > 0:
            return {}
        raise ValueError("division by zero")
    v = min(d for d, _ in terms)
    holomorphic = {d - v: coeff for d, coeff in terms}
    shifted = _power_holomorphic(holomorphic, n, pmax - n * v)
    out: LaurentMap = {}
    for p, coeff in shifted.items():
        q = p + n * v
        if q <= pmax and not _is_zero(coeff):
            out[q] = coeff
    return {p: out[p] for p in sorted(out)}


def _power_holomorphic(h: LaurentMap, n: int, pmax: int) -> LaurentMap:
    if n == 0:
        return {0: sympy.Integer(1)} if pmax >= 0 else {}
    if n == 1:
        return {p: h[p] for p in sorted(h) if p <= pmax}
    if n > 1:
        acc: LaurentMap = {0: sympy.Integer(1)}
        for _ in range(n):
            acc = convolve(acc, h, pmax=pmax)
        return acc
    inverted = _invert_holomorphic(h, pmax)
    if n == -1:
        return inverted
    acc = {0: sympy.Integer(1)}
    for _ in range(-n):
        acc = convolve(acc, inverted, pmax=pmax)
    return acc


def _invert_holomorphic(h: LaurentMap, pmax: int) -> LaurentMap:
    if pmax < 0:
        return {}
    u0 = h.get(0)
    if u0 is None or _is_zero(u0):
        raise ValueError("cannot invert vanishing constant term")
    terms: list[sympy.Expr] = [sympy.Integer(0)] * (pmax + 1)
    terms[0] = _expand_coeff(sympy.Integer(1) / u0)
    for k in range(1, pmax + 1):
        acc = sympy.Integer(0)
        for j in range(1, k + 1):
            uj = h.get(j)
            if uj is None or _is_zero(uj):
                continue
            acc += uj * terms[k - j]
        terms[k] = _expand_coeff(-acc / u0)
    return {k: terms[k] for k in range(pmax + 1) if not _is_zero(terms[k])}


def _safe_val(expr: sympy.Expr, t: sympy.Expr) -> int:
    """Lower bound on valuation; cancellation may raise the true order."""
    if _is_zero(expr):
        return INF_VAL
    if not expr.has(t):
        return 0
    if isinstance(expr, sympy.Add):
        return min(_safe_val(arg, t) for arg in expr.args)
    if isinstance(expr, sympy.Mul):
        return sum(_safe_val(arg, t) for arg in expr.args)
    if isinstance(expr, sympy.Pow):
        return _as_int_power(expr.exp) * _safe_val(expr.base, t)
    poly = _as_poly(expr, t)
    if poly is None:
        raise ValueError("not a rational function of t")
    if poly.is_zero:
        return INF_VAL
    terms = _poly_terms(poly)
    if not terms:
        return INF_VAL
    return min(d for d, _ in terms)


def _as_poly(expr: sympy.Expr, t: sympy.Expr) -> Optional[sympy.Poly]:
    try:
        expanded = sympy.expand(expr)
        return sympy.Poly(expanded, t, domain=sympy.EX)
    except (sympy.PolynomialError, ValueError, TypeError, AttributeError):
        return None
    except Exception:
        return None


def _poly_terms(poly: sympy.Poly) -> list[tuple[int, sympy.Expr]]:
    out: list[tuple[int, sympy.Expr]] = []
    for monom, coeff in poly.terms():
        if _is_zero(coeff):
            continue
        out.append((int(monom[0]), coeff))
    return out


def _add_maps(left: LaurentMap, right: LaurentMap) -> LaurentMap:
    buckets: dict[int, list[sympy.Expr]] = defaultdict(list)
    for power, coeff in left.items():
        if not _is_zero(coeff):
            buckets[power].append(coeff)
    for power, coeff in right.items():
        if not _is_zero(coeff):
            buckets[power].append(coeff)
    return _finalize(buckets)


def _finalize(buckets: Mapping[int, list[sympy.Expr]]) -> LaurentMap:
    out: LaurentMap = {}
    for power in sorted(buckets):
        parts = buckets[power]
        if not parts:
            continue
        coeff = parts[0] if len(parts) == 1 else sympy.Add(*parts)
        coeff = _expand_coeff(coeff)
        if not _is_zero(coeff):
            out[int(power)] = coeff
    return out


def _expand_coeff(expr: sympy.Expr) -> sympy.Expr:
    try:
        return sympy.expand(expr)
    except Exception:
        return expr


def _is_zero(expr: sympy.Expr) -> bool:
    if expr == 0:
        return True
    try:
        return sympy.expand(expr) == 0
    except Exception:
        return False


def _as_int_power(n: Any) -> int:
    return _as_int(n, name="power")


def _as_power(power: Any) -> int:
    return _as_int(power, name="Laurent power")


def _as_int(value: Any, *, name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, got {type(value)!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, sympy.Integer):
        return int(value)
    raise TypeError(f"{name} must be an integer, got {type(value)!r}")


def _as_expr(value: Any) -> sympy.Expr:
    if isinstance(value, sympy.Expr):
        return value
    if isinstance(value, bool):
        raise TypeError(f"unsupported type: {type(value)!r}")
    if isinstance(value, int):
        return sympy.Integer(value)
    raise TypeError(f"unsupported type: {type(value)!r}")
