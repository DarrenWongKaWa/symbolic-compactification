"""Minimal JSON-based session / run persistence. No database.

On-disk layout under ``<workspace_root>/runs/<run-id>/``::

    manifest.json      run metadata + current expression record + step index
    steps/step_NNN.json   one file per recorded step (zero-padded index)
    packets/packet_NNN.json  conjecture-packet provenance records (v0.2.2)
    final/current.json    promoted current expression (text + sha256)

All payloads are produced via the kernel dataclasses' ``to_dict()`` methods,
so no sympy object is ever written to JSON (expressions are stored as str()).

``SessionState`` gains one runtime-only attribute, ``run_root`` (a str path),
set by ``init_session`` / ``load_session``. It is never serialized.
"""
from __future__ import annotations

import json
import secrets
import time
from pathlib import Path
from typing import Optional

from .models import (AGENT_PROTOCOL_VERSION, ENGINE_VERSION, NONZERO,
                     PROPOSAL_EVIDENCE_KIND, PROPOSER_HARNESS_SUBAGENT,
                     PROPOSER_MAIN_AGENT, PROPOSER_MODE_UNKNOWN,
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
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise AdapterError("RUN_MANIFEST_UNREADABLE") from None


def _manifest_payload(session: SessionState, meta: Optional[dict]) -> dict:
    return {
        "run_id": session.run_id,
        "created_at": session.created_at,
        "engine_version": ENGINE_VERSION,
        # agent-protocol version (v0.2.1): the proposer/conjecture protocol
        # in force for this run; the deterministic engine stays v0.2.0
        "agent_protocol_version": AGENT_PROTOCOL_VERSION,
        "engine_git_sha": engine_git_sha(),
        "meta": meta or {},
        "current": None if session.current is None else session.current.to_dict(),
        "steps": [s.to_dict() for s in session.steps],
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
                 meta: Optional[dict] = None) -> SessionState:
    """Create ``<workspace_root>/runs/<run-id>/`` with manifest, steps/, final/.

    Returns a ``SessionState`` carrying the runtime ``run_root`` attribute so
    subsequent ``record_step`` / ``promote`` calls know where to write.
    """
    run_id = _run_id()
    run_root = Path(workspace_root) / "runs" / run_id
    (run_root / "steps").mkdir(parents=True, exist_ok=True)
    (run_root / "final").mkdir(parents=True, exist_ok=True)

    session = SessionState(run_id=run_id)
    session.run_root = str(run_root)  # runtime-only, never serialized
    _write_json(run_root / "manifest.json", _manifest_payload(session, meta))
    return session


def load_session(workspace_root: str, run_id: str) -> SessionState:
    """Re-hydrate a ``SessionState`` from an existing run's manifest.json."""
    run_root = Path(workspace_root) / "runs" / run_id
    manifest = _read_json(run_root / "manifest.json")

    current = None
    cur = manifest.get("current")
    if cur is not None:
        current = ExpressionRecord(
            text=cur["text"], sha256=cur["sha256"],
            source_path=cur.get("source_path"), parsed_expr=None,
            symbols=list(cur.get("symbols", [])),
        )
    session = SessionState(run_id=manifest["run_id"],
                           created_at=manifest["created_at"],
                           current=current)
    for st in manifest.get("steps", []):
        status = st.get("status")
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
        ))
    session.run_root = str(run_root)
    return session


def set_current(session: SessionState, record: ExpressionRecord,
                meta: Optional[dict] = None) -> None:
    """Install an initial current expression on a fresh session (ingestion)."""
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
    step_path = run_root / "steps" / f"step_{step.step:03d}.json"
    _write_json(step_path, step.to_dict())
    session.steps.append(step)
    _write_json(run_root / "manifest.json", _manifest_payload(session, meta))
    return step_path


def promote(session: SessionState, candidate_record: ExpressionRecord,
            meta: Optional[dict] = None) -> Path:
    """Promote a candidate to the new current expression.

    Valid ONLY when the last recorded step's verdict is ZERO; any other
    verdict (NONZERO/UNKNOWN, or no steps at all) raises
    ``AdapterError("VERDICT_NOT_ZERO")``. Writes ``final/current.json`` with
    the expression text and its sha256, updates the session and manifest.
    Returns the final file path.
    """
    if not session.steps or session.steps[-1].verdict != ZERO:
        raise AdapterError("VERDICT_NOT_ZERO")

    run_root = _run_root(session)
    session.current = candidate_record
    final_payload = {
        "text": candidate_record.text,
        "sha256": candidate_record.sha256,
        "sha256_of_text": sha256_text(candidate_record.text),
        "promoted_at_step": session.steps[-1].step,
        "symbols": [dict(s) for s in candidate_record.symbols],
    }
    final_path = run_root / "final" / "current.json"
    _write_json(final_path, final_payload)
    _write_json(run_root / "manifest.json", _manifest_payload(session, meta))
    return final_path


def record_packet_provenance(session: SessionState, record: dict) -> Path:
    """Persist one minimal conjecture-packet provenance record (v0.2.2).

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
    index = len(session.steps) + 1
    path = packets / f"packet_{index:03d}.json"
    _write_json(path, record)
    return path


# --------------------------------------------------------------------------- #
# A/B telemetry helper (v0.2.1): cheap run summary from existing records
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
      * ``proposer_mode``        MAIN_AGENT_ONLY | HARNESS_SUBAGENT | UNKNOWN,
                                 derived STRICTLY from recorded invocation
                                 evidence (never inferred from the role
                                 contract merely existing/being read)
      * ``packets_recorded``     number of conjecture-packet provenance
                                 records present under ``packets/``

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
        "proposer_mode": _derive_proposer_mode(proposals),
        "packets_recorded": packets_recorded,
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
    * proposals recorded with explicit ``invocation_mode == "main_agent"``
      (the default for ``record_proposal`` without a subagent id) ->
      MAIN_AGENT_ONLY;
    * ambiguous or absent evidence -> UNKNOWN.

    Never infers subagent use from the role contract merely existing or being
    read: a recorded subagent id is the ONLY evidence that selects
    HARNESS_SUBAGENT. Runs with no proposal steps report UNKNOWN (no evidence
    either way).
    """
    if not proposals:
        return PROPOSER_MODE_UNKNOWN

    saw_subagent = False
    saw_main_agent = False
    for st in proposals:
        ev = _proposal_invocation_evidence(st)
        if ev is None:
            # a proposal marker without invocation evidence is ambiguous
            return PROPOSER_MODE_UNKNOWN
        subagent_id = ev.get("subagent_id")
        if subagent_id is not None and str(subagent_id).strip():
            saw_subagent = True
        elif ev.get("invocation_mode") == "main_agent":
            saw_main_agent = True
        else:
            # evidence present but neither a subagent id nor an explicit
            # main_agent mode marker: ambiguous
            return PROPOSER_MODE_UNKNOWN

    if saw_subagent:
        return PROPOSER_HARNESS_SUBAGENT
    if saw_main_agent:
        return PROPOSER_MAIN_AGENT
    return PROPOSER_MODE_UNKNOWN
