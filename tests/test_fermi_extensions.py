"""Two-Fermi products and real-axis poles (eta -> 0+), checked against quadrature."""
from __future__ import annotations

import mpmath as mp
import pytest
import sympy as sp

from symbolic_compactification.manybody import verify_fermi_integral
from symbolic_compactification.manybody.fermi_integral import fermi_integral

pytestmark = pytest.mark.release_critical

beta, G, eta = sp.symbols("beta G eta", positive=True)
a, b, w = sp.symbols("a b w", real=True)
nF, nB = sp.Function("nF"), sp.Function("nB")
VALS = {beta: sp.Rational(3, 2), G: sp.Rational(1, 2), a: sp.Rational(1, 3), b: sp.Rational(-2, 5)}


def _fermi(x):
    return 1 / (sp.exp(VALS[beta] * x) + 1)


def _bose(x):
    return 1 / (sp.exp(VALS[beta] * x) - 1)


def _quad(expr, points):
    with mp.workdps(30):
        f = sp.lambdify(w, expr.subs(VALS).replace(nF, _fermi), "mpmath")
        return complex(mp.quad(f, points))


@pytest.mark.parametrize("integrand", [
    nF(w + a) * nF(b - w) / (w**2 + G**2),
    nF(w - a) * nF(w + b) * w / ((w**2 + G**2) * (w - 1 + sp.I * G)),
])
def test_two_fermi_factors_match_quadrature(integrand):
    closed = complex(sp.N(fermi_integral(integrand, w, beta).subs(VALS).replace(nB, _bose), 20))
    assert abs(closed - _quad(integrand, [-mp.inf, -5, 0, 5, mp.inf])) < 1e-12


def test_real_axis_pole_limit_matches_quadrature():
    J = nF(w) / ((w - a + sp.I * eta) * (w - b + sp.I * G))
    limit = complex(sp.N(fermi_integral(J, w, beta).subs(eta, 0).subs(VALS), 20))
    A = float(VALS[a])
    small = _quad(J.subs(eta, sp.Float("1e-6", 30)),
                  [-mp.inf, -5, A - 0.1, A - 1e-3, A, A + 1e-3, A + 0.1, 5, mp.inf])
    assert abs(limit - small) < 1e-4


def test_card_level_routes():
    S = [{"name": "beta"}, {"name": "G"}, {"name": "eta"}, {"name": "a"}, {"name": "w"}]
    kw = {"variable": "w", "beta": "beta", "symbols": S, "positive": ("beta", "G")}
    closed = fermi_integral(nF(w) / ((w - a + sp.I * eta) * (w + sp.I * G)), w, beta).subs(eta, 0)
    ok = verify_fermi_integral("nF(w)/((w - a + I*eta)*(w + I*G))", str(closed),
                               infinitesimal="eta", **kw)
    assert ok["status"] == "CERTIFIED_BY_RULE"
    no_eta = verify_fermi_integral("nF(w)/((w - a)*(w + I*G))", "0", **kw)
    assert "POLE_ON_REAL_AXIS" in no_eta["reasons"]
    same = verify_fermi_integral("nF(w + a)*nF(w + a)/(w**2 + G**2)", "0", **kw)
    assert same["status"] == "UNKNOWN" and "UNSUPPORTED_FERMI_PRODUCT" in same["reasons"]
