"""General numeric support for a scalar claim ``lhs == rhs``.

Numeric agreement is support, never a proof: the check refutes a wrong rewrite
with an explicit counterexample and supports a correct one, always under the
``NUMERICAL_SUPPORT`` status.
"""
from __future__ import annotations

import pytest

from symbolic_compactification.manybody import (NUMERICAL_SUPPORT,
                                                check_numeric_equivalence)

ONE_SYMBOL = [{"name": "x", "real": True}]
TWO_SYMBOLS = [{"name": "a", "real": True}, {"name": "c", "real": True}]


@pytest.mark.parametrize("lhs, rhs, symbols", [
    ("sin(x)**2 + cos(x)**2", "1", ONE_SYMBOL),
    ("(x**2 - 1)/(x - 1)", "x + 1", ONE_SYMBOL),
    ("(a**2 - c**2)/(a - c)", "a + c", TWO_SYMBOLS),
])
def test_true_identities_are_supported(lhs, rhs, symbols):
    result = check_numeric_equivalence(lhs, rhs, symbols=symbols)
    assert result["status"] == NUMERICAL_SUPPORT
    assert result["numeric"] == "AGREES", result.get("reasons")
    assert result["points"] >= 8
    assert len(result["certificate_hash"]) == 64


def test_sign_error_disagrees_with_a_counterexample():
    result = check_numeric_equivalence(
        "sin(x)**2 + cos(x)**2", "1 + x/1000", symbols=ONE_SYMBOL)
    assert result["status"] == NUMERICAL_SUPPORT
    assert result["numeric"] == "DISAGREES"
    point = result["counterexample"]["point"]
    assert set(point) == {"x"}
    assert result["counterexample"]["lhs_value"] is not None


def test_vacuous_zero_identity_is_unavailable():
    result = check_numeric_equivalence("x - x", "0", symbols=ONE_SYMBOL)
    assert result["numeric"] == "UNAVAILABLE"
    assert "VACUOUS_BOTH_SIDES_NEAR_ZERO" in result["reasons"]


def test_undeclared_name_fails_closed():
    result = check_numeric_equivalence("sin(q)", "0", symbols=ONE_SYMBOL)
    assert result["numeric"] == "UNAVAILABLE"
    assert any(r.startswith("PARSE_FAILED") for r in result["reasons"])


def test_coincidence_edge_is_added_for_two_real_symbols():
    result = check_numeric_equivalence(
        "(a**2 - c**2)/(a - c)", "a + c", symbols=TWO_SYMBOLS, count=12)
    # 12 generic witnesses plus at least one a->c coincidence probe.
    assert result["certificate"]["edge_pairs"] >= 1
    assert result["points"] > 12
