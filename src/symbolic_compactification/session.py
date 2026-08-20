"""Minimal JSON-based session / run persistence. No database.

On-disk layout under ``<workspace_root>/runs/<run-id>/``::

    manifest.json      run metadata + current expression record + step index
    steps/step_NNN.json   one file per recorded step (zero-padded index)
    packets/packet_NNN.json  conjecture-packet provenance records
    final/current.json    promoted current expression (text + sha256)

All payloads are produced via the kernel dataclasses' ``to_dict()`` methods,
so no sympy object is ever written to JSON (expressions are stored as str()).

``SessionState`` gains one runtime-only attribute, ``run_root`` (a str path),
set by ``init_session`` / ``load_session``. It is never serialized.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import tempfile
import time
from pathlib import Path
from typing import Optional

from .models import (AGENT_PROTOCOL_VERSION, ASSUMPTION_STATUS_VALUES,
                     ENGINE_VERSION, PACKAGE_VERSION, NONZERO,
                     PROPOSAL_EVIDENCE_KIND, PROPOSER_HARNESS_SUBAGENT,
                     PROPOSER_MAIN_AGENT, PROPOSER_MODE_UNKNOWN,
                     PROPOSER_SUBAGENT_UNAVAILABLE, PROOF_STATUS_VALUES,
                     REQUESTED_ARMS,
                     STEP_STATUSES, UNKNOWN, ZERO, AdapterError,
                     ExpressionRecord, SessionState, StepRecord,
                     engine_git_sha, sha256_text)

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _run_id() -> str:
    """Timestamp + short random hex, e.g. ``20260819T083015Z-a1b2c3``."""
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return f"{stamp}-{secrets.token_hex(3)}"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _read_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise AdapterError("RUN_MANIFEST_UNREADABLE") from None
    if not isinstance(payload, dict):
        raise AdapterError("RUN_MANIFEST_UNREADABLE")
    return payload


def _manifest_payload(session: SessionState, meta: Optional[dict]) -> dict:
    existing_meta = dict(getattr(session, "meta", {}))
    if meta:
        existing_meta.update(meta)
    session.meta = existing_meta
    return {
        "run_id": session.run_id,
        "created_at": session.created_at,
        "repository_version": getattr(
            session, "repository_version", PACKAGE_VERSION),
        "engine_version": getattr(session, "engine_version", ENGINE_VERSION),
        # proposer/state/reporting protocol in force for this run
        "agent_protocol_version": getattr(
            session, "agent_protocol_version", AGENT_PROTOCOL_VERSION),
        "engine_git_sha": (getattr(session, "engine_git_sha", None)
                           or engine_git_sha()),
        # declared A/B experiment arm; None when undeclared
        "requested_arm": getattr(session, "requested_arm", None),
        "policies": dict(getattr(session, "policies", {})),
        "meta": existing_meta,
        "current": None if session.current is None else session.current.to_dict(),
        "steps": [s.to_dict() for s in session.steps],
    }


def _normalize_requested_arm(arm) -> Optional[str]:
    """Normalize a requested-arm declaration to ``None`` / ``"A"`` / ``"B"``.

    Fail-closed: anything else raises ``REQUESTED_ARM_INVALID``. The arm is
    a DECLARATION of intent only; whether it was actually honored is derived
    strictly from recorded proposer evidence (see ``run_summary``).
    """
    if arm is None:
        return None
    if isinstance(arm, str) and arm.strip().upper() in REQUESTED_ARMS:
        return arm.strip().upper()
    raise AdapterError("REQUESTED_ARM_INVALID")


_RUN_ID_RE = re.compile(r"\d{8}T\d{6}Z-[0-9a-f]{6}\Z")


def _normalize_run_id(run_id: str) -> str:
    if not isinstance(run_id, str) or not _RUN_ID_RE.fullmatch(run_id):
        raise AdapterError("RUN_ID_INVALID")
    return run_id


def _policy_snapshot() -> dict:
    """Capture all effective policy defaults once at run initialization."""
    from .budgets import get_budget_policy
    from .parser import get_parse_policy
    from .transforms import get_transform_policy
    from .verifier import get_verify_policy
    return {
        "parse": get_parse_policy(),
        "verify": get_verify_policy(),
        "transform": get_transform_policy(),
        "budget": get_budget_policy(),
    }


def _run_root(session: SessionState) -> Path:
    root = getattr(session, "run_root", None)
    if not root:
        raise AdapterError("SESSION_NOT_PERSISTED")
    return Path(root)


# --------------------------------------------------------------------------- #
# public API
# --------------------------------------------------------------------------- #

def init_session(workspace_root: str = "workspace",
                 meta: Optional[dict] = None,
                 requested_arm: Optional[str] = None) -> SessionState:
    """Create ``<workspace_root>/runs/<run-id>/`` with manifest, steps/, final/.

    ``requested_arm`` optionally declares the A/B experiment arm
    this run is meant to execute (``"A"`` main-agent-only / ``"B"``
    harness-subagent proposer; case-insensitive; default None = undeclared).
    It is a DECLARATION of intent: whether the arm was actually honored is
    derived strictly from recorded proposer evidence by ``run_summary``
    (``ab_arm_valid`` / ``invalid_reason``). Unknown arm values fail closed
    with ``REQUESTED_ARM_INVALID``.

    Returns a ``SessionState`` carrying the runtime ``run_root`` attribute so
    subsequent ``record_step`` / ``promote`` calls know where to write.
    """
    run_id = _run_id()
    run_root = Path(workspace_root) / "runs" / run_id
    (run_root / "steps").mkdir(parents=True, exist_ok=False)
    (run_root / "final").mkdir(parents=True, exist_ok=True)

    session = SessionState(run_id=run_id)
    session.run_root = str(run_root)  # runtime-only, never serialized
    session.requested_arm = _normalize_requested_arm(requested_arm)
    session.repository_version = PACKAGE_VERSION
    session.engine_version = ENGINE_VERSION
    session.agent_protocol_version = AGENT_PROTOCOL_VERSION
    session.engine_git_sha = engine_git_sha()
    session.policies = _policy_snapshot()
    session.meta = dict(meta or {})
    _write_json(run_root / "manifest.json", _manifest_payload(session, meta))
    return session


def set_requested_arm(session: SessionState, arm: Optional[str],
                      meta: Optional[dict] = None) -> None:
    """Declare (or clear, with ``arm=None``) the run's requested A/B arm.

    Persists the declaration into the run manifest; ``run_summary`` then
    derives ``ab_arm_valid`` / ``invalid_reason`` from recorded proposer
    evidence. Unknown arm values fail closed with ``REQUESTED_ARM_INVALID``.
    """
    session.requested_arm = _normalize_requested_arm(arm)
    _write_json(_run_root(session) / "manifest.json",
                _manifest_payload(session, meta))


def load_session(workspace_root: str, run_id: str) -> SessionState:
    """Re-hydrate a ``SessionState`` from an existing run's manifest.json."""
    run_id = _normalize_run_id(run_id)
    run_root = Path(workspace_root) / "runs" / run_id
    manifest = _read_json(run_root / "manifest.json")
    if (manifest.get("run_id") != run_id
            or not isinstance(manifest.get("created_at"), str)
            or not isinstance(manifest.get("steps", []), list)):
        raise AdapterError("RUN_MANIFEST_UNREADABLE")

    current = None
    cur = manifest.get("current")
    if cur is not None:
        current = ExpressionRecord(
            text=cur["text"], sha256=cur["sha256"],
            source_path=cur.get("source_path"), parsed_expr=None,
            symbols=list(cur.get("symbols", [])),
            functions=list(cur.get("functions", [])),
        )
    session = SessionState(run_id=manifest["run_id"],
                           created_at=manifest["created_at"],
                           current=current)
    # Restore the declared A/B arm (None for older manifests).
    session.requested_arm = _normalize_requested_arm(
        manifest.get("requested_arm"))
    session.repository_version = manifest.get(
        "repository_version", manifest.get("engine_version", ENGINE_VERSION))
    session.engine_version = manifest.get("engine_version", ENGINE_VERSION)
    session.agent_protocol_version = manifest.get(
        "agent_protocol_version", AGENT_PROTOCOL_VERSION)
    session.engine_git_sha = manifest.get("engine_git_sha", "unknown")
    session.policies = dict(manifest.get("policies", {}))
    session.meta = dict(manifest.get("meta", {}))
    for st in manifest.get("steps", []):
        status = st.get("status")
        assumption_status = st.get("assumption_status")
        proof_status = st.get("proof_status")
        session.steps.append(StepRecord(
            step=st["step"], current_hash=st["current_hash"],
            candidate_hash=st["candidate_hash"],
            candidate_text=st["candidate_text"], residual=st.get("residual"),
            verdict=st["verdict"], evidence=list(st.get("evidence", [])),
            timestamp=st.get("timestamp", ""),
            status=status if status in STEP_STATUSES else None,
            telemetry=dict(st.get("telemetry", {})),
            engine_version=st.get("engine_version", ENGINE_VERSION),
            engine_git_sha=st.get("engine_git_sha", "unknown"),
            assumption_status=(assumption_status
                               if assumption_status in ASSUMPTION_STATUS_VALUES
                               else None),
            proof_status=(proof_status
                          if proof_status in PROOF_STATUS_VALUES else None),
        ))
    session.run_root = str(run_root)
    return session


def set_current(session: SessionState, record: ExpressionRecord,
                meta: Optional[dict] = None) -> None:
    """Install an initial current expression on a fresh session (ingestion)."""
    if session.current is not None or session.steps:
        raise AdapterError("CURRENT_ALREADY_SET")
    session.current = record
    _write_json(_run_root(session) / "manifest.json",
                _manifest_payload(session, meta))


def record_step(session: SessionState, step: StepRecord,
                meta: Optional[dict] = None) -> Path:
    """Persist one step: write ``steps/step_<NNN>.json`` and refresh manifest.

    The step file is exactly ``step.to_dict()`` (JSON-native). The StepRecord
    is also appended to the in-memory session. Returns the step file path.
    """
    run_root = _run_root(session)
    expected = len(session.steps) + 1
    if step.step != expected:
        raise AdapterError("STEP_SEQUENCE_INVALID")
    if session.current is not None and step.current_hash != session.current.sha256:
        raise AdapterError("CURRENT_STATE_MISMATCH")
    step_path = run_root / "steps" / f"step_{step.step:03d}.json"
    if step_path.exists():
        raise AdapterError("STEP_ALREADY_EXISTS")
    # Fill the orthogonal proof axis when a caller used the older low-level
    # StepRecord API.  Contradictory explicit values were rejected by the
    # model; these defaults make the persisted transition mechanically clear.
    if step.proof_status is None:
        if step.status == "HYPOTHESIS":
            step.proof_status = "HYPOTHESIS"
        elif step.verdict == ZERO:
            step.proof_status = "PROVEN"
        elif step.verdict == NONZERO:
            step.proof_status = "REFUTED"
        elif step.verdict == UNKNOWN:
            step.proof_status = "PROOF_REQUIRED"
    _write_json(step_path, step.to_dict())
    session.steps.append(step)
    _write_json(run_root / "manifest.json", _manifest_payload(session, meta))
    return step_path


def proposal_assumption_status(session: SessionState,
                               candidate_text: str) -> Optional[str]:
    """Return the nearest recorded proposal's assumption gate for a candidate."""
    for step in reversed(session.steps):
        if step.candidate_text != candidate_text:
            continue
        for evidence in step.evidence:
            if (isinstance(evidence, dict)
                    and evidence.get("kind") == PROPOSAL_EVIDENCE_KIND):
                status = evidence.get("assumptions_status")
                return (status if status in ASSUMPTION_STATUS_VALUES
                        else None)
    return None


def promote(session: SessionState, candidate_record: ExpressionRecord,
            meta: Optional[dict] = None) -> Path:
    """Promote a candidate to the new current expression.

    Valid ONLY when the last recorded step's verdict is ZERO; any other
    verdict (NONZERO/UNKNOWN, or no steps at all) raises
    ``AdapterError("VERDICT_NOT_ZERO")``. Writes ``final/current.json`` with
    the expression text and its sha256, updates the session and manifest.
    Returns the final file path.
    """
    if not session.steps:
        raise AdapterError("VERDICT_NOT_ZERO")
    last = session.steps[-1]
    zero_evidence = any(
        isinstance(item, dict) and item.get("kind") in {
            "exact_symbolic_zero",
            "exact_symbolic_zero_after_complex_normalization",
        }
        for item in last.evidence)
    if (last.verdict != ZERO or last.status != "CERTIFIED"
            or last.proof_status != "PROVEN" or not zero_evidence):
        raise AdapterError("VERDICT_NOT_ZERO")
    if session.current is None or last.current_hash != session.current.sha256:
        raise AdapterError("CURRENT_STATE_MISMATCH")
    if (last.candidate_hash != candidate_record.sha256
            or last.candidate_text != candidate_record.text):
        raise AdapterError("CANDIDATE_STATE_MISMATCH")
    if last.assumption_status == "HUMAN_REQUIRED":
        raise AdapterError("HUMAN_AUTHORIZATION_REQUIRED")
    if proposal_assumption_status(
            session, candidate_record.text) == "HUMAN_REQUIRED":
        raise AdapterError("HUMAN_AUTHORIZATION_REQUIRED")

    run_root = _run_root(session)
    session.current = candidate_record
    final_payload = {
        "text": candidate_record.text,
        "sha256": candidate_record.sha256,
        "sha256_of_text": sha256_text(candidate_record.text),
        "promoted_at_step": session.steps[-1].step,
        "symbols": [dict(s) for s in candidate_record.symbols],
        "functions": list(candidate_record.functions),
    }
    final_path = run_root / "final" / "current.json"
    _write_json(final_path, final_payload)
    _write_json(run_root / "manifest.json", _manifest_payload(session, meta))
    return final_path


def record_packet_provenance(session: SessionState, record: dict) -> Path:
    """Persist one minimal conjecture-packet provenance record.

    Writes ``packets/packet_<NNN>.json`` (zero-padded, monotonically
    numbered) carrying the NEUTRAL provenance fields only: the certified-state
    and structural-representation hashes, the goal, the declared assumptions,
    whether verifier feedback was included, and the withheld-attention list.
    NO chain-of-thought and NO reasoning text beyond those structured fields
    are ever written. Returns the record file path.

    Raises:
        AdapterError("SESSION_NOT_PERSISTED") if the session has no run_root.
    """
    run_root = _run_root(session)
    packets = run_root / "packets"
    packets.mkdir(parents=True, exist_ok=True)
    existing = []
    for candidate in packets.glob("packet_*.json"):
        try:
            existing.append(int(candidate.stem.split("_")[-1]))
        except ValueError:
            continue
    index = max(existing, default=0) + 1
    path = packets / f"packet_{index:03d}.json"
    if path.exists():
        raise AdapterError("PACKET_ALREADY_EXISTS")
    _write_json(path, record)
    return path


# --------------------------------------------------------------------------- #
# A/B telemetry helper: cheap run summary from existing records
# --------------------------------------------------------------------------- #

def run_summary(run_dir) -> dict:
    """Cheap A/B run summary computed from EXISTING step records.

    Reads ``<run_dir>/manifest.json`` and aggregates the step telemetry
    already recorded there — no new framework, no reconstruction from
    mtimes. Proposal steps (evidence kind ``proposer_candidate``) are kept
    separate from real verification steps.

    Returns a JSON-serializable dict:
      * ``run_id`` / ``engine_version`` / ``agent_protocol_version``
      * ``candidates_proposed``  number of recorded proposer HYPOTHESIS steps
      * ``zero_promotions``      verification steps adjudicated ZERO
      * ``nonzero_count``        verification steps adjudicated NONZERO
      * ``unknown_count``        verification steps adjudicated UNKNOWN
      * ``verifier_calls``       real verification steps (proposals excluded)
      * ``wall_time_seconds``    total recorded verifier wall time
      * ``count_ops_first``      count_ops before the FIRST verified step
      * ``count_ops_current``    count_ops after the LATEST verified step
      * ``proposer_mode``        MAIN_AGENT_ONLY | HARNESS_SUBAGENT |
                                 SUBAGENT_UNAVAILABLE | UNKNOWN, derived
                                 STRICTLY from recorded invocation evidence
                                 (never inferred from the role contract
                                 merely existing/being read)
      * ``packets_recorded``     number of conjecture-packet provenance
                                 records present under ``packets/``
      * ``requested_arm``        the declared A/B arm ("A"/"B") or None
      * ``ab_arm_valid``         bool: was the declared arm actually honored,
                                 judged STRICTLY from recorded proposer
                                 evidence (True when no arm was declared)
      * ``invalid_reason``       None when valid; otherwise a short code
                                 (e.g. ``SUBAGENT_NOT_INVOKED`` for arm B
                                 without any recorded subagent id)

    Raises:
        AdapterError("RUN_MANIFEST_UNREADABLE") if the manifest is absent
        or malformed.
    """
    run_dir = Path(run_dir)
    manifest = _read_json(run_dir / "manifest.json")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("steps"), list):
        raise AdapterError("RUN_MANIFEST_UNREADABLE")
    steps = manifest["steps"]

    def _is_proposal(st: dict) -> bool:
        return any(e.get("kind") == PROPOSAL_EVIDENCE_KIND
                   for e in st.get("evidence", [])
                   if isinstance(e, dict))

    verified = [st for st in steps if not _is_proposal(st)]
    proposals = [st for st in steps if _is_proposal(st)]

    wall = 0.0
    for st in steps:
        t = (st.get("telemetry") or {}).get("wall_time_seconds")
        if isinstance(t, (int, float)) and not isinstance(t, bool):
            wall += float(t)

    def _ops(st: dict, key: str):
        v = (st.get("telemetry") or {}).get(key)
        return v if isinstance(v, int) and not isinstance(v, bool) else None

    ops_first = next((_ops(st, "count_ops_before") for st in verified
                      if _ops(st, "count_ops_before") is not None), None)
    ops_current = next((_ops(st, "count_ops_after")
                        for st in reversed(verified)
                        if _ops(st, "count_ops_after") is not None), None)

    packets_dir = run_dir / "packets"
    packets_recorded = (
        len([p for p in packets_dir.glob("packet_*.json")])
        if packets_dir.is_dir() else 0)

    proposer_mode = _derive_proposer_mode(proposals)
    requested_arm = _normalize_requested_arm(manifest.get("requested_arm"))
    ab_arm_valid, invalid_reason = _derive_arm_valid(requested_arm,
                                                     proposer_mode)

    return {
        "run_id": manifest.get("run_id"),
        "engine_version": manifest.get("engine_version"),
        "agent_protocol_version": manifest.get("agent_protocol_version"),
        "candidates_proposed": len(proposals),
        "zero_promotions": sum(1 for st in verified
                               if st.get("verdict") == ZERO),
        "nonzero_count": sum(1 for st in verified
                             if st.get("verdict") == NONZERO),
        "unknown_count": sum(1 for st in verified
                             if st.get("verdict") == UNKNOWN),
        "verifier_calls": len(verified),
        "wall_time_seconds": wall,
        "count_ops_first": ops_first,
        "count_ops_current": ops_current,
        "proposer_mode": proposer_mode,
        "packets_recorded": packets_recorded,
        "requested_arm": requested_arm,
        "ab_arm_valid": ab_arm_valid,
        "invalid_reason": invalid_reason,
    }


def _proposal_invocation_evidence(st: dict) -> Optional[dict]:
    """Return the ``proposer_candidate`` evidence dict of a proposal step."""
    for e in st.get("evidence", []):
        if isinstance(e, dict) and e.get("kind") == PROPOSAL_EVIDENCE_KIND:
            return e
    return None


def _derive_proposer_mode(proposals: list) -> str:
    """Derive ``proposer_mode`` STRICTLY from recorded invocation evidence.

    * any proposal step carrying a recorded ``subagent_id`` -> HARNESS_SUBAGENT;
    * any explicit ``subagent_unavailable`` record (the harness cannot expose
      native subagent invocation for this run) -> SUBAGENT_UNAVAILABLE;
    * proposals recorded with explicit ``invocation_mode == "main_agent"``
      (the default for ``record_proposal`` without a subagent id) ->
      MAIN_AGENT_ONLY;
    * ambiguous or absent evidence -> UNKNOWN.

    Never infers subagent use from the role contract merely existing or being
    read: a recorded subagent id is the ONLY evidence that selects
    HARNESS_SUBAGENT. SUBAGENT_UNAVAILABLE is an EXPLICIT record, distinct
    from UNKNOWN (ambiguous/absent evidence). Runs with no proposal steps
    report UNKNOWN (no evidence either way). Precedence when evidence mixes:
    HARNESS_SUBAGENT > SUBAGENT_UNAVAILABLE > MAIN_AGENT_ONLY.
    """
    if not proposals:
        return PROPOSER_MODE_UNKNOWN

    saw_subagent = False
    saw_main_agent = False
    saw_unavailable = False
    for st in proposals:
        ev = _proposal_invocation_evidence(st)
        if ev is None:
            # a proposal marker without invocation evidence is ambiguous
            return PROPOSER_MODE_UNKNOWN
        subagent_id = ev.get("subagent_id")
        if subagent_id is not None and str(subagent_id).strip():
            saw_subagent = True
        elif ev.get("invocation_mode") == "subagent_unavailable" \
                or ev.get("unavailable") is True:
            saw_unavailable = True
        elif ev.get("invocation_mode") == "main_agent":
            saw_main_agent = True
        else:
            # evidence present but neither a subagent id nor an explicit
            # mode marker: ambiguous
            return PROPOSER_MODE_UNKNOWN

    if saw_subagent:
        return PROPOSER_HARNESS_SUBAGENT
    if saw_unavailable:
        return PROPOSER_SUBAGENT_UNAVAILABLE
    if saw_main_agent:
        return PROPOSER_MAIN_AGENT
    return PROPOSER_MODE_UNKNOWN


def _derive_arm_valid(requested_arm: Optional[str], proposer_mode: str
                      ) -> tuple:
    """Derive ``(ab_arm_valid, invalid_reason)`` from recorded evidence.

    Rules, judged STRICTLY from ``proposer_mode`` (itself derived
    only from recorded invocation evidence — never from the role contract
    existing/being read, never from an internal in-process callback):

    * no arm declared            -> valid, no reason;
    * arm "B" (subagent proposer) valid IFF proposer_mode == HARNESS_SUBAGENT
      (i.e. a harness subagent id was RECORDED); otherwise invalid with
      ``SUBAGENT_NOT_INVOKED``;
    * arm "A" (main-agent only) valid IFF there is no subagent evidence
      (MAIN_AGENT_ONLY or an explicit SUBAGENT_UNAVAILABLE — in both cases
      the main agent did the proposing); HARNESS_SUBAGENT is invalid with
      ``SUBAGENT_INVOKED``, and UNKNOWN evidence is invalid with
      ``PROPOSER_MODE_UNKNOWN`` (fail closed: absence of evidence is not
      evidence of arm A).
    """
    if requested_arm is None:
        return True, None
    if requested_arm == "B":
        if proposer_mode == PROPOSER_HARNESS_SUBAGENT:
            return True, None
        return False, "SUBAGENT_NOT_INVOKED"
    if requested_arm == "A":
        if proposer_mode in (PROPOSER_MAIN_AGENT,
                             PROPOSER_SUBAGENT_UNAVAILABLE):
            return True, None
        if proposer_mode == PROPOSER_HARNESS_SUBAGENT:
            return False, "SUBAGENT_INVOKED"
        return False, "PROPOSER_MODE_UNKNOWN"
    # a non-A/B arm cannot enter the manifest via the validated setters,
    # but a hand-edited manifest must still fail closed, not crash
    return False, "REQUESTED_ARM_UNKNOWN"
