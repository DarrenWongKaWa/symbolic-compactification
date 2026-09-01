"""Scientifically-neutral generic symbolic smoke tests.

These exercise the strict parser and exact verifier on generic complex-variable,
rational, polynomial and trigonometric identities loaded from the committed
``tests/fixtures/basic/`` fixtures. There is deliberately NO domain-specific content:
only generic symbols (a, b, t, x, y) and standard operations.

Every identity pair must adjudicate ZERO; every deliberately-broken mutation of
the base identity must adjudicate NONZERO with an exact counterexample.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from symbolic_compactification import (
    NONZERO,
    ZERO,
    load_expression,
    verify_equivalent,
)
from symbolic_compactification.cli import load_symbols_file

# --------------------------------------------------------------------------- #
# fixture locations
# --------------------------------------------------------------------------- #

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "tests" / "fixtures" / "basic"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def symbols() -> list:
    """The canonical generic symbol declarations from tests/fixtures/basic."""
    return load_symbols_file(str(EXAMPLES / "symbols.json"))


def load_fixture(name: str):
    """Load one examples/basic expression file against the canonical symbols."""
    return load_expression(str(EXAMPLES / name), symbols())


def verify(current_name: str, candidate_name: str):
    """Verify two fixture files against each other using the canonical symbols."""
    current = load_fixture(current_name)
    candidate = load_fixture(candidate_name)
    return verify_equivalent(current.text, candidate.text, symbols())


# --------------------------------------------------------------------------- #
# identities: must adjudicate ZERO
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("current,candidate", [
    # complex-variable identity: a*conj(b) + conj(a)*b == 2*re(a*conj(b))
    ("identity_current.txt", "identity_candidate.txt"),
    # rational identity over a real nonzero t with t^2 denominators
    ("identity_rational_current.txt", "identity_rational_candidate.txt"),
    # half-factor identity: re(a*conj(b)) == (a*conj(b) + conj(a)*b)/2
    ("identity_half_current.txt", "identity_half_candidate.txt"),
    # polynomial identity: (x + y)^2 == x^2 + 2*x*y + y^2
    ("identity_polynomial_current.txt", "identity_polynomial_candidate.txt"),
    # trigonometric identity: sin(x)^2 + cos(x)^2 == 1
    ("identity_trig_current.txt", "identity_trig_candidate.txt"),
])
def test_generic_identity_is_zero(current, candidate):
    result = verify(current, candidate)
    assert result.verdict == ZERO, (
        f"{current} == {candidate} expected ZERO, got {result.verdict}: "
        f"residual={result.residual!r}"
    )
    assert result.verifier == "python_sympy_exact_v1"


# --------------------------------------------------------------------------- #
# mutations: must adjudicate NONZERO with an exact counterexample
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("current,mutation", [
    # sign flip on the RHS
    ("identity_current.txt", "mutation_wrong_sign.txt"),
    # wrong coefficient on the RHS
    ("identity_current.txt", "mutation_wrong_coefficient.txt"),
    # missing factor 1/2 on the RHS
    ("identity_half_current.txt", "mutation_missing_half.txt"),
    # denominator power t^2 -> t^3
    ("identity_rational_current.txt", "mutation_wrong_denominator_power.txt"),
    # dropped term on the LHS
    ("identity_current.txt", "mutation_missing_term.txt"),
])
def test_generic_mutation_is_nonzero(current, mutation):
    result = verify(current, mutation)
    assert result.verdict == NONZERO, (
        f"{current} vs {mutation} expected NONZERO, got {result.verdict}: "
        f"residual={result.residual!r}"
    )
    assert result.counterexample is not None, (
        f"{mutation} refuted NONZERO but carried no exact counterexample"
    )
    assert "point" in result.counterexample
    assert "exact_value" in result.counterexample
    assert result.counterexample["exact_value"] != "0"
