"""Definite integrals with limits: int_a^b f(x) dx == claim.

The integral is not evaluated by trusting a CAS. The engine proposes an
antiderivative F, and the check uses only facts that are verified here:

1. f is entire in x (polynomials, exp, sin, cos, sinh, cosh of entire
   arguments), so it has no singularity on any path from a to b;
2. F' = f exactly (the residual simplifies to 0), and F is entire in x too;
3. by the fundamental theorem of calculus the integral is F(b) - F(a).

An infinite limit is allowed when every term of F is x^k exp(s x) with a
slope s whose real part has the sign that makes the term vanish there,
decided from the declared positive and real symbols; a constant term of F
at that end is kept. Otherwise the check is not decided.

F may hold 1/a for a parameter a (int exp(a x) dx = exp(a x)/a): the
identity is then exact for generic parameter values, which is how such
claims are stated. The result is CERTIFIED_BY_RULE (rule
FTC_ENTIRE_ANTIDERIVATIVE) or NONZERO with a counterexample, never an
engine ZERO for the integral itself.
"""
from __future__ import annotations

from typing import Any, Iterable

import sympy

from ..budgets import run_symbolic_operation
from ..models import AdapterError
from ._common import CERTIFIED_BY_RULE, NONZERO, UNKNOWN, certificate_hash, text_hash
from .calculus import CalculusSpace, _simplify_zero, compare

FTC_ENTIRE_ANTIDERIVATIVE = "FTC_ENTIRE_ANTIDERIVATIVE"
_ENTIRE_FUNCTIONS = (sympy.exp, sympy.sin, sympy.cos, sympy.sinh, sympy.cosh)
_ENTIRE_ANTIDERIVATIVES = (*_ENTIRE_FUNCTIONS, sympy.erf, sympy.erfi, sympy.Si, sympy.Shi)


class _Refusal(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def is_entire(expr: sympy.Expr, x: sympy.Symbol, allowed=_ENTIRE_FUNCTIONS) -> bool:
    """Whether expr is built from x by +, *, nonnegative integer powers and
    entire functions of entire arguments. Anything else (a denominator in x,
    sqrt, log, |x|, an unknown function of x) is not accepted."""
    if not expr.has(x):
        return True
    if expr == x:
        return True
    if isinstance(expr, (sympy.Add, sympy.Mul)):
        return all(is_entire(a, x, allowed) for a in expr.args)
    if isinstance(expr, sympy.Pow):
        base, exp = expr.args
        if exp.has(x):
            return (not base.has(x)) and base != 0 and is_entire(exp, x, allowed)
        return bool(exp.is_Integer and exp >= 0) and is_entire(base, x, allowed)
    if isinstance(expr, allowed):
        return all(is_entire(a, x, allowed) for a in expr.args)
    return False


def _generic_branch(expr: sympy.Expr) -> sympy.Expr:
    """Piecewise((exp(a x)/a, Ne(a, 0)), (x, True)) -> exp(a x)/a: the
    branch for generic parameter values."""
    return expr.replace(lambda e: isinstance(e, sympy.Piecewise), lambda e: e.args[0].expr)


def _denominator_free(F: sympy.Expr, x: sympy.Symbol) -> sympy.Expr:
    """Rewrite c/(a exp(u) + b exp(u)) as c exp(-u)/(a + b), term by term,
    so that an exponential in a denominator is not mistaken for a pole."""
    terms = []
    for term in sympy.Add.make_args(sympy.expand(F)):
        num, den = sympy.fraction(term)
        den = sympy.factor(den)
        down = [f for f in sympy.Mul.make_args(den) if isinstance(f, sympy.exp)]
        terms.append(num * sympy.exp(-sympy.Add(*(e.args[0] for e in down))) / (den / sympy.Mul(*down)))
    return sympy.Add(*terms)


def _antiderivative(f: sympy.Expr, x: sympy.Symbol) -> sympy.Expr:
    try:
        F = run_symbolic_operation("integrate", sympy.integrate, (f, x),
                                   budget_key="simplify_seconds")
    except AdapterError:
        raise _Refusal("ANTIDERIVATIVE_TIMEOUT")
    except Exception:                       # SymPy raises many kinds of errors here
        raise _Refusal("ANTIDERIVATIVE_FAILED")
    F = _generic_branch(F)
    # SymPy may write exp(-u) as 1/exp(u) or 1/(a exp(u) + b exp(u)): move
    # such exponentials to the numerator before the entire test
    if F.has(sympy.Integral) or not is_entire(_denominator_free(F, x), x, _ENTIRE_ANTIDERIVATIVES):
        raise _Refusal("ANTIDERIVATIVE_NOT_ELEMENTARY_ENTIRE")
    if not _simplify_zero(sympy.diff(F, x) - f):
        raise _Refusal("ANTIDERIVATIVE_NOT_VERIFIED")
    return F


def _sign_of(value: sympy.Expr) -> int | None:
    if value.is_positive:
        return 1
    if value.is_negative:
        return -1
    return None


def _exp_terms(F: sympy.Expr, x: sympy.Symbol) -> list[tuple[sympy.Expr, sympy.Expr]]:
    """F as a sum of rest * exp(arg) terms, with every exponential (also one
    SymPy put in a denominator, 1/(c exp(u)) = exp(-u)/c) moved into arg.
    Refuses when a term has x outside the exponential and outside a
    polynomial factor."""
    out = []
    F = sympy.expand(F.rewrite(sympy.exp))
    for term in sympy.Add.make_args(F):
        num, den = sympy.fraction(sympy.factor_terms(term))
        den = sympy.factor(den)
        up = [f for f in sympy.Mul.make_args(num) if isinstance(f, sympy.exp)]
        down = [f for f in sympy.Mul.make_args(den) if isinstance(f, sympy.exp)]
        rest = (num / sympy.Mul(*up)) / (den / sympy.Mul(*down))
        arg = sympy.expand(sympy.Add(*(e.args[0] for e in up)) - sympy.Add(*(e.args[0] for e in down)))
        if rest.has(sympy.exp) or not sympy.expand(rest).is_polynomial(x):
            raise _Refusal("INFINITE_LIMIT_TERM_NOT_DECAYING")
        out.append((rest, arg))
    return out


def _value_at_infinity(F: sympy.Expr, x: sympy.Symbol, direction: int) -> sympy.Expr:
    """lim F(x) for x -> direction*oo when each term is c x^k exp(s x) with
    Re(direction*s) < 0 (it vanishes) or x-free (it stays); else refuse."""
    total = sympy.Integer(0)
    for rest, arg in _exp_terms(F, x):
        if not rest.has(x) and not arg.has(x):
            total += rest * sympy.exp(arg)
            continue
        slope = arg.diff(x)
        if slope.has(x):
            raise _Refusal("INFINITE_LIMIT_TERM_NOT_DECAYING")
        if _sign_of(sympy.re(direction * slope)) != -1:
            raise _Refusal("INFINITE_LIMIT_DECAY_UNDECIDED")
    return total


def _at(F: sympy.Expr, x: sympy.Symbol, limit: sympy.Expr) -> sympy.Expr:
    if limit in (sympy.oo, -sympy.oo):
        return _value_at_infinity(F, x, 1 if limit == sympy.oo else -1)
    if limit.has(sympy.oo, sympy.zoo, sympy.nan):
        raise _Refusal("LIMIT_NOT_UNDERSTOOD")
    return F.subs(x, limit)


def verify_definite_integral(integrand: str, claim: str, *, variable: str, lower: str,
                             upper: str, symbols: Any, functions: Iterable[str] = (),
                             definitions: dict | None = None,
                             positive: tuple[str, ...] = ()) -> dict:
    """int_lower^upper integrand d(variable) == claim, for an entire integrand."""
    inputs = {"rule": FTC_ENTIRE_ANTIDERIVATIVE, "integrand_sha256": text_hash(integrand),
              "claim_sha256": text_hash(claim), "variable": variable,
              "lower": str(lower), "upper": str(upper)}
    try:
        space = CalculusSpace(symbols, functions, definitions=definitions)
        x = space.symbol(variable)
        f = space.parse_expanded(integrand)
        target = space.parse_expanded(claim)
        a, b = (space.parse_expanded(str(v)) for v in (lower, upper))
    except AdapterError as exc:
        return {**inputs, "status": UNKNOWN, "reasons": [f"PARSE_FAILED:{exc.code}"]}
    if a.has(x) or b.has(x) or target.has(x):
        return {**inputs, "status": UNKNOWN, "reasons": ["INTEGRATION_VARIABLE_OUTSIDE_INTEGRAND"]}
    sure = {s: sympy.Symbol(s.name, positive=True) for s in space.positives(tuple(positive))}
    back = {v: k for k, v in sure.items()}
    try:
        if not is_entire(f, x):
            raise _Refusal("INTEGRAND_NOT_ENTIRE")
        F = _antiderivative(f.xreplace(sure), x.xreplace(sure))
        closed = (_at(F, x, b.xreplace(sure)) - _at(F, x, a.xreplace(sure))).xreplace(back)
    except _Refusal as refusal:
        return {**inputs, "status": UNKNOWN, "reasons": [refusal.reason]}
    result = compare(closed, target, space, positive)
    status = {"ZERO": CERTIFIED_BY_RULE, "NONZERO": NONZERO}.get(result["verdict"], UNKNOWN)
    cert = {**inputs, "status": status, "derived": str(closed)[:4000]}
    return {**cert, "reasons": result.get("reasons", []),
            "counterexample": result.get("counterexample"),
            "diagnosis": result.get("diagnosis"),
            "certificate_hash": certificate_hash(cert) if status == CERTIFIED_BY_RULE else None}
