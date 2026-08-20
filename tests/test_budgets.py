"""Generic regression tests for wall-clock budgets (v0.2).

Synthetic content only. Covers the fail-closed budget contract:
* ``run_with_budget`` returns results within budget and raises
  ``BudgetExceeded`` (code TIME_BUDGET_EXCEEDED) beyond it;
* worker exceptions propagate unchanged (they are not budget events);
* ``set_budget_policy`` rejects unknown keys / invalid modes;
* a verifier-level timeout yields UNKNOWN with evidence kind
  TIME_BUDGET_EXCEEDED and NEVER ZERO or NONZERO.
"""
import time

import pytest

from symbolic_compactification import (NONZERO, UNKNOWN, ZERO,
                                       AdapterError, BudgetExceeded,
                                       get_budget_policy, run_with_budget,
                                       set_budget_policy, verify_equivalent)


def _restore_policy(saved):
    set_budget_policy(**saved)


def _boom():
    raise ValueError("worker failure")


# --------------------------------------------------------------------------- #
# run_with_budget mechanics
# --------------------------------------------------------------------------- #

def test_run_with_budget_returns_result_within_budget():
    assert run_with_budget(sum, ((1, 2, 3),), seconds=5.0,
                           operation="sum") == 6


def test_timeout_raises_budget_exceeded_with_stable_code():
    with pytest.raises(BudgetExceeded) as excinfo:
        run_with_budget(time.sleep, (0.5,), seconds=0.01,
                        operation="sleep")
    assert excinfo.value.code == "TIME_BUDGET_EXCEEDED"
    assert excinfo.value.operation == "sleep"


def test_worker_exception_propagates_unchanged():
    with pytest.raises(ValueError, match="worker failure"):
        run_with_budget(_boom, (), seconds=5.0, operation="boom")


def test_inline_mode_runs_directly():
    assert run_with_budget(lambda: 7, (), seconds=5.0,
                           operation="inline", mode="inline") == 7


def test_set_budget_policy_rejects_unknown_key():
    with pytest.raises(AdapterError) as excinfo:
        set_budget_policy(no_such_budget=1.0)
    assert excinfo.value.code == "BUDGET_POLICY_KEY_UNKNOWN"


def test_set_budget_policy_rejects_invalid_mode():
    with pytest.raises(AdapterError) as excinfo:
        set_budget_policy(mode="warp")
    assert excinfo.value.code == "BUDGET_POLICY_KEY_UNKNOWN"


def test_default_policy_shape():
    pol = get_budget_policy()
    assert pol["mode"] == "process"
    for key in ("mode", "residual_seconds", "expand_seconds",
                "simplify_seconds", "probe_simplify_seconds",
                "equals_seconds", "expand_complex_seconds",
                "factor_seconds", "factor_terms_seconds",
                "together_seconds", "cancel_seconds",
                "finite_expand_seconds"):
        assert key in pol


# --------------------------------------------------------------------------- #
# verifier-level timeout: UNKNOWN, never ZERO/NONZERO
# --------------------------------------------------------------------------- #

def _install_slow_simplify(monkeypatch, pause_seconds=0.5):
    """Deterministic stand-in for a runaway simplify: sleeps past any tiny
    budget. Keeps the timeout test free of wall-clock races."""
    import sympy

    def _slow_simplify(expr, *args, **kwargs):
        time.sleep(pause_seconds)
        return expr

    monkeypatch.setattr(sympy, "simplify", _slow_simplify)


def test_tiny_simplify_budget_yields_unknown_time_budget_exceeded(monkeypatch):
    """Force a tiny simplify budget (0.5 ms) on a residual that only a
    simplify can settle: the verdict must be UNKNOWN with evidence kind
    TIME_BUDGET_EXCEEDED — a timeout is never converted into ZERO or
    NONZERO."""
    _install_slow_simplify(monkeypatch)
    saved = get_budget_policy()
    try:
        set_budget_policy(mode="thread", simplify_seconds=0.0005)
        result = verify_equivalent(
            "(x**2 - 1)/(x - 1)", "x + 1",
            [{"name": "x", "real": True, "nonzero": True}])
    finally:
        _restore_policy(saved)

    assert result.verdict == UNKNOWN
    assert result.verdict not in (ZERO, NONZERO)
    kinds = {e.get("kind") for e in result.evidence}
    assert "TIME_BUDGET_EXCEEDED" in kinds
    timeout_evidence = [e for e in result.evidence
                        if e.get("kind") == "TIME_BUDGET_EXCEEDED"]
    assert timeout_evidence[0]["operation"] == "simplify"
    assert result.counterexample is None


def test_timeout_never_yields_a_definite_verdict_on_hard_residuals(monkeypatch):
    """Same invariant on a second residual shape: any budget breach keeps
    the verdict out of ZERO/NONZERO (fail-closed)."""
    _install_slow_simplify(monkeypatch)
    saved = get_budget_policy()
    try:
        set_budget_policy(mode="thread", simplify_seconds=0.0005)
        result = verify_equivalent(
            "1/x + 1/y", "(x + y)/(x*y)",
            [{"name": "x", "real": True, "nonzero": True},
             {"name": "y", "real": True, "nonzero": True}])
    finally:
        _restore_policy(saved)

    assert result.verdict not in (ZERO, NONZERO)
    assert result.verdict == UNKNOWN
    kinds = {e.get("kind") for e in result.evidence}
    assert "TIME_BUDGET_EXCEEDED" in kinds
