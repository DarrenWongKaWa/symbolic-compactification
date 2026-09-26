"""Identities with divided differences, derivatives and series coefficients.

Claim language (on top of the usual expression syntax):
  DD_f(x0, x1, ..., xr)   divided difference of a declared function f;
                          repeated nodes use the confluent limit
  D_f(k, x)               k-th derivative of f at x (k a literal integer)
Declared functions are *arbitrary* smooth functions. An identity is ZERO
only if SymPy reduces the residual to zero (after expanding divided
differences and canonicalizing polygammas by reflection). NONZERO needs a
proof: every declared function is replaced by a concrete test function and
the residual is shown nonzero at a rational point (``equals(0) is False``).
An identity that holds for all smooth f must hold for that one, so this is
a genuine counterexample. Anything else is UNKNOWN, with numerical
agreement reported as support only.
"""
from __future__ import annotations

import random
from typing import Any, Iterable

import sympy

from ..budgets import BudgetExceeded, run_symbolic_operation
from ..models import AdapterError
from ._common import Namespace, sample_points
from .special import reflect_polygamma

_T = sympy.Dummy("t")


def divided_difference(F, nodes: list) -> sympy.Expr:
    """f[x0..xr] with repeated nodes handled by the confluent limit."""
    nodes = list(nodes)
    if len(nodes) == 1:
        return F(nodes[0])
    first = nodes[0]
    distinct = [n for n in nodes[1:] if sympy.simplify(n - first) != 0]
    if not distinct:
        r = len(nodes) - 1
        return sympy.Subs(sympy.Derivative(F(_T), (_T, r)), _T, first).doit() / sympy.factorial(r)
    last, rest = distinct[0], list(nodes[1:])
    rest.remove(last)
    ordered = [first, *rest, last]
    return (divided_difference(F, ordered[:-1]) - divided_difference(F, ordered[1:])) / (first - last)


class CalculusSpace(Namespace):
    """Namespace that also knows DD_f and D_f for each declared function."""

    def __init__(self, symbols: Any, functions: Iterable[str] = (), *,
                 complex_names: tuple[str, ...] = ()):
        self.user_functions = [str(f) for f in functions]
        helpers = [f"{p}_{f}" for f in self.user_functions for p in ("DD", "D")]
        super().__init__(symbols, [*self.user_functions, *helpers], complex_names=complex_names)

    def expand(self, expr: sympy.Expr) -> sympy.Expr:
        for name in self.user_functions:
            F = sympy.Function(name)
            expr = expr.replace(sympy.Function(f"DD_{name}"),
                                lambda *nodes, F=F: divided_difference(F, list(nodes)))
            expr = expr.replace(sympy.Function(f"D_{name}"),
                                lambda k, x, F=F: self._derivative(F, k, x))
        return expr

    @staticmethod
    def _derivative(F, k, x):
        if not (k.is_Integer and k >= 0):
            raise AdapterError("DERIVATIVE_ORDER_NOT_LITERAL")
        return sympy.Subs(sympy.Derivative(F(_T), (_T, int(k))), _T, x).doit()

    def parse_expanded(self, text: str) -> sympy.Expr:
        return self.expand(self.parse(text))


def _simplify_zero(residual: sympy.Expr) -> bool:
    for candidate in (residual, reflect_polygamma(residual)):
        try:
            simplified = run_symbolic_operation(
                "simplify", sympy.simplify, (candidate,), budget_key="simplify_seconds")
            if simplified == 0:
                return True
            rewritten = run_symbolic_operation(
                "simplify", sympy.simplify, (sympy.expand(simplified.rewrite(sympy.exp)),),
                budget_key="simplify_seconds")
            if rewritten == 0:
                return True
        except BudgetExceeded:
            continue
    return False


def _test_functions(names: list[str], seed: int) -> dict:
    rng = random.Random(seed)
    out = {}
    for name in names:
        a, b, c = (sympy.Rational(rng.randint(3, 9), rng.randint(5, 11)) for _ in range(3))
        out[name] = sympy.Lambda(_T, sympy.exp(a * _T) * sympy.cos(b * _T) + c * _T ** 3)
    return out


def _concretize(expr: sympy.Expr, names: list[str], seed: int) -> sympy.Expr:
    for name, lam in _test_functions(names, seed).items():
        expr = expr.replace(sympy.Function(name), lam)
    return expr.doit()


def _certified_value(value: sympy.Expr):
    """Value with 30 guaranteed digits, or None (strict evalf)."""
    if value.free_symbols or value.has(sympy.zoo, sympy.nan, sympy.oo):
        return None
    try:
        number = value.evalf(30, strict=True)
    except (sympy.core.evalf.PrecisionExhausted, TypeError, ValueError, ZeroDivisionError):
        return None
    return number if number.is_Number or number.is_number else None


def _screen(residual, names, free, positive) -> tuple[dict | None, bool]:
    """(counterexample, all_small). A value certified to 30 digits and larger
    than 1e-20 in magnitude proves the residual is not identically zero."""
    all_small = True
    for seed in (11, 23, 37):
        concrete = _concretize(residual, names, seed)
        for point in sample_points(free, positive=positive, count=2, seed=seed):
            number = _certified_value(concrete.subs(point))
            if number is None:
                all_small = False
                continue
            if abs(number) > sympy.Float("1e-20"):
                return ({"point": {str(k): str(v) for k, v in point.items()},
                         "test_functions": {n: str(l) for n, l in _test_functions(names, seed).items()},
                         "value": str(sympy.N(number, 15))}, False)
    return None, all_small


def compare(lhs: sympy.Expr, rhs: sympy.Expr, space: CalculusSpace,
            positive: tuple[str, ...] = ()) -> dict:
    residual = lhs - rhs
    pos = space.positives(tuple(positive))
    hit, all_small = _screen(residual, space.user_functions, residual.free_symbols, pos)
    if hit is not None:
        return {"verdict": "NONZERO", "reasons": ["COUNTEREXAMPLE"], "counterexample": hit}
    if _simplify_zero(residual):
        return {"verdict": "ZERO", "reasons": []}
    reasons = ["NUMERICAL_SUPPORT_ONLY"] if all_small else ["UNDECIDED"]
    return {"verdict": "UNKNOWN", "reasons": reasons}


def verify_identity(lhs: str, rhs: str, *, symbols: Any, functions: Iterable[str] = (),
                    positive: tuple[str, ...] = ()) -> dict:
    """ZERO / NONZERO / UNKNOWN for an identity with DD_f and D_f."""
    try:
        space = CalculusSpace(symbols, functions)
        left, right = space.parse_expanded(lhs), space.parse_expanded(rhs)
    except AdapterError as exc:
        return {"verdict": "UNKNOWN", "reasons": [f"PARSE_FAILED:{exc.code}"]}
    return compare(left, right, space, positive)


def _series_coefficient(expr, variable, order):
    series = sympy.series(expr, variable, 0, order + 1).removeO()
    return sympy.expand(series).coeff(variable, order).doit()


def verify_series_coefficient(expr: str, claim: str, *, variable: str, order: int,
                              symbols: Any, functions: Iterable[str] = (),
                              positive: tuple[str, ...] = ()) -> dict:
    """[variable^order] of expr (Taylor/Laurent at 0) versus the claim."""
    try:
        space = CalculusSpace(symbols, functions)
        w = space.symbol(variable)
        body, target = space.parse_expanded(expr), space.parse_expanded(claim)
    except AdapterError as exc:
        return {"verdict": "UNKNOWN", "reasons": [f"PARSE_FAILED:{exc.code}"]}
    try:
        coefficient = run_symbolic_operation(
            "series", _series_coefficient, (body, w, int(order)), budget_key="simplify_seconds")
    except (BudgetExceeded, NotImplementedError, ValueError, TypeError):
        return {"verdict": "UNKNOWN", "reasons": ["SERIES_NOT_COMPUTED"]}
    result = compare(coefficient, target, space, positive)
    return {**result, "coefficient": str(coefficient)[:2000]}
