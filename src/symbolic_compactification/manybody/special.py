"""Special-function rewrites that the exact verifier cannot find on its own.

Finite-temperature formulas mix two representations of the same object:
digamma functions of 1/2 +- i beta (e - mu)/(2 pi) and Fermi / tanh / exp
forms. They are linked by the reflection formula

    psi(1 - z) - psi(z) = pi cot(pi z),

differentiated k times:

    psi^(k)(1/2 + u) = (-1)^k [ psi^(k)(1/2 - u) + pi d^k/dz^k cot(pi z) |_{z = 1/2 - u} ].

``reflect_polygamma`` applies this to one member of each +-u pair (chosen by
a canonical ordering of u), so the pair collapses into trig terms, e.g.
psi(1/2 + i y) - psi(1/2 - i y) = i pi tanh(pi y). Both sides of the formula
are equal as meromorphic functions, so the rewrite never changes a value.
"""
from __future__ import annotations

import sympy

_Z = sympy.Dummy("z")
_HALF = sympy.Rational(1, 2)


def _rewrite(order: sympy.Expr, argument: sympy.Expr) -> sympy.Expr:
    u = sympy.expand(argument - _HALF)
    if u == 0 or not order.is_Integer or order < 0:
        return sympy.polygamma(order, argument)
    # rewrite only the canonically "positive" member of a +-u pair
    if not (sympy.expand(-u).sort_key() < u.sort_key()):
        return sympy.polygamma(order, argument)
    k = int(order)
    cot = sympy.diff(sympy.cot(sympy.pi * _Z), _Z, k).subs(_Z, _HALF - u)
    return (-1) ** k * (sympy.polygamma(k, _HALF - u) + sympy.pi * cot)


def reflect_polygamma(expr: sympy.Expr) -> sympy.Expr:
    """Canonicalize psi^(k)(1/2 + u) against psi^(k)(1/2 - u)."""
    expr = expr.replace(lambda e: isinstance(e, sympy.digamma),
                        lambda e: sympy.polygamma(0, e.args[0]))
    return expr.replace(lambda e: isinstance(e, sympy.polygamma),
                        lambda e: _rewrite(*e.args))
