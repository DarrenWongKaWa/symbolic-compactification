"""Multivariate series CONTROL for iterated-limit toys.

Not a verifier. Iterated limits are not joint limits. If ops exceed
``OPS_CAP`` or a series/limit step fails, return None / commuting=None
(UNKNOWN). Never a family certificate.
"""
from __future__ import annotations

from typing import Any, Optional

import sympy

OPS_CAP = 40
CHAR_CAP = 2048
SERIES_ORDERS = (1, 2, 4, 6)
LHOPITAL_ROUNDS = 4
UNKNOWN = "UNKNOWN"
COMPARED = "COMPARED"
INF_ORDER = 10**9

_NONFINITE = (
    sympy.nan,
    sympy.zoo,
    sympy.oo,
    sympy.S.NaN,
    sympy.S.ComplexInfinity,
    sympy.S.Infinity,
    sympy.S.NegativeInfinity,
)
_PROBE = (sympy.Integer(2), sympy.Integer(3), sympy.Integer(5))

_NOTE_COMPARED = (
    "CONTROL only, not a verifier; iterated limits are not joint limits "
    "and must not be read as a family certificate."
)
_NOTE_ORDER = (
    "order-dependent iterated limits; CONTROL only, not a verifier; "
    "not a family certificate."
)
_NOTE_UNKNOWN = (
    "UNKNOWN: ops cap or series failure; CONTROL only, not a verifier; "
    "never a family certificate."
)


def iterated_limits(expr: Any, steps: Any) -> Optional[sympy.Expr]:
    """Apply one-parameter limits in the given order.

    ``steps`` is a sequence of ``(variable, point)``. Returns the finite
    value, or ``None`` on size-guard / parse / series failure.
    """
    try:
        return _iterated_limits(expr, steps)
    except Exception:
        return None


def _iterated_limits(expr: Any, steps: Any) -> Optional[sympy.Expr]:
    current = _as_expr(expr)
    if current is None:
        return None
    parsed = _parse_steps(steps, current)
    if not parsed:
        return None
    if _too_large(current):
        return None
    for var, point in parsed:
        current = _one_parameter_limit(current, var, point)
        if current is None:
            return None
        if _too_large(current):
            return None
    return current


def multivariate_control(expr: Any, vars_and_points: Any) -> dict[str, Any]:
    """Compare iterated-limit orders on a small toy.

    Returns ``commuting`` True/False, or None when the comparison is
    UNKNOWN. ``order_a`` follows ``vars_and_points``; ``order_b`` is the
    reversed order. Does not certify a family.
    """
    try:
        return _multivariate_control(expr, vars_and_points)
    except Exception:
        return _unknown(ops=None, extra="exception")


def _multivariate_control(expr: Any, vars_and_points: Any) -> dict[str, Any]:
    parsed_expr = _as_expr(expr)
    if parsed_expr is None:
        return _unknown(ops=None, extra="unparsed")
    ops = _count_ops(parsed_expr)
    if _too_large(parsed_expr):
        return _unknown(ops=ops, extra="ops_cap")
    parsed = _parse_steps(vars_and_points, parsed_expr)
    if not parsed:
        return _unknown(ops=ops, extra="bad_steps")

    order_a_steps = parsed
    order_b_steps = list(reversed(parsed))
    val_a = iterated_limits(parsed_expr, order_a_steps)
    val_b = iterated_limits(parsed_expr, order_b_steps)
    agree = _values_equal(val_a, val_b) if val_a is not None and val_b is not None else None

    mixed = _mixed_derivatives_agree(parsed_expr, parsed)
    cross = _cross_terms_agree(parsed_expr, parsed)

    if val_a is None or val_b is None or agree is None:
        return {
            "commuting": None,
            "order_a": val_a,
            "order_b": val_b,
            "note": _NOTE_UNKNOWN,
            "mixed_derivatives_agree": mixed,
            "cross_terms_agree": cross,
            "ops": ops,
            "status": UNKNOWN,
        }
    commuting = bool(agree)
    return {
        "commuting": commuting,
        "order_a": val_a,
        "order_b": val_b,
        "note": _NOTE_COMPARED if commuting else _NOTE_ORDER,
        "mixed_derivatives_agree": mixed,
        "cross_terms_agree": cross,
        "ops": ops,
        "status": COMPARED,
    }


def _unknown(*, ops: Optional[int], extra: str = "") -> dict[str, Any]:
    note = _NOTE_UNKNOWN
    if extra:
        note = f"{_NOTE_UNKNOWN} ({extra})"
    return {
        "commuting": None,
        "order_a": None,
        "order_b": None,
        "note": note,
        "mixed_derivatives_agree": None,
        "cross_terms_agree": None,
        "ops": ops,
        "status": UNKNOWN,
    }


def _as_expr(expr: Any) -> Optional[sympy.Expr]:
    if isinstance(expr, str):
        if len(expr) > CHAR_CAP:
            return None
        try:
            expr = sympy.sympify(expr)
        except (sympy.SympifyError, TypeError, ValueError):
            return None
        except Exception:
            return None
    if not isinstance(expr, sympy.Expr):
        try:
            expr = sympy.sympify(expr)
        except Exception:
            return None
    if not isinstance(expr, sympy.Expr):
        return None
    if getattr(expr, "is_Relational", False):
        return None
    return expr


def _as_symbol(var: Any, expr: sympy.Expr) -> Optional[sympy.Expr]:
    if isinstance(var, sympy.Expr) and var.is_symbol:
        return var
    if isinstance(var, str):
        if len(var) > CHAR_CAP:
            return None
        for s in expr.free_symbols:
            if str(s) == var:
                return s
        try:
            got = sympy.sympify(var)
        except Exception:
            return None
        if isinstance(got, sympy.Expr) and got.is_symbol:
            return got
        return None
    try:
        got = sympy.sympify(var)
    except Exception:
        return None
    if isinstance(got, sympy.Expr) and got.is_symbol:
        return got
    return None


def _as_point(point: Any, expr: sympy.Expr) -> Optional[sympy.Expr]:
    if isinstance(point, sympy.Expr):
        return point
    if isinstance(point, str):
        if len(point) > CHAR_CAP:
            return None
        for s in expr.free_symbols:
            if str(s) == point:
                return s
        try:
            return sympy.sympify(point)
        except Exception:
            return None
    try:
        got = sympy.sympify(point)
    except Exception:
        return None
    if isinstance(got, sympy.Expr):
        return got
    return None


def _parse_steps(
    steps: Any,
    expr: sympy.Expr,
) -> Optional[list[tuple[sympy.Expr, sympy.Expr]]]:
    if steps is None:
        return None
    if isinstance(steps, dict):
        items = list(steps.items())
    else:
        try:
            items = list(steps)
        except TypeError:
            return None
    if not items:
        return None
    out: list[tuple[sympy.Expr, sympy.Expr]] = []
    for item in items:
        if isinstance(item, dict):
            raw_var = item.get("variable", item.get("var"))
            raw_pt = item.get(
                "target_value",
                item.get("point", item.get("target")),
            )
        elif isinstance(item, (tuple, list)) and len(item) == 2:
            raw_var, raw_pt = item
        else:
            return None
        var = _as_symbol(raw_var, expr)
        point = _as_point(raw_pt, expr)
        if var is None or point is None:
            return None
        out.append((var, point))
    return out


def _count_ops(expr: sympy.Expr) -> int:
    try:
        return int(sympy.count_ops(expr, visual=False))
    except Exception:
        return OPS_CAP + 1


def _too_large(expr: sympy.Expr) -> bool:
    return _count_ops(expr) > OPS_CAP


def _is_finite(expr: Any) -> bool:
    if expr is None:
        return False
    if not isinstance(expr, sympy.Basic):
        try:
            expr = sympy.sympify(expr)
        except Exception:
            return False
    if any(expr == sentinel for sentinel in _NONFINITE):
        return False
    try:
        if expr.has(*_NONFINITE) or expr.has(sympy.nan):
            return False
    except Exception:
        return False
    if isinstance(expr, sympy.Limit) or expr.has(sympy.Limit):
        return False
    try:
        if expr.is_infinite is True:
            return False
    except Exception:
        pass
    return True


def _sure_zero(expr: sympy.Expr) -> Optional[bool]:
    if expr == 0:
        return True
    try:
        if expr.is_zero is True:
            return True
        if expr.is_zero is False:
            return False
    except Exception:
        pass
    try:
        expanded = sympy.expand(expr)
        if expanded == 0:
            return True
        ez = expanded.equals(0)
    except Exception:
        return None
    if ez is True:
        return True
    if ez is False:
        return False
    return None


def _values_equal(a: Any, b: Any) -> Optional[bool]:
    if a is None or b is None:
        return None
    if a == b:
        return True
    try:
        diff = sympy.expand(a - b)
    except Exception:
        return None
    if diff == 0:
        return True
    try:
        cancelled = sympy.cancel(sympy.together(diff))
        if cancelled == 0:
            return True
        diff = cancelled
    except Exception:
        pass
    if _count_ops(diff) > OPS_CAP:
        return None
    try:
        ez = diff.equals(0)
    except Exception:
        ez = None
    if ez is True:
        return True
    if ez is False:
        return False
    try:
        if diff.is_zero is False:
            return False
    except Exception:
        pass
    return _refute_by_probe(diff)


def _refute_by_probe(diff: sympy.Expr) -> Optional[bool]:
    """Exact rational probe may refute equality. Never confirms it."""
    free = tuple(sorted(diff.free_symbols, key=str))
    if not free:
        return None
    for i, z in enumerate(_PROBE):
        subs = {sym: _PROBE[(i + k) % len(_PROBE)] for k, sym in enumerate(free)}
        try:
            val = diff.xreplace(subs)
        except Exception:
            continue
        if not _is_finite(val):
            continue
        try:
            if val == 0 or val.is_zero is True:
                continue
            if val.is_zero is False:
                return False
            ez = val.equals(0)
        except Exception:
            continue
        if ez is False:
            return False
    return None


def _one_parameter_limit(
    expr: sympy.Expr,
    var: sympy.Expr,
    point: sympy.Expr,
) -> Optional[sympy.Expr]:
    if _too_large(expr):
        return None
    if var == point:
        return expr if _is_finite(expr) else None
    if not expr.has(var):
        return expr if _is_finite(expr) else None
    for step in (
        _step_substitution,
        _step_cancel,
        _step_valuation,
        _step_series,
        _step_lhopital,
    ):
        try:
            got = step(expr, var, point)
        except Exception:
            got = None
        if got is None:
            continue
        if not _is_finite(got):
            return None
        return got
    return None


def _step_substitution(
    expr: sympy.Expr,
    var: sympy.Expr,
    point: sympy.Expr,
) -> Optional[sympy.Expr]:
    try:
        val = expr.xreplace({var: point})
    except Exception:
        return None
    if _is_finite(val):
        return val
    return None


def _step_cancel(
    expr: sympy.Expr,
    var: sympy.Expr,
    point: sympy.Expr,
) -> Optional[sympy.Expr]:
    try:
        reduced = sympy.cancel(sympy.together(expr))
        val = reduced.xreplace({var: point})
    except Exception:
        return None
    if _is_finite(val):
        return val
    return None


def _poly_in(expr: sympy.Expr, t: sympy.Expr) -> Optional[sympy.Poly]:
    try:
        expanded = sympy.expand(expr)
        return sympy.Poly(expanded, t, domain=sympy.EX)
    except (sympy.PolynomialError, ValueError, TypeError, AttributeError):
        return None
    except Exception:
        return None


def _zero_order(expr: sympy.Expr, t: sympy.Expr, maxn: int = 8) -> Optional[int]:
    try:
        if sympy.expand(expr) == 0:
            return INF_ORDER
    except Exception:
        pass
    p = _poly_in(expr, t)
    if p is not None:
        if p.is_zero:
            return INF_ORDER
        return int(min(p.monoms())[0])
    cur = expr
    for k in range(maxn + 1):
        try:
            val = cur.xreplace({t: 0})
        except Exception:
            return None
        if not _is_finite(val):
            return None
        z = _sure_zero(val)
        if z is True:
            try:
                cur = sympy.diff(cur, t)
            except Exception:
                return None
            continue
        if z is False:
            return k
        return None
    return None


def _leading_coeff(expr: sympy.Expr, t: sympy.Expr, k: int) -> Optional[sympy.Expr]:
    p = _poly_in(expr, t)
    if p is not None:
        try:
            return p.nth(k)
        except Exception:
            return None
    try:
        cur = sympy.diff(expr, t, k) if k else expr
        val = cur.xreplace({t: 0})
        return sympy.cancel(val / sympy.factorial(k))
    except Exception:
        return None


def _step_valuation(
    expr: sympy.Expr,
    var: sympy.Expr,
    point: sympy.Expr,
) -> Optional[sympy.Expr]:
    t = sympy.Dummy("t")
    try:
        e = expr.xreplace({var: point + t})
        e = sympy.cancel(sympy.together(e))
        n, d = sympy.fraction(e)
    except Exception:
        return None
    vn = _zero_order(n, t)
    vd = _zero_order(d, t)
    if vn is None or vd is None:
        return None
    if vn >= INF_ORDER and vd >= INF_ORDER:
        return None
    if vn >= INF_ORDER:
        return sympy.Integer(0)
    if vd >= INF_ORDER:
        return None
    v = vn - vd
    if v > 0:
        return sympy.Integer(0)
    if v < 0:
        return sympy.zoo
    n_lead = _leading_coeff(n, t, vn)
    d_lead = _leading_coeff(d, t, vd)
    if n_lead is None or d_lead is None:
        return None
    if _sure_zero(d_lead) is True:
        return None
    try:
        cand = sympy.cancel(n_lead / d_lead)
    except Exception:
        return None
    if _is_finite(cand):
        return cand
    return None


def _series_constant(series_expr: sympy.Expr, var: sympy.Expr, point: sympy.Expr) -> Optional[sympy.Expr]:
    if not isinstance(series_expr, sympy.Expr) or series_expr.has(sympy.Limit):
        return None
    try:
        core = series_expr.removeO() if series_expr.has(sympy.Order) else series_expr
        const = sympy.expand(core.xreplace({var: point}))
    except Exception:
        return None
    if _is_finite(const):
        return const
    if const == sympy.zoo or (isinstance(const, sympy.Expr) and const.has(sympy.zoo)):
        return sympy.zoo
    return None


def _step_series(
    expr: sympy.Expr,
    var: sympy.Expr,
    point: sympy.Expr,
) -> Optional[sympy.Expr]:
    for nterms in SERIES_ORDERS:
        try:
            s = expr.series(var, point, nterms)
        except Exception:
            s = None
        const = _series_constant(s, var, point) if s is not None else None
        if const is not None:
            return const
    t = sympy.Dummy("t")
    try:
        e = expr.xreplace({var: point + t})
    except Exception:
        return None
    for nterms in SERIES_ORDERS:
        try:
            s = e.series(t, 0, nterms)
        except Exception:
            continue
        const = _series_constant(s, t, sympy.Integer(0))
        if const is not None:
            return const
    return None


def _step_lhopital(
    expr: sympy.Expr,
    var: sympy.Expr,
    point: sympy.Expr,
) -> Optional[sympy.Expr]:
    try:
        n, d = sympy.fraction(sympy.together(expr))
    except Exception:
        return None
    for _ in range(LHOPITAL_ROUNDS):
        try:
            n0 = n.xreplace({var: point})
            d0 = d.xreplace({var: point})
        except Exception:
            return None
        nz = _sure_zero(n0)
        dz = _sure_zero(d0)
        if nz is True and dz is True:
            try:
                n = sympy.diff(n, var)
                d = sympy.diff(d, var)
            except Exception:
                return None
            continue
        if dz is True:
            return None
        if nz is False and dz is False and _is_finite(n0) and _is_finite(d0):
            try:
                cand = sympy.cancel(n0 / d0)
            except Exception:
                return None
            if _is_finite(cand):
                return cand
            return None
        return None
    try:
        n0 = n.xreplace({var: point})
        d0 = d.xreplace({var: point})
    except Exception:
        return None
    if _is_finite(n0) and _is_finite(d0) and _sure_zero(d0) is False:
        try:
            cand = sympy.cancel(n0 / d0)
        except Exception:
            return None
        if _is_finite(cand):
            return cand
    return None


def _mixed_derivatives_agree(
    expr: sympy.Expr,
    steps: list[tuple[sympy.Expr, sympy.Expr]],
) -> Optional[bool]:
    if len(steps) < 2:
        return None
    x, _px = steps[0]
    y, _py = steps[1]
    if x == y:
        return None
    try:
        dxy = sympy.diff(expr, x, y)
        dyx = sympy.diff(expr, y, x)
    except Exception:
        return None
    if _too_large(dxy) or _too_large(dyx):
        return None
    return _values_equal(dxy, dyx)


def _cross_terms_agree(
    expr: sympy.Expr,
    steps: list[tuple[sympy.Expr, sympy.Expr]],
) -> Optional[bool]:
    """Compare truncated iterated series in both orders (cross terms)."""
    if len(steps) < 2:
        return None
    x, x0 = steps[0]
    y, y0 = steps[1]
    if x == y:
        return None
    t = sympy.Dummy("t")
    u = sympy.Dummy("u")
    try:
        e = expr.xreplace({x: x0 + t, y: y0 + u})
    except Exception:
        return None
    if _too_large(e):
        return None
    nterms = 4
    try:
        s_tu = e.series(t, 0, nterms)
        s_ut = e.series(u, 0, nterms)
        if not isinstance(s_tu, sympy.Expr) or not isinstance(s_ut, sympy.Expr):
            return None
        if s_tu.has(sympy.Limit) or s_ut.has(sympy.Limit):
            return None
        a = s_tu.removeO() if s_tu.has(sympy.Order) else s_tu
        b = s_ut.removeO() if s_ut.has(sympy.Order) else s_ut
        a = a.series(u, 0, nterms)
        b = b.series(t, 0, nterms)
        if not isinstance(a, sympy.Expr) or not isinstance(b, sympy.Expr):
            return None
        if a.has(sympy.Limit) or b.has(sympy.Limit):
            return None
        a = a.removeO() if a.has(sympy.Order) else a
        b = b.removeO() if b.has(sympy.Order) else b
    except Exception:
        return None
    return _values_equal(a, b)
