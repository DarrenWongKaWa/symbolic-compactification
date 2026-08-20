"""v0.2.2 audit-delta: proposer modes, A/B arm validity and invocation
provenance contract names.

Deterministic fixtures only (no network, no live models). Covers:

* ``PROPOSER_MODES`` carries all four modes; ``SUBAGENT_UNAVAILABLE`` is
  recordable via ``record_proposal(unavailable=True)`` and is DISTINCT from
  ``UNKNOWN`` in ``run_summary``.
* ``ab_arm_valid`` / ``invalid_reason`` derived strictly from recorded
  proposer evidence: arm B requires a recorded harness id, arm A requires
  no subagent evidence, an undeclared arm makes no validity claim.
* ``init_session(requested_arm=...)`` / ``set_requested_arm`` fail closed
  on unknown arms; ``load_session`` restores the declaration; the CLI
  ``init-session --requested-arm B`` smoke path persists it.
* ``record_proposal`` accepts the v0.2.2 CONTRACT provenance names
  (``harness_task_or_subagent_id`` / ``invoked_at`` / ``returned_at`` /
  ``parent_agent_step`` / ``conjecture_packet_sha256``), surfaces them in
  the step evidence alongside the legacy aliases, and the legacy alias
  keyword path still works on its own.
"""
from __future__ import annotations

import json

import pytest

from symbolic_compactification import (
    PROPOSAL_EVIDENCE_KIND,
    AdapterError,
    ExpressionRecord,
    normalize_symbols,
    parse_expression,
    record_proposal,
    run_summary,
    set_current,
    set_requested_arm,
    sha256_text,
)
from symbolic_compactification.cli import main as cli_main
from symbolic_compactification.models import (
    PROPOSER_HARNESS_SUBAGENT,
    PROPOSER_MAIN_AGENT,
    PROPOSER_MODES,
    PROPOSER_MODE_UNKNOWN,
    PROPOSER_SUBAGENT_UNAVAILABLE,
    REQUESTED_ARMS,
)
from symbolic_compactification.session import init_session, load_session


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


def _run_root(tmp_path, session):
    return tmp_path / "runs" / session.run_id


def _proposal_evidence(step) -> dict:
    marked = [e for e in step.evidence
              if isinstance(e, dict)
              and e.get("kind") == PROPOSAL_EVIDENCE_KIND]
    assert len(marked) == 1
    return marked[0]


def _arm_session(tmp_path, arm):
    session = init_session(workspace_root=str(tmp_path), requested_arm=arm)
    set_current(session, _record("x**2 + 2*x + 1"))
    return session


# --------------------------------------------------------------------------- #
# proposer-mode vocabulary + SUBAGENT_UNAVAILABLE
# --------------------------------------------------------------------------- #

def test_proposer_modes_vocabulary_contains_all_four_modes():
    assert set(PROPOSER_MODES) == {
        PROPOSER_MAIN_AGENT,
        PROPOSER_HARNESS_SUBAGENT,
        PROPOSER_SUBAGENT_UNAVAILABLE,
        PROPOSER_MODE_UNKNOWN,
    }
    # SUBAGENT_UNAVAILABLE is a first-class mode DISTINCT from UNKNOWN
    assert PROPOSER_SUBAGENT_UNAVAILABLE != PROPOSER_MODE_UNKNOWN
    assert set(REQUESTED_ARMS) == {"A", "B"}


def test_subagent_unavailable_recordable_and_distinct_from_unknown(tmp_path):
    session = _arm_session(tmp_path, None)

    step = record_proposal(
        session, _candidate("(x+1)**2", candidate_id="cand-unavail"),
        unavailable=True)

    ev = _proposal_evidence(step)
    assert ev["invocation_mode"] == "subagent_unavailable"
    assert ev["unavailable"] is True
    # an unavailable harness never carries a subagent id
    assert ev["harness_task_or_subagent_id"] is None
    assert ev["subagent_id"] is None

    summary = run_summary(_run_root(tmp_path, session))
    assert summary["proposer_mode"] == PROPOSER_SUBAGENT_UNAVAILABLE
    assert summary["proposer_mode"] != PROPOSER_MODE_UNKNOWN
    assert summary["proposer_mode"] in PROPOSER_MODES


def test_unavailable_combined_with_subagent_id_fails_closed(tmp_path):
    """An unavailable harness cannot have invoked a subagent: the
    contradiction is rejected, never recorded silently."""
    session = _arm_session(tmp_path, None)
    with pytest.raises(AdapterError) as excinfo:
        record_proposal(session, _candidate("(x+1)**2", "cand-bad"),
                        unavailable=True,
                        harness_task_or_subagent_id="sub-1")
    assert excinfo.value.code == "PROPOSAL_INVALID"


def test_unavailable_beats_main_agent_but_not_subagent_in_mixed_runs(tmp_path):
    """Documented precedence: HARNESS_SUBAGENT > SUBAGENT_UNAVAILABLE >
    MAIN_AGENT_ONLY when evidence mixes across proposal steps."""
    session = _arm_session(tmp_path, None)
    record_proposal(session, _candidate("(x+1)**2", "c-main"))
    record_proposal(session, _candidate("(x+1)**2", "c-unavail"),
                    unavailable=True)
    summary = run_summary(_run_root(tmp_path, session))
    assert summary["proposer_mode"] == PROPOSER_SUBAGENT_UNAVAILABLE

    record_proposal(session, _candidate("(x+1)**2", "c-sub"),
                    harness_task_or_subagent_id="sub-9")
    summary = run_summary(_run_root(tmp_path, session))
    assert summary["proposer_mode"] == PROPOSER_HARNESS_SUBAGENT


# --------------------------------------------------------------------------- #
# ab_arm_valid / invalid_reason (judged strictly from recorded evidence)
# --------------------------------------------------------------------------- #

def test_arm_b_without_subagent_evidence_is_invalid(tmp_path):
    session = _arm_session(tmp_path, "B")
    record_proposal(session, _candidate("(x+1)**2", "c-main"))

    summary = run_summary(_run_root(tmp_path, session))
    assert summary["requested_arm"] == "B"
    assert summary["proposer_mode"] == PROPOSER_MAIN_AGENT
    assert summary["ab_arm_valid"] is False
    assert summary["invalid_reason"] == "SUBAGENT_NOT_INVOKED"


def test_arm_b_with_recorded_harness_id_is_valid(tmp_path):
    session = _arm_session(tmp_path, "B")
    record_proposal(session, _candidate("(x+1)**2", "c-sub"),
                    harness_task_or_subagent_id="sub-77")

    summary = run_summary(_run_root(tmp_path, session))
    assert summary["requested_arm"] == "B"
    assert summary["proposer_mode"] == PROPOSER_HARNESS_SUBAGENT
    assert summary["ab_arm_valid"] is True
    assert summary["invalid_reason"] is None


def test_arm_a_without_subagent_evidence_is_valid(tmp_path):
    session = _arm_session(tmp_path, "A")
    record_proposal(session, _candidate("(x+1)**2", "c-main"))

    summary = run_summary(_run_root(tmp_path, session))
    assert summary["requested_arm"] == "A"
    assert summary["ab_arm_valid"] is True
    assert summary["invalid_reason"] is None


def test_arm_a_with_subagent_evidence_is_invalid(tmp_path):
    session = _arm_session(tmp_path, "A")
    record_proposal(session, _candidate("(x+1)**2", "c-sub"),
                    harness_task_or_subagent_id="sub-77")

    summary = run_summary(_run_root(tmp_path, session))
    assert summary["requested_arm"] == "A"
    assert summary["proposer_mode"] == PROPOSER_HARNESS_SUBAGENT
    assert summary["ab_arm_valid"] is False
    assert summary["invalid_reason"] == "SUBAGENT_INVOKED"


def test_arm_a_with_explicit_subagent_unavailable_is_valid(tmp_path):
    """An explicit SUBAGENT_UNAVAILABLE record means the MAIN agent did the
    proposing — arm A is honored."""
    session = _arm_session(tmp_path, "A")
    record_proposal(session, _candidate("(x+1)**2", "c-unavail"),
                    unavailable=True)

    summary = run_summary(_run_root(tmp_path, session))
    assert summary["proposer_mode"] == PROPOSER_SUBAGENT_UNAVAILABLE
    assert summary["ab_arm_valid"] is True
    assert summary["invalid_reason"] is None


def test_arm_a_with_no_evidence_at_all_fails_closed(tmp_path):
    """Absence of evidence is not evidence of arm A: with zero proposals
    the mode is UNKNOWN and arm A is invalid with PROPOSER_MODE_UNKNOWN."""
    session = _arm_session(tmp_path, "A")
    summary = run_summary(_run_root(tmp_path, session))
    assert summary["proposer_mode"] == PROPOSER_MODE_UNKNOWN
    assert summary["ab_arm_valid"] is False
    assert summary["invalid_reason"] == "PROPOSER_MODE_UNKNOWN"


def test_no_requested_arm_makes_no_validity_claim(tmp_path):
    """requested_arm None: the summary makes NO validity claim — ab_arm_valid
    is vacuously True with no invalid_reason, whatever the evidence."""
    session = _arm_session(tmp_path, None)
    record_proposal(session, _candidate("(x+1)**2", "c-sub"),
                    harness_task_or_subagent_id="sub-3")

    summary = run_summary(_run_root(tmp_path, session))
    assert summary["requested_arm"] is None
    assert summary["ab_arm_valid"] is True
    assert summary["invalid_reason"] is None


# --------------------------------------------------------------------------- #
# arm declaration persistence (init/set/load) + CLI smoke
# --------------------------------------------------------------------------- #

def test_requested_arm_rejected_when_unknown(tmp_path):
    with pytest.raises(AdapterError) as excinfo:
        init_session(workspace_root=str(tmp_path), requested_arm="C")
    assert excinfo.value.code == "REQUESTED_ARM_INVALID"


def test_requested_arm_case_insensitive_and_persisted(tmp_path):
    session = init_session(workspace_root=str(tmp_path), requested_arm="b")
    assert session.requested_arm == "B"
    manifest = json.loads(
        (_run_root(tmp_path, session) / "manifest.json")
        .read_text(encoding="utf-8"))
    assert manifest["requested_arm"] == "B"


def test_set_requested_arm_persists_and_clears(tmp_path):
    session = _arm_session(tmp_path, None)
    set_requested_arm(session, "A")
    manifest = json.loads(
        (_run_root(tmp_path, session) / "manifest.json")
        .read_text(encoding="utf-8"))
    assert manifest["requested_arm"] == "A"

    set_requested_arm(session, None)
    manifest = json.loads(
        (_run_root(tmp_path, session) / "manifest.json")
        .read_text(encoding="utf-8"))
    assert manifest["requested_arm"] is None

    with pytest.raises(AdapterError) as excinfo:
        set_requested_arm(session, "Z")
    assert excinfo.value.code == "REQUESTED_ARM_INVALID"


def test_load_session_restores_requested_arm(tmp_path):
    session = _arm_session(tmp_path, "B")
    reloaded = load_session(str(tmp_path), session.run_id)
    assert reloaded.requested_arm == "B"
    summary = run_summary(_run_root(tmp_path, session))
    assert summary["requested_arm"] == "B"


def test_cli_init_session_requested_arm_smoke(tmp_path, capsys):
    """CLI smoke: init-session --requested-arm B exits 0, prints the arm,
    and persists the declaration into the run manifest."""
    exit_code = cli_main([
        "init-session", "--workspace", str(tmp_path), "--requested-arm", "B"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "arm:      B" in out

    run_id = next(line.split("run_id:")[1].strip()
                  for line in out.splitlines() if "run_id:" in line)
    manifest = json.loads(
        (tmp_path / "runs" / run_id / "manifest.json")
        .read_text(encoding="utf-8"))
    assert manifest["requested_arm"] == "B"


# --------------------------------------------------------------------------- #
# invocation provenance: v0.2.2 contract names + legacy aliases
# --------------------------------------------------------------------------- #

def test_contract_provenance_names_recorded_in_step_evidence(tmp_path):
    session = _arm_session(tmp_path, None)
    packet_sha = "f" * 64

    step = record_proposal(
        session, _candidate("(x+1)**2", candidate_id="cand-contract"),
        harness_task_or_subagent_id="task-77",
        invoked_at="2026-03-01T10:00:00Z",
        returned_at="2026-03-01T10:00:09Z",
        parent_agent_step=4,
        conjecture_packet_sha256=packet_sha)

    ev = _proposal_evidence(step)
    # CONTRACT field names are present and carry the supplied values
    assert ev["harness_task_or_subagent_id"] == "task-77"
    assert ev["invoked_at"] == "2026-03-01T10:00:00Z"
    assert ev["returned_at"] == "2026-03-01T10:00:09Z"
    assert ev["parent_agent_step"] == 4
    assert ev["conjecture_packet_sha256"] == packet_sha
    assert ev["invocation_mode"] == "subagent"
    # legacy aliases are ALSO written (pre-v0.2.2 consumers keep working)
    assert ev["subagent_id"] == "task-77"
    assert ev["invocation_timestamp"] == ev["invoked_at"]
    assert ev["parent_step_index"] == 4

    # the evidence survives the JSON round-trip into the step file
    step_file = (_run_root(tmp_path, session) / "steps" / "step_001.json")
    persisted = json.loads(step_file.read_text(encoding="utf-8"))
    pev = next(e for e in persisted["evidence"]
               if e.get("kind") == PROPOSAL_EVIDENCE_KIND)
    assert pev["harness_task_or_subagent_id"] == "task-77"
    assert pev["returned_at"] == "2026-03-01T10:00:09Z"
    assert pev["conjecture_packet_sha256"] == packet_sha

    summary = run_summary(_run_root(tmp_path, session))
    assert summary["proposer_mode"] == PROPOSER_HARNESS_SUBAGENT


def test_legacy_alias_keywords_still_work_alone(tmp_path):
    session = _arm_session(tmp_path, None)

    step = record_proposal(
        session, _candidate("(x+1)**2", candidate_id="cand-legacy"),
        subagent_id="legacy-9",
        invocation_timestamp="2026-03-02T11:00:00Z",
        parent_step_index=2)

    ev = _proposal_evidence(step)
    # legacy inputs surface under BOTH the contract names and the aliases
    assert ev["harness_task_or_subagent_id"] == "legacy-9"
    assert ev["subagent_id"] == "legacy-9"
    assert ev["invoked_at"] == "2026-03-02T11:00:00Z"
    assert ev["invocation_timestamp"] == "2026-03-02T11:00:00Z"
    assert ev["parent_agent_step"] == 2
    assert ev["parent_step_index"] == 2
    # fields introduced in v0.2.2 default to None when not supplied
    assert ev["returned_at"] is None
    assert ev["conjecture_packet_sha256"] is None

    summary = run_summary(_run_root(tmp_path, session))
    assert summary["proposer_mode"] == PROPOSER_HARNESS_SUBAGENT
