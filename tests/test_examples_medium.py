"""Smoke the medium Sum-compactification fixtures."""
from pathlib import Path

from symbolic_compactification import NONZERO, ZERO, verify_equivalent
from symbolic_compactification.cli import load_namespace_file

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "medium"


def _ns():
    return load_namespace_file(str(EXAMPLES / "symbols.json"))


def _text(name: str) -> str:
    return (EXAMPLES / name).read_text(encoding="utf-8").strip()


def test_medium_candidate_is_exact_zero():
    symbols, functions = _ns()
    result = verify_equivalent(
        _text("current.txt"), _text("candidate.txt"),
        symbols, functions=functions)
    assert result.verdict == ZERO
    assert result.simplified_residual == "0"


def test_medium_mutation_is_nonzero():
    symbols, functions = _ns()
    result = verify_equivalent(
        _text("current.txt"), _text("mutation.txt"),
        symbols, functions=functions)
    assert result.verdict == NONZERO
    assert result.counterexample is not None
