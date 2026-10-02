"""Identities with divided differences, derivatives and series coefficients.

Claim language (on top of the usual expression syntax):
  DD_f(x0, x1, ..., xr)   divided difference of a declared function f;
                          repeated nodes use the confluent limit
  D_f(k, x)               k-th derivative of f at x (k a literal integer)
  Diff(expr, x, k)        k-th derivative of any expression in the symbol x
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
import re
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


_DEF_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(([^()]*)\)\s*$")
_MAX_DEPTH = 12


def _parse_definition_key(key: str) -> tuple[str, tuple[str, ...]]:
    match = _DEF_RE.match(key)
    if not match:
        raise AdapterError("DEFINITION_KEY_INVALID")
    params = tuple(p.strip() for p in match.group(2).split(",") if p.strip())
    return match.group(1), params


class CalculusSpace(Namespace):
    """Namespace that also knows DD_f and D_f for each declared function, and
    named definitions ``name(params): body`` that may use each other."""

    def __init__(self, symbols: Any, functions: Iterable[str] = (), *,
                 complex_names: tuple[str, ...] = (), definitions: dict | None = None):
        self.user_functions = [str(f) for f in functions]
        self.defs = {}
        for key, body in (definitions or {}).items():
            name, params = _parse_definition_key(str(key))
            self.defs[name] = (params, str(body))
        names = [*self.user_functions, *self.defs]
        helpers = [f"{p}_{f}" for f in names for p in ("DD", "D")] + ["Diff"]
        declared = {(s if isinstance(s, str) else s.get("name")) for s in (symbols or [])}
        extra = [{"name": p, "real": True} for params, _ in self.defs.values()
                 for p in params if p not in declared]
        seen, unique_extra = set(), []
        for item in extra:
            if item["name"] not in seen:
                seen.add(item["name"])
                unique_extra.append(item)
        super().__init__([*(symbols or []), *unique_extra], [*names, *helpers],
                         complex_names=complex_names)
        self._lambdas: dict = {}

    def _lambda(self, name):
        if name not in self._lambdas:
            params, body = self.defs[name]
            self._lambdas[name] = sympy.Lambda(tuple(self.symbol(p) for p in params), self.parse(body))
        return self._lambdas[name]

    def expand(self, expr: sympy.Expr) -> sympy.Expr:
        from sympy.core.function import AppliedUndef
        for _ in range(_MAX_DEPTH):
            before = expr
            present = {f.func.__name__ for f in expr.atoms(AppliedUndef)}
            # only definitions this expression uses are parsed: an unrelated
            # shared definition must not affect the check
            for name in [n for n in [*self.user_functions, *self.defs]
                         if {n, f"DD_{n}", f"D_{n}"} & present]:
                F = self._lambda(name) if name in self.defs else sympy.Function(name)
                expr = expr.replace(sympy.Function(f"DD_{name}"),
                                    lambda *nodes, F=F: divided_difference(F, list(nodes)))
                expr = expr.replace(sympy.Function(f"D_{name}"),
                                    lambda k, x, F=F: self._derivative(F, k, x))
            for name in [n for n in self.defs if n in present]:
                expr = expr.replace(sympy.Function(name), self._lambda(name))
            expr = expr.replace(sympy.Function("Diff"), self._diff)
            if expr == before:
                return expr
        raise AdapterError("DEFINITIONS_TOO_DEEP_OR_CYCLIC")

    @staticmethod
    def _diff(expr, variable, k):
        """Diff(expr, x, k): k-th derivative of any expression in a symbol."""
        if not (isinstance(variable, sympy.Symbol) and k.is_Integer and k >= 0):
            raise AdapterError("DIFF_ARGUMENTS_INVALID")
        return sympy.diff(expr, variable, int(k)).doit()

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
        except (BudgetExceeded, AttributeError, TypeError, RecursionError):
            continue            # a failed simplification is "not shown zero", never ZERO
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
        # G(t, t') gets a test function of all its arguments, not a unary one
        expr = expr.replace(sympy.Function(name),
                            lambda *args, lam=lam: lam(sum((k + 1) * a for k, a in enumerate(args))))
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


def _tiny(value) -> bool:
    try:
        estimate = sympy.N(value, 60)
    except (TypeError, ValueError, ZeroDivisionError):
        return False
    return estimate.is_number and not estimate.has(sympy.zoo, sympy.nan) and abs(estimate) < 1e-40


def _screen(residual, names, free, positive) -> tuple[dict | None, bool]:
    """(counterexample, all_small). A value certified to 30 digits and larger
    than 1e-20 in magnitude proves the residual is not identically zero."""
    all_small = True
    for seed in (11, 23, 37):
        concrete = _concretize(residual, names, seed)
        for point in sample_points(free, positive=positive, count=2, seed=seed):
            value = concrete.subs(point)
            number = _certified_value(value)
            if number is None:
                # strict evalf cannot certify digits of a value that is 0; a
                # 60-digit estimate may support ZERO but never proves NONZERO
                if not _tiny(value):
                    all_small = False
                continue
            if abs(number) > sympy.Float("1e-20"):
                return ({"point": {str(k): str(v) for k, v in point.items()},
                         "test_functions": {n: str(l) for n, l in _test_functions(names, seed).items()},
                         "value": str(sympy.N(number, 15))}, False)
    return None, all_small


def _numeric(expr, names, point, seed):
    value = _certified_value(_concretize(expr, names, seed).subs(point))
    return None if value is None else complex(value)


def diagnose(lhs, rhs, space, positive=(), labels: tuple[str, ...] = ()) -> list[str]:
    """Name a simple relation between claim (rhs) and computed value (lhs).

    Convention slips (sign, factor 2, conjugation, a swapped label pair)
    are the commonest transcription errors; naming them makes a NONZERO
    actionable. Matches are numerical at two sample points, so they are
    hints, never verdicts.
    """
    names, pos = space.user_functions, space.positives(tuple(positive))
    syms = [space.symbol(n) for n in labels]
    candidates = {
        "claim = -(computed)": -lhs,
        "claim = conj(computed): check index order or the sign of i": sympy.conjugate(lhs),
        "claim = -conj(computed)": -sympy.conjugate(lhs),
        "claim = 2 * computed (missing factor 1/2 in the claim?)": 2 * lhs,
        "claim = computed / 2 (missing factor 2 in the claim?)": lhs / 2,
    }
    for i, a in enumerate(syms):
        for b in syms[i + 1:]:
            swapped = lhs.xreplace({a: b, b: a})
            candidates[f"claim = computed with {a} <-> {b} (index order)"] = swapped
            candidates[f"claim = conj(computed) with {a} <-> {b}"] = sympy.conjugate(swapped)
    free = (lhs.free_symbols | rhs.free_symbols)
    points = sample_points(free, positive=pos, count=2, seed=41)
    found = []
    for text, cand in candidates.items():
        ok = True
        for point in points:
            r, c = _numeric(rhs, names, point, 11), _numeric(cand, names, point, 11)
            if r is None or c is None or abs(r - c) > 1e-12 * max(1.0, abs(r)):
                ok = False
                break
        if ok:
            found.append(text)
    return found


def _explicit_re_im(expr: sympy.Expr) -> sympy.Expr:
    """re(x), im(x) -> (x + conj x)/2, (x - conj x)/(2i): both sides then
    evaluate and simplify like any other expression."""
    expr = expr.replace(sympy.im, lambda x: (x - sympy.conjugate(x)) / (2 * sympy.I))
    expr = expr.replace(sympy.re, lambda x: (x + sympy.conjugate(x)) / 2)
    # polygammas are real-analytic: conj psi^(k)(z) = psi^(k)(conj z)
    return expr.replace(
        lambda e: isinstance(e, sympy.conjugate) and isinstance(e.args[0], sympy.polygamma),
        lambda e: sympy.polygamma(e.args[0].args[0], sympy.conjugate(e.args[0].args[1])))


def compare(lhs: sympy.Expr, rhs: sympy.Expr, space: CalculusSpace,
            positive: tuple[str, ...] = (), labels: tuple[str, ...] = ()) -> dict:
    lhs, rhs = _explicit_re_im(lhs), _explicit_re_im(rhs)
    residual = lhs - rhs
    pos = space.positives(tuple(positive))
    hit, all_small = _screen(residual, space.user_functions, residual.free_symbols, pos)
    if hit is not None:
        return {"verdict": "NONZERO", "reasons": ["COUNTEREXAMPLE"], "counterexample": hit,
                "diagnosis": diagnose(lhs, rhs, space, positive, labels)}
    if _simplify_zero(residual):
        return {"verdict": "ZERO", "reasons": []}
    reasons = ["NUMERICAL_SUPPORT_ONLY"] if all_small else ["UNDECIDED"]
    return {"verdict": "UNKNOWN", "reasons": reasons}


def verify_identity(lhs: str, rhs: str, *, symbols: Any, functions: Iterable[str] = (),
                    positive: tuple[str, ...] = (), definitions: dict | None = None,
                    labels: tuple[str, ...] = ()) -> dict:
    """ZERO / NONZERO / UNKNOWN for an identity with DD_f, D_f and definitions."""
    try:
        space = CalculusSpace(symbols, functions, definitions=definitions)
        left, right = space.parse_expanded(lhs), space.parse_expanded(rhs)
    except AdapterError as exc:
        return {"verdict": "UNKNOWN", "reasons": [f"PARSE_FAILED:{exc.code}"]}
    return compare(left, right, space, positive, labels)


def _series_coefficient(expr, variable, order):
    series = sympy.series(expr, variable, 0, order + 1).removeO()
    return sympy.expand(series).coeff(variable, order).doit()


def verify_series_coefficient(expr: str, claim: str, *, variable: str, order: int,
                              symbols: Any, functions: Iterable[str] = (),
                              positive: tuple[str, ...] = (), definitions: dict | None = None,
                              labels: tuple[str, ...] = ()) -> dict:
    """[variable^order] of expr (Taylor/Laurent at 0) versus the claim."""
    try:
        space = CalculusSpace(symbols, functions, definitions=definitions)
        w = space.symbol(variable)
        body, target = space.parse_expanded(expr), space.parse_expanded(claim)
    except AdapterError as exc:
        return {"verdict": "UNKNOWN", "reasons": [f"PARSE_FAILED:{exc.code}"]}
    try:
        coefficient = run_symbolic_operation(
            "series", _series_coefficient, (body, w, int(order)), budget_key="simplify_seconds")
    except (BudgetExceeded, NotImplementedError, ValueError, TypeError):
        return {"verdict": "UNKNOWN", "reasons": ["SERIES_NOT_COMPUTED"]}
    result = compare(coefficient, target, space, positive, labels)
    return {**result, "coefficient": str(coefficient)[:2000]}
