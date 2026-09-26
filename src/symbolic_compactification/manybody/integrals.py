"""Numerical support for real-frequency Green's-function integrals.

Identities such as  int dw nF(w) G^R(w) G^A(w)  ->  digamma closed forms
come from closing a contour through the Fermi-function poles. The engine does
not evaluate these integrals symbolically. This module compares the claimed
closed form with high-precision quadrature at deterministic rational sample
points, splitting the real line at the real parts of the integrand's poles.
The result is NUMERICAL_SUPPORT: it can expose a wrong sign or factor, but
it never certifies the identity.
"""
from __future__ import annotations

from typing import Any

import mpmath
import sympy

from ..models import AdapterError
from ._common import (NUMERIC_AGREES, NUMERIC_DISAGREES, NUMERIC_UNAVAILABLE,
                      Namespace, expand_distributions, sample_points)

NUMERICAL_SUPPORT = "NUMERICAL_SUPPORT"


def _breakpoints(integrand: sympy.Expr, w: sympy.Symbol, point: dict) -> list:
    _, den = sympy.fraction(sympy.together(integrand.subs(point)))
    cuts = set()
    for factor in sympy.Mul.make_args(den):
        base, _ = factor.as_base_exp()
        if base.has(w) and base.is_polynomial(w):
            for root in sympy.Poly(base, w).nroots(n=30):
                cuts.add(mpmath.mpf(str(sympy.re(root))))
    return sorted(cuts)


def check_frequency_integral(integrand: str, claim: str, *, variable: str,
                             symbols: Any, functions: Any = None, beta: str | None = None,
                             prefactor: str = "1", positive: tuple[str, ...] = (),
                             count: int = 3,
                             tolerance: str = "1e-10") -> dict:
    """Compare  prefactor * int_R integrand dw  with the claimed closed form."""
    try:
        space = Namespace(symbols, functions)
        w = space.symbol(variable)
        b = space.symbol(beta) if beta else None
        f = space.parse(integrand)
        target = space.parse(claim)
        pre = space.parse(prefactor)
        pos = space.positives(tuple(positive))
        if b is not None:
            f, target = expand_distributions(f, b), expand_distributions(target, b)
    except AdapterError as exc:
        return {"status": NUMERICAL_SUPPORT, "numeric": NUMERIC_UNAVAILABLE,
                "reasons": [f"PARSE_FAILED:{exc.code}"]}
    free = (f.free_symbols | target.free_symbols | pre.free_symbols) - {w}
    positive_syms = ((b,) if b is not None else ()) + pos
    worst = mpmath.mpf(0)
    try:
        with mpmath.workdps(30):
            for point in sample_points(free, positive=positive_syms, count=count):
                g = sympy.lambdify(w, (pre * f).subs(point), "mpmath")
                nodes = [-mpmath.inf, *_breakpoints(f, w, point), mpmath.inf]
                value = mpmath.quad(g, nodes)
                exact = mpmath.mpmathify(complex(sympy.N(target.subs(point), 30)))
                worst = max(worst, abs(value - exact) / max(mpmath.mpf(1), abs(exact)))
    except (ValueError, TypeError, ZeroDivisionError, ArithmeticError):
        return {"status": NUMERICAL_SUPPORT, "numeric": NUMERIC_UNAVAILABLE, "reasons": []}
    agrees = worst < mpmath.mpf(tolerance)
    return {"status": NUMERICAL_SUPPORT,
            "numeric": NUMERIC_AGREES if agrees else NUMERIC_DISAGREES,
            "points": count, "max_rel_diff": mpmath.nstr(worst, 3), "reasons": []}
