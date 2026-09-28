"""Exact real-frequency integrals of rational functions times Fermi functions.

For I = int_R R(w) nF(c + w) dw with R rational and O(1/w^2), write

    nF(x) = 1/2 + (i/2 pi) [psi(1/2 + i beta x/(2 pi)) - psi(1/2 - i beta x/(2 pi))].

psi(1/2 + i beta x/2pi) has its poles in the upper half plane (UHP) of x, so
it is analytic in the lower one (LHP); psi(1/2 - i beta x/2pi) is analytic
in the UHP. Close each piece where it is analytic (psi grows only like
log|w|, so O(1/w^2) is enough on the arcs):

    int R/2            =  pi i  sum_UHP Res[R]
    int R psi(1/2+iy)  = -2pi i sum_LHP Res[R psi(1/2+iy)]
    int R psi(1/2-iy)  =  2pi i sum_UHP Res[R psi(1/2-iy)]

Higher-order poles give polygammas. Hypotheses checked mechanically:
rational coefficient functions with decay gap >= 2, a single nF factor per
term with argument c +- w, and every pole of R in a half plane that the
declared assumptions decide (e.g. Gamma > 0 via ``positive``). The claim is
then compared with the closed form by the exact identity check. Terms
without nF are integrated by residues in the UHP. The result is
CERTIFIED_BY_RULE (rule FERMI_RESIDUE_SPLITTING), never an engine ZERO for
the integral itself.
"""
from __future__ import annotations

from typing import Any, Iterable

import sympy

from ..models import AdapterError
from ._common import CERTIFIED_BY_RULE, NONZERO, UNKNOWN, certificate_hash, expand_distributions, text_hash
from .calculus import CalculusSpace, compare

FERMI_RESIDUE_SPLITTING = "FERMI_RESIDUE_SPLITTING"
_HALF = sympy.Rational(1, 2)


class _Refusal(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _unit_argument(arg, w):
    """nF(arg) with arg = c - w rewritten as 1 - nF(-c + w); returns (sign, c, const)
    so that nF(arg) = const + sign * nF(c + w)."""
    arg = sympy.expand(arg)
    slope = arg.diff(w)
    if slope == 1:
        return 1, sympy.expand(arg - w), 0
    if slope == -1:
        return -1, sympy.expand(-arg - w), 1
    raise _Refusal("FERMI_ARGUMENT_NOT_C_PLUS_MINUS_W")


def reduce_fermi_products(expr, w):
    """Products of two Fermi factors in w become linear in nF.

    With x = a + w and y = b + w, y - x = b - a does not depend on w and
        nF(x) nF(y) = nF(x) - (1 + nB(b - a)) (nF(x) - nF(y)),
    which is exact for b != a (generic parameters). nF(c - w) = 1 - nF(-c + w)
    first brings every argument to slope +1.
    """
    nF, nB = sympy.Function("nF"), sympy.Function("nB")
    out = sympy.Integer(0)
    for term in sympy.Add.make_args(sympy.expand(expr, mul=True, multinomial=False, power_exp=False)):
        calls = [f for f in sympy.Mul.make_args(term) if isinstance(f, sympy.Function) and f.func == nF
                 and f.args[0].has(w)]
        powers = [f for f in sympy.Mul.make_args(term) if isinstance(f, sympy.Pow)
                  and isinstance(f.base, sympy.Function) and f.base.func == nF and f.base.args[0].has(w)]
        if powers or len(calls) > 2:
            raise _Refusal("UNSUPPORTED_FERMI_PRODUCT")
        if len(calls) < 2:
            out += term
            continue
        rest = term / (calls[0] * calls[1])
        (s1, a, k1), (s2, b, k2) = (_unit_argument(c.args[0], w) for c in calls)
        if sympy.simplify(b - a) == 0:
            raise _Refusal("FERMI_PRODUCT_SAME_ARGUMENT")
        fx, fy = nF(a + w), nF(b + w)
        product = fx - (1 + nB(b - a)) * (fx - fy)
        # (k1 + s1 fx)(k2 + s2 fy) with fx fy replaced by the linear form
        out += rest * (k1 * k2 + k1 * s2 * fy + k2 * s1 * fx + s1 * s2 * product)
    return out


def _split_terms(expr, w):
    """{c: R_c(w)} for R_c(w) nF(c + w), plus None -> fermion-free part."""
    nF = sympy.Function("nF")
    groups: dict = {}
    expr = reduce_fermi_products(expr, w)
    for term in sympy.Add.make_args(sympy.expand(expr, mul=True, multinomial=False, power_exp=False)):
        calls = [f for f in term.atoms(sympy.Function) if f.func == nF]
        if not calls:
            groups[None] = groups.get(None, 0) + term
            continue
        if len(calls) != 1 or term.count(nF) != 1:
            raise _Refusal("MORE_THAN_ONE_FERMI_FACTOR")
        call = calls[0]
        arg = sympy.expand(call.args[0])
        slope = arg.diff(w)
        if slope == -1:
            term, arg = term.subs(w, -w), sympy.expand(arg.subs(w, -w))
            call = nF(arg)
        elif slope != 1:
            raise _Refusal("FERMI_ARGUMENT_NOT_C_PLUS_MINUS_W")
        c = sympy.expand(arg - w)
        coeff = sympy.cancel(term / call)
        if coeff.has(nF):
            raise _Refusal("MORE_THAN_ONE_FERMI_FACTOR")
        groups[c] = groups.get(c, 0) + coeff
    return groups


def _poles(R, w):
    R = sympy.together(R)
    if not R.is_rational_function(w):
        raise _Refusal("COEFFICIENT_NOT_RATIONAL_IN_VARIABLE")
    num, den = sympy.fraction(R)
    pn, pd = sympy.Poly(sympy.expand(num), w), sympy.Poly(sympy.expand(den), w)
    if pd.degree() - pn.degree() < 2:
        raise _Refusal("INTEGRAND_DECAY_BELOW_1_OVER_W2")
    roots = sympy.roots(pd)
    if sum(roots.values()) != pd.degree():
        raise _Refusal("DENOMINATOR_ROOTS_NOT_EXPLICIT")
    out = []
    for p, m in roots.items():
        im = sympy.im(p)
        if im.is_positive:
            out.append((p, m, +1))
        elif im.is_negative:
            out.append((p, m, -1))
        elif im.is_zero:
            raise _Refusal("POLE_ON_REAL_AXIS")
        else:
            raise _Refusal("POLE_HALF_PLANE_UNDETERMINED")
    return R, out


def _residue(R, w, p, m, g=sympy.Integer(1)):
    regular = sympy.cancel((w - p) ** m * R)
    return sympy.diff(regular * g, w, m - 1).subs(w, p) / sympy.factorial(m - 1)


def fermi_integral(expr, w, beta):
    """Closed form of int_R expr dw, expr = sum R_c(w) nF(c + w) + R_0(w)."""
    total = sympy.Integer(0)
    for c, coeff in _split_terms(expr, w).items():
        R, poles = _poles(coeff, w)
        for p, m, side in poles:
            if c is None:
                if side > 0:
                    total += 2 * sympy.pi * sympy.I * _residue(R, w, p, m)
                continue
            y = beta * (c + w) / (2 * sympy.pi)
            if side > 0:
                total += sympy.pi * sympy.I * _residue(R, w, p, m)
                total += _residue(R, w, p, m, sympy.polygamma(0, _HALF - sympy.I * y))
            else:
                total += _residue(R, w, p, m, sympy.polygamma(0, _HALF + sympy.I * y))
    return total


def verify_fermi_integral(integrand: str, claim: str, *, variable: str, beta: str,
                          symbols: Any, functions: Iterable[str] = (),
                          definitions: dict | None = None,
                          positive: tuple[str, ...] = (),
                          infinitesimal: str | None = None) -> dict:
    """int_R integrand d(variable) == claim, integrand built from nF(c +- w).

    ``infinitesimal`` names a positive symbol eta that moves real-axis
    poles off the axis (w - a + i eta): the integral is done at eta > 0 and
    the claim is compared with its limit eta -> 0+. The limit is taken by
    substitution, which is exact because the closed form is analytic in eta
    at 0 unless a denominator vanishes there; that case is refused.
    """
    inputs = {"rule": FERMI_RESIDUE_SPLITTING, "integrand_sha256": text_hash(integrand),
              "claim_sha256": text_hash(claim), "variable": variable, "beta": beta,
              **({"infinitesimal": infinitesimal} if infinitesimal else {})}
    if infinitesimal and infinitesimal not in positive:
        positive = (*positive, infinitesimal)
    try:
        space = CalculusSpace(symbols, functions, definitions=definitions)
        w, b = space.symbol(variable), space.symbol(beta)
        body = space.parse_expanded(integrand)
        target = expand_distributions(space.parse_expanded(claim), b)
    except AdapterError as exc:
        return {**inputs, "status": UNKNOWN, "reasons": [f"PARSE_FAILED:{exc.code}"]}
    sure = {s: sympy.Symbol(s.name, positive=True) for s in space.positives(tuple(positive))}
    back = {v: k for k, v in sure.items()}
    try:
        closed = fermi_integral(body.xreplace(sure), w, b.xreplace(sure)).xreplace(back)
    except _Refusal as refusal:
        return {**inputs, "status": UNKNOWN, "reasons": [refusal.reason]}
    if infinitesimal:
        eta = space.symbol(infinitesimal)
        limit = closed.subs(eta, 0)
        if limit.has(sympy.zoo, sympy.nan, sympy.oo) or target.has(eta):
            return {**inputs, "status": UNKNOWN, "reasons": ["INFINITESIMAL_LIMIT_NOT_REGULAR"]}
        closed = limit
    result = compare(closed, target, space, positive)
    status = {"ZERO": CERTIFIED_BY_RULE, "NONZERO": NONZERO}.get(result["verdict"], UNKNOWN)
    cert = {**inputs, "status": status, "derived": str(closed)[:4000]}
    return {**cert, "reasons": result.get("reasons", []),
            "counterexample": result.get("counterexample"),
            "diagnosis": result.get("diagnosis"),
            "certificate_hash": certificate_hash(cert) if status == CERTIFIED_BY_RULE else None}
