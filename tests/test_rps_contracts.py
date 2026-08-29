"""Contract freeze: grammar constants match the markdown, no Guo, no search."""
from __future__ import annotations

from pathlib import Path

from research.representation_program_search.grammar_v1 import (
    ACTIONS,
    ABLATIONS,
    CONDITIONS,
    GRAMMAR_ID,
    OPERATORS,
    OPTIONAL_LATER,
)


HERE = Path(__file__).resolve().parents[1] / "research" / "representation_program_search"


def test_required_contract_files_exist():
    for name in (
        "PROBLEM_STATEMENT.md",
        "REPRESENTATION_GRAMMAR_V1.md",
        "PROGRAM_IR.md",
        "SEARCH_STATE_IR.md",
        "SCORING_POLICY.md",
        "CAUSAL_EXPERIMENT.md",
        "GUO_POLICY.md",
        "HISTORICAL_DIAGNOSTIC.md",
    ):
        assert (HERE / name).is_file(), name


def test_hermite_is_not_newton():
    assert "NEWTON_DD" in OPERATORS and "HERMITE_DD" in OPERATORS
    assert "NEWTON_DD" != "HERMITE_DD"
    assert "ADD_REPEATED_NODE" in ACTIONS
    g = (HERE / "REPRESENTATION_GRAMMAR_V1.md").read_text()
    assert "NODES[x, x]" in g
    assert "structurally different" in g.lower() or "structurally different" in g


def test_optional_operators_not_in_v1():
    assert not set(OPTIONAL_LATER) & set(OPERATORS)


def test_conditions_and_ablations():
    assert CONDITIONS[-1] == "F0"
    assert "G_NO_HERMITE" in ABLATIONS
    assert GRAMMAR_ID == "RepresentationGrammarV1"


def test_no_guo_rescue_in_contracts():
    blob = (HERE / "GUO_POLICY.md").read_text() + (HERE / "PROBLEM_STATEMENT.md").read_text()
    assert "UNKNOWN LEVEL_B" in blob
    assert "Do not run new Guo search" in blob or "not a new scientific case" in blob.lower() or "Guo is sealed" in blob


def test_old_test_is_historical_diagnostic():
    t = (HERE / "HISTORICAL_DIAGNOSTIC.md").read_text()
    assert "sciml-tweedie-gauss-01" in t
    assert "headline TEST" in t or "HISTORICAL_DIAGNOSTIC" in t
