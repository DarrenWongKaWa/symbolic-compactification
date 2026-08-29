"""Exact affine argument normalizer for z = z0 + c t.

Accept only when the reconstructed linear form matches the input by
``expand(z - (z0 + c*t)) == 0``, with ``z0`` and ``c`` free of ``t``.
Otherwise return UNSUPPORTED. Quadratic or non-affine rational arguments
are UNSUPPORTED. This is not a remainder certificate and not hop ZERO.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union

import sympy

from research.remainder_certification.schema import UNSUPPORTED

OPS_CAP = 80
CHAR_CAP = 4096

_ZERO = sympy.Integer(0)


@dataclass(frozen=True)
class AffineNormalization:
    """Accepted split ``z = z0 + c t`` with ``residual`` identically 0."""

    z0: sympy.Expr
    c: sympy.Expr
    residual: sympy.Expr


AffineResult = Union[AffineNormalization, str]


def normalize_affine(z: Any, t: Any) -> AffineResult:
    """Return ``(z0, c, residual=0)`` if ``z`` is affine in ``t``, else UNSUPPORTED."""
    try:
        return _normalize_affine(z, t)
    except Exception:
        return UNSUPPORTED


def _normalize_affine(z: Any, t: Any) -> AffineResult:
    expr = _as_expr(z)
    if expr is None:
        return UNSUPPORTED
    t_sym = _as_symbol(t, expr)
    if t_sym is None:
        return UNSUPPORTED
    if _unusable(expr) or _too_large(expr):
        return UNSUPPORTED

    z0, c = _extract_affine(expr, t_sym)
    if z0 is None or c is None:
        return UNSUPPORTED
    z0 = sympy.expand(z0)
    c = sympy.expand(c)
    if _unusable(z0) or _unusable(c):
        return UNSUPPORTED
    if z0.has(t_sym) or c.has(t_sym):
        return UNSUPPORTED

    residual = sympy.expand(expr - (z0 + c * t_sym))
    if residual != 0:
        return UNSUPPORTED
    return AffineNormalization(z0=z0, c=c, residual=_ZERO)


def _extract_affine(
    expr: sympy.Expr, t: sympy.Symbol
) -> tuple[sympy.Expr | None, sympy.Expr | None]:
    # together is extraction-only; residual is expand of the original expr.
    lowered = sympy.expand(expr.doit())
    if _unusable(lowered):
        return (None, None)
    collected = sympy.together(lowered)
    num, den = sympy.fraction(collected)
    num = sympy.expand(num)
    den = sympy.expand(den)
    if den == 0 or den.has(t) or _unusable(num) or _unusable(den):
        return (None, None)
    if not num.has(t):
        return (num / den, _ZERO)
    try:
        poly = sympy.Poly(num, t, domain=sympy.EX)
    except (sympy.PolynomialError, ValueError, TypeError):
        return (None, None)
    deg = poly.degree()
    if deg > 1:
        return (None, None)
    const = poly.nth(0) if deg >= 0 else _ZERO
    linear = poly.nth(1) if deg >= 1 else _ZERO
    if const.has(t) or linear.has(t):
        return (None, None)
    return (const / den, linear / den)


def _as_expr(z: Any) -> sympy.Expr | None:
    if isinstance(z, bool) or isinstance(z, (float, sympy.Float)):
        return None
    if isinstance(z, int):
        return sympy.Integer(z)
    if isinstance(z, sympy.Expr):
        return z
    return None


def _as_symbol(t: Any, expr: sympy.Expr) -> sympy.Symbol | None:
    if isinstance(t, sympy.Symbol):
        return t
    if isinstance(t, str) and t:
        for sym in expr.free_symbols:
            if isinstance(sym, sympy.Symbol) and sym.name == t:
                return sym
        return sympy.Symbol(t)
    return None


def _unusable(expr: sympy.Expr) -> bool:
    banned = (
        sympy.Float,
        sympy.nan,
        sympy.zoo,
        sympy.oo,
        sympy.S.NegativeInfinity,
        sympy.S.ComplexInfinity,
    )
    try:
        return bool(expr.has(*banned))
    except Exception:
        return True


def _too_large(expr: sympy.Expr) -> bool:
    try:
        if sympy.count_ops(expr) > OPS_CAP:
            return True
        if len(str(expr)) > CHAR_CAP:
            return True
    except Exception:
        return True
    return False
