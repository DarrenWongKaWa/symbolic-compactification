"""Exact residual / one-parameter limit helpers for toy families.

ZERO only on algebraic identity. Infinity, directional disagreement, and
nonzero residuals are NONZERO. Timeout / missing / failure is UNKNOWN,
never ZERO.
"""
from __future__ import annotations

from typing import Any, Optional

import sympy

from symbolic_compactification import parse_expression
from symbolic_compactification.models import AdapterError

ZERO = "ZERO"
NONZERO = "NONZERO"
UNKNOWN = "UNKNOWN"

_INF = (sympy.oo, -sympy.oo, sympy.zoo)


def parse_text(text: Any, symbols: list) -> Any:
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None
    try:
        return parse_expression(s, symbols)
    except (AdapterError, Exception):
        return None


def symbol_map(*exprs: Any) -> dict[str, sympy.Symbol]:
    out: dict[str, sympy.Symbol] = {}
    for e in exprs:
        for s in getattr(e, "free_symbols", set()) or []:
            out[str(s.name)] = s
    return out


def resolve_point(text: str, smap: dict[str, Any]) -> Any:
    key = str(text).strip()
    if not key:
        return None
    if key in smap:
        return smap[key]
    if key.lstrip("-").isdigit():
        return sympy.Integer(int(key))
    return None


def is_infinity(expr: Any) -> bool:
    if expr is None:
        return False
    if expr in _INF:
        return True
    inf = getattr(expr, "is_infinite", None)
    if inf is True:
        return True
    try:
        if expr.has(sympy.oo) or expr.has(-sympy.oo) or expr.has(sympy.zoo):
            return True
    except Exception:
        return False
    return False


def is_undefined(expr: Any) -> bool:
    if expr is None:
        return True
    if expr is sympy.nan:
        return True
    try:
        if expr.has(sympy.nan):
            return True
    except Exception:
        return True
    return False


def is_unevaluated_limit(expr: Any) -> bool:
    if expr is None:
        return False
    if isinstance(expr, sympy.Limit):
        return True
    try:
        return bool(isinstance(expr, sympy.Expr) and expr.has(sympy.Limit))
    except Exception:
        return False


def take_limit(expr: Any, var: Any, point: Any, dir: Optional[str] = None):
    if expr is None or var is None or point is None:
        return None
    try:
        if dir is None:
            got = sympy.limit(expr, var, point)
        else:
            got = sympy.limit(expr, var, point, dir=dir)
    except Exception:
        return None
    if is_unevaluated_limit(got):
        return None
    return got


def _is_exact_nonzero_number(expr: Any) -> bool:
    if expr is None:
        return False
    if is_infinity(expr):
        return True
    try:
        if expr.free_symbols:
            return False
    except Exception:
        return False
    try:
        if expr == 0:
            return False
    except Exception:
        return False
    try:
        if expr.is_number and expr != 0:
            return True
    except Exception:
        pass
    return expr != 0


def residual_verdict(left: Any, right: Any) -> tuple[str, Any]:
    """ZERO only on exact identity. Never numeric agreement."""
    if left is None or right is None:
        return UNKNOWN, None
    try:
        residual = left - right
    except Exception:
        return UNKNOWN, None
    try:
        if residual == 0 or left == right:
            return ZERO, residual
    except Exception:
        pass
    for transform in (
        (lambda e: e),
        sympy.expand,
        sympy.cancel,
        sympy.together,
        sympy.simplify,
    ):
        try:
            got = transform(residual)
        except Exception:
            continue
        try:
            if got == 0:
                return ZERO, got
        except Exception:
            pass
        if is_infinity(got) or is_undefined(got):
            return NONZERO, got
        if _is_exact_nonzero_number(got):
            return NONZERO, got
        try:
            cancelled = sympy.cancel(sympy.together(got))
            if cancelled == 0:
                return ZERO, cancelled
        except Exception:
            pass
        try:
            num, den = sympy.fraction(sympy.together(got))
            num_e = sympy.expand(sympy.cancel(num))
            if num_e == 0:
                return ZERO, got
            den_e = sympy.expand(den)
            if den_e == 0:
                continue
            try:
                poly = sympy.Poly(num_e, domain="QQ")
            except Exception:
                continue
            if poly.is_zero:
                return ZERO, got
            return NONZERO, got
        except Exception:
            pass
    try:
        expanded = sympy.expand(sympy.cancel(residual))
        if expanded == 0:
            return ZERO, expanded
        if is_infinity(expanded) or is_undefined(expanded):
            return NONZERO, expanded
        poly = sympy.Poly(expanded, domain="QQ")
        if poly.is_zero:
            return ZERO, expanded
        return NONZERO, expanded
    except Exception:
        pass
    return UNKNOWN, residual


def substitute_or_limit(expr: Any, var: Any, point: Any) -> tuple[Any, str]:
    """Prefer cancelled substitution when the denominator is nonzero."""
    if expr is None or var is None or point is None:
        return None, "missing"
    try:
        cancelled = sympy.cancel(expr)
    except Exception:
        cancelled = expr
    try:
        sub = cancelled.xreplace({var: point})
    except Exception:
        sub = None
    if (
        sub is not None
        and not is_undefined(sub)
        and not is_infinity(sub)
    ):
        try:
            den = sympy.denom(sympy.together(cancelled))
            den_at = sympy.expand(den.xreplace({var: point}))
            if den_at != 0:
                return sub, "substitute"
        except Exception:
            return sub, "substitute"
    two = take_limit(expr, var, point)
    if two is None:
        return None, "limit_failed"
    return two, "limit"
