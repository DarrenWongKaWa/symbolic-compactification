"""Matsubara sums by the residue theorem: textbook identities and refusals."""
from __future__ import annotations

import pytest

from symbolic_compactification.manybody import (MATSUBARA_POLES_OFF_AXIS,
                                                matsubara_closed_form,
                                                verify_matsubara_sum)

pytestmark = pytest.mark.release_critical

SYMBOLS = [
    {"name": "a", "real": True}, {"name": "c", "real": True},
    {"name": "e", "real": True}, {"name": "g", "real": True, "nonzero": True},
    {"name": "beta", "real": True, "nonzero": True},
]
OFF_AXIS = (MATSUBARA_POLES_OFF_AXIS,)


def check(summand, claim, statistics="fermion", **kw):
    return verify_matsubara_sum(summand, claim, variable="z", beta="beta",
                                statistics=statistics, symbols=SYMBOLS, **kw)


@pytest.mark.parametrize("summand, claim, statistics, extra", [
    ("1/((z-a)*(z-c))", "(nF(a)-nF(c))/(a-c)", "fermion", {}),
    ("1/((z-a)*(z-c))", "-(nB(a)-nB(c))/(a-c)", "boson", {"declared_rules": OFF_AXIS}),
    ("1/((z-a)*(z+a))", "-tanh(beta*a/2)/(2*a)", "fermion", {}),
    ("1/(z-a)**2", "-beta*exp(beta*a)/(exp(beta*a)+1)**2", "fermion", {}),
    ("1/(z-a)", "nF(a)", "fermion", {"convergence": "plus"}),
    ("1/(z-a)", "nF(a)-1", "fermion", {"convergence": "minus"}),
    ("1/(z-a)", "-nB(a)", "boson", {"convergence": "plus", "declared_rules": OFF_AXIS}),
    ("1/((z-e-I*g)*(z-e+I*g))", "(nF(e+I*g)-nF(e-I*g))/(2*I*g)", "fermion",
     {"declared_rules": OFF_AXIS}),
])
def test_textbook_sums_are_certified_by_rule(summand, claim, statistics, extra):
    result = check(summand, claim, statistics, **extra)
    assert result.status == "CERTIFIED_BY_RULE", result.reasons
    assert result.symbolic_verdict == "ZERO"
    assert result.numeric["status"] == "AGREES"
    assert result.certificate_hash and len(result.certificate_hash) == 64


def test_sign_error_is_nonzero_with_counterexample():
    result = check("1/((z-a)*(z-c))", "(nF(c)-nF(a))/(a-c)")
    assert result.status == "NONZERO"
    assert result.numeric["status"] == "DISAGREES"
    assert result.certificate_hash is None


@pytest.mark.parametrize("summand, extra, reason", [
    ("z/(z-a)", {}, "MATSUBARA_SUM_DIVERGES"),
    ("1/(z-a)", {}, "CONVERGENCE_FACTOR_REQUIRED"),
    ("exp(z)/(z-a)**2", {}, "SUMMAND_NOT_RATIONAL_IN_VARIABLE"),
])
def test_theorem_hypotheses_fail_closed(summand, extra, reason):
    result = check(summand, "0", **extra)
    assert result.status == "UNKNOWN"
    assert reason in result.reasons


def test_bosonic_pole_at_zero_frequency_needs_declaration():
    result = check("1/((z-a)*(z-c))", "-(nB(a)-nB(c))/(a-c)", "boson")
    assert result.status == "ASSUMPTION_REQUIRED"
    assert "POLE_AXIS_SEPARATION_NOT_PROVEN" in result.reasons


def test_fermionic_real_poles_are_off_axis_without_declaration():
    # fermionic frequencies never vanish, so real poles (even a = 0) are safe
    assert check("1/((z-a)*(z-c))", "(nF(a)-nF(c))/(a-c)").status == "CERTIFIED_BY_RULE"


def test_closed_form_helper_returns_none_outside_theorem():
    kw = {"variable": "z", "beta": "beta", "statistics": "fermion", "symbols": SYMBOLS}
    assert matsubara_closed_form("z/(z-a)", **kw) is None
    assert "exp" in matsubara_closed_form("1/((z-a)*(z-c))", **kw)
