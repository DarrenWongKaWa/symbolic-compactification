"""Regression tests for proposer/packet provenance and the v0.2.2 status
taxonomy.

Deterministic fixtures only (no network, no live models):
* ``record_proposal`` invocation provenance — WITH a harness subagent id
  (HARNESS_SUBAGENT) and WITHOUT (MAIN_AGENT_ONLY); ambiguous/absent
  evidence derives UNKNOWN, never inference.
* Packet provenance records (``packets/packet_NNN.json``) carry ONLY the
  neutral structured fields — a strict key inventory proves no
  chain-of-thought/reasoning text is ever persisted.
* Status taxonomy: PROOF_REQUIRED is an accepted step status, distinct
  from HUMAN_REQUIRED (an assumptions/certification gate) and from the
  verifier verdict UNKNOWN; HUMAN_REQUIRED candidates still cannot be
  promoted without a real ZERO verification step.
"""
from __future__ import annotations

import inspect
import json
import re

import pytest
import sympy

import symbolic_compactification.models as models_module
from symbolic_compactification import (
    AGENT_PROTOCOL_VERSION,
    ENGINE_VERSION,
    PROPOSAL_EVIDENCE_KIND,
    STEP_STATUSES,
    UNKNOWN,
    ZERO,
    AdapterError,
    ExpressionRecord,
    StepRecord,
    build_conjecture_packet,
    normalize_symbols,
    parse_expression,
    record_proposal,
    record_step,
    run_summary,
    set_current,
    sha256_text,
    verify_equivalent,
)
from symbolic_compactification.conjecture import ASSUMPTION_STATUSES
from symbolic_compactification.session import init_session, promote

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _record(text: str, symbols=("x",)) -> ExpressionRecord:
    declared = normalize_symbols(list(symbols))
    parsed = parse_expression(text, declared)
    return ExpressionRecord(
        text=text,
        sha256=sha256_text(text),
        source_path=None,
        parsed_expr=parsed,
        symbols=declared,
    )


def _candidate(expression: str, candidate_id: str, **overrides) -> dict:
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


def _verification_step(session, candidate_rec, result, status: str):
    return StepRecord(
        step=len(session.steps) + 1,
        current_hash=session.current.sha256,
        candidate_hash=candidate_rec.sha256,
        candidate_text=candidate_rec.text,
        residual=result.residual,
        verdict=result.verdict,
        evidence=list(result.evidence),
        status=status,
        telemetry={
            "input_chars": len(session.current.text),
            "output_chars": len(candidate_rec.text),
            "count_ops_before": sympy.count_ops(session.current.parsed_expr),
            "count_ops_after": sympy.count_ops(candidate_rec.parsed_expr),
            "primitive": None,
            "wall_time_seconds": result.seconds,
            "verdict": result.verdict,
            "timeout_status": None,
            "engine_version": ENGINE_VERSION,
        },
    )


def _run_root(tmp_path, session):
    return tmp_path / "runs" / session.run_id


def _proposal_evidence(step: StepRecord) -> dict:
    marked = [e for e in step.evidence
              if isinstance(e, dict) and e.get("kind") == PROPOSAL_EVIDENCE_KIND]
    assert len(marked) == 1
    return marked[0]


# --------------------------------------------------------------------------- #
# record_proposal invocation provenance
# --------------------------------------------------------------------------- #

def test_record_proposal_with_subagent_id_records_full_provenance(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    set_current(session, _record("x**2 + 2*x + 1"))

    step = record_proposal(
        session, _candidate("(x+1)**2", candidate_id="cand-sub-1"),
        harness_task_or_subagent_id="subagent-42",
        invocation_timestamp="2026-01-02T03:04:05Z",
        parent_step_index=0)

    ev = _proposal_evidence(step)
    assert step.status == "HYPOTHESIS"
    assert step.verdict == UNKNOWN
    assert ev["role"] == "STRUCTURAL_PROPOSER"
    assert ev["candidate_id"] == "cand-sub-1"
    assert ev["invocation_mode"] == "subagent"
    assert ev["subagent_id"] == "subagent-42"
    # caller-supplied invocation timestamp is carried verbatim
    assert ev["invocation_timestamp"] == "2026-01-02T03:04:05Z"
    assert _ISO_UTC.match(ev["proposal_timestamp"])
    assert _HEX64.match(ev["proposal_sha256"]), \
        "proposal_sha256 must be a 64-hex content hash"
    assert ev["parent_step_index"] == 0
    # proposal content is content-addressed and reproducible
    from symbolic_compactification import canonical_json
    from symbolic_compactification.conjecture import validate_candidate
    validated = validate_candidate(_candidate("(x+1)**2", "cand-sub-1"))
    assert ev["proposal_sha256"] == sha256_text(canonical_json(validated))

    summary = run_summary(_run_root(tmp_path, session))
    assert summary["proposer_mode"] == "HARNESS_SUBAGENT"
    assert summary["candidates_proposed"] == 1
    # proposals carry no verifier verdicts
    assert summary["unknown_count"] == 0
    assert summary["verifier_calls"] == 0


def test_record_proposal_without_subagent_id_is_main_agent_only(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    set_current(session, _record("x**2 + 2*x + 1"))

    step = record_proposal(session,
                           _candidate("(x+1)**2", candidate_id="cand-main-1"))

    ev = _proposal_evidence(step)
    assert ev["role"] == "STRUCTURAL_PROPOSER"
    assert ev["invocation_mode"] == "main_agent"
    assert ev["subagent_id"] is None
    assert _HEX64.match(ev["proposal_sha256"])
    assert _ISO_UTC.match(ev["invocation_timestamp"])
    assert _ISO_UTC.match(ev["proposal_timestamp"])
    # default parent link: the step count at proposal time
    assert ev["parent_step_index"] == 0

    summary = run_summary(_run_root(tmp_path, session))
    assert summary["proposer_mode"] == "MAIN_AGENT_ONLY"


def test_record_proposal_blank_subagent_id_is_not_a_subagent(tmp_path):
    """A blank/whitespace id is NOT subagent evidence (fail closed)."""
    session = init_session(workspace_root=str(tmp_path))
    set_current(session, _record("x"))

    step = record_proposal(session, _candidate("x", candidate_id="cand-blank"),
                           harness_task_or_subagent_id="   ")
    ev = _proposal_evidence(step)
    assert ev["invocation_mode"] == "main_agent"
    assert ev["subagent_id"] is None

    summary = run_summary(_run_root(tmp_path, session))
    assert summary["proposer_mode"] == "MAIN_AGENT_ONLY"


def test_proposer_mode_mixed_subagent_and_main_is_harness_subagent(tmp_path):
    """Any recorded subagent id selects HARNESS_SUBAGENT for the run."""
    session = init_session(workspace_root=str(tmp_path))
    set_current(session, _record("x**2 + 2*x + 1"))

    record_proposal(session, _candidate("(x+1)**2", candidate_id="c1"))
    record_proposal(session, _candidate("(x+1)**2", candidate_id="c2"),
                    harness_task_or_subagent_id="sub-1")

    summary = run_summary(_run_root(tmp_path, session))
    assert summary["proposer_mode"] == "HARNESS_SUBAGENT"
    assert summary["candidates_proposed"] == 2


def test_proposer_mode_unknown_paths(tmp_path):
    """UNKNOWN: no proposals at all, and ambiguous proposal markers (a
    proposer evidence kind WITHOUT invocation fields). proposer_mode is
    derived strictly from recorded evidence — never inferred."""
    session = init_session(workspace_root=str(tmp_path))
    set_current(session, _record("x"))
    assert run_summary(_run_root(tmp_path, session))["proposer_mode"] == "UNKNOWN"

    # ambiguous: a proposal marker lacking invocation evidence
    session.steps.clear()
    ambiguous = StepRecord(
        step=1,
        current_hash=session.current.sha256,
        candidate_hash=sha256_text("x"),
        candidate_text="x",
        residual=None,
        verdict=UNKNOWN,
        evidence=[{"kind": PROPOSAL_EVIDENCE_KIND}],
        status="HYPOTHESIS",
    )
    record_step(session, ambiguous)
    assert run_summary(_run_root(tmp_path, session))["proposer_mode"] == "UNKNOWN"


# --------------------------------------------------------------------------- #
# packet provenance records: neutral structured fields ONLY
# --------------------------------------------------------------------------- #

# Every record MUST carry these neutral structured fields (presence, not
# exhaustiveness: the field set may grow additively in later protocols).
_REQUIRED_PACKET_RECORD_KEYS = frozenset({
    "record_type",
    "agent_protocol_version",
    "engine_version",
    "packet_sha256",
    "certified_state_sha256",
    "structural_representation_sha256",
    "goal",
    "declared_assumptions",
    "verifier_feedback_included",
    "withheld",
})

# No chain-of-thought / reasoning-text field may EVER appear in a record.
_FORBIDDEN_PACKET_RECORD_KEYS = frozenset({
    "chain_of_thought", "reasoning", "reasoning_text", "thoughts",
    "rationale", "internal_notes",
})


def test_packet_provenance_record_fields_and_key_inventory(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    current = _record("x**2 + 2*x + 1")
    set_current(session, current)

    packet = build_conjecture_packet(
        session, goal="factor the expanded polynomial")

    packets_dir = _run_root(tmp_path, session) / "packets"
    record_path = packets_dir / "packet_001.json"
    assert record_path.is_file(), "packet provenance record was not written"
    record = json.loads(record_path.read_text(encoding="utf-8"))

    # key inventory: every required neutral field is present, and NO
    # chain-of-thought/reasoning-text field is ever persisted
    assert _REQUIRED_PACKET_RECORD_KEYS <= frozenset(record)
    assert not (_FORBIDDEN_PACKET_RECORD_KEYS & frozenset(record))

    assert record["record_type"] == "conjecture_packet_provenance"
    assert record["agent_protocol_version"] == AGENT_PROTOCOL_VERSION
    assert record["engine_version"] == ENGINE_VERSION
    assert record["packet_sha256"] == packet["packet_sha256"]
    assert record["certified_state_sha256"] == current.sha256
    assert record["structural_representation_sha256"] == \
        sha256_text(packet["structural_form"])
    assert record["goal"] == "factor the expanded polynomial"
    assert any(a.get("name") == "x" and a.get("real") is True
               and a.get("nonzero") is False
               for a in record["declared_assumptions"])
    assert record["verifier_feedback_included"] is False
    assert isinstance(record["withheld"], list) and record["withheld"]
    assert "git_history" in record["withheld"]


def test_packet_provenance_flags_included_verifier_feedback(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    set_current(session, _record("x**2"))

    build_conjecture_packet(session, feedback=[
        {"verdict": "NONZERO", "residual": "2*x"}])

    record = json.loads(
        (_run_root(tmp_path, session) / "packets" / "packet_001.json")
        .read_text(encoding="utf-8"))
    assert record["verifier_feedback_included"] is True


def test_packets_recorded_counts_provenance_records(tmp_path):
    """Packet records are numbered after the step index at assembly time,
    so the realistic flow interleaves them with recorded steps."""
    session = init_session(workspace_root=str(tmp_path))
    set_current(session, _record("x**2"))
    assert run_summary(_run_root(tmp_path, session))["packets_recorded"] == 0

    build_conjecture_packet(session, goal="first")          # packet_001
    record_proposal(session, _candidate("x**2", candidate_id="c1"))
    build_conjecture_packet(session, goal="second")         # packet_002

    packets_dir = _run_root(tmp_path, session) / "packets"
    assert (packets_dir / "packet_001.json").is_file()
    assert (packets_dir / "packet_002.json").is_file()
    summary = run_summary(_run_root(tmp_path, session))
    assert summary["packets_recorded"] == 2


# --------------------------------------------------------------------------- #
# status taxonomy: PROOF_REQUIRED vs HUMAN_REQUIRED vs UNKNOWN
# --------------------------------------------------------------------------- #

def test_step_status_vocabulary_contains_all_four_states():
    # all four states are part of the vocabulary (superset check: the
    # taxonomy may grow additively, but these four must never disappear)
    assert {"HYPOTHESIS", "UNVERIFIED", "CERTIFIED",
            "PROOF_REQUIRED"} <= set(STEP_STATUSES)
    # the module's documented vocabulary (docstrings/comments) names all four
    source = inspect.getsource(models_module)
    for state in ("HYPOTHESIS", "UNVERIFIED", "CERTIFIED", "PROOF_REQUIRED"):
        assert state in source
    # PROOF_REQUIRED is a proof-gap status, NOT an assumptions status
    assert "PROOF_REQUIRED" not in ASSUMPTION_STATUSES
    assert {"DECLARED", "HUMAN_REQUIRED", "NONE"} <= set(ASSUMPTION_STATUSES)


def test_proof_required_is_an_accepted_step_status():
    step = StepRecord(
        step=1, current_hash="h", candidate_hash="c", candidate_text="x",
        residual="r", verdict=UNKNOWN, status="PROOF_REQUIRED")
    assert step.status == "PROOF_REQUIRED"
    assert step.to_dict()["status"] == "PROOF_REQUIRED"
    # distinct from the other states — not silently normalized
    assert step.status != "HUMAN_REQUIRED"
    assert step.status != "UNVERIFIED"
    with pytest.raises(AdapterError) as excinfo:
        StepRecord(step=1, current_hash="h", candidate_hash="c",
                   candidate_text="x", residual=None, verdict=UNKNOWN,
                   status="NOT_A_STATUS")
    assert excinfo.value.code == "STEP_STATUS_INVALID"


def test_human_required_candidate_cannot_promote_without_zero_step(tmp_path):
    """A HUMAN_REQUIRED proposal is recordable but is NOT a certification:
    promotion stays hard-gated on a real ZERO verification step."""
    session = init_session(workspace_root=str(tmp_path))
    current = _record("x**2 + 2*x + 1")
    set_current(session, current)

    step = record_proposal(
        session,
        _candidate("(x+1)**2", candidate_id="cand-human",
                   assumptions_status="HUMAN_REQUIRED",
                   required_assumptions=["x is real"]))
    assert step.evidence[0]["assumptions_status"] == "HUMAN_REQUIRED"

    # a proposal alone (whatever its assumptions status) never promotes
    with pytest.raises(AdapterError) as excinfo:
        promote(session, _record("(x+1)**2"))
    assert excinfo.value.code == "VERDICT_NOT_ZERO"

    # only a REAL ZERO verification step unlocks promotion
    candidate = _record("(x+1)**2")
    result = verify_equivalent(current.text, candidate.text, ["x"])
    assert result.verdict == ZERO
    record_step(session, _verification_step(
        session, candidate, result, status="CERTIFIED"))
    final_path = promote(session, candidate)
    final = json.loads(final_path.read_text(encoding="utf-8"))
    assert final["text"] == "(x+1)**2"
