"""Divided differences, series coefficients and digamma reflection."""
from __future__ import annotations

import json

import pytest
import sympy

from symbolic_compactification import cli
from symbolic_compactification.manybody import (certify_remainder, reflect_polygamma,
                                                verify_identity, verify_series_coefficient)

pytestmark = pytest.mark.release_critical

S = [{"name": n} for n in ("x", "y", "z", "w", "a")]
T = [{"name": "beta", "nonzero": True}, {"name": "G", "nonzero": True},
     {"name": "e"}, {"name": "mu"}]
ZP = "1/2 + beta*G/(2*pi) + I*beta*(e-mu)/(2*pi)"
ZM = "1/2 + beta*G/(2*pi) - I*beta*(e-mu)/(2*pi)"
RHO0 = f"1/2 + I/(2*pi)*(polygamma(0, {ZP}) - polygamma(0, {ZM}))"


@pytest.mark.parametrize("lhs, rhs, verdict", [
    ("DD_f(x,y,y)", "(DD_f(x,y) - D_f(1,y))/(x - y)", "ZERO"),
    ("DD_f(x,y,y)", "(DD_f(x,y) - D_f(1,y))/(y - x)", "NONZERO"),
    ("DD_f(x,x,x)", "D_f(2,x)/2", "ZERO"),
    ("DD_f(x,x,x)", "D_f(2,x)", "NONZERO"),
    ("DD_f(x,x,y)", "(D_f(1,x) - DD_f(x,y))/(x - y)", "ZERO"),
    ("DD_f(x,y,z)", "DD_f(z,x,y)", "ZERO"),
])
def test_divided_difference_identities(lhs, rhs, verdict):
    result = verify_identity(lhs, rhs, symbols=S, functions=["f"])
    assert result["verdict"] == verdict
    if verdict == "NONZERO":
        assert result["counterexample"]["test_functions"]["f"]


def test_series_coefficient_of_shifted_node():
    kw = {"variable": "w", "order": 2, "symbols": S, "functions": ["f"]}
    assert verify_series_coefficient("DD_f(x+w,y,z)", "DD_f(x,x,x,y,z)", **kw)["verdict"] == "ZERO"
    assert verify_series_coefficient("DD_f(x+w,y,z)", "2*DD_f(x,x,x,y,z)", **kw)["verdict"] == "NONZERO"


def test_reflection_links_digamma_and_fermi_forms():
    b, e, mu = sympy.symbols("beta e mu", real=True)
    y = b * (e - mu) / (2 * sympy.pi)
    rho0 = sympy.Rational(1, 2) + sympy.I / (2 * sympy.pi) * (
        sympy.polygamma(0, sympy.Rational(1, 2) + sympy.I * y)
        - sympy.polygamma(0, sympy.Rational(1, 2) - sympy.I * y))
    residual = reflect_polygamma(rho0) - 1 / (sympy.exp(b * (e - mu)) + 1)
    assert sympy.simplify(residual.rewrite(sympy.exp)) == 0


def test_gamma_limit_of_digamma_occupation_via_series():
    kw = {"variable": "G", "point": "0", "symbols": T, "positive": ("beta", "G")}
    fermi = "1/(exp(beta*(e-mu))+1)"
    assert certify_remainder(RHO0, fermi, order=1, **kw).status == "CERTIFIED_BY_RULE"
    assert certify_remainder(RHO0, fermi, order=2, **kw).status == "NONZERO"


def test_cli_identity_and_coefficient(capsys):
    symbols = json.dumps(S)
    assert cli.main(["manybody", "identity", "--lhs", "DD_f(x,x,x)", "--rhs", "D_f(2,x)/2",
                     "--functions", "f", "--symbols", symbols]) == 0
    assert json.loads(capsys.readouterr().out)["verdict"] == "ZERO"
    assert cli.main(["manybody", "coefficient", "--expr", "DD_f(x+w,y,z)", "--claim",
                     "DD_f(x,x,x,y,z)", "--variable", "w", "--order", "2",
                     "--functions", "f", "--symbols", symbols]) == 0
    assert json.loads(capsys.readouterr().out)["verdict"] == "ZERO"
