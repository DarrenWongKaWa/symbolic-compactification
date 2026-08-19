"""Residual construction and session-recording payload regression tests.

Scientifically neutral: only generic symbols (x) and standard operations.
Contract under test: the residual is ``current - candidate`` (never the
reverse), and ``residual_record`` produces a JSON-serializable payload whose
hash fields are 64-char lowercase SHA-256 hex digests.
"""
from __future__ import annotations

import json
import re

import sympy

from symbolic_compactification import (
    ZERO,
    ExpressionRecord,
    make_residual,
    parse_expression,
    residual_record,
    sha256_text,
    verify_equivalent,
)

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _record(text: str) -> ExpressionRecord:
    return ExpressionRecord(
        text=text,
        sha256=sha256_text(text),
        source_path=None,
        parsed_expr=None,
        symbols=[{"name": "x", "real": True, "nonzero": False}],
    )


# --------------------------------------------------------------------------- #
# make_residual: current-minus-candidate semantics
# --------------------------------------------------------------------------- #

def test_make_residual_is_current_minus_candidate():
    current = parse_expression("x", ["x"])
    candidate = parse_expression("1", ["x"])
    residual = make_residual(current, candidate)
    assert sympy.expand(residual) == sympy.expand(current - candidate)
    assert sympy.expand(residual - (current - candidate)) == 0


def test_make_residual_direction_is_not_commutative():
    current = parse_expression("x", ["x"])
    candidate = parse_expression("1", ["x"])
    forward = make_residual(current, candidate)
    reverse = make_residual(candidate, current)
    assert sympy.expand(forward + reverse) == 0  # antisymmetric
    assert sympy.expand(forward) != sympy.expand(reverse)


def test_make_residual_zero_for_exact_identity():
    current = parse_expression("x**2 + 2*x + 1", ["x"])
    candidate = parse_expression("(x+1)**2", ["x"])
    assert sympy.expand(make_residual(current, candidate)) == 0


# --------------------------------------------------------------------------- #
# residual_record: fields, hashes, JSON serializability
# --------------------------------------------------------------------------- #

def test_residual_record_fields_and_hashes():
    current_rec = _record("x**2 + 2*x + 1")
    candidate_rec = _record("(x+1)**2")
    result = verify_equivalent(current_rec.text, candidate_rec.text, ["x"])
    assert result.verdict == ZERO

    record = residual_record(current_rec, candidate_rec, result)
    assert record["construction"] == "difference_current_minus_candidate"
    assert record["current_sha256"] == sha256_text(current_rec.text)
    assert record["candidate_sha256"] == sha256_text(candidate_rec.text)
    assert record["residual"] == result.residual
    assert record["simplified_residual"] == result.simplified_residual
    assert record["verdict"] == ZERO
    assert record["residual_sha256"] == sha256_text(result.residual)
    for key in ("current_sha256", "candidate_sha256", "residual_sha256"):
        assert HEX64.match(record[key]), f"{key} is not a sha256 hex digest"


def test_residual_record_without_result():
    record = residual_record(_record("x"), _record("x + 1"), None)
    assert record["residual"] is None
    assert record["simplified_residual"] is None
    assert record["residual_sha256"] is None
    assert record["verdict"] is None
    assert HEX64.match(record["current_sha256"])
    assert HEX64.match(record["candidate_sha256"])


def test_residual_record_json_serializable():
    current_rec = _record("x**2 + 2*x + 1")
    candidate_rec = _record("(x+1)**2")
    result = verify_equivalent(current_rec.text, candidate_rec.text, ["x"])
    record = residual_record(current_rec, candidate_rec, result)
    round_tripped = json.loads(json.dumps(record))
    assert round_tripped == record
