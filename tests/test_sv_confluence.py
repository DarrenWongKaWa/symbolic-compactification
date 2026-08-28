"""Typed confluence limit cascade. Timeout is UNKNOWN, never ZERO."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.representation_invention.dd import newton_first, repeated_diagonal
from research.scalable_verification.api import NONZERO, UNKNOWN, ZERO
from research.scalable_verification.confluence import (
    LIMIT_MODE,
    LIMIT_OPS_CAP,
    LIMIT_SECONDS,
    check_limit,
)
from research.scalable_verification.confluence import engine as confluence_engine
from symbolic_compactification.budgets import BudgetExceeded


def _xy():
    return sympy.symbols("x y")


@pytest.fixture
def no_blind_limit(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("sympy.limit must not run on this case")

    monkeypatch.setattr(confluence_engine, "_budgeted_sympy_limit", _boom)


def test_limit_budget_constants():
    assert LIMIT_SECONDS > 0
    assert LIMIT_SECONDS <= 8
    assert LIMIT_OPS_CAP == 80
    assert LIMIT_MODE == "process"


def test_rational_difference_of_squares_to_2x(no_blind_limit):
    x, y = _xy()
    r = check_limit((x**2 - y**2) / (x - y), y, x, 2 * x)
    assert r.verdict == ZERO
    assert r.verdict != UNKNOWN
    assert r.provenance == "together_cancel"
    assert any(s.startswith("together_cancel") for s in r.steps)


def test_exp_first_dd_to_exp(no_blind_limit):
    x, y = _xy()
    z = sympy.symbols("z")
    F = newton_first(sympy.exp(z), z, x, y)
    r = check_limit(F, y, x, sympy.exp(x))
    assert r.verdict == ZERO
    assert r.provenance in {
        "valuation",
        "series",
        "lhopital",
        "newton_first_dd",
    }
    assert r.provenance != "UNKNOWN"
    assert repeated_diagonal(sympy.exp(z), z, x) == sympy.exp(x)


def test_continuous_substitution(no_blind_limit):
    x, y = _xy()
    r = check_limit(x + y, y, x, 2 * x)
    assert r.verdict == ZERO
    assert r.provenance == "substitution"


def test_wrong_target_is_nonzero(no_blind_limit):
    x, y = _xy()
    r = check_limit((x**2 - y**2) / (x - y), y, x, 3 * x)
    assert r.verdict == NONZERO
    assert r.verdict != ZERO


def test_non_removable_pole(no_blind_limit):
    x, y = _xy()
    r = check_limit(1 / (x - y), y, x, sympy.Integer(0))
    assert r.verdict == NONZERO
    assert r.verdict != ZERO
    assert r.provenance in {"valuation", "series", "together_cancel"}


def test_wrong_sign_exp_dd(no_blind_limit):
    x, y = _xy()
    z = sympy.symbols("z")
    F = -newton_first(sympy.exp(z), z, x, y)
    r = check_limit(F, y, x, sympy.exp(x))
    assert r.verdict == NONZERO
    assert r.verdict != ZERO


def test_timeout_is_unknown_never_zero(monkeypatch):
    def _boom(*_a, **_k):
        raise BudgetExceeded("confluence_limit", LIMIT_SECONDS)

    monkeypatch.setattr(confluence_engine, "_budgeted_sympy_limit", _boom)
    x, y = _xy()
    r = check_limit(sympy.exp(1 / (y - x)), y, x, sympy.Integer(0))
    assert r.verdict == UNKNOWN
    assert r.verdict != ZERO
    assert "timeout" in r.provenance


def test_size_guard_skips_limit_unknown(monkeypatch):
    monkeypatch.setattr(confluence_engine, "_ops_too_large", lambda _e: True)

    def _boom(*_a, **_k):
        raise AssertionError("sympy.limit skipped when count_ops > 80")

    monkeypatch.setattr(confluence_engine, "_budgeted_sympy_limit", _boom)
    x, y = _xy()
    r = check_limit(sympy.exp(1 / (y - x)), y, x, sympy.Integer(0))
    assert r.verdict == UNKNOWN
    assert r.verdict != ZERO
    assert "skip_count_ops" in r.provenance


def test_newton_first_dd_helper_uses_repeated_diagonal():
    x, y, z = sympy.symbols("x y z")
    F = newton_first(sympy.exp(z), z, x, y)
    got = confluence_engine._step_newton_first_dd(F, y, x)
    assert got is not None
    assert confluence_engine._expr_equal(got, sympy.exp(x)) is True
    assert confluence_engine._expr_equal(got, -sympy.exp(x)) is False
    assert confluence_engine._expr_equal(
        got, repeated_diagonal(sympy.exp(z), z, x),
    ) is True


def test_result_carries_step_provenance(no_blind_limit):
    x, y = _xy()
    r = check_limit((x**2 - y**2) / (x - y), y, x, 2 * x)
    assert isinstance(r.provenance, str)
    assert r.provenance
    assert isinstance(r.steps, tuple)
    assert r.steps
    payload = r.to_dict()
    assert payload["verdict"] == ZERO
    assert payload["provenance"] == r.provenance
