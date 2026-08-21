"""Long-expression ingestion and verification smoke tests.

These deterministically synthesize a large (~20-30KB) generic expression at test
time (written to ``tmp_path``, never committed), then prove that:

  * ``load_expression`` ingests it and records the correct raw-byte SHA-256,
  * the parser stays within its configured limits (char gate AND node cap), and
    that the char gate genuinely rejects oversized input (EXPRESSION_TOO_LARGE),
  * an exact re-expansion of the same expression verifies ZERO,
  * a single-coefficient mutation verifies NONZERO with an exact counterexample.

The construction is generic math only (one symbol ``x``, rational coefficients,
powers, additions). No parser safety limit is weakened here; the synthetic
expression is sized to sit comfortably inside the existing bounded policy.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest
import sympy

from symbolic_compactification import (
    NONZERO,
    ZERO,
    AdapterError,
    load_expression,
    verify_equivalent,
)

# --------------------------------------------------------------------------- #
# construction parameters
# --------------------------------------------------------------------------- #

REPO_ROOT = Path(__file__).resolve().parent.parent

# One generic real symbol keeps probing fast and the construction purely neutral.
LONG_SYMBOLS = [{"name": "x", "real": True, "nonzero": False}]

# Number of Rational-coefficient power terms. Sized so the serialized text lands
# in the ~20-30KB window while the parsed node count stays under the 4000 cap.
NUM_TERMS = 900
TERM_SEED = 20260819
ORDER_SEED = 7
MUTATION_INDEX = 450


# --------------------------------------------------------------------------- #
# deterministic synthesis
# --------------------------------------------------------------------------- #

def build_terms(n: int = NUM_TERMS, seed: int = TERM_SEED) -> list[str]:
    """Deterministically build ``n`` distinct ``Rational(p,q)*x**i`` terms."""
    rng = random.Random(seed)
    terms = []
    for i in range(1, n + 1):
        p = rng.randint(1000, 9999)
        q = rng.randint(1000, 9999)
        terms.append(f"Rational({p},{q})*x**{i}")
    return terms


@pytest.fixture(scope="module")
def long_expression() -> dict:
    """The synthetic expression plus an exact re-expansion and one mutation."""
    terms = build_terms()
    text = " + ".join(terms)

    # Exact transformation: same multiset of terms in a different (seeded) order.
    order = list(range(len(terms)))
    random.Random(ORDER_SEED).shuffle(order)
    reordered = " + ".join(terms[i] for i in order)
    assert reordered != text

    # Single-coefficient mutation: bump one term's numerator by 1.
    mutated = list(terms)
    p_str, rest = mutated[MUTATION_INDEX].split(",", 1)
    p = int(p_str[len("Rational("):])
    mutated[MUTATION_INDEX] = f"Rational({p + 1},{rest}"
    mutated_text = " + ".join(mutated)
    assert mutated_text != text

    return {"terms": terms, "text": text, "reordered": reordered,
            "mutated": mutated_text}


def write_fixture(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def write_symbols(tmp_path: Path) -> Path:
    p = tmp_path / "symbols.json"
    p.write_text(json.dumps({"symbols": LONG_SYMBOLS}), encoding="utf-8")
    return p


# --------------------------------------------------------------------------- #
# ingestion, hashing, and policy bounds
# --------------------------------------------------------------------------- #

def test_long_expression_ingests_and_hashes(tmp_path, long_expression):
    text = long_expression["text"]
    path = write_fixture(tmp_path, "current.txt", text)

    record = load_expression(str(path), LONG_SYMBOLS)

    # SHA-256 is taken over the RAW file bytes and must match a recomputation.
    raw = path.read_bytes()
    assert record.sha256 == hashlib.sha256(raw).hexdigest()
    assert record.source_path == str(path)
    assert record.text == text.strip()
    assert record.symbols == LONG_SYMBOLS


def test_long_expression_within_configured_limits(tmp_path, long_expression):
    text = long_expression["text"]
    path = write_fixture(tmp_path, "current.txt", text)

    # The text must fit the char gate and parse successfully under defaults.
    from symbolic_compactification import PARSE_POLICY
    assert len(text) <= PARSE_POLICY["max_expr_chars"]
    assert 20_000 <= len(text) <= 30_000

    record = load_expression(str(path), LONG_SYMBOLS)
    ops = sympy.count_ops(record.parsed_expr, visual=False)
    assert ops <= PARSE_POLICY["max_nodes"], (
        f"synthetic expression has {ops} ops, exceeding the node cap"
    )
    # The construction must exercise many terms/operators, not a trivial blob.
    assert len(record.parsed_expr.args) == NUM_TERMS


def test_char_gate_rejects_oversized_expression(tmp_path, long_expression):
    """Prove the char bound is enforced, not silently deleted.

    A policy with a too-small ``max_expr_chars`` must raise EXPRESSION_TOO_LARGE
    on the same expression that loads fine under the default policy. This does
    NOT weaken the default limit; it only tightens it for this single call.
    """
    text = long_expression["text"]
    path = write_fixture(tmp_path, "current.txt", text)

    with pytest.raises(AdapterError) as exc_info:
        load_expression(str(path), LONG_SYMBOLS,
                        policy={"max_expr_chars": 1024})
    assert exc_info.value.code == "EXPRESSION_TOO_LARGE"


# --------------------------------------------------------------------------- #
# verification over the long expression
# --------------------------------------------------------------------------- #

def test_exact_transformation_is_zero(long_expression):
    result = verify_equivalent(long_expression["text"],
                               long_expression["reordered"], LONG_SYMBOLS)
    assert result.verdict == ZERO, (
        f"expected ZERO, got {result.verdict}: residual={result.residual!r}"
    )


def test_single_coefficient_mutation_is_nonzero(long_expression):
    result = verify_equivalent(long_expression["text"],
                               long_expression["mutated"], LONG_SYMBOLS)
    assert result.verdict == NONZERO, (
        f"expected NONZERO, got {result.verdict}: residual={result.residual!r}"
    )
    assert result.counterexample is not None
    assert result.counterexample["exact_value"] != "0"


# --------------------------------------------------------------------------- #
# CLI path (subprocess): exit 0 for ZERO, exit 2 for NONZERO
# --------------------------------------------------------------------------- #

def run_cli_verify(tmp_path: Path, current_text: str, candidate_text: str) -> subprocess.CompletedProcess:
    symbols_path = write_symbols(tmp_path)
    current = write_fixture(tmp_path, "current.txt", current_text)
    candidate = write_fixture(tmp_path, "candidate.txt", candidate_text)
    env = os.environ.copy()
    src = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "symbolic_compactification.cli", "verify",
         "--current", str(current),
         "--candidate", str(candidate),
         "--symbols", str(symbols_path)],
        capture_output=True, text=True, timeout=300, env=env,
    )


def test_cli_verify_zero_exit(tmp_path, long_expression):
    proc = run_cli_verify(tmp_path, long_expression["text"],
                          long_expression["reordered"])
    assert proc.returncode == 0, proc.stderr
    assert "verdict:" in proc.stdout and ZERO in proc.stdout


def test_cli_verify_nonzero_exit(tmp_path, long_expression):
    proc = run_cli_verify(tmp_path, long_expression["text"],
                          long_expression["mutated"])
    assert proc.returncode == 2, proc.stderr
    assert NONZERO in proc.stdout
