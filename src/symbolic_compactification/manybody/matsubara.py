"""Matsubara frequency sums of rational summands by the residue theorem.

For a rational F(z) whose poles z_k avoid the Matsubara axis,

    fermions  T sum_n F(i w_n) =  sum_k Res[F(z) nF(z),  z_k]
    bosons    T sum_n F(i v_n) = -sum_k Res[F(z) nB(z),  z_k]

when deg(den) - deg(num) >= 2. With exactly one power of decay the sum needs
a convergence factor exp(+-i w_n 0+): ``plus`` keeps the formulas above,
``minus`` uses  -sum Res[F nF(-z)]  (fermions) and  +sum Res[F nB(-z)]
(bosons). The theorem's hypotheses are checked here:

* F is rational in z and every denominator factor has explicit roots;
* the decay condition, or a declared convergence factor for 1/z decay;
* each pole is provably off the Matsubara axis, or the workspace declares
  ``MATSUBARA_POLES_OFF_AXIS``.

The claimed closed form is then compared with the residue sum by the exact
verifier. A deterministic mpmath summation at rational sample points is an
independent cross-check; on its own it is numerical support, never a proof.
"""
from __future__ import annotations

from typing import Any, Optional

import mpmath
import sympy

from ..audit.schema import MATSUBARA_POLES_OFF_AXIS, MATSUBARA_RESIDUE_THEOREM
from ..models import AdapterError
from ..verifier import verify_equivalent
from ._common import (ASSUMPTION_REQUIRED, CERTIFIED_BY_RULE, NONZERO,
                      NUMERIC_AGREES, NUMERIC_DISAGREES, NUMERIC_UNAVAILABLE,
                      UNKNOWN, ManyBodyResult, Namespace, bose, certificate_hash,
                      expand_distributions, fermi, sample_points, text_hash)

STATISTICS = ("fermion", "boson")
CONVERGENCE = ("none", "plus", "minus")
_NUMERIC_TOLERANCE = mpmath.mpf("1e-12")


def _poles(F: sympy.Expr, z: sympy.Symbol) -> tuple[dict, list[str]]:
    """Pole -> order for a rational F, or refusal reasons."""
    _, den = sympy.fraction(sympy.together(F))
    poles: dict = {}
    for factor in sympy.Mul.make_args(den):
        base, exponent = factor.as_base_exp()
        if not base.has(z):
            continue
        if not (exponent.is_Integer and exponent > 0):
            return {}, ["NON_POLYNOMIAL_DENOMINATOR"]
        poly = sympy.Poly(base, z)
        roots = sympy.roots(poly)
        if sum(roots.values()) != poly.degree():
            return {}, ["DENOMINATOR_ROOTS_NOT_EXPLICIT"]
        for root, mult in roots.items():
            # Heuristic zero test: an unmerged double pole leaves a singular
            # residue term, which verify_matsubara_sum refuses (never ZERO).
            match = next((p for p in poles if sympy.simplify(p - root) == 0), root)
            poles[match] = poles.get(match, 0) + mult * int(exponent)
    return poles, []


def _decay_gap(F: sympy.Expr, z: sympy.Symbol) -> tuple[int, sympy.Expr]:
    num, den = sympy.fraction(sympy.together(F))
    pn, pd = sympy.Poly(sympy.expand(num), z), sympy.Poly(sympy.expand(den), z)
    gap = pd.degree() - pn.degree()
    tail = pn.LC() / pd.LC() if gap == 1 else sympy.Integer(0)
    return gap, tail


def _off_axis(pole: sympy.Expr, statistics: str) -> bool:
    re_part, im_part = pole.as_real_imag()
    if re_part.is_nonzero:
        return True
    if im_part.is_zero:
        # fermionic frequencies never vanish; the bosonic v_0 = 0 does
        return statistics == "fermion" or bool(pole.is_nonzero)
    return False


def _residue_sum(F, z, poles, weight) -> sympy.Expr:
    num, den = sympy.fraction(sympy.together(F))
    total = sympy.Integer(0)
    for pole, order in poles.items():
        if order == 1:
            # N(p) w(p) / D'(p): exact, also for a pole sqrt(k^2 + m^2), where
            # cancel cannot remove (z - sqrt(k^2 + m^2)) from z^2 - k^2 - m^2
            total += num.subs(z, pole) * weight(pole) / sympy.diff(den, z).subs(z, pole)
            continue
        regular = sympy.cancel((z - pole) ** order * F)
        term = sympy.diff(regular * weight(z), z, order - 1).subs(z, pole)
        total += term / sympy.factorial(order - 1)
    return total


def residue_closed_form(F, z, beta, poles, statistics: str, convergence: str) -> sympy.Expr:
    if statistics == "fermion":
        if convergence == "minus":
            return -_residue_sum(F, z, poles, lambda x: fermi(beta, -x))
        return _residue_sum(F, z, poles, lambda x: fermi(beta, x))
    if convergence == "minus":
        return _residue_sum(F, z, poles, lambda x: bose(beta, -x))
    return -_residue_sum(F, z, poles, lambda x: bose(beta, x))


def numeric_matsubara_sum(F, z, beta, values: dict, statistics: str,
                          tail: sympy.Expr, convergence: str) -> mpmath.mpc:
    """T sum_n F(i w_n) by symmetric pairing and mpmath acceleration."""
    f = sympy.lambdify(z, F.subs(values), "mpmath")
    T = 1 / mpmath.mpmathify(sympy.N(values[beta], 30))
    if statistics == "fermion":
        w = lambda n: (2 * n + 1) * mpmath.pi * T  # noqa: E731
        total = mpmath.nsum(lambda n: f(1j * w(n)) + f(-1j * w(n)), [0, mpmath.inf])
    else:
        w = lambda n: 2 * n * mpmath.pi * T  # noqa: E731
        total = f(0) + mpmath.nsum(lambda n: f(1j * w(n)) + f(-1j * w(n)), [1, mpmath.inf])
    total = T * total
    c = mpmath.mpmathify(complex(sympy.N(tail.subs(values), 30)))
    if convergence == "plus":
        total += c / 2
    elif convergence == "minus":
        total -= c / 2
    return total


def _numeric_check(F, z, beta, closed, claim, statistics, tail, convergence,
                   positive=()) -> dict:
    free = (closed.free_symbols | claim.free_symbols | F.free_symbols) - {z}
    worst = mpmath.mpf(0)
    try:
        with mpmath.workdps(30):
            for point in sample_points(free, positive=(beta, *positive)):
                exact = mpmath.mpmathify(complex(sympy.N(claim.subs(point), 30)))
                summed = numeric_matsubara_sum(F, z, beta, point, statistics, tail, convergence)
                scale = max(mpmath.mpf(1), abs(exact))
                worst = max(worst, abs(summed - exact) / scale)
    except (ValueError, TypeError, ZeroDivisionError, ArithmeticError):
        return {"status": NUMERIC_UNAVAILABLE, "points": 0}
    status = NUMERIC_AGREES if worst < _NUMERIC_TOLERANCE else NUMERIC_DISAGREES
    return {"status": status, "points": 3, "max_rel_diff": mpmath.nstr(worst, 3)}


def _counterexample(closed, target, beta, free, positive) -> Optional[dict]:
    """Exact nonzero value of closed - target at a rational point, if provable.

    Same standard as the exact verifier: ``value.equals(0) is False``.
    """
    for point in sample_points(free, positive=(beta, *positive), count=3, seed=7):
        value = (closed - target).subs(point)
        if value.equals(0) is False:
            return {str(k): str(v) for k, v in point.items()}
    return None


def verify_matsubara_sum(summand: str, claim: str, *, variable: str, beta: str,
                         statistics: str, symbols: Any, functions: Any = None,
                         convergence: str = "none",
                         declared_rules: tuple[str, ...] = (),
                         positive: tuple[str, ...] = (),
                         numeric: bool = True,
                         definitions: dict | None = None) -> ManyBodyResult:
    """Check  T sum_n summand(i w_n) == claim  under the residue theorem.
    Named definitions (omega_k() = sqrt(k^2 + m^2)) are expanded first."""
    inputs = {"rule": MATSUBARA_RESIDUE_THEOREM, "summand_sha256": text_hash(summand),
              "claim_sha256": text_hash(claim), "variable": variable, "beta": beta,
              "statistics": statistics, "convergence": convergence}

    def result(status, reasons, derived="", verdict="NOT_RUN", numeric_info=None):
        cert = {**inputs, "status": status, "derived": derived,
                "symbolic_verdict": verdict, "numeric": numeric_info or {}}
        return ManyBodyResult(
            kind="MATSUBARA_SUM", status=status, rule_id=MATSUBARA_RESIDUE_THEOREM,
            reasons=tuple(reasons), derived=derived, symbolic_verdict=verdict,
            numeric=numeric_info or {}, certificate=cert,
            certificate_hash=certificate_hash(cert) if status == CERTIFIED_BY_RULE else None)

    if statistics not in STATISTICS or convergence not in CONVERGENCE:
        return result(UNKNOWN, ["MATSUBARA_SPEC_INVALID"])
    try:
        if definitions:
            from .calculus import CalculusSpace
            space = CalculusSpace(symbols, functions or (), complex_names=(variable,),
                                  definitions=definitions)
            parse = space.parse_expanded
        else:
            space = Namespace(symbols, functions, complex_names=(variable,))
            parse = space.parse
        z, b = space.symbol(variable), space.symbol(beta)
        pos = space.positives(tuple(positive))
        F = parse(summand)
        target = expand_distributions(parse(claim), b)
    except AdapterError as exc:
        return result(UNKNOWN, [f"PARSE_FAILED:{exc.code}"])
    if not F.is_rational_function(z):
        return result(UNKNOWN, ["SUMMAND_NOT_RATIONAL_IN_VARIABLE"])
    gap, tail = _decay_gap(F, z)
    if gap <= 0:
        return result(UNKNOWN, ["MATSUBARA_SUM_DIVERGES"])
    if gap == 1 and convergence == "none":
        return result(UNKNOWN, ["CONVERGENCE_FACTOR_REQUIRED"])
    if gap >= 2:
        tail = sympy.Integer(0)
    poles, reasons = _poles(F, z)
    if reasons:
        return result(UNKNOWN, reasons)
    if not all(_off_axis(p, statistics) for p in poles):
        if MATSUBARA_POLES_OFF_AXIS not in declared_rules:
            return result(ASSUMPTION_REQUIRED, ["POLE_AXIS_SEPARATION_NOT_PROVEN"])
    closed = residue_closed_form(F, z, b, poles, statistics, convergence)
    derived = str(closed)
    if closed.has(sympy.zoo, sympy.nan, sympy.oo, -sympy.oo):
        return result(UNKNOWN, ["RESIDUE_EVALUATION_SINGULAR"], derived)
    lhs, rhs = closed.rewrite(sympy.exp), target.rewrite(sympy.exp)
    verdict = verify_equivalent(
        str(lhs), str(rhs), space.declared_for(lhs, rhs),
        functions=space.functions).verdict
    numeric_info = (_numeric_check(F, z, b, closed, target, statistics, tail,
                                   convergence, pos)
                    if numeric else {"status": "NOT_RUN"})
    if verdict not in ("ZERO", "NONZERO") and numeric_info.get("status") == NUMERIC_DISAGREES:
        point = _counterexample(closed, target, b, (lhs.free_symbols | rhs.free_symbols), pos)
        if point is not None:
            numeric_info = {**numeric_info, "counterexample": point}
            verdict = "NONZERO"
    if verdict == "ZERO":
        if numeric_info.get("status") == NUMERIC_DISAGREES:
            return result(UNKNOWN, ["NUMERIC_CROSSCHECK_DISAGREES"], derived, verdict, numeric_info)
        return result(CERTIFIED_BY_RULE, [], derived, verdict, numeric_info)
    if verdict == "NONZERO":
        return result(NONZERO, ["CLAIM_DIFFERS_FROM_RESIDUE_SUM"], derived, verdict, numeric_info)
    extra = ["NUMERICAL_SUPPORT_ONLY"] if numeric_info.get("status") == NUMERIC_AGREES else []
    return result(UNKNOWN, ["SYMBOLIC_COMPARISON_UNDECIDED", *extra], derived, verdict, numeric_info)


def matsubara_closed_form(summand: str, *, variable: str, beta: str, statistics: str,
                          symbols: Any, functions: Any = None,
                          convergence: str = "none") -> Optional[str]:
    """Residue closed form as a string, or None when the theorem does not apply."""
    space = Namespace(symbols, functions, complex_names=(variable,))
    z, b = space.symbol(variable), space.symbol(beta)
    F = space.parse(summand)
    if not F.is_rational_function(z):
        return None
    gap, _ = _decay_gap(F, z)
    if gap <= 0 or (gap == 1 and convergence == "none"):
        return None
    poles, reasons = _poles(F, z)
    if reasons:
        return None
    return str(residue_closed_form(F, z, b, poles, statistics, convergence))
