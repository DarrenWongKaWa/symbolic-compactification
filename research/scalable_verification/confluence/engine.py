"""Typed check ``lim_{y -> x} F = G``.

Cheap cascade first. Never convert timeout or size-guard to ZERO.
``sympy.limit`` runs only under ``run_with_budget`` (process, ``<= 8s``)
and is skipped when ``count_ops(F) > 80``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

import sympy

from research.representation_invention.dd import newton_first, repeated_diagonal
from research.scalable_verification.api import NONZERO, UNKNOWN, ZERO
from symbolic_compactification.budgets import BudgetExceeded, run_with_budget

LIMIT_SECONDS = 8.0
LIMIT_OPS_CAP = 80
LIMIT_MODE = "process"
_LHOPITAL_ROUNDS = 4
_SERIES_ORDERS = (1, 2, 4, 6)
_VALUATION_MAXN = 8
_INF_ORDER = 10**9

_NONFINITE = (
    sympy.nan,
    sympy.zoo,
    sympy.oo,
    sympy.S.NaN,
    sympy.S.ComplexInfinity,
    sympy.S.Infinity,
    sympy.S.NegativeInfinity,
)


@dataclass(frozen=True)
class ConfluenceResult:
    """Verdict of ``lim_{y -> x} F = G`` plus cascade provenance."""

    verdict: str
    provenance: str
    steps: tuple[str, ...]
    witness: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _count_ops(expr: sympy.Expr) -> int:
    try:
        return int(sympy.count_ops(expr, visual=False))
    except Exception:
        return LIMIT_OPS_CAP + 1


def _ops_too_large(expr: sympy.Expr) -> bool:
    return _count_ops(expr) > LIMIT_OPS_CAP


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


def _expr_equal(a: sympy.Expr, b: sympy.Expr) -> Optional[bool]:
    if a == b:
        return True
    try:
        d = sympy.expand(a - b)
    except Exception:
        return None
    if d == 0:
        return True
    if _count_ops(d) > LIMIT_OPS_CAP:
        return None
    try:
        ez = d.equals(0)
    except Exception:
        ez = None
    if ez is True:
        return True
    if ez is False:
        return False
    return None


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
    return _expr_equal(expr, sympy.Integer(0))


def _poly_in(expr: sympy.Expr, t: sympy.Expr) -> Optional[sympy.Poly]:
    try:
        expanded = sympy.expand(expr)
        return sympy.Poly(expanded, t, domain=sympy.EX)
    except (sympy.PolynomialError, ValueError, TypeError, AttributeError):
        return None
    except Exception:
        return None


def _zero_order(expr: sympy.Expr, t: sympy.Expr, maxn: int = _VALUATION_MAXN) -> Optional[int]:
    try:
        if sympy.expand(expr) == 0:
            return _INF_ORDER
    except Exception:
        pass
    p = _poly_in(expr, t)
    if p is not None:
        if p.is_zero:
            return _INF_ORDER
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
    cur = expr
    try:
        if k:
            cur = sympy.diff(expr, t, k)
        val = cur.xreplace({t: 0})
        return sympy.cancel(val / sympy.factorial(k))
    except Exception:
        return None


def _unknown(steps: list[str], provenance: str, extra: Optional[str] = None) -> ConfluenceResult:
    if extra:
        steps.append(extra)
    return ConfluenceResult(UNKNOWN, provenance, tuple(steps), None)


def _adjudicate(
    candidate: sympy.Expr,
    G: sympy.Expr,
    step: str,
    steps: list[str],
    *,
    kind: str = "finite",
) -> Optional[ConfluenceResult]:
    if kind == "pole":
        if _is_finite(G):
            steps.append(f"{step}:pole")
            return ConfluenceResult(NONZERO, step, tuple(steps), "zoo")
        eq = _expr_equal(candidate, G)
        if eq is True:
            steps.append(f"{step}:ZERO")
            return ConfluenceResult(ZERO, step, tuple(steps), str(candidate))
        if eq is False:
            steps.append(f"{step}:NONZERO")
            return ConfluenceResult(NONZERO, step, tuple(steps), str(candidate))
        steps.append(f"{step}:pole_undecided")
        return None
    if not _is_finite(candidate):
        steps.append(f"{step}:not_finite")
        return None
    eq = _expr_equal(candidate, G)
    if eq is True:
        steps.append(f"{step}:ZERO")
        return ConfluenceResult(ZERO, step, tuple(steps), str(candidate))
    if eq is False:
        steps.append(f"{step}:NONZERO")
        return ConfluenceResult(NONZERO, step, tuple(steps), str(candidate))
    steps.append(f"{step}:undecided")
    return None


def _step_substitution(F: sympy.Expr, y: sympy.Expr, x: sympy.Expr) -> Optional[sympy.Expr]:
    try:
        val = F.xreplace({y: x})
    except Exception:
        return None
    if _is_finite(val):
        return val
    return None


def _step_together_cancel(F: sympy.Expr, y: sympy.Expr, x: sympy.Expr) -> Optional[sympy.Expr]:
    try:
        reduced = sympy.cancel(sympy.together(F))
        val = reduced.xreplace({y: x})
    except Exception:
        return None
    if _is_finite(val):
        return val
    return None


def _step_valuation(F: sympy.Expr, y: sympy.Expr, x: sympy.Expr) -> Optional[tuple[str, sympy.Expr]]:
    t = sympy.Dummy("t")
    try:
        e = F.xreplace({y: x + t})
        e = sympy.cancel(sympy.together(e))
        n, d = sympy.fraction(e)
    except Exception:
        return None
    vn = _zero_order(n, t)
    vd = _zero_order(d, t)
    if vn is None or vd is None:
        return None
    if vn >= _INF_ORDER and vd >= _INF_ORDER:
        return None
    if vn >= _INF_ORDER:
        return ("finite", sympy.Integer(0))
    if vd >= _INF_ORDER:
        return None
    v = vn - vd
    if v > 0:
        return ("finite", sympy.Integer(0))
    if v < 0:
        return ("pole", sympy.zoo)
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
        return ("finite", cand)
    return None


def _step_series(F: sympy.Expr, y: sympy.Expr, x: sympy.Expr) -> Optional[tuple[str, sympy.Expr]]:
    t = sympy.Dummy("t")
    try:
        e = F.xreplace({y: x + t})
    except Exception:
        return None
    for nterms in _SERIES_ORDERS:
        try:
            s = e.series(t, 0, nterms)
        except Exception:
            continue
        if not isinstance(s, sympy.Expr) or s.has(sympy.Limit):
            continue
        try:
            core = s.removeO() if s.has(sympy.Order) else s
            expanded = sympy.expand(core)
            n, d = sympy.fraction(sympy.together(expanded))
        except Exception:
            continue
        pn, pd = _poly_in(n, t), _poly_in(d, t)
        if pn is None or pd is None or pd.is_zero:
            continue
        if pn.is_zero:
            return ("finite", sympy.Integer(0))
        vn = int(min(pn.monoms())[0])
        vd = int(min(pd.monoms())[0])
        v = vn - vd
        if v < 0:
            return ("pole", sympy.zoo)
        if v > 0:
            return ("finite", sympy.Integer(0))
        n_lead = pn.nth(vn)
        d_lead = pd.nth(vd)
        if _sure_zero(d_lead) is True:
            continue
        try:
            cand = sympy.cancel(n_lead / d_lead)
        except Exception:
            continue
        if _is_finite(cand):
            return ("finite", cand)
    return None


def _step_lhopital(F: sympy.Expr, y: sympy.Expr, x: sympy.Expr) -> Optional[tuple[str, sympy.Expr]]:
    try:
        n, d = sympy.fraction(sympy.together(F))
    except Exception:
        return None
    for _ in range(_LHOPITAL_ROUNDS):
        try:
            n0 = n.xreplace({y: x})
            d0 = d.xreplace({y: x})
        except Exception:
            return None
        nz = _sure_zero(n0)
        dz = _sure_zero(d0)
        if nz is True and dz is True:
            try:
                n = sympy.diff(n, y)
                d = sympy.diff(d, y)
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
                return ("finite", cand)
            return None
        return None
    try:
        n0 = n.xreplace({y: x})
        d0 = d.xreplace({y: x})
    except Exception:
        return None
    if _is_finite(n0) and _is_finite(d0) and _sure_zero(d0) is False:
        try:
            cand = sympy.cancel(n0 / d0)
        except Exception:
            return None
        if _is_finite(cand):
            return ("finite", cand)
    return None


def _step_newton_first_dd(F: sympy.Expr, y: sympy.Expr, x: sympy.Expr) -> Optional[sympy.Expr]:
    if x == y:
        return None
    try:
        delta = sympy.cancel(sympy.together(F * (x - y)))
    except Exception:
        return None
    try:
        diag = delta.xreplace({y: x})
    except Exception:
        return None
    if _sure_zero(diag) is not True:
        return None
    try:
        dx = sympy.diff(delta, x)
    except Exception:
        return None
    if y in dx.free_symbols:
        try:
            residual = dx - dx.xreplace({y: x})
        except Exception:
            return None
        if _sure_zero(residual) is not True:
            return None
    z = sympy.Dummy("z")
    c = sympy.Dummy("c")
    f = delta.xreplace({x: z, y: c})
    try:
        nf = newton_first(f, z, x, y)
    except Exception:
        return None
    if _expr_equal(nf, F) is not True:
        return None
    try:
        return repeated_diagonal(f, z, x)
    except Exception:
        return None


def _sympy_limit_fn(expr: sympy.Expr, var: sympy.Expr, point: sympy.Expr) -> sympy.Expr:
    # Two-sided: confluence does not prefer a one-sided approach direction.
    return sympy.limit(expr, var, point, dir="+-")


def _budgeted_sympy_limit(F: sympy.Expr, y: sympy.Expr, x: sympy.Expr) -> sympy.Expr:
    seconds = min(float(LIMIT_SECONDS), 8.0)
    if seconds <= 0:
        raise BudgetExceeded("confluence_limit", seconds)
    return run_with_budget(
        _sympy_limit_fn,
        (F, y, x),
        seconds=seconds,
        mode=LIMIT_MODE,
        operation="confluence_limit",
    )


def _step_sympy_limit(
    F: sympy.Expr,
    y: sympy.Expr,
    x: sympy.Expr,
    steps: list[str],
) -> tuple[Optional[tuple[str, sympy.Expr]], Optional[ConfluenceResult]]:
    """Guarded ``sympy.limit``. Timeout / size-guard → UNKNOWN, never ZERO."""
    if _ops_too_large(F):
        steps.append("sympy.limit:skip_count_ops")
        return None, ConfluenceResult(
            UNKNOWN, "sympy.limit:skip_count_ops", tuple(steps), None,
        )
    try:
        lim = _budgeted_sympy_limit(F, y, x)
    except BudgetExceeded:
        steps.append("sympy.limit:timeout")
        return None, ConfluenceResult(
            UNKNOWN, "sympy.limit:timeout", tuple(steps), None,
        )
    except ValueError as exc:
        steps.append("sympy.limit:ValueError")
        if "does not exist" in str(exc).lower():
            return ("pole", sympy.zoo), None
        return None, None
    except Exception as exc:
        steps.append(f"sympy.limit:{type(exc).__name__}")
        return None, None
    if isinstance(lim, sympy.Limit) or (isinstance(lim, sympy.Expr) and lim.has(sympy.Limit)):
        steps.append("sympy.limit:unevaluated")
        return None, None
    if not _is_finite(lim):
        return ("pole", sympy.zoo), None
    return ("finite", lim), None


def check_limit(
    F: sympy.Expr,
    y: sympy.Expr,
    x: sympy.Expr,
    G: sympy.Expr,
) -> ConfluenceResult:
    """Typed check that ``lim_{y -> x} F = G``. Timeout is UNKNOWN, never ZERO."""
    steps: list[str] = []
    try:
        if not isinstance(F, sympy.Basic):
            F = sympy.sympify(F)
        if not isinstance(G, sympy.Basic):
            G = sympy.sympify(G)
        if not isinstance(y, sympy.Basic):
            y = sympy.sympify(y)
        if not isinstance(x, sympy.Basic):
            x = sympy.sympify(x)
    except Exception:
        return _unknown(steps, "UNKNOWN", "parse:failed")

    try:
        sub = _step_substitution(F, y, x)
        if sub is not None:
            got = _adjudicate(sub, G, "substitution", steps)
            if got is not None:
                return got
        else:
            steps.append("substitution:not_finite")

        tc = _step_together_cancel(F, y, x)
        if tc is not None:
            got = _adjudicate(tc, G, "together_cancel", steps)
            if got is not None:
                return got
        else:
            steps.append("together_cancel:not_finite")

        val = _step_valuation(F, y, x)
        if val is not None:
            kind, cand = val
            got = _adjudicate(cand, G, "valuation", steps, kind=kind)
            if got is not None:
                return got
        else:
            steps.append("valuation:failed")

        ser = _step_series(F, y, x)
        if ser is not None:
            kind, cand = ser
            got = _adjudicate(cand, G, "series", steps, kind=kind)
            if got is not None:
                return got
        else:
            steps.append("series:failed")

        lh = _step_lhopital(F, y, x)
        if lh is not None:
            kind, cand = lh
            got = _adjudicate(cand, G, "lhopital", steps, kind=kind)
            if got is not None:
                return got
        else:
            steps.append("lhopital:failed")

        nd = _step_newton_first_dd(F, y, x)
        if nd is not None:
            got = _adjudicate(nd, G, "newton_first_dd", steps)
            if got is not None:
                return got
        else:
            steps.append("newton_first_dd:failed")

        lim, early = _step_sympy_limit(F, y, x, steps)
        if early is not None:
            return early
        if lim is not None:
            kind, cand = lim
            got = _adjudicate(cand, G, "sympy.limit", steps, kind=kind)
            if got is not None:
                return got

        return _unknown(steps, "UNKNOWN")
    except BudgetExceeded:
        steps.append("timeout")
        return ConfluenceResult(UNKNOWN, "timeout", tuple(steps), None)
    except Exception as exc:
        steps.append(f"error:{type(exc).__name__}")
        return ConfluenceResult(UNKNOWN, "UNKNOWN", tuple(steps), None)
