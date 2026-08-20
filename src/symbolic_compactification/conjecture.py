"""Agent-protocol layer (v0.2.1): conjecture packets and proposer candidates.

This module is the ONLY new machinery of the v0.2.1 agent-protocol increment.
The deterministic engine (parser, verifier, budgets, transforms, rules) is
unchanged from v0.2.0; nothing here can verify, certify or promote anything.

There is deliberately NO agent runtime, NO LLM API integration, and NO
orchestration system in this repository. The "proposer" is a harness-native
subagent (Qoder / Codex / Claude Code each provide their own native subagent
facility); the main agent feeds it the role contract
(``roles/STRUCTURAL_PROPOSER.md``) plus a conjecture packet built by
``build_conjecture_packet`` and receives back candidate JSON validated by
``validate_candidate``.

Contents
--------
* ``build_conjecture_packet(source, *, goal=None, feedback=None)`` —
  deterministic, JSON-serializable assembly of the proposer's input packet
  from the current certified expression record (or a session holding it).
* ``validate_candidate(candidate)`` — strict schema enforcement for proposer
  output. The status is FORCED to ``HYPOTHESIS``; any claim of another status
  (e.g. ``CERTIFIED``) is rejected. Validation NEVER certifies.
* ``record_proposal(session, candidate)`` — records a validated proposal as a
  ``HYPOTHESIS`` step via the existing StepRecord/session machinery. No
  promotion is possible from this path (promotion stays hard-gated on a ZERO
  verdict of a real verification step).

Zero scientific content: everything here is generic plumbing.
"""
from __future__ import annotations

from typing import Any, Optional, Union

import sympy

from .models import (AGENT_PROTOCOL_VERSION, DEFAULT_PROPOSER_ROLE,
                     ENGINE_VERSION, NONZERO, PROPOSAL_EVIDENCE_KIND, UNKNOWN,
                     ZERO, AdapterError, ExpressionRecord, SessionState,
                     StepRecord, _now_iso, canonical_json, sha256_text)
from .parser import parse_expression
from .structure import structure_summary

__all__ = [
    "ASSUMPTION_STATUSES", "CONFIDENCE_LEVELS", "PROPOSAL_EVIDENCE_KIND",
    "build_conjecture_packet", "validate_candidate", "record_proposal",
]

# Assumption status of a candidate: every required assumption is either
# already DECLARED on record, or a NEW assumption requiring human
# authorization (HUMAN_REQUIRED); NONE when no assumptions are needed.
#
# Taxonomy note (v0.2.2): ``PROOF_REQUIRED`` is a STEP status (models.py),
# not an assumption status — it marks "assumptions already sufficient, but the
# verifier cannot prove the claim". It must NOT be conflated with
# ``HUMAN_REQUIRED``: the inability to prove a limit/special-function identity
# is a proof gap (PROOF_REQUIRED), not a request for new human-authorized
# assumptions (HUMAN_REQUIRED). HUMAN_REQUIRED remains a certification gate.
ASSUMPTION_STATUSES = ("DECLARED", "HUMAN_REQUIRED", "NONE")

CONFIDENCE_LEVELS = ("low", "medium", "high")

# Evidence kind marking a step as a proposer hypothesis (no verifier call);
# defined in models.py and shared with ``session.run_summary``.

# Attention isolation: what the packet deliberately does NOT carry. The
# proposer must reason from structure, not from implementation archaeology
# or flattened diagnostic residue.
_WITHHELD_ATTENTION = [
    "git_history",
    "test_suite_output",
    "parser_cli_implementation",
    "telemetry_internals",
    "unrelated_shell_logs",
    "flattened_diagnostic_terms",
    "repository_maintenance_tasks",
]

_VERDICTS = (ZERO, NONZERO, UNKNOWN)

# The exact candidate schema: required keys only; unknown keys are rejected.
_CANDIDATE_STRING_FIELDS = (
    "candidate_id",
    "hypothesis",
    "candidate_expression_or_rewrite",
    "rationale",
    "expected_structural_benefit",
    "suggested_verification_strategy",
)
_CANDIDATE_KEYS = frozenset(_CANDIDATE_STRING_FIELDS + (
    "status", "required_assumptions", "assumptions_status", "confidence"))


# --------------------------------------------------------------------------- #
# conjecture packet assembly (deterministic; JSON-serializable)
# --------------------------------------------------------------------------- #

def _resolve_record(source: Union[SessionState, ExpressionRecord, Any]
                    ) -> ExpressionRecord:
    """Extract the current expression record from a session or a bare record."""
    if isinstance(source, SessionState):
        record = source.current
    elif isinstance(source, ExpressionRecord):
        record = source
    else:
        raise AdapterError("CONJECTURE_SOURCE_MALFORMED")
    if record is None:
        raise AdapterError("NO_CURRENT_EXPRESSION")
    return record


def _structural_view(record: ExpressionRecord
                     ) -> tuple[Optional[sympy.Expr], Optional[str]]:
    """Best-effort structural form of the record; never raises.

    Prefers the record's cached parse (``load_expression`` always sets it).
    If absent, re-parses strictly with the record's declared symbols; if that
    fails (e.g. the text needs a declared-function namespace the record does
    not persist), the packet degrades to text-only rather than failing.
    """
    if record.parsed_expr is not None:
        return record.parsed_expr, None
    try:
        return parse_expression(record.text, record.symbols), None
    except AdapterError as exc:
        return None, exc.code


def _normalize_feedback(feedback: Any) -> list[dict]:
    """Normalize verifier feedback to a list of {verdict, residual,
    counterexample} dicts. Only the most relevant fields are carried."""
    if feedback is None:
        return []
    items = feedback if isinstance(feedback, list) else [feedback]
    out: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            raise AdapterError("FEEDBACK_MALFORMED")
        verdict = item.get("verdict")
        if verdict is not None and verdict not in _VERDICTS:
            raise AdapterError("FEEDBACK_MALFORMED")
        entry: dict = {"verdict": verdict}
        residual = item.get("simplified_residual") or item.get("residual")
        if residual is not None:
            if not isinstance(residual, str):
                raise AdapterError("FEEDBACK_MALFORMED")
            entry["residual"] = residual
        if item.get("counterexample") is not None:
            entry["counterexample"] = item["counterexample"]
        out.append(entry)
    return out


def build_conjecture_packet(source: Union[SessionState, ExpressionRecord],
                            *,
                            goal: Optional[str] = None,
                            feedback: Any = None) -> dict:
    """Deterministically assemble the STRUCTURAL_PROPOSER conjecture packet.

    Args:
        source:   a ``SessionState`` (its current record is used) or a bare
                  ``ExpressionRecord`` holding the current CERTIFIED
                  expression.
        goal:     optional user-supplied scientific goal string (opaque to
                  the engine; carried verbatim).
        feedback: optional recent verifier feedback — one dict or a list of
                  dicts with ``verdict`` and optionally ``residual`` /
                  ``simplified_residual`` / ``counterexample``.

    Returns:
        A JSON-serializable dict: the packet INCLUDED fields (current
        expression text + hash, structural form, structure_summary, declared
        symbols/functions/assumptions, goal, verifier feedback) plus explicit
        ``included`` / ``withheld`` attention lists. Deterministic: no
        timestamps, no randomness.

    Raises:
        AdapterError("CONJECTURE_SOURCE_MALFORMED") - bad source type
        AdapterError("NO_CURRENT_EXPRESSION")       - session has no current
        AdapterError("CONJECTURE_GOAL_MALFORMED")   - non-string / empty goal
        AdapterError("FEEDBACK_MALFORMED")          - bad feedback shape
    """
    record = _resolve_record(source)
    if goal is not None and (not isinstance(goal, str) or not goal.strip()):
        raise AdapterError("CONJECTURE_GOAL_MALFORMED")

    expr, parse_gap = _structural_view(record)
    if expr is not None:
        structural_form: Optional[str] = str(expr)
        summary: Optional[dict] = structure_summary(expr)
        # The record does not persist a separately declared function
        # namespace; report the undefined-function names observed in the
        # structural form (sorted, deterministic).
        functions = sorted({
            type(sub).__name__
            for sub in sympy.preorder_traversal(expr)
            if isinstance(sub, sympy.core.function.AppliedUndef)
        })
    else:
        structural_form, summary, functions = None, None, []

    declared_symbols = [dict(s) for s in record.symbols]
    # Declared assumptions are exactly the assumption flags on record; the
    # proposer may never extend them (see the role contract).
    declared_assumptions = [
        {"name": s["name"], "real": s.get("real", True),
         "nonzero": s.get("nonzero", False)}
        for s in declared_symbols
    ]

    # Provenance hashes (v0.2.2): the certified state is the record's own
    # content hash; the structural representation is the structural_form text.
    certified_state_sha256 = record.sha256
    structural_representation_sha256 = (
        sha256_text(structural_form) if structural_form is not None else None)

    packet: dict = {
        "packet_type": "conjecture_packet",
        "agent_protocol_version": AGENT_PROTOCOL_VERSION,
        "engine_version": ENGINE_VERSION,
        "current_expression": record.text,
        "current_sha256": record.sha256,
        "certified_state_sha256": certified_state_sha256,
        "structural_representation_sha256":
            structural_representation_sha256,
        "structural_form": structural_form,
        "structure_summary": summary,
        "declared_symbols": declared_symbols,
        "declared_functions": functions,
        "declared_assumptions": declared_assumptions,
        "goal": goal,
        "verifier_feedback": _normalize_feedback(feedback),
        # self-describing attention isolation (see roles/STRUCTURAL_PROPOSER.md)
        "included": [
            "current_expression", "current_sha256", "certified_state_sha256",
            "structural_representation_sha256", "structural_form",
            "structure_summary", "declared_symbols", "declared_functions",
            "declared_assumptions", "goal", "verifier_feedback",
        ],
        "withheld": list(_WITHHELD_ATTENTION),
    }
    if parse_gap is not None:
        # Text-only degradation is recorded explicitly; never silent.
        packet["structural_form_note"] = (
            f"structural form unavailable (strict re-parse failed: "
            f"{parse_gap}); text is primary")

    # Deterministic packet digest (v0.2.2): canonical JSON of every field
    # except the digest itself, so rebuilds are byte-stable.
    packet["packet_sha256"] = sha256_text(canonical_json(packet))

    # Persist a minimal NEUTRAL provenance record when a persisted session is
    # available. No chain-of-thought, no reasoning text — structured fields
    # only. Best-effort: a bare ExpressionRecord (no run dir) skips this.
    if isinstance(source, SessionState) and getattr(source, "run_root", None):
        _persist_packet_provenance(source, packet, goal, declared_assumptions,
                                   feedback, certified_state_sha256,
                                   structural_representation_sha256)
    return packet


def _persist_packet_provenance(session, packet, goal, declared_assumptions,
                               feedback, certified_state_sha256,
                               structural_representation_sha256) -> None:
    """Write the neutral conjecture-packet provenance record to the run dir."""
    from .session import record_packet_provenance  # local: avoid import cycle
    record = {
        "record_type": "conjecture_packet_provenance",
        "agent_protocol_version": AGENT_PROTOCOL_VERSION,
        "engine_version": ENGINE_VERSION,
        "packet_sha256": packet.get("packet_sha256"),
        "certified_state_sha256": certified_state_sha256,
        "structural_representation_sha256":
            structural_representation_sha256,
        "goal": goal,
        "declared_assumptions": declared_assumptions,
        "verifier_feedback_included": bool(_normalize_feedback(feedback)),
        "withheld": list(_WITHHELD_ATTENTION),
    }
    try:
        record_packet_provenance(session, record)
    except AdapterError:
        # A missing/unwritable run dir must never break packet assembly; the
        # packet itself remains fully usable in-memory.
        pass


# --------------------------------------------------------------------------- #
# candidate validation (schema enforcement; NEVER certifies)
# --------------------------------------------------------------------------- #

def validate_candidate(candidate: Any) -> dict:
    """Strictly validate one STRUCTURAL_PROPOSER candidate.

    Enforces the output contract of ``roles/STRUCTURAL_PROPOSER.md``:
    all required fields present and non-empty, unknown keys rejected,
    ``assumptions_status`` in ``ASSUMPTION_STATUSES``, ``confidence`` in
    ``CONFIDENCE_LEVELS``. The ``status`` is FORCED to ``HYPOTHESIS``: an
    absent status defaults to it, and any OTHER claimed status — including
    ``CERTIFIED`` or ``UNVERIFIED`` — is a violation and rejected.

    NOTE: validation NEVER certifies. A validated candidate is an unproven
    claim; only the deterministic verifier's ZERO verdict certifies, and
    only the main agent's promotion path advances the state.

    Returns:
        A normalized copy of the candidate (status == "HYPOTHESIS").

    Raises:
        AdapterError("PROPOSAL_INVALID") on any violation.
    """
    if not isinstance(candidate, dict):
        raise AdapterError("PROPOSAL_INVALID")
    if set(candidate) - _CANDIDATE_KEYS:
        raise AdapterError("PROPOSAL_INVALID")

    out: dict = {}
    for key in _CANDIDATE_STRING_FIELDS:
        value = candidate.get(key)
        if not isinstance(value, str) or not value.strip():
            raise AdapterError("PROPOSAL_INVALID")
        out[key] = value.strip()

    # Status: forced to HYPOTHESIS; claiming any other status is rejected.
    status = candidate.get("status", "HYPOTHESIS")
    if status != "HYPOTHESIS":
        raise AdapterError("PROPOSAL_INVALID")
    out["status"] = "HYPOTHESIS"

    required_assumptions = candidate.get("required_assumptions")
    if not isinstance(required_assumptions, list) or not all(
            isinstance(a, (str, dict)) for a in required_assumptions):
        raise AdapterError("PROPOSAL_INVALID")
    out["required_assumptions"] = list(required_assumptions)

    assumptions_status = candidate.get("assumptions_status")
    if not isinstance(assumptions_status, str) or \
            assumptions_status.upper() not in ASSUMPTION_STATUSES:
        raise AdapterError("PROPOSAL_INVALID")
    out["assumptions_status"] = assumptions_status.upper()

    confidence = candidate.get("confidence")
    if not isinstance(confidence, str) or \
            confidence.lower() not in CONFIDENCE_LEVELS:
        raise AdapterError("PROPOSAL_INVALID")
    out["confidence"] = confidence.lower()

    return out


# --------------------------------------------------------------------------- #
# proposal recording (HYPOTHESIS step; promotion impossible from this path)
# --------------------------------------------------------------------------- #

def record_proposal(session: SessionState, candidate: Any, *,
                    role: str = DEFAULT_PROPOSER_ROLE,
                    harness_task_or_subagent_id: Optional[str] = None,
                    invocation_timestamp: Optional[str] = None,
                    parent_step_index: Optional[int] = None,
                    unavailable: bool = False,
                    subagent_id: Optional[str] = None,
                    invoked_at: Optional[str] = None,
                    parent_agent_step: Optional[int] = None,
                    conjecture_packet_sha256: Optional[str] = None,
                    returned_at: Optional[str] = None) -> StepRecord:
    """Record a validated proposer candidate as a HYPOTHESIS step.

    Uses the existing ``StepRecord`` status machinery: the step is written
    with ``status="HYPOTHESIS"`` and ``verdict=UNKNOWN`` (NO verifier ran on
    it — it is a proposal, not an adjudication). Promotion remains
    hard-gated on a real verification step's ZERO verdict, so nothing here
    can advance the current expression.

    Invocation provenance (v0.2.2) is recorded in the step's evidence —
    structured fields only, no reasoning text. The CONTRACT field names and
    their backward-compatible aliases (both are written; existing consumers
    keep working):

      ============================  ==============================
      contract field                legacy alias (still written)
      ============================  ==============================
      ``role``                      ``role``
      ``harness_task_or_subagent_id``  ``subagent_id``
      ``invoked_at``                ``invocation_timestamp``
      ``returned_at``               (new; may be None)
      ``parent_agent_step``         ``parent_step_index``
      ``candidate_id``              ``candidate_id``
      ``proposal_sha256``           ``proposal_sha256``
      ``conjecture_packet_sha256``  (new; may be None)
      ============================  ==============================

    plus ``invocation_mode`` (``main_agent`` | ``subagent`` |
    ``subagent_unavailable``), ``unavailable`` (bool), ``assumptions_status``,
    ``confidence`` and ``proposal_timestamp`` (when this record was written).

    ``unavailable=True`` records the SUBAGENT_UNAVAILABLE mode explicitly:
    the harness cannot expose native subagent invocation for this run. It is
    DISTINCT from UNKNOWN (ambiguous/absent evidence) and must not carry a
    subagent id (fail closed: ``PROPOSAL_INVALID``). Keyword aliases resolve
    as: ``subagent_id`` unless ``harness_task_or_subagent_id`` is given,
    ``invoked_at`` unless ``invocation_timestamp`` is given, and
    ``parent_agent_step`` unless ``parent_step_index`` is given.

    HARNESS_SUBAGENT is NEVER faked: it requires a RECORDED harness
    task/subagent id. An internal in-process callback is not a subagent, and
    reading ``roles/STRUCTURAL_PROPOSER.md`` is never evidence of any mode.

    Raises:
        AdapterError("PROPOSAL_INVALID")     - candidate fails validation,
                                               or ``unavailable`` is combined
                                               with a subagent id
        AdapterError("NO_CURRENT_EXPRESSION") - session has no current
        AdapterError("SESSION_NOT_PERSISTED") - session has no run_root
    """
    validated = validate_candidate(candidate)
    if session.current is None:
        raise AdapterError("NO_CURRENT_EXPRESSION")

    # resolve keyword aliases: contract names win over legacy names
    if harness_task_or_subagent_id is None and subagent_id is not None:
        harness_task_or_subagent_id = subagent_id
    if invocation_timestamp is None and invoked_at is not None:
        invocation_timestamp = invoked_at
    if parent_step_index is None and parent_agent_step is not None:
        parent_step_index = parent_agent_step

    raw_subagent_id = (str(harness_task_or_subagent_id).strip()
                       if harness_task_or_subagent_id is not None else None) or None
    if unavailable:
        if raw_subagent_id is not None:
            # fail closed: an unavailable harness cannot have invoked a
            # subagent; the contradiction must never be recorded silently
            raise AdapterError("PROPOSAL_INVALID")
        invocation_mode = "subagent_unavailable"
    else:
        invocation_mode = "subagent" if raw_subagent_id else "main_agent"
    if invocation_timestamp is None:
        invocation_timestamp = _now_iso()
    if parent_step_index is None:
        parent_step_index = len(session.steps)
    proposal_sha256 = sha256_text(canonical_json(validated))
    proposal_timestamp = _now_iso()
    if conjecture_packet_sha256 is not None:
        conjecture_packet_sha256 = str(conjecture_packet_sha256)
    if returned_at is not None:
        returned_at = str(returned_at)

    step = StepRecord(
        step=len(session.steps) + 1,
        current_hash=session.current.sha256,
        candidate_hash=sha256_text(validated["candidate_expression_or_rewrite"]),
        candidate_text=validated["candidate_expression_or_rewrite"],
        residual=None,
        # no verifier ran: a proposal is never evidence for or against itself
        verdict=UNKNOWN,
        evidence=[{
            "kind": PROPOSAL_EVIDENCE_KIND,
            "candidate_id": validated["candidate_id"],
            "assumptions_status": validated["assumptions_status"],
            "confidence": validated["confidence"],
            # invocation provenance (v0.2.2) — structured fields only.
            # Contract field names first, legacy aliases after; both are
            # written so existing consumers keep working (see docstring
            # mapping table).
            "role": role,
            "harness_task_or_subagent_id": raw_subagent_id,
            "invoked_at": invocation_timestamp,
            "returned_at": returned_at,
            "parent_agent_step": parent_step_index,
            "proposal_sha256": proposal_sha256,
            "conjecture_packet_sha256": conjecture_packet_sha256,
            "invocation_mode": invocation_mode,
            "unavailable": bool(unavailable),
            # legacy aliases (pre-v0.2.2 consumers)
            "subagent_id": raw_subagent_id,
            "invocation_timestamp": invocation_timestamp,
            "proposal_timestamp": proposal_timestamp,
            "parent_step_index": parent_step_index,
        }],
        status="HYPOTHESIS",
        telemetry={
            "primitive": "proposal",
            "wall_time_seconds": 0.0,
            "verdict": None,
            "engine_version": ENGINE_VERSION,
            "agent_protocol_version": AGENT_PROTOCOL_VERSION,
            "proposal": validated,
        },
    )
    from .session import record_step  # local import: no import cycle at load
    record_step(session, step, meta={"agent_protocol": "record_proposal"})
    return step
