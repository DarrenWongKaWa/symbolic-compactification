"""Exact local Laurent series of one polygamma atom.

Substitutes Dummy ``t = var - point`` and expands
``r(t)*polygamma(k, z(t))`` in ``t`` only. Typical atoms are <80 ops.
A singular argument ``z(t)`` at ``t = 0`` is empty with ``exact=False``.
Does not emit a hop verdict. Timeout/size-guard is empty, never ZERO.
"""
from __future__ import annotations

from typing import Any, Optional

import sympy

SERIES_OPS_CAP = 80
_SHIFT_TRIES = (8, 16, 32)
_PMIN_FLOOR = -64
_PMAX_CEIL = 24

_NONFINITE = (
    sympy.nan,
    sympy.zoo,
    sympy.oo,
    -sympy.oo,
    sympy.S.NaN,
    sympy.S.ComplexInfinity,
    sympy.S.Infinity,
    sympy.S.NegativeInfinity,
)


class LaurentCoeffs(dict):
    """Map integer power -> coefficient. ``exact`` is True iff series succeeded."""

    def __init__(self, coeffs: dict[int, sympy.Expr] | None = None, *, exact: bool = False):
        super().__init__()
        if coeffs:
            for power, coeff in coeffs.items():
                self[int(power)] = coeff
        self.exact = bool(exact)


def expand_polygamma_atom(
    term: Any,
    var: Any,
    point: Any,
    pmin: Any,
    pmax: Any,
) -> dict[int, sympy.Expr]:
    """Laurent coefficients of one polygamma atom in Dummy ``t = var - point``.

    Returns a ``dict[int, sympy.Expr]`` for powers ``pmin..pmax`` inclusive.
    The mapping has ``exact is True`` iff every returned coefficient is exact.
    On failure the dict is empty and ``exact is False``.
    """
    try:
        return _expand(term, var, point, pmin, pmax)
    except Exception:
        return LaurentCoeffs({}, exact=False)


def _expand(
    term: Any,
    var: Any,
    point: Any,
    pmin: Any,
    pmax: Any,
) -> LaurentCoeffs:
    expr = _as_expr(term)
    degeneration = _as_expr(var)
    target = _as_expr(point)
    lo = _as_int(pmin)
    hi = _as_int(pmax)
    if expr is None or degeneration is None or target is None:
        return LaurentCoeffs({}, exact=False)
    if lo is None or hi is None:
        return LaurentCoeffs({}, exact=False)
    if lo < _PMIN_FLOOR or hi > _PMAX_CEIL:
        return LaurentCoeffs({}, exact=False)
    if _count_ops(expr) > SERIES_OPS_CAP:
        return LaurentCoeffs({}, exact=False)
    if not expr.atoms(sympy.polygamma):
        return LaurentCoeffs({}, exact=False)

    t = sympy.Dummy("t")
    try:
        local = expr.xreplace({degeneration: target + t})
    except Exception:
        return LaurentCoeffs({}, exact=False)
    if not isinstance(local, sympy.Expr):
        return LaurentCoeffs({}, exact=False)
    if _count_ops(local) > SERIES_OPS_CAP:
        return LaurentCoeffs({}, exact=False)
    if not local.atoms(sympy.polygamma):
        return LaurentCoeffs({}, exact=False)
    if _any_argument_singular(local, t):
        return LaurentCoeffs({}, exact=False)

    nterms = hi + 1
    if nterms < 0:
        nterms = 0
    try:
        series_expr = local.series(t, 0, nterms)
    except Exception:
        return LaurentCoeffs({}, exact=False)
    if not isinstance(series_expr, sympy.Expr) or series_expr.has(sympy.Limit):
        return LaurentCoeffs({}, exact=False)
    core = series_expr.removeO() if series_expr.has(sympy.Order) else series_expr
    if not isinstance(core, sympy.Expr):
        return LaurentCoeffs({}, exact=False)
    if _has_t_log(core, t) or _pg_argument_depends_on_t(core, t):
        return LaurentCoeffs({}, exact=False)

    coeffs = _laurent_window(core, t, lo, hi)
    if coeffs is None:
        return LaurentCoeffs({}, exact=False)
    return LaurentCoeffs(coeffs, exact=True)


def _laurent_window(
    core: sympy.Expr,
    t: sympy.Expr,
    pmin: int,
    pmax: int,
) -> Optional[dict[int, sympy.Expr]]:
    if pmax < pmin:
        return {}
    needed = max(0, -pmin)
    poly = None
    shift_used = None
    for extra in _SHIFT_TRIES:
        shift = max(needed, extra)
        try:
            w = sympy.expand(sympy.together(core * t**shift))
            poly = sympy.Poly(w, t, domain=sympy.EX)
        except (sympy.PolynomialError, ValueError, TypeError, AttributeError):
            continue
        except Exception:
            return None
        shift_used = shift
        break
    if poly is None or shift_used is None:
        return None
    out: dict[int, sympy.Expr] = {}
    for k in range(pmin, pmax + 1):
        idx = k + shift_used
        if idx < 0:
            return None
        try:
            ck = poly.nth(idx)
        except Exception:
            return None
        ck = _as_expr(ck)
        if ck is None:
            return None
        if ck.has(t) or _nonfinite(ck):
            return None
        out[k] = ck
    return out


def _any_argument_singular(expr: sympy.Expr, t: sympy.Expr) -> bool:
    args: list[sympy.Expr] = []
    for pg in expr.atoms(sympy.polygamma):
        if len(pg.args) < 2:
            return True
        arg = pg.args[1]
        if not isinstance(arg, sympy.Expr):
            return True
        args.append(arg)
    if not args:
        return True
    return any(_argument_singular(z, t) for z in args)


def _argument_singular(z: sympy.Expr, t: sympy.Expr) -> bool:
    if not z.has(t):
        return False
    try:
        s = z.series(t, 0, 2)
    except Exception:
        return True
    if not isinstance(s, sympy.Expr) or s.has(sympy.Limit):
        return True
    core = s.removeO() if s.has(sympy.Order) else s
    if _has_t_log(core, t):
        return True
    try:
        sympy.Poly(sympy.expand(core), t, domain=sympy.EX)
    except Exception:
        return True
    return False


def _pg_argument_depends_on_t(expr: sympy.Expr, t: sympy.Expr) -> bool:
    for pg in expr.atoms(sympy.polygamma):
        if len(pg.args) < 2:
            return True
        arg = pg.args[1]
        if isinstance(arg, sympy.Expr) and arg.has(t):
            return True
    return False


def _has_t_log(expr: sympy.Expr, t: sympy.Expr) -> bool:
    try:
        logs = expr.atoms(sympy.log)
    except Exception:
        return True
    return any(isinstance(lg, sympy.Expr) and lg.has(t) for lg in logs)


def _nonfinite(expr: sympy.Expr) -> bool:
    try:
        if any(expr == sentinel for sentinel in _NONFINITE):
            return True
        if expr.has(*_NONFINITE):
            return True
    except Exception:
        pass
    try:
        if getattr(expr, "is_infinite", None) is True:
            return True
    except Exception:
        pass
    try:
        if getattr(expr, "is_nan", None) is True:
            return True
    except Exception:
        pass
    return False


def _count_ops(expr: sympy.Expr) -> int:
    try:
        return int(sympy.count_ops(expr, visual=False))
    except Exception:
        return SERIES_OPS_CAP + 1


def _as_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, sympy.Integer):
        return int(value)
    return None


def _as_expr(value: Any) -> Optional[sympy.Expr]:
    if isinstance(value, bool):
        return None
    if isinstance(value, sympy.Expr):
        return value
    if isinstance(value, int):
        return sympy.Integer(value)
    return None
