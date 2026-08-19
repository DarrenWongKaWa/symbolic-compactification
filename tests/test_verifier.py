"""Exact residual verifier regression tests (fail-closed verdict semantics).

Scientifically neutral: only generic symbols (x, y, a, b) and standard
operations. Contract under test:

* ZERO    only for an exact symbolic zero of the simplified residual
* NONZERO only with a proven exact counterexample (rational probe lattice)
* UNKNOWN everywhere else, including every construction/parse failure
"""
from __future__ import annotations

import json

import pytest

from symbolic_compactification import (
    NONZERO,
    UNKNOWN,
    VERIFIER_NAME,
    ZERO,
    verify_equivalent,
)

COMPLEX_AB = [{"name": "a", "real": False}, {"name": "b", "real": False}]


def kinds(result):
    return [e.get("kind") for e in result.evidence]


ZERO_KINDS = {"exact_symbolic_zero",
              "exact_symbolic_zero_after_complex_normalization"}


# --------------------------------------------------------------------------- #
# exact ZERO identities
# --------------------------------------------------------------------------- #

def test_exact_zero_binomial_square():
    result = verify_equivalent("(x+1)**2", "x**2 + 2*x + 1", ["x"])
    assert result.verdict == ZERO
    assert result.counterexample is None
    assert result.simplified_residual == "0"
    assert set(kinds(result)) & ZERO_KINDS


def test_exact_zero_trig_pythagorean():
    result = verify_equivalent("sin(x)**2 + cos(x)**2", "1", ["x"])
    assert result.verdict == ZERO
    assert result.counterexample is None
    assert set(kinds(result)) & ZERO_KINDS


def test_exact_zero_exp_addition():
    result = verify_equivalent("exp(x)*exp(y)", "exp(x + y)", ["x", "y"])
    assert result.verdict == ZERO
    assert result.counterexample is None
    assert set(kinds(result)) & ZERO_KINDS


def test_exact_zero_complex_real_part_normalization():
    # 2*re(a*conj(b)) == a*conj(b) + conj(a)*b with a, b declared complex
    result = verify_equivalent(
        "2*re(a*conjugate(b))",
        "a*conjugate(b) + conjugate(a)*b",
        COMPLEX_AB)
    assert result.verdict == ZERO
    assert result.counterexample is None
    assert set(kinds(result)) & ZERO_KINDS


def test_exact_zero_polarization_identity():
    # |a+b|^2 - |a-b|^2 == 2*(a*conj(b) + conj(a)*b) with a, b complex
    result = verify_equivalent(
        "Abs(a+b)**2 - Abs(a-b)**2",
        "2*(a*conjugate(b) + conjugate(a)*b)",
        COMPLEX_AB)
    assert result.verdict == ZERO
    assert result.counterexample is None
    assert set(kinds(result)) & ZERO_KINDS


# --------------------------------------------------------------------------- #
# exact NONZERO
# --------------------------------------------------------------------------- #

def test_nonzero_simple_shift():
    result = verify_equivalent("x", "x + 1", ["x"])
    assert result.verdict == NONZERO
    assert result.counterexample is not None
    assert "point" in result.counterexample
    assert result.counterexample["exact_value"] != "0"
    assert "exact_counterexample" in kinds(result)


# --------------------------------------------------------------------------- #
# UNKNOWN (fail-closed): adversarial polynomial vanishing on the whole lattice
# --------------------------------------------------------------------------- #

def test_unknown_adversarial_polynomial_vanishing_on_probe_lattice():
    # Every real probe in {-2, -1, -1/2, 1/2, 1, 2} is an exact root of this
    # polynomial, so no probe can refute it; the simplifier cannot prove it
    # nonzero either. The only admissible verdict is UNKNOWN — never NONZERO.
    adversarial = ("(x - 1)*(x - Rational(1,2))*(x + 1)"
                   "*(x + 2)*(x - 2)*(x + Rational(1,2))")
    result = verify_equivalent("0", adversarial, ["x"])
    assert result.verdict == UNKNOWN
    assert result.counterexample is None
    assert ("simplification_undecided_no_exact_counterexample"
            in kinds(result))


# --------------------------------------------------------------------------- #
# no-bogus-counterexample guard
# --------------------------------------------------------------------------- #

# KNOWN KERNEL PERFORMANCE BUG (reported to leader, engine accepted as-is):
# the probe loop in verifier.py calls ``value.equals(0)`` with no time bound.
# For this case a single equals(0) call on a nested-radical probe value takes
# anywhere from <1s to >5 minutes (measured 0.8s / 183s / 321s across runs —
# nondeterministic). The verdict contract below always holds (UNKNOWN, no
# counterexample); only the wall-clock cost is pathological. Expected kernel
# behavior: bounded adjudication returning UNKNOWN promptly.
def test_no_bogus_counterexample_abs_sqrt_complex():
    result = verify_equivalent(
        "Abs(sqrt(a))", "sqrt(Abs(a))", [{"name": "a", "real": False}])
    assert result.verdict in (ZERO, UNKNOWN)
    assert result.counterexample is None


# --------------------------------------------------------------------------- #
# adversarial mutations of the base identity — every one must be NONZERO
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("description,current,candidate", [
    ("wrong sign", "(x+1)**2", "x**2 - 2*x + 1"),
    ("wrong coefficient", "(x+1)**2", "x**2 + 3*x + 1"),
    ("wrong power on linear term", "(x+1)**2", "x**2 + 2*x**2 + 1"),
    ("missing term", "(x+1)**2", "x**2 + 1"),
    ("missing half factor", "sin(x)**2 + cos(x)**2", "Rational(1,2)"),
    ("trig identity doubled", "sin(x)**2 + cos(x)**2", "2"),
])
def test_mutated_identity_is_nonzero(description, current, candidate):
    result = verify_equivalent(current, candidate, ["x"])
    assert result.verdict == NONZERO, (
        f"{description}: expected NONZERO, got {result.verdict} "
        f"(residual={result.residual!r})")
    assert result.counterexample is not None, (
        f"{description}: NONZERO verdict without an exact counterexample")
    assert result.counterexample["exact_value"] != "0"
    assert "exact_counterexample" in kinds(result)


# --------------------------------------------------------------------------- #
# result shape, evidence metadata and JSON serializability
# --------------------------------------------------------------------------- #

def test_result_shape_and_json_serializable():
    result = verify_equivalent("(x+1)**2", "x**2 + 2*x + 1", ["x"])
    assert result.verifier == VERIFIER_NAME
    assert isinstance(result.residual, str)
    assert isinstance(result.seconds, float)
    payload = result.to_dict()
    json.dumps(payload)  # must not raise
    assert payload["verdict"] == ZERO


def test_residual_string_is_expanded_difference():
    result = verify_equivalent("x", "x + 1", ["x"])
    assert result.residual == "-1"


def test_declared_assumptions_recorded_in_evidence():
    result = verify_equivalent("x", "x", ["x"],
                               assumptions={"note": "generic-test-metadata"})
    assert result.verdict == ZERO
    assert {"kind": "declared_assumptions",
            "assumptions": {"note": "generic-test-metadata"}} in result.evidence


# --------------------------------------------------------------------------- #
# fail-closed construction failures -> UNKNOWN, never an exception
# --------------------------------------------------------------------------- #

def test_scope_mismatch_fails_closed_unknown():
    # y is declared on neither side's symbol list: parse fails, and the
    # verifier must return UNKNOWN with construction_or_parse_failed evidence
    result = verify_equivalent("x + y", "x", ["x"])
    assert result.verdict == UNKNOWN
    assert result.counterexample is None
    evidence = result.evidence[0]
    assert evidence["kind"] == "construction_or_parse_failed"
    assert evidence["code"] == "UNDECLARED_OR_DISALLOWED_NAME"


def test_empty_side_fails_closed_unknown():
    result = verify_equivalent("", "x", ["x"])
    assert result.verdict == UNKNOWN
    assert result.evidence[0]["kind"] == "construction_or_parse_failed"
    assert result.evidence[0]["code"] == "EMPTY_EXPRESSION"


def test_non_string_input_fails_closed_unknown():
    result = verify_equivalent(None, "x", ["x"])
    assert result.verdict == UNKNOWN
    assert result.evidence[0]["kind"] == "construction_or_parse_failed"


def test_malformed_symbols_fail_closed_unknown():
    result = verify_equivalent("x", "x", [])
    assert result.verdict == UNKNOWN
    assert result.evidence[0]["kind"] == "construction_or_parse_failed"
    assert result.evidence[0]["code"] == "CLAIM_SYMBOLS_MALFORMED"
