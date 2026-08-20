"""v0.2.2 audit-delta: translation fidelity classes.

Deterministic, neutral synthetic fixtures only. Exercises ALL FIVE fidelity
classes of ``translation_fidelity``:

* BYTE_IDENTICAL          - identical strings (no parsing needed);
* STRUCTURALLY_IDENTICAL  - distinct text, identical canonical AST
                            (presentation-only difference);
* SEMANTICALLY_EQUIVALENT - matching structure + a zero semantic residual
                            (expansion; harmless Add/Mul reordering);
* MISMATCH                - provable structural difference: a changed Sum
                            bound, a differing Sum count, a changed
                            Piecewise condition;
* UNKNOWN                 - unparseable/garbage input fails CLOSED (never
                            claimed equivalent).

Also asserts the structural comparison dimensions directly: differing Sum
counts/bounds and Piecewise branch/condition differences are surfaced in the
returned ``structure`` inventory.
"""
from __future__ import annotations

from symbolic_compactification import (
    FIDELITY_CLASSES,
    translation_fidelity,
)
from symbolic_compactification.fidelity import (
    FIDELITY_BYTE_IDENTICAL,
    FIDELITY_MISMATCH,
    FIDELITY_SEMANTICALLY_EQUIVALENT,
    FIDELITY_STRUCTURALLY_IDENTICAL,
    FIDELITY_UNKNOWN,
)

_SYMBOLS = ["n", "N", "M", "x", "k"]
_FUNCTIONS = ["f", "g"]


# --------------------------------------------------------------------------- #
# vocabulary
# --------------------------------------------------------------------------- #

def test_fidelity_classes_vocabulary_is_complete_and_ordered():
    assert FIDELITY_CLASSES == (
        "BYTE_IDENTICAL",
        "STRUCTURALLY_IDENTICAL",
        "SEMANTICALLY_EQUIVALENT",
        "MISMATCH",
        "UNKNOWN",
    )
    assert (FIDELITY_BYTE_IDENTICAL, FIDELITY_STRUCTURALLY_IDENTICAL,
            FIDELITY_SEMANTICALLY_EQUIVALENT, FIDELITY_MISMATCH,
            FIDELITY_UNKNOWN) == FIDELITY_CLASSES


# --------------------------------------------------------------------------- #
# BYTE_IDENTICAL
# --------------------------------------------------------------------------- #

def test_byte_identical_for_identical_strings():
    result = translation_fidelity(
        "Sum(f(n), (n, 1, N))", "Sum(f(n), (n, 1, N))",
        symbols=_SYMBOLS, functions=_FUNCTIONS)
    assert result["fidelity"] == FIDELITY_BYTE_IDENTICAL


def test_byte_identical_needs_no_parsing():
    """Even garbage that is byte-identical on both sides is BYTE_IDENTICAL:
    the class is a pure text comparison."""
    result = translation_fidelity("@@ not parseable @@", "@@ not parseable @@")
    assert result["fidelity"] == FIDELITY_BYTE_IDENTICAL


# --------------------------------------------------------------------------- #
# STRUCTURALLY_IDENTICAL (presentation-only)
# --------------------------------------------------------------------------- #

def test_structurally_identical_for_presentation_only_difference():
    # commutative reordering: distinct text, identical canonical AST
    result = translation_fidelity("x + 1", "1 + x", symbols=["x"])
    assert result["fidelity"] == FIDELITY_STRUCTURALLY_IDENTICAL

    result = translation_fidelity("2*x", "x*2", symbols=["x"])
    assert result["fidelity"] == FIDELITY_STRUCTURALLY_IDENTICAL


# --------------------------------------------------------------------------- #
# SEMANTICALLY_EQUIVALENT (zero semantic residual)
# --------------------------------------------------------------------------- #

def test_semantically_equivalent_for_expansion():
    result = translation_fidelity("(x+1)**2", "x**2 + 2*x + 1",
                                  symbols=["x"])
    assert result["fidelity"] == FIDELITY_SEMANTICALLY_EQUIVALENT
    # matching structure on both sides is reported alongside
    assert result["structure"]["source"]["free_symbols"] == ["x"]
    assert result["structure"]["target"]["free_symbols"] == ["x"]


def test_semantically_equivalent_for_factored_vs_expanded():
    """Distinct canonical ASTs, matching structure, zero residual."""
    result = translation_fidelity("(x+1)*(x-1)", "x**2 - 1", symbols=["x"])
    assert result["fidelity"] == FIDELITY_SEMANTICALLY_EQUIVALENT


def test_harmless_add_mul_reordering_is_never_counted_against_fidelity():
    """Commutative Add/Mul reordering normalizes to the IDENTICAL canonical
    AST: the strongest applicable class, never MISMATCH/UNKNOWN."""
    result = translation_fidelity(
        "x**2 + 2*x + 1 + x**3", "1 + x**3 + x**2 + 2*x", symbols=["x"])
    assert result["fidelity"] == FIDELITY_STRUCTURALLY_IDENTICAL

    result = translation_fidelity("2*x*y", "y*x*2", symbols=["x", "y"])
    assert result["fidelity"] == FIDELITY_STRUCTURALLY_IDENTICAL


# --------------------------------------------------------------------------- #
# MISMATCH (provable structural difference)
# --------------------------------------------------------------------------- #

def test_mismatch_detects_changed_sum_bound():
    result = translation_fidelity(
        "Sum(f(n), (n, 1, N))", "Sum(f(n), (n, 1, N + 1))",
        symbols=_SYMBOLS, functions=_FUNCTIONS)
    assert result["fidelity"] == FIDELITY_MISMATCH
    assert "sums" in result["reason"]
    # the structural inventory names the differing Sums explicitly
    assert result["structure"]["source"]["sums"] != \
        result["structure"]["target"]["sums"]


def test_mismatch_detects_different_sum_counts():
    result = translation_fidelity(
        "Sum(f(n), (n, 1, N)) + Sum(g(n), (n, 1, N))",
        "Sum(f(n), (n, 1, N))",
        symbols=_SYMBOLS, functions=_FUNCTIONS)
    assert result["fidelity"] == FIDELITY_MISMATCH
    assert len(result["structure"]["source"]["sums"]) == 2
    assert len(result["structure"]["target"]["sums"]) == 1


def test_mismatch_detects_different_piecewise_condition():
    result = translation_fidelity(
        "Piecewise((x, x > 0), (0, True))",
        "Piecewise((x, x > 1), (0, True))",
        symbols=["x"])
    assert result["fidelity"] == FIDELITY_MISMATCH
    assert "piecewise_branches" in result["reason"]
    assert result["structure"]["source"]["piecewise_branches"] != \
        result["structure"]["target"]["piecewise_branches"]


def test_mismatch_detects_different_piecewise_branch_count():
    result = translation_fidelity(
        "Piecewise((x, x > 0), (-x, x < 0), (0, True))",
        "Piecewise((x, x > 0), (0, True))",
        symbols=["x"])
    assert result["fidelity"] == FIDELITY_MISMATCH


def test_mismatch_on_concrete_nonzero_residual():
    """Same structure, provably different by a concrete constant."""
    result = translation_fidelity("x + 1", "x + 2", symbols=["x"])
    assert result["fidelity"] == FIDELITY_MISMATCH
    assert "nonzero semantic residual" in result["reason"]


# --------------------------------------------------------------------------- #
# UNKNOWN (fail-closed)
# --------------------------------------------------------------------------- #

def test_unknown_when_a_side_fails_to_parse():
    result = translation_fidelity(
        "Sum(f(n), (n, 1, N))", "@@ this is not an expression ((",
        symbols=_SYMBOLS, functions=_FUNCTIONS)
    assert result["fidelity"] == FIDELITY_UNKNOWN
    assert result["fidelity"] != FIDELITY_SEMANTICALLY_EQUIVALENT


def test_unknown_when_source_fails_to_parse():
    result = translation_fidelity("definitely )) not math", "x + 1",
                                  symbols=["x"])
    assert result["fidelity"] == FIDELITY_UNKNOWN


def test_unknown_uses_declared_namespace_consistently():
    """An undeclared identifier on one side fails the strict parse: the
    comparison fails CLOSED to UNKNOWN rather than guessing."""
    result = translation_fidelity("x + 1", "y + 1", symbols=["x"])
    assert result["fidelity"] == FIDELITY_UNKNOWN
