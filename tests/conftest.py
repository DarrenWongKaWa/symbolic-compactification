"""Test-collection policy for the explicit release-critical gate."""
from __future__ import annotations


def pytest_ignore_collect(collection_path, config):
    """Keep ``pytest -m release_critical`` fast and dependency-minimal.

    Marker filtering normally happens after importing every test module.  The
    wider historical suite includes tests for optional extras, so a core-only
    release environment could fail during unrelated collection before pytest
    reaches the marked gate.  The exact release command owns one explicit test
    module and may skip importing every other ``test_*.py`` module.

    Other marker expressions and ordinary test invocations are unchanged.
    """
    if config.getoption("markexpr") != "release_critical":
        return None
    if (collection_path.suffix == ".py"
            and collection_path.name.startswith("test_")):
        return collection_path.name != "test_release_critical.py"
    return None
