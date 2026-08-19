"""Synthetic end-to-end protocol tests for the STRUCTURAL_PROPOSER layer
(agent protocol v0.2.1).

Everything here is scripted: the "proposer" is a plain deterministic Python
callable returning pre-authored candidate dicts (``ScriptedProposer``) — NO
live model, NO network. Only generic symbols (x, n, N) and undefined-function
names (f, g) are used; zero scientific content.

Coverage:
* CASE A — end-to-end synthetic loop: packet -> scripted proposal ->
  validation -> exact ZERO verification -> promotion (CERTIFIED step).
* CASE B — refuted candidate: NONZERO with residual + counterexample, the
  feedback round-trips through a new conjecture packet, the scripted
  proposer corrects itself -> ZERO -> promoted.
* CASE C — fail-closed UNKNOWN: no promotion, current unchanged; the
  proposer decomposes into a smaller HYPOTHESIS claim; no false
  certification anywhere.
* Proposal steps can NEVER promote (VERDICT_NOT_ZERO gate).
* assumptions_status HUMAN_REQUIRED candidates are recordable but never
  auto-certified: only a normal ZERO verification step unlocks promotion.
* Manifest records agent_protocol_version 0.2.1 and engine_version 0.2.0.
* run_summary separates proposal steps from verification steps.
"""
from __future__ import annotations

import json

import pytest
import sympy

from symbolic_compactification import (
    AGENT_PROTOCOL_VERSION,
    ENGINE_VERSION,
    NONZERO,
    PROPOSAL_EVIDENCE_KIND,
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
    validate_candidate,
    verify_equivalent,
)
from symbolic_compactification.session import init_session, promote

# A candidate engineered so every exact rational probe in the lattice is a
# root: no probe can be PROVEN nonzero, simplify cannot decide, so the
# fail-closed verdict is UNKNOWN (the same construction the session suite
# already pins down as adversarial-UNKNOWN).
ADVERSARIAL_UNKNOWN_CANDIDATE = (
    "(x - 1)*(x - Rational(1,2))*(x + 1)"
    "*(x + 2)*(x - 2)*(x + Rational(1,2))")


# --------------------------------------------------------------------------- #
# helpers: scripted proposer + record/step builders
# --------------------------------------------------------------------------- #

class ScriptedProposer:
    """Deterministic mock of the STRUCTURAL_PROPOSER subagent.

    A plain Python callable: receives a conjecture packet, returns the next
    pre-authored candidate dict from its script. Records every packet it saw
    so tests can assert on the feedback round-trip.
    """

    def __init__(self, script):
        self._script = list(script)
        self.received_packets = []

    def __call__(self, packet):
        self.received_packets.append(packet)
        assert self._script, "proposer script exhausted unexpectedly"
        return self._script.pop(0)


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


def _verification_step(session, candidate_rec, result, status: str):
    """A real verification StepRecord with cli-style telemetry."""
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


def _read_manifest(tmp_path, session):
    return json.loads((_run_root(tmp_path, session)
                       / "manifest.json").read_text("utf-8"))


# --------------------------------------------------------------------------- #
# CASE A — end-to-end synthetic loop: proposal -> ZERO -> promotion
# --------------------------------------------------------------------------- #

def test_case_a_end_to_end_synthetic_loop(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    current_rec = _record("Sum(f(n) + g(n), (n, 1, N))",
                          symbols=("N", "n"), functions=("f", "g"))
    set_current(session, current_rec)

    # main agent assembles the conjecture packet from the certified state
    packet = build_conjecture_packet(
        session, goal="split the combined sum into its structural summands")
    assert packet["current_expression"] == current_rec.text
    assert packet["structure_summary"]["sums"] == 1

    # scripted proposer exploits the sum-of-sums structure
    proposer = ScriptedProposer([_candidate(
        "Sum(f(n), (n, 1, N)) + Sum(g(n), (n, 1, N))",
        candidate_id="case-a-split-sum",
        hypothesis="the summand is a sum of two kernels; Sum splits "
                   "linearly over it",
    )])
    validated = validate_candidate(proposer(packet))
    assert validated["status"] == "HYPOTHESIS"
    record_proposal(session, validated)

    # deterministic verifier adjudicates: exact ZERO
    candidate_rec = _record(validated["candidate_expression_or_rewrite"],
                            symbols=("N", "n"), functions=("f", "g"))
    result = verify_equivalent(session.current.text, candidate_rec.text,
                               current_rec.symbols, functions=["f", "g"])
    assert result.verdict == ZERO
    record_step(session, _verification_step(
        session, candidate_rec, result, status="CERTIFIED"))

    # promotion (main agent only) advances the certified state
    promote(session, candidate_rec)
    assert session.current.text == candidate_rec.text
    final = json.loads((_run_root(tmp_path, session) / "final"
                        / "current.json").read_text("utf-8"))
    assert final["text"] == candidate_rec.text
    assert final["sha256"] == candidate_rec.sha256

    # proposal stays HYPOTHESIS; only the verification step is CERTIFIED
    assert [s.status for s in session.steps] == ["HYPOTHESIS", "CERTIFIED"]
    assert [s.verdict for s in session.steps] == [UNKNOWN, ZERO]
    assert _read_manifest(tmp_path, session)["current"]["text"] == \
        candidate_rec.text


# --------------------------------------------------------------------------- #
# CASE B — NONZERO refutation, residual feedback, corrected candidate
# --------------------------------------------------------------------------- #

def test_case_b_nonzero_feedback_then_corrected_candidate_promotes(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    current_rec = _record("x**2 + 2*x + 1")
    set_current(session, current_rec)

    proposer = ScriptedProposer([
        # first attempt: plausible but wrong constant term
        _candidate("x**2 + 2*x - 1", candidate_id="case-b-wrong-constant"),
        # corrected after seeing the residual feedback
        _candidate("(x+1)**2", candidate_id="case-b-corrected"),
    ])

    # round 1: candidate refuted with an exact counterexample
    packet1 = build_conjecture_packet(
        session, goal="factor the expanded polynomial")
    validated1 = validate_candidate(proposer(packet1))
    record_proposal(session, validated1)
    result1 = verify_equivalent(session.current.text,
                                validated1["candidate_expression_or_rewrite"],
                                ["x"])
    assert result1.verdict == NONZERO
    assert result1.residual and result1.simplified_residual
    assert result1.counterexample is not None
    assert result1.counterexample["exact_value"]
    record_step(session, _verification_step(
        session,
        _record(validated1["candidate_expression_or_rewrite"]),
        result1, status="UNVERIFIED"))

    # round 2: residual + counterexample fed back through the packet
    packet2 = build_conjecture_packet(session, feedback={
        "verdict": result1.verdict,
        "simplified_residual": result1.simplified_residual,
        "counterexample": result1.counterexample,
    })
    feedback_entry = packet2["verifier_feedback"][0]
    assert feedback_entry["verdict"] == NONZERO
    assert feedback_entry["residual"] == result1.simplified_residual
    assert feedback_entry["counterexample"] == result1.counterexample

    validated2 = validate_candidate(proposer(packet2))
    record_proposal(session, validated2)
    result2 = verify_equivalent(session.current.text,
                                validated2["candidate_expression_or_rewrite"],
                                ["x"])
    assert result2.verdict == ZERO
    candidate_rec = _record(validated2["candidate_expression_or_rewrite"])
    record_step(session, _verification_step(
        session, candidate_rec, result2, status="CERTIFIED"))

    promote(session, candidate_rec)
    assert session.current.text == "(x+1)**2"
    final = json.loads((_run_root(tmp_path, session) / "final"
                        / "current.json").read_text("utf-8"))
    assert final["text"] == "(x+1)**2"

    # the proposer saw exactly two packets, the second carrying feedback
    assert len(proposer.received_packets) == 2
    assert proposer.received_packets[0]["verifier_feedback"] == []
    assert proposer.received_packets[1]["verifier_feedback"][0][
        "verdict"] == NONZERO


# --------------------------------------------------------------------------- #
# CASE C — UNKNOWN: fail-closed, no promotion, decomposition into HYPOTHESIS
# --------------------------------------------------------------------------- #

def test_case_c_unknown_never_promotes_and_decomposes_to_hypothesis(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    current_rec = _record("0")
    set_current(session, current_rec)

    proposer = ScriptedProposer([
        # difficult candidate engineered to land in the UNKNOWN path
        _candidate(ADVERSARIAL_UNKNOWN_CANDIDATE,
                   candidate_id="case-c-difficult"),
        # decomposition: a strictly smaller claim, still unproven
        _candidate("x**2 - 1", candidate_id="case-c-smaller-lemma",
                   hypothesis="the factor pair (x-1)*(x+1) alone equals "
                              "x**2 - 1; a smaller lemma to certify first"),
    ])

    packet = build_conjecture_packet(session)
    validated = validate_candidate(proposer(packet))
    record_proposal(session, validated)

    result = verify_equivalent(session.current.text,
                               validated["candidate_expression_or_rewrite"],
                               ["x"])
    assert result.verdict == UNKNOWN
    assert result.counterexample is None
    record_step(session, _verification_step(
        session, _record(ADVERSARIAL_UNKNOWN_CANDIDATE),
        result, status="UNVERIFIED"))

    # fail-closed: promotion is refused, current stays untouched
    with pytest.raises(AdapterError) as excinfo:
        promote(session, _record(ADVERSARIAL_UNKNOWN_CANDIDATE))
    assert excinfo.value.code == "VERDICT_NOT_ZERO"
    assert session.current.text == "0"
    assert not (_run_root(tmp_path, session) / "final"
                / "current.json").exists()

    # the proposer decomposes: the smaller claim is recorded as a HYPOTHESIS
    decomposed = validate_candidate(proposer(build_conjecture_packet(session)))
    decomp_step = record_proposal(session, decomposed)
    assert decomp_step.status == "HYPOTHESIS"
    assert decomp_step.verdict == UNKNOWN
    assert decomp_step.evidence[0]["kind"] == PROPOSAL_EVIDENCE_KIND

    # no false certification ANYWHERE in the run
    for step in session.steps:
        assert step.status != "CERTIFIED"
        assert step.verdict != ZERO
    with pytest.raises(AdapterError) as excinfo:
        promote(session, _record("x**2 - 1"))
    assert excinfo.value.code == "VERDICT_NOT_ZERO"
    manifest = _read_manifest(tmp_path, session)
    assert manifest["current"]["text"] == "0"
    assert all(s["status"] != "CERTIFIED" for s in manifest["steps"])


# --------------------------------------------------------------------------- #
# contract: a proposal step can NEVER promote
# --------------------------------------------------------------------------- #

def test_record_proposal_writes_hypothesis_step_that_can_never_promote(
        tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    set_current(session, _record("x**2 + 2*x + 1"))

    step = record_proposal(session, _candidate("(x+1)**2",
                                               candidate_id="never-promote"))
    assert step.status == "HYPOTHESIS"
    assert step.verdict == UNKNOWN          # no verifier ran on a proposal
    assert step.evidence[0]["kind"] == PROPOSAL_EVIDENCE_KIND
    assert step.telemetry["primitive"] == "proposal"
    assert step.telemetry["agent_protocol_version"] == AGENT_PROTOCOL_VERSION
    assert step.telemetry["engine_version"] == ENGINE_VERSION

    # persisted step file carries the same markers
    step_file = _run_root(tmp_path, session) / "steps" / "step_001.json"
    data = json.loads(step_file.read_text("utf-8"))
    assert data["status"] == "HYPOTHESIS"
    assert data["verdict"] == UNKNOWN
    assert data["evidence"][0]["kind"] == PROPOSAL_EVIDENCE_KIND

    # promotion is hard-gated: a proposal alone is NEVER enough
    with pytest.raises(AdapterError) as excinfo:
        promote(session, _record("(x+1)**2"))
    assert excinfo.value.code == "VERDICT_NOT_ZERO"
    assert list((_run_root(tmp_path, session) / "final").iterdir()) == []
    assert session.current.text == "x**2 + 2*x + 1"


# --------------------------------------------------------------------------- #
# contract: HUMAN_REQUIRED assumptions are never auto-certified
# --------------------------------------------------------------------------- #

def test_human_required_candidate_never_auto_certified(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    set_current(session, _record("(x+1)**2"))

    human_candidate = _candidate(
        "x**2 + 2*x + 1", candidate_id="human-gated",
        required_assumptions=["x is an integer"],
        assumptions_status="HUMAN_REQUIRED",
        confidence="low")
    step = record_proposal(session, human_candidate)

    # recordable, with the gate marker persisted in the step evidence
    assert step.status == "HYPOTHESIS"
    assert step.evidence[0]["assumptions_status"] == "HUMAN_REQUIRED"

    # the protocol path does NOT auto-verify/promote a HUMAN_REQUIRED
    # candidate: the proposal alone cannot advance the state
    with pytest.raises(AdapterError) as excinfo:
        promote(session, _record("x**2 + 2*x + 1"))
    assert excinfo.value.code == "VERDICT_NOT_ZERO"

    # ... it still requires a NORMAL ZERO verification step; only that
    # deterministic adjudication (with the declared assumptions on record)
    # unlocks the main agent's promotion path.
    candidate_rec = _record("x**2 + 2*x + 1")
    result = verify_equivalent(session.current.text, candidate_rec.text,
                               ["x"])
    assert result.verdict == ZERO
    record_step(session, _verification_step(
        session, candidate_rec, result, status="CERTIFIED"))
    promote(session, candidate_rec)
    assert session.current.text == "x**2 + 2*x + 1"


# --------------------------------------------------------------------------- #
# contract: manifest carries both protocol versions
# --------------------------------------------------------------------------- #

def test_manifest_records_agent_protocol_and_engine_versions(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    set_current(session, _record("x"))
    manifest = _read_manifest(tmp_path, session)
    assert manifest["agent_protocol_version"] == "0.2.2"
    assert manifest["engine_version"] == "0.2.0"
    assert AGENT_PROTOCOL_VERSION == "0.2.2"
    assert ENGINE_VERSION == "0.2.0"


# --------------------------------------------------------------------------- #
# contract: run_summary separates proposals from verifications
# --------------------------------------------------------------------------- #

def test_run_summary_counters_exclude_proposal_steps(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    current_rec = _record("x**2 + 2*x + 1")
    set_current(session, current_rec)

    # 1 proposal step (no verifier ran)
    record_proposal(session, _candidate("(x+1)**2", candidate_id="summary-p"))

    # verification 1: ZERO
    ok_rec = _record("(x+1)**2")
    result_zero = verify_equivalent(current_rec.text, ok_rec.text, ["x"])
    assert result_zero.verdict == ZERO
    record_step(session, _verification_step(
        session, ok_rec, result_zero, status="CERTIFIED"))

    # verification 2: NONZERO
    bad_rec = _record("x**2 + 2*x + 3")
    result_nonzero = verify_equivalent(current_rec.text, bad_rec.text, ["x"])
    assert result_nonzero.verdict == NONZERO
    record_step(session, _verification_step(
        session, bad_rec, result_nonzero, status="UNVERIFIED"))

    summary = run_summary(_run_root(tmp_path, session))
    assert summary["agent_protocol_version"] == "0.2.2"
    assert summary["engine_version"] == "0.2.0"
    assert summary["candidates_proposed"] == 1
    assert summary["zero_promotions"] == 1
    assert summary["nonzero_count"] == 1
    # the proposal's UNKNOWN verdict must NOT leak into unknown_count or
    # verifier_calls
    assert summary["unknown_count"] == 0
    assert summary["verifier_calls"] == 2

    # count_ops fields come from verification telemetry only
    ops_current = sympy.count_ops(current_rec.parsed_expr)
    ops_ok = sympy.count_ops(ok_rec.parsed_expr)
    ops_bad = sympy.count_ops(bad_rec.parsed_expr)
    assert summary["count_ops_first"] == ops_current
    assert summary["count_ops_current"] == ops_bad
    assert ops_ok != ops_bad  # guards against a vacuous equality
