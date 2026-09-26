"""Remainder certificates for asymptotic expansions."""
from __future__ import annotations

import pytest

from symbolic_compactification.manybody import (certify_remainder,
                                                check_frequency_integral,
                                                estimate_remainder_order)

pytestmark = pytest.mark.release_critical

SYMBOLS = [
    {"name": "a", "real": True}, {"name": "b", "real": True},
    {"name": "c", "real": True}, {"name": "e", "real": True, "nonzero": True},
    {"name": "g", "real": True, "nonzero": True},
    {"name": "w", "real": True, "nonzero": True},
    {"name": "x", "real": True, "nonzero": True},
    {"name": "beta", "real": True, "nonzero": True},
]


def cert(f, p, variable, point, order, **kw):
    return certify_remainder(f, p, variable=variable, point=point, order=order,
                             symbols=SYMBOLS, **kw)


@pytest.mark.parametrize("f, p, variable, point, order, extra, limit", [
    ("a/g + b*g", "a/g", "g", "0", 1, {}, "b"),                      # Laurent in Gamma
    ("1/(I*w - e)", "1/(I*w) + e/(I*w)**2", "w", "oo", -3, {}, "I*e**2"),  # G(iw) tail
    ("polygamma(0, x)", "log(x) - 1/(2*x)", "x", "oo", -2, {}, "-1/12"),
    ("exp(-1/x)", "0", "x", "0", 5, {"direction": "+"}, "0"),         # beyond all orders
])
def test_remainders_are_certified(f, p, variable, point, order, extra, limit):
    result = cert(f, p, variable, point, order, **extra)
    assert result.status == "CERTIFIED_BY_RULE", result.reasons
    assert result.derived.split(", ")[0] == limit
    assert result.numeric["status"] == "AGREES"
    assert len(result.certificate_hash) == 64


def test_overclaimed_order_is_nonzero():
    result = cert("1/(I*w - e)", "1/(I*w) + e/(I*w)**2", "w", "oo", -4)
    assert result.status == "NONZERO"
    assert "REMAINDER_QUOTIENT_DIVERGES" in result.reasons


def test_parameter_dependent_divergence_stays_unknown():
    # c may be zero, and then the claim holds: not decided without a sign
    result = cert("a/g + c*g", "a/g", "g", "0", 2)
    assert result.status == "UNKNOWN"


def test_two_sided_limit_must_agree():
    result = cert("exp(-1/x)", "0", "x", "0", 1)
    assert result.status != "CERTIFIED_BY_RULE"


def test_numeric_order_estimate_is_support_only():
    report = estimate_remainder_order("polygamma(0, x)", "log(x) - 1/(2*x)",
                                      variable="x", point="oo", symbols=SYMBOLS)
    assert report["status"] == "NUMERICAL_SUPPORT"
    assert abs(report["slopes"][-1] + 2) < 1e-3


def test_fermi_lorentzian_integral_numerical_support():
    kw = {"variable": "w", "symbols": SYMBOLS, "beta": "beta", "positive": ("g",)}
    lorentz = "nF(w)*g/pi/((w - e)**2 + g**2)"
    good = "1/2 - im(polygamma(0, 1/2 + beta*(g + I*e)/(2*pi)))/pi"
    bad = "1/2 + im(polygamma(0, 1/2 + beta*(g + I*e)/(2*pi)))/pi"
    assert check_frequency_integral(lorentz, good, **kw)["numeric"] == "AGREES"
    assert check_frequency_integral(lorentz, bad, **kw)["numeric"] == "DISAGREES"
    assert check_frequency_integral(lorentz, good, **kw)["status"] == "NUMERICAL_SUPPORT"


def test_direction_is_refused_at_infinity():
    result = cert("1/(I*w - e)", "1/(I*w)", "w", "oo", -2, direction="+")
    assert result.status == "UNKNOWN"
    assert "DIRECTION_NOT_APPLICABLE_AT_INFINITY" in result.reasons
