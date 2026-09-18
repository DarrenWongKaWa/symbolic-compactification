"""Test-collection policy for the explicit release-critical gate."""
from __future__ import annotations


def pytest_sessionfinish(session, exitstatus):
    """Reap budget workers so Python 3.13 pytest does not hang after pass."""
    try:
        from symbolic_compactification.budgets import shutdown_budget_pool
    except Exception:
        return
    shutdown_budget_pool()


def pytest_ignore_collect(collection_path, config):
    """Keep ``pytest -m release_critical`` fast and dependency-minimal.

    Marker filtering normally happens after importing every test module.  The
    wider historical suite includes tests for optional extras, so a core-only
    release environment could fail during unrelated collection before pytest
    reaches the marked gate.  The exact release command owns one explicit test
    module and may skip importing every other ``test_*.py`` module.

    Other marker expressions and ordinary test invocations are unchanged.
    """
    markexpr = config.getoption("markexpr")
    if (collection_path.suffix == ".py"
            and collection_path.name.startswith("test_")):
        if markexpr == "release_critical":
            return collection_path.name != "test_release_critical.py"
        if markexpr == "derivation_audit_release_critical":
            return collection_path.name != (
                "test_derivation_audit_release_critical.py")
    return None
