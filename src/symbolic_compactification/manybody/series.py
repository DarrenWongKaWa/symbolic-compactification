"""Exact sums  sum_{n=n0}^infinity R(n)  of rational functions (digamma rule).

With R = P/Q, deg Q - deg P >= 2 and the partial fractions

    R(n) = sum_k sum_{m} c_{k,m} / (n + a_k)^m ,

convergence forces sum_k c_{k,1} = 0, and

    sum_{n>=n0} 1/(n + a)^m = (-1)^m psi^{(m-1)}(n0 + a) / (m-1)!     (m >= 2)
    sum_{n>=n0} sum_k c_k/(n + a_k) = - sum_k c_k psi(n0 + a_k)        (m = 1).

This is the relation Matsubara-type sums are reduced to. Hypotheses
checked mechanically: R rational in n with decay gap >= 2 and explicit
roots. The rule also needs n0 + a_k not in {0, -1, -2, ...}; for symbolic
a_k this is reported as the assumption SERIES_POLES_OFF_SUMMATION_RANGE,
and a pole that provably sits on the range is refused. The claim is then
compared with the closed form by the exact identity check: the result is
CERTIFIED_BY_RULE (rule RATIONAL_SERIES_DIGAMMA) or NONZERO.
"""
from __future__ import annotations

from typing import Any, Iterable

import sympy

from ..models import AdapterError
from ._common import CERTIFIED_BY_RULE, NONZERO, UNKNOWN, certificate_hash, text_hash
from .calculus import CalculusSpace, compare

RATIONAL_SERIES_DIGAMMA = "RATIONAL_SERIES_DIGAMMA"


class _Refusal(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def series_closed_form(expr, n, n0=0):
    """(closed form, assumptions) of sum_{n>=n0} expr."""
    R = sympy.together(expr)
    if not R.is_rational_function(n):
        raise _Refusal("SUMMAND_NOT_RATIONAL_IN_INDEX")
    num, den = sympy.fraction(R)
    pn, pd = sympy.Poly(sympy.expand(num), n), sympy.Poly(sympy.expand(den), n)
    if pd.degree() - pn.degree() < 2:
        raise _Refusal("SUMMAND_DECAY_BELOW_1_OVER_N2")
    roots = sympy.roots(pd)
    if sum(roots.values()) != pd.degree():
        raise _Refusal("DENOMINATOR_ROOTS_NOT_EXPLICIT")
    total, assumptions = sympy.Integer(0), set()
    for root, mult in roots.items():
        a = -root                                    # factor (n + a)
        shifted = sympy.simplify(n0 + a)
        if shifted.is_integer and shifted.is_nonpositive:
            raise _Refusal("POLE_ON_SUMMATION_RANGE")
        if not shifted.is_number:
            assumptions.add("SERIES_POLES_OFF_SUMMATION_RANGE")
        regular = sympy.cancel((n - root) ** mult * R)
        for m in range(1, mult + 1):
            # coefficient of 1/(n - root)^m in the Laurent expansion at root
            c = sympy.diff(regular, n, mult - m).subs(n, root) / sympy.factorial(mult - m)
            if m == 1:
                total += -c * sympy.polygamma(0, shifted)
            else:
                total += c * (-1) ** m * sympy.polygamma(m - 1, shifted) / sympy.factorial(m - 1)
    return total, sorted(assumptions)


def verify_series_sum(summand: str, claim: str, *, variable: str, symbols: Any,
                      lower: int | str = 0, functions: Iterable[str] = (),
                      definitions: dict | None = None, positive: tuple[str, ...] = ()) -> dict:
    """sum_{n=lower}^oo summand == claim. lower = "-oo" is a sum over all
    integers, taken as sum_{n>=0} [R(n) + R(-n-1)]."""
    bilateral = str(lower).strip() in ("-oo", "-inf")
    inputs = {"rule": RATIONAL_SERIES_DIGAMMA, "summand_sha256": text_hash(summand),
              "claim_sha256": text_hash(claim), "variable": variable,
              "lower": "-oo" if bilateral else int(lower)}
    try:
        space = CalculusSpace(symbols, functions, definitions=definitions)
        n = space.symbol(variable)
        body, target = space.parse_expanded(summand), space.parse_expanded(claim)
    except AdapterError as exc:
        return {**inputs, "status": UNKNOWN, "reasons": [f"PARSE_FAILED:{exc.code}"]}
    sure = {s: sympy.Symbol(s.name, positive=True) for s in space.positives(tuple(positive))}
    back = {v: k for k, v in sure.items()}
    if bilateral:
        body, lower = body + body.subs(n, -n - 1), 0        # n < 0 folded onto n >= 0
    try:
        closed, assumptions = series_closed_form(body.xreplace(sure), n, int(lower))
    except _Refusal as refusal:
        return {**inputs, "status": UNKNOWN, "reasons": [refusal.reason]}
    closed = closed.xreplace(back)
    result = compare(closed, target, space, positive)
    status = {"ZERO": CERTIFIED_BY_RULE, "NONZERO": NONZERO}.get(result["verdict"], UNKNOWN)
    cert = {**inputs, "status": status, "derived": str(closed)[:4000], "assumptions": assumptions}
    return {**cert, "reasons": [*result.get("reasons", []), *assumptions],
            "counterexample": result.get("counterexample"), "diagnosis": result.get("diagnosis"),
            "certificate_hash": certificate_hash(cert) if status == CERTIFIED_BY_RULE else None}
