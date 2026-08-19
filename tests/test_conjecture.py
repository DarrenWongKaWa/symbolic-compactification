"""Contract tests for the agent-protocol layer (v0.2.1): conjecture packets
and STRUCTURAL_PROPOSER candidate validation.

Synthetic only: generic symbols (x, n, N) and undefined-function names
(f, g); zero scientific content. No live model, no network — everything is
deterministic plain-Python input/output against ``build_conjecture_packet``
and ``validate_candidate``.

Contract under test (see roles/STRUCTURAL_PROPOSER.md sections 3 and 6):
* the conjecture packet carries exactly the INCLUDED fields (current
  expression + hash, structural form, structure_summary, declared
  symbols/functions/assumptions, goal, verifier feedback) and declares the
  WITHHELD attention categories; it is JSON-serializable and deterministic;
* ``validate_candidate`` enforces the output schema strictly: required
  non-empty string fields, no unknown keys, enum fields coerced/validated,
  and the status FORCED to HYPOTHESIS — any claimed CERTIFIED (or any other
  status, e.g. "ZERO") is rejected with PROPOSAL_INVALID. Validation NEVER
  certifies.
"""
from __future__ import annotations

import json

import pytest

from symbolic_compactification import (
    AGENT_PROTOCOL_VERSION,
    ENGINE_VERSION,
    NONZERO,
    AdapterError,
    ExpressionRecord,
    build_conjecture_packet,
    normalize_symbols,
    parse_expression,
    sha256_text,
    validate_candidate,
)

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _record(text: str, symbols=("x",), functions=None) -> ExpressionRecord:
    declared = normalize_symbols(list(symbols))
    parsed = parse_expression(text, declared,
                              functions=list(functions) if functions else None)
    return ExpressionRecord(
        text=text,
        sha256=sha256_text(text),
        source_path=None,
        parsed_expr=parsed,
        symbols=declared,
    )


def _candidate(expression: str, candidate_id: str = "c-test", **overrides):
    """A well-formed candidate dict per the section-6 output contract."""
    base = {
        "candidate_id": candidate_id,
        "hypothesis": "synthetic structural hypothesis",
        "candidate_expression_or_rewrite": expression,
        "rationale": "synthetic rationale",
        "expected_structural_benefit": "synthetic benefit",
        "suggested_verification_strategy": "exact residual verification",
        "required_assumptions": [],
        "assumptions_status": "NONE",
        "confidence": "medium",
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# build_conjecture_packet: INCLUDED fields
# --------------------------------------------------------------------------- #

def test_packet_contains_all_required_fields_and_versions():
    record = _record("(x+1)**2")
    packet = build_conjecture_packet(
        record, goal="factor the expanded polynomial")

    assert packet["packet_type"] == "conjecture_packet"
    assert packet["agent_protocol_version"] == AGENT_PROTOCOL_VERSION == "0.2.1"
    assert packet["engine_version"] == ENGINE_VERSION == "0.2.0"
    assert packet["current_expression"] == "(x+1)**2"
    assert packet["current_sha256"] == sha256_text("(x+1)**2")
    # structural form + cheap structural inventory are present
    assert isinstance(packet["structural_form"], str)
    assert packet["structural_form"]
    assert isinstance(packet["structure_summary"], dict)
    assert packet["structure_summary"]["count_ops"] > 0
    # declared symbols / assumptions carried exactly as on record
    assert packet["declared_symbols"] == [{"name": "x", "real": True,
                                           "nonzero": False}]
    assert packet["declared_assumptions"] == [{"name": "x", "real": True,
                                               "nonzero": False}]
    assert packet["declared_functions"] == []
    assert packet["goal"] == "factor the expanded polynomial"
    assert packet["verifier_feedback"] == []
    # every INCLUDED field is actually present in the packet
    for field in packet["included"]:
        assert field in packet


def test_packet_reports_observed_undefined_functions():
    record = _record("f(n) + g(n)", symbols=("n",), functions=("f", "g"))
    packet = build_conjecture_packet(record)
    assert packet["declared_functions"] == ["f", "g"]
    assert packet["structure_summary"]["indexed_calls"] == 2
    assert packet["structure_summary"]["indexed_names"] == ["f", "g"]


def test_packet_carries_verifier_feedback_when_supplied():
    record = _record("x**2 + 2*x + 1")
    feedback = {
        "verdict": NONZERO,
        "simplified_residual": "2",
        "counterexample": {"point": {"x": "1"}, "exact_value": "2"},
    }
    packet = build_conjecture_packet(record, feedback=feedback)
    assert len(packet["verifier_feedback"]) == 1
    entry = packet["verifier_feedback"][0]
    assert entry["verdict"] == NONZERO
    assert entry["residual"] == "2"
    assert entry["counterexample"] == feedback["counterexample"]


def test_packet_is_json_serializable_and_deterministic():
    record = _record("(x+1)**2")
    feedback = {"verdict": NONZERO, "residual": "2"}
    packet = build_conjecture_packet(record, feedback=feedback, goal="g")
    # round-trips through JSON without loss
    round_tripped = json.loads(json.dumps(packet))
    assert round_tripped == packet
    # deterministic: rebuilding yields the identical payload
    assert build_conjecture_packet(record, feedback=feedback, goal="g") == packet


def test_packet_declares_withheld_attention_categories():
    packet = build_conjecture_packet(_record("x"))
    withheld = packet["withheld"]
    assert isinstance(withheld, list) and withheld
    for category in ("git_history", "test_suite_output",
                     "parser_cli_implementation", "telemetry_internals",
                     "flattened_diagnostic_terms"):
        assert category in withheld


def test_packet_error_paths_fail_closed():
    # bad source type
    with pytest.raises(AdapterError) as excinfo:
        build_conjecture_packet("not a record")
    assert excinfo.value.code == "CONJECTURE_SOURCE_MALFORMED"

    # session without a current expression
    from symbolic_compactification import SessionState
    empty = SessionState(run_id="synthetic-run")
    with pytest.raises(AdapterError) as excinfo:
        build_conjecture_packet(empty)
    assert excinfo.value.code == "NO_CURRENT_EXPRESSION"

    # malformed goal (non-string / blank)
    with pytest.raises(AdapterError) as excinfo:
        build_conjecture_packet(_record("x"), goal=123)
    assert excinfo.value.code == "CONJECTURE_GOAL_MALFORMED"
    with pytest.raises(AdapterError) as excinfo:
        build_conjecture_packet(_record("x"), goal="   ")
    assert excinfo.value.code == "CONJECTURE_GOAL_MALFORMED"

    # malformed feedback shapes
    for bad in ({"verdict": "BOGUS"}, {"verdict": NONZERO, "residual": 42},
                ["not-a-dict"]):
        with pytest.raises(AdapterError) as excinfo:
            build_conjecture_packet(_record("x"), feedback=bad)
        assert excinfo.value.code == "FEEDBACK_MALFORMED"


# --------------------------------------------------------------------------- #
# validate_candidate: schema enforcement; NEVER certifies
# --------------------------------------------------------------------------- #

def test_validate_accepts_well_formed_and_forces_hypothesis():
    # status omitted: defaults to HYPOTHESIS
    out = validate_candidate(_candidate("(x+1)**2"))
    assert out["status"] == "HYPOTHESIS"
    assert out["candidate_expression_or_rewrite"] == "(x+1)**2"
    assert out["assumptions_status"] == "NONE"
    assert out["confidence"] == "medium"

    # status explicitly HYPOTHESIS: accepted
    out2 = validate_candidate(_candidate("(x+1)**2", status="HYPOTHESIS"))
    assert out2["status"] == "HYPOTHESIS"


@pytest.mark.parametrize("claimed_status", ["CERTIFIED", "ZERO", "UNVERIFIED"])
def test_validate_rejects_any_claimed_status_other_than_hypothesis(
        claimed_status):
    with pytest.raises(AdapterError) as excinfo:
        validate_candidate(_candidate("(x+1)**2", status=claimed_status))
    assert excinfo.value.code == "PROPOSAL_INVALID"


def test_validate_rejects_unknown_keys():
    with pytest.raises(AdapterError) as excinfo:
        validate_candidate(_candidate("(x+1)**2", surprise_field="x"))
    assert excinfo.value.code == "PROPOSAL_INVALID"


def test_validate_enforces_confidence_enum():
    with pytest.raises(AdapterError) as excinfo:
        validate_candidate(_candidate("x", confidence="very high"))
    assert excinfo.value.code == "PROPOSAL_INVALID"
    # case-insensitive acceptance, normalized to lowercase
    assert validate_candidate(_candidate("x", confidence="HIGH"))[
        "confidence"] == "high"


def test_validate_enforces_assumptions_status_enum():
    with pytest.raises(AdapterError) as excinfo:
        validate_candidate(_candidate("x", assumptions_status="PENDING"))
    assert excinfo.value.code == "PROPOSAL_INVALID"
    # case-insensitive acceptance, normalized to uppercase
    assert validate_candidate(
        _candidate("x", assumptions_status="declared"))[
        "assumptions_status"] == "DECLARED"


@pytest.mark.parametrize("field", [
    "candidate_id", "hypothesis", "candidate_expression_or_rewrite",
    "rationale", "expected_structural_benefit",
    "suggested_verification_strategy",
])
def test_validate_rejects_missing_or_blank_required_string_fields(field):
    missing = _candidate("x")
    del missing[field]
    with pytest.raises(AdapterError) as excinfo:
        validate_candidate(missing)
    assert excinfo.value.code == "PROPOSAL_INVALID"

    blank = _candidate("x", **{field: "   "})
    with pytest.raises(AdapterError) as excinfo:
        validate_candidate(blank)
    assert excinfo.value.code == "PROPOSAL_INVALID"


def test_validate_rejects_bad_shapes():
    # not a dict at all
    with pytest.raises(AdapterError) as excinfo:
        validate_candidate(["not", "a", "dict"])
    assert excinfo.value.code == "PROPOSAL_INVALID"

    # required_assumptions must be a list of strings/dicts
    with pytest.raises(AdapterError) as excinfo:
        validate_candidate(_candidate("x", required_assumptions="x > 0"))
    assert excinfo.value.code == "PROPOSAL_INVALID"
    with pytest.raises(AdapterError) as excinfo:
        validate_candidate(_candidate("x", required_assumptions=[42]))
    assert excinfo.value.code == "PROPOSAL_INVALID"

    # valid non-empty assumptions list passes through
    out = validate_candidate(_candidate(
        "x", required_assumptions=["x is real"],
        assumptions_status="DECLARED"))
    assert out["required_assumptions"] == ["x is real"]
