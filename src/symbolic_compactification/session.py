"""Minimal JSON-based session / run persistence. No database.

On-disk layout under ``<workspace_root>/runs/<run-id>/``::

    manifest.json      run metadata + current expression record + step index
    steps/step_NNN.json   one file per recorded step (zero-padded index)
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

from .models import (ENGINE_VERSION, STEP_STATUSES, ZERO, AdapterError,
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
