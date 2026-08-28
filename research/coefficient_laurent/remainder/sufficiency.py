"""Remainder sufficiency for a rational × polygamma Laurent atom.

Why series through t^0 is enough
--------------------------------
An atom is ``A(t) = R(t) * polygamma(n, z(t))`` with ``R`` rational and
``z(t) = α + β t`` affine in the degeneration coordinate ``t``. For
``n >= -1``, polygamma is meromorphic with poles only at nonpositive
integers of the argument (order ``n+1`` when ``n >= 0``). For
``n <= -2`` it is entire.

If ``α = z(0)`` is certified not a nonpositive integer, then
``polygamma(n, z(t))`` is holomorphic at ``t = 0``. All polar behaviour
of ``A`` at ``t = 0`` comes from ``R``, so a given pole order ``pmin``
is a lower bound on the valuation. The Laurent series

    A(t) = sum_{k = pmin}^{∞} c_k t^k

has a finite principal part. Truncation through the constant term leaves

    A(t) - sum_{k = pmin}^{0} c_k t^k = sum_{k >= 1} c_k t^k = O(t),

which is holomorphic and vanishes as ``t → 0``. LEVEL C therefore only
needs coefficients ``t^{pmin} … t^0``. Positive powers are remainder
and cannot affect a regularized limit (negative coefficients cancelled,
``t^0`` matched to the diagonal target).

If ``z(0)`` might be a polygamma pole, ``pmin`` may miss extra negative
powers of order up to ``n+1``. Then ``remainder_ok`` is False and the
remainder verdict is UNKNOWN (fail closed, not NONZERO).
"""
from __future__ import annotations

from typing import Any, Optional

import sympy

from research.coefficient_laurent.schema import UNKNOWN, ZERO

REQUIRED_PMAX = 0
CHAR_CAP = 4096
OPS_CAP = 80

SUFFICIENCY_REASON = (
    "If the affine argument z(t)=α+βt has α not a nonpositive integer, "
    "polygamma is holomorphic at t=0, so the atom is meromorphic with "
    "pole order at most the rational pmin. Series through t^0 leaves an "
    "O(t) holomorphic remainder that vanishes as t→0; LEVEL C needs "
    "only t^{pmin}…t^0. If z(0) might be a polygamma pole, remainder_ok "
    "is False and the remainder verdict is UNKNOWN."
)

_PARSE_LOCAL: dict[str, Any] = {
    "polygamma": sympy.polygamma,
    "PolyGamma": sympy.polygamma,
    "digamma": sympy.digamma,
    "psi": sympy.digamma,
    "gamma": sympy.gamma,
    "loggamma": sympy.loggamma,
    "pi": sympy.pi,
    "I": sympy.I,
    "E": sympy.E,
    "oo": sympy.oo,
    "exp": sympy.exp,
    "log": sympy.log,
    "sin": sympy.sin,
    "cos": sympy.cos,
    "Integer": sympy.Integer,
    "Rational": sympy.Rational,
}
if hasattr(sympy, "trigamma"):
    _PARSE_LOCAL["trigamma"] = sympy.trigamma


def remainder_ok(
    argument: Any,
    t: Any = None,
    *,
    pmin: Any = None,
    order: Any = None,
) -> bool:
    """True iff series through t^0 is a certified sufficient remainder.

    ``argument`` is the polygamma argument (affine in ``t``), a full
    atom ``R(t)*polygamma(n, z(t))``, a string, or a ``LaurentAtom``.
    False means the remainder verdict is UNKNOWN, not NONZERO.
    """
    try:
        return _remainder_ok(argument, t, pmin=pmin, order=order)
    except Exception:
        return False


def remainder_verdict(
    argument: Any,
    t: Any = None,
    *,
    pmin: Any = None,
    order: Any = None,
) -> str:
    """ZERO when remainder_ok, else UNKNOWN (never NONZERO)."""
    if remainder_ok(argument, t, pmin=pmin, order=order):
        return ZERO
    return UNKNOWN


def required_pmin(
    pmin: Any,
    argument: Any = None,
    t: Any = None,
    *,
    order: Any = None,
) -> Optional[int]:
    """Lowest Laurent power that LEVEL C must retain, or None if UNKNOWN.

    When ``remainder_ok``, polygamma adds no poles at ``t = 0``, so the
    given atom/rational pole order ``pmin`` is the lower end of the
    window ``t^{pmin} … t^0`` (see ``REQUIRED_PMAX``). If the argument
    at ``t = 0`` might be a polygamma pole, return None.
    """
    try:
        k = _as_int(pmin)
        if k is None:
            return None
        if argument is not None and not remainder_ok(
            argument, t, pmin=k, order=order
        ):
            return None
        return k
    except Exception:
        return None


def _remainder_ok(
    argument: Any,
    t: Any,
    *,
    pmin: Any,
    order: Any,
) -> bool:
    if pmin is not None and _as_int(pmin) is None:
        return False
    expr, t_sym = _coerce_argument(argument, t)
    if expr is None or t_sym is None:
        return False
    if _too_large(expr):
        return False
    checks = _unit_checks(expr, t_sym, order)
    if not checks:
        return False
    return all(checks)


def _unit_checks(
    expr: sympy.Expr,
    t: sympy.Symbol,
    order: Any,
) -> list[bool] | None:
    units = _pg_units(expr, order)
    if units is None:
        return None
    out: list[bool] = []
    for z, n in units:
        if _too_large(z):
            return None
        affine = _affine_coeffs(z, t)
        if affine is None:
            return None
        alpha, _beta = affine
        poles = _order_has_poles(n)
        if poles is False:
            out.append(True)
            continue
        kind = _classify_alpha(alpha)
        if kind == "regular":
            out.append(True)
            continue
        return None
    return out


def _pg_units(
    expr: sympy.Expr, order: Any
) -> list[tuple[sympy.Expr, Any]] | None:
    units: list[tuple[sympy.Expr, Any]] = []
    for pg in expr.atoms(sympy.polygamma):
        if len(pg.args) < 2:
            return None
        units.append((pg.args[1], pg.args[0]))
    if hasattr(sympy, "digamma"):
        for fn in expr.atoms(sympy.digamma):
            if not fn.args:
                return None
            units.append((fn.args[0], 0))
    if hasattr(sympy, "trigamma"):
        for fn in expr.atoms(sympy.trigamma):
            if not fn.args:
                return None
            units.append((fn.args[0], 1))
    if hasattr(sympy, "loggamma"):
        for fn in expr.atoms(sympy.loggamma):
            if not fn.args:
                return None
            units.append((fn.args[0], -1))
    if units:
        return units
    return [(expr, order)]


def _order_has_poles(n: Any) -> Optional[bool]:
    """True: poles at Z_<=0; False: entire; None: unknown."""
    if n is None:
        return None
    k = _as_int(n)
    if k is None:
        return None
    if k <= -2:
        return False
    return True


def _affine_coeffs(
    z: sympy.Expr, t: sympy.Symbol
) -> Optional[tuple[sympy.Expr, sympy.Expr]]:
    try:
        expr = sympy.together(sympy.expand(z))
        num, den = sympy.fraction(expr)
        num = sympy.expand(num)
        den = sympy.expand(den)
        if den == 0 or den.has(t):
            return None
        if not num.has(t):
            return (num / den, sympy.Integer(0))
        poly = sympy.Poly(num, t, domain=sympy.EX)
        if poly.degree() > 1:
            return None
        beta = (poly.nth(1) if poly.degree() >= 1 else sympy.Integer(0)) / den
        alpha = poly.nth(0) / den
        if alpha.has(t) or beta.has(t):
            return None
        return (alpha, beta)
    except Exception:
        return None


def _classify_alpha(alpha: sympy.Expr) -> str:
    """``pole`` | ``regular`` | ``unknown`` relative to Z_<=0."""
    try:
        a = sympy.simplify(sympy.expand(alpha))
    except Exception:
        return "unknown"
    if not isinstance(a, sympy.Basic):
        return "unknown"
    if a.free_symbols:
        return "unknown"
    if a in (sympy.nan, sympy.zoo, sympy.oo, sympy.S.NegativeInfinity):
        return "unknown"
    try:
        if a.is_infinite:
            return "unknown"
    except Exception:
        return "unknown"
    if isinstance(a, (sympy.Float, float)):
        return "unknown"

    re, im = sympy.simplify(sympy.re(a)), sympy.simplify(sympy.im(a))
    if im.free_symbols or re.free_symbols:
        return "unknown"
    if im != 0 and im.is_zero is not True:
        if isinstance(im, (sympy.Float, float)):
            return "unknown"
        if im.is_number and im != 0:
            return "regular"
        if im.is_zero is False:
            return "regular"
        return "unknown"

    x = re
    if isinstance(x, (sympy.Float, float)):
        return "unknown"
    if isinstance(x, sympy.Integer) or x.is_Integer is True:
        try:
            return "pole" if int(x) <= 0 else "regular"
        except Exception:
            return "unknown"
    if x.is_rational is True:
        try:
            q = int(x.q)
            if q != 1:
                return "regular"
            return "pole" if int(x.p) <= 0 else "regular"
        except Exception:
            return "unknown"
    if x.is_integer is False:
        return "regular"
    try:
        s = sympy.simplify(sympy.sin(sympy.pi * x))
        if s == 0:
            if x.is_positive is True:
                return "regular"
            if x.is_nonpositive is True:
                return "pole"
            return "unknown"
        if s != 0 and s.is_number:
            return "regular"
    except Exception:
        return "unknown"
    return "unknown"


def _coerce_argument(
    argument: Any, t: Any
) -> tuple[Optional[sympy.Expr], Optional[sympy.Symbol]]:
    argument, t = _unwrap_atom(argument, t)
    t_sym = _as_symbol(t) if t is not None else None
    expr = _as_expr(argument, t_sym)
    if expr is None:
        return None, None
    if t_sym is None:
        t_sym = _infer_t(expr)
    if t_sym is None:
        return None, None
    return expr, t_sym


def _unwrap_atom(argument: Any, t: Any) -> tuple[Any, Any]:
    if isinstance(argument, dict):
        inner = argument.get("argument", argument)
        if t is None:
            t = argument.get("degeneration_variable") or argument.get("t")
        return inner, t
    arg_txt = getattr(argument, "argument", None)
    if isinstance(arg_txt, str) and not isinstance(argument, sympy.Basic):
        if t is None:
            t = getattr(argument, "degeneration_variable", None) or getattr(
                argument, "t", None
            )
        return arg_txt, t
    return argument, t


def _as_symbol(t: Any) -> Optional[sympy.Symbol]:
    if isinstance(t, sympy.Symbol):
        return t
    if isinstance(t, str) and t:
        if len(t) > 64:
            return None
        return sympy.Symbol(t)
    return None


def _infer_t(expr: sympy.Expr) -> Optional[sympy.Symbol]:
    frees = [s for s in expr.free_symbols if isinstance(s, sympy.Symbol)]
    if len(frees) == 1:
        return frees[0]
    if len(frees) == 0:
        return sympy.Dummy("t")
    return None


def _as_expr(argument: Any, t: Optional[sympy.Symbol]) -> Optional[sympy.Expr]:
    if argument is None:
        return None
    if isinstance(argument, bool):
        return None
    if isinstance(argument, (int, sympy.Integer)):
        return sympy.Integer(argument)
    if isinstance(argument, sympy.Basic):
        return argument
    if isinstance(argument, str):
        if len(argument) > CHAR_CAP:
            return None
        local = dict(_PARSE_LOCAL)
        if t is not None:
            local[str(t)] = t
            local["t"] = t
        else:
            local["t"] = sympy.Symbol("t")
        try:
            out = sympy.parse_expr(
                argument, local_dict=local, evaluate=True
            )
        except Exception:
            return None
        if isinstance(out, sympy.Expr):
            return out
        return None
    return None


def _as_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, sympy.Integer):
        return int(value)
    try:
        n = sympy.Integer(value)
        if n == value:
            return int(n)
    except Exception:
        return None
    return None


def _too_large(expr: sympy.Expr) -> bool:
    try:
        return int(sympy.count_ops(expr, visual=False)) > OPS_CAP
    except Exception:
        return True
