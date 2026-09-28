"""Remainder certificates for asymptotic expansions.

A claim  f(x) = P(x) + O(x**n)  as x -> x0  holds when the quotient
q(x) = (f - P) / x**n  has a finite limit at x0 (the definition of O). The
engine computes that limit exactly; a finite value, identical from each
declared side, gives a remainder certificate. At infinity use a negative
order: O(1/w**3) is order -3, and q = (f - P) * w**3.

What this covers: expansions of rational functions, Laurent expansions in a
broadening Gamma -> 0, high-frequency tails of Green's functions, and any
closed form SymPy can take the limit of. What it does not cover: expansions
known only as asymptotic series (Sommerfeld, Stirling) when SymPy cannot take
the limit. ``estimate_remainder_order`` then gives numerical support from the
scaling of |f - P|, which is never a certificate.

The exact limit is cross-checked numerically at rational sample points of
the other symbols; a disagreement leaves the claim UNKNOWN.
"""
from __future__ import annotations

from typing import Any

import mpmath
import sympy

from ..audit.schema import ASYMPTOTIC_REMAINDER_LIMIT
from ..budgets import BudgetExceeded, run_symbolic_operation
from ..models import AdapterError
from .special import reflect_polygamma
from ._common import (CERTIFIED_BY_RULE, NONZERO, NUMERIC_AGREES,
                      NUMERIC_DISAGREES, NUMERIC_UNAVAILABLE, UNKNOWN,
                      ManyBodyResult, Namespace, certificate_hash, sample_points,
                      text_hash)

DIRECTIONS = ("+", "-", "+-")
_INFINITE = (sympy.oo, -sympy.oo, sympy.zoo)


def _point(text: str) -> sympy.Expr:
    table = {"0": sympy.Integer(0), "oo": sympy.oo, "+oo": sympy.oo, "-oo": -sympy.oo}
    if text not in table:
        raise AdapterError("ASYMPTOTIC_POINT_UNSUPPORTED")
    return table[text]


def _sides(point: sympy.Expr, direction: str) -> tuple[tuple[sympy.Expr, str], ...]:
    if point in (sympy.oo, -sympy.oo):
        return ((point, "-" if point == sympy.oo else "+"),)
    return tuple((point, side) for side in ("+", "-") if side in direction)


def _classify(value: sympy.Expr, sample: dict | None = None) -> str:
    # |q| -> oo means some admissible parameter point violates the claimed
    # order (the verifier's NONZERO semantics), e.g. I*oo or oo*sign(c).
    if value in _INFINITE or sympy.Abs(value) == sympy.oo:
        return "INFINITE"
    if sample and value.has(sympy.oo, -sympy.oo, sympy.zoo):
        at_point = value.subs(sample)
        if at_point in _INFINITE or sympy.Abs(at_point) == sympy.oo:
            return "INFINITE"  # e.g. oo*c/|c| at an admissible c != 0
    if value is sympy.nan or value.has(sympy.nan, sympy.zoo, sympy.oo, -sympy.oo) \
            or value.has(sympy.Limit) or isinstance(value, sympy.AccumBounds) \
            or value.has(sympy.AccumBounds):
        return "UNDECIDED"
    return "FINITE"


def _numeric_limit_check(q, x, point, value, free, positive=()) -> dict:
    """q near the point must approach the exact limit at sample points."""
    approach = ([mpmath.mpf(10) ** k for k in (8, 12, 16)] if point == sympy.oo else
                [-(mpmath.mpf(10) ** k) for k in (8, 12, 16)] if point == -sympy.oo else
                [mpmath.mpf(10) ** -k for k in (8, 12, 16)])
    worst = mpmath.mpf(0)
    try:
        with mpmath.workdps(60):
            for sample in sample_points(free, positive=positive):
                target = mpmath.mpmathify(complex(sympy.N(value.subs(sample), 60)))
                f = sympy.lambdify(x, q.subs(sample), "mpmath")
                last = f(approach[-1])
                worst = max(worst, abs(last - target) / max(mpmath.mpf(1), abs(target)))
    except (ValueError, TypeError, ZeroDivisionError, ArithmeticError):
        return {"status": NUMERIC_UNAVAILABLE, "points": 0}
    status = NUMERIC_AGREES if worst < mpmath.mpf("1e-6") else NUMERIC_DISAGREES
    return {"status": status, "points": 3, "max_rel_diff": mpmath.nstr(worst, 3)}


def _certified_nonzero(value: sympy.Expr, sample: dict) -> bool:
    try:
        number = value.subs(sample).evalf(30, strict=True)
    except (sympy.core.evalf.PrecisionExhausted, TypeError, ValueError, ZeroDivisionError):
        return False
    return bool(number.is_number) and abs(number) > sympy.Float("1e-20")


def _series_terms(expr: sympy.Expr, var: sympy.Symbol, upto: int):
    """Laurent coefficients {power: coeff} below var**upto, or None."""
    try:
        series = run_symbolic_operation(
            "series", sympy.series, (expr, var, 0, upto), budget_key="simplify_seconds")
    except (BudgetExceeded, NotImplementedError, ValueError, TypeError):
        return None
    terms: dict[int, sympy.Expr] = {}
    for term in sympy.Add.make_args(sympy.expand(series.removeO())):
        coeff, power = term.as_coeff_exponent(var)
        if coeff.has(var) or not power.is_Integer or coeff.has(sympy.log):
            return None  # not a plain Laurent series
        terms[int(power)] = terms.get(int(power), 0) + coeff
    return terms


def _series_route(num, x, x0, order, sample):
    """Certify num = O(x**order) from its Laurent coefficients.

    Every coefficient below the claimed order must vanish identically
    (checked with polygamma reflection and simplify), and the next one is
    reported as the limit. A coefficient certified nonzero at an admissible
    sample point refutes the claim. Returns None when undecided.
    """
    from .calculus import _simplify_zero
    var, n = x, order
    if x0 in (sympy.oo, -sympy.oo):
        var = sympy.Dummy("t", positive=True)
        num = num.subs(x, (1 if x0 == sympy.oo else -1) / var)
        n = -order
    terms = _series_terms(num, var, n + 1)
    if terms is None:
        return None
    for power in sorted(p for p in terms if p < n):
        coeff = terms[power]
        if _certified_nonzero(coeff, sample):
            return (NONZERO, str(coeff), ["LOWER_ORDER_TERM_NONZERO"])
        if not _simplify_zero(coeff):
            return None
    leading = sympy.simplify(reflect_polygamma(terms.get(n, sympy.Integer(0))))
    if x0 in (sympy.oo, -sympy.oo) and x0 == -sympy.oo:
        leading = leading * (-1) ** n
    return (CERTIFIED_BY_RULE, leading, [])


def certify_remainder(function: str, approximant: str, *, variable: str, point: str,
                      order: int, symbols: Any, functions: Any = None,
                      direction: str = "+-", positive: tuple[str, ...] = (),
                      definitions: dict | None = None,
                      numeric: bool = True) -> ManyBodyResult:
    """Certify  function = approximant + O(variable**order)  as variable -> point."""
    inputs = {"rule": ASYMPTOTIC_REMAINDER_LIMIT, "function_sha256": text_hash(function),
              "approximant_sha256": text_hash(approximant), "variable": variable,
              "point": point, "order": int(order), "direction": direction}

    def result(status, reasons, derived="", verdict="NOT_RUN", numeric_info=None):
        cert = {**inputs, "status": status, "limit": derived,
                "symbolic_verdict": verdict, "numeric": numeric_info or {}}
        return ManyBodyResult(
            kind="ASYMPTOTIC_REMAINDER", status=status, rule_id=ASYMPTOTIC_REMAINDER_LIMIT,
            reasons=tuple(reasons), derived=derived, symbolic_verdict=verdict,
            numeric=numeric_info or {}, certificate=cert,
            certificate_hash=certificate_hash(cert) if status == CERTIFIED_BY_RULE else None)

    if direction not in DIRECTIONS:
        return result(UNKNOWN, ["ASYMPTOTIC_SPEC_INVALID"])
    if point in ("oo", "+oo", "-oo") and direction != "+-":
        # the side is fixed by the sign of infinity; refuse rather than ignore
        return result(UNKNOWN, ["DIRECTION_NOT_APPLICABLE_AT_INFINITY"])
    try:
        x0 = _point(point)
        from .calculus import CalculusSpace
        space = CalculusSpace(symbols, functions or (), definitions=definitions)
        x = space.symbol(variable)
        f, P = space.parse_expanded(function), space.parse_expanded(approximant)
        pos = space.positives(tuple(positive))
    except AdapterError as exc:
        return result(UNKNOWN, [f"PARSE_FAILED:{exc.code}"])
    q = (f - P) / x ** int(order)
    free_params = (q.free_symbols - {x})
    sample = sample_points(free_params, positive=pos, count=1)[0] if free_params else {}
    limits, failure = [], None
    for pt, side in _sides(x0, direction):
        try:
            value = run_symbolic_operation(
                "limit", sympy.limit, (q, x, pt, side), budget_key="simplify_seconds")
        except BudgetExceeded:
            failure = "LIMIT_TIME_BUDGET_EXCEEDED"
            break
        except (NotImplementedError, ValueError, TypeError):
            failure = "LIMIT_NOT_COMPUTED"
            break
        limits.append(sympy.simplify(value))
    kinds = {_classify(v, sample) for v in limits} if failure is None else {"UNDECIDED"}
    derived = ", ".join(str(v) for v in limits)
    if "INFINITE" in kinds:
        return result(NONZERO, ["REMAINDER_QUOTIENT_DIVERGES"], derived, "INFINITE",
                      {"counterexample": {str(k): str(v) for k, v in sample.items()}})
    if kinds != {"FINITE"}:
        series = _series_route(f - P, x, x0, int(order), sample)
        if series is not None:
            status, value, reasons = series
            if status == NONZERO:
                return result(NONZERO, reasons, value, "SERIES",
                              {"counterexample": {str(k): str(v) for k, v in sample.items()}})
            limits, derived, kinds = [value], str(value), {"FINITE"}
        else:
            return result(UNKNOWN, [failure or "LIMIT_NOT_DECIDED"], derived, "UNDECIDED")
    if len(limits) == 2 and sympy.simplify(limits[0] - limits[1]) != 0:
        return result(UNKNOWN, ["ONE_SIDED_LIMITS_DIFFER"], derived, "FINITE")
    free = (q.free_symbols | limits[0].free_symbols) - {x}
    numeric_info = (_numeric_limit_check(q, x, x0, limits[0], free, pos)
                    if numeric else {"status": "NOT_RUN"})
    if numeric_info.get("status") == NUMERIC_DISAGREES:
        return result(UNKNOWN, ["NUMERIC_CROSSCHECK_DISAGREES"], derived, "FINITE", numeric_info)
    return result(CERTIFIED_BY_RULE, [], derived, "FINITE", numeric_info)


def estimate_remainder_order(function: str, approximant: str, *, variable: str,
                             point: str, symbols: Any, functions: Any = None,
                             values: dict | None = None, steps: int = 6) -> dict:
    """Effective exponent of |f - P| from successive halvings (numerical support).

    Returns the local slopes d log|f - P| / d log|x - x0|. Asymptotic-only series
    such as the Sommerfeld expansion show a slope that stays at or above the
    claimed order; this is evidence, not a remainder certificate.
    """
    space = Namespace(symbols, functions)
    x = space.symbol(variable)
    r = space.parse(function) - space.parse(approximant)
    free = r.free_symbols - {x}
    sample = values or (sample_points(free, count=1)[0] if free else {})
    f = sympy.lambdify(x, r.subs(sample), "mpmath")
    x0 = _point(point)
    with mpmath.workdps(50):
        if x0 == 0:
            grid = [mpmath.mpf(2) ** -(4 + k) for k in range(steps)]
        else:
            grid = [mpmath.mpf(2) ** (4 + k) for k in range(steps)]
        mags = [abs(f(t)) for t in grid]
        slopes = []
        for (t1, m1), (t2, m2) in zip(zip(grid, mags), zip(grid[1:], mags[1:])):
            if m1 == 0 or m2 == 0:
                slopes.append(None)
                continue
            slopes.append(float(mpmath.log(m2 / m1) / mpmath.log(t2 / t1)))
    return {"status": "NUMERICAL_SUPPORT", "point": point, "slopes": slopes,
            "sample": {str(k): str(v) for k, v in sample.items()}}
