"""Session persistence regression tests against the documented run contract.

Contract under test:
* ``init_session`` creates ``<workspace_root>/runs/<run-id>/`` containing
  ``manifest.json`` plus ``steps/`` and ``final/`` directories.
* ``record_step`` writes ``steps/step_NNN.json`` carrying the step number,
  both content hashes, the candidate, the residual, the verdict, the
  evidence list and a timestamp.
* ``promote`` is valid ONLY after a ZERO verdict; promoting on a NONZERO or
  UNKNOWN last verdict (or with no steps) raises.

Scientifically neutral: only generic symbols (x) and standard operations.
"""
from __future__ import annotations

import json
import re

import pytest

from symbolic_compactification import (
    NONZERO,
    UNKNOWN,
    ZERO,
    AdapterError,
    ExpressionRecord,
    StepRecord,
    normalize_symbols,
    sha256_text,
    verify_equivalent,
)
from symbolic_compactification.session import (
    init_session,
    load_session,
    promote,
    record_step,
    set_current,
)

HEX64 = re.compile(r"^[0-9a-f]{64}$")

ADVERSARIAL_UNKNOWN_CANDIDATE = (
    "(x - 1)*(x - Rational(1,2))*(x + 1)"
    "*(x + 2)*(x - 2)*(x + Rational(1,2))")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _record(text: str) -> ExpressionRecord:
    return ExpressionRecord(
        text=text,
        sha256=sha256_text(text),
        source_path=None,
        parsed_expr=None,
        symbols=normalize_symbols(["x"]),
    )


def _step(number: int, current_rec: ExpressionRecord,
          candidate_rec: ExpressionRecord, result) -> StepRecord:
    return StepRecord(
        step=number,
        current_hash=current_rec.sha256,
        candidate_hash=candidate_rec.sha256,
        candidate_text=candidate_rec.text,
        residual=result.residual,
        verdict=result.verdict,
        evidence=list(result.evidence),
    )


def _run_root(tmp_path, session):
    return tmp_path / "runs" / session.run_id


# --------------------------------------------------------------------------- #
# init_session: on-disk layout
# --------------------------------------------------------------------------- #

def test_init_session_creates_run_layout(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    run_root = _run_root(tmp_path, session)
    assert (run_root / "manifest.json").is_file()
    assert (run_root / "steps").is_dir()
    assert (run_root / "final").is_dir()

    manifest = json.loads((run_root / "manifest.json").read_text("utf-8"))
    assert manifest["run_id"] == session.run_id
    assert manifest["current"] is None
    assert manifest["steps"] == []
    assert manifest["created_at"]  # non-empty timestamp


# --------------------------------------------------------------------------- #
# record_step: step files and manifest refresh
# --------------------------------------------------------------------------- #

def test_record_step_writes_step_files(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    run_root = _run_root(tmp_path, session)
    current_rec = _record("x**2 + 2*x + 1")
    set_current(session, current_rec)

    # step 1: exact identity -> ZERO
    candidate_rec = _record("(x+1)**2")
    result = verify_equivalent(current_rec.text, candidate_rec.text, ["x"])
    assert result.verdict == ZERO
    path = record_step(session, _step(1, current_rec, candidate_rec, result))

    assert path == run_root / "steps" / "step_001.json"
    data = json.loads(path.read_text("utf-8"))
    assert data["step"] == 1
    assert data["current_hash"] == current_rec.sha256
    assert data["candidate_hash"] == candidate_rec.sha256
    assert HEX64.match(data["current_hash"])
    assert HEX64.match(data["candidate_hash"])
    assert data["candidate_text"] == "(x+1)**2"
    assert data["residual"] == result.residual
    assert data["verdict"] == ZERO
    assert data["evidence"] == result.evidence
    assert isinstance(data["timestamp"], str) and data["timestamp"]

    # step 2: refuted candidate -> NONZERO, zero-padded filename continues
    refuted_rec = _record("x**2 + 1")
    result2 = verify_equivalent(current_rec.text, refuted_rec.text, ["x"])
    path2 = record_step(session, _step(2, current_rec, refuted_rec, result2))
    assert path2 == run_root / "steps" / "step_002.json"
    data2 = json.loads(path2.read_text("utf-8"))
    assert data2["step"] == 2
    assert data2["verdict"] == result2.verdict

    # manifest carries the growing step index
    manifest = json.loads((run_root / "manifest.json").read_text("utf-8"))
    assert [s["step"] for s in manifest["steps"]] == [1, 2]
    assert manifest["current"]["text"] == current_rec.text


# --------------------------------------------------------------------------- #
# promote: ZERO-only gate
# --------------------------------------------------------------------------- #

def test_promote_without_steps_raises(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    with pytest.raises(AdapterError) as excinfo:
        promote(session, _record("(x+1)**2"))
    assert excinfo.value.code == "VERDICT_NOT_ZERO"


def test_promote_on_nonzero_verdict_raises(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    current_rec = _record("x")
    candidate_rec = _record("x + 1")
    result = verify_equivalent(current_rec.text, candidate_rec.text, ["x"])
    assert result.verdict == NONZERO
    record_step(session, _step(1, current_rec, candidate_rec, result))

    with pytest.raises(AdapterError) as excinfo:
        promote(session, candidate_rec)
    assert excinfo.value.code == "VERDICT_NOT_ZERO"
    assert list((_run_root(tmp_path, session) / "final").iterdir()) == []


def test_promote_on_unknown_verdict_raises(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    current_rec = _record("0")
    candidate_rec = _record(ADVERSARIAL_UNKNOWN_CANDIDATE)
    result = verify_equivalent(current_rec.text, candidate_rec.text, ["x"])
    assert result.verdict == UNKNOWN
    record_step(session, _step(1, current_rec, candidate_rec, result))

    with pytest.raises(AdapterError) as excinfo:
        promote(session, candidate_rec)
    assert excinfo.value.code == "VERDICT_NOT_ZERO"


def test_promote_after_zero_writes_final(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    run_root = _run_root(tmp_path, session)
    current_rec = _record("x**2 + 2*x + 1")
    set_current(session, current_rec)
    candidate_rec = _record("(x+1)**2")
    result = verify_equivalent(current_rec.text, candidate_rec.text, ["x"])
    assert result.verdict == ZERO
    record_step(session, _step(1, current_rec, candidate_rec, result))

    final_path = promote(session, candidate_rec)
    assert final_path == run_root / "final" / "current.json"
    payload = json.loads(final_path.read_text("utf-8"))
    assert payload["text"] == "(x+1)**2"
    assert payload["sha256"] == candidate_rec.sha256
    assert session.current.text == "(x+1)**2"

    manifest = json.loads((run_root / "manifest.json").read_text("utf-8"))
    assert manifest["current"]["text"] == "(x+1)**2"


# --------------------------------------------------------------------------- #
# load_session: manifest round-trip
# --------------------------------------------------------------------------- #

def test_load_session_round_trip(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    current_rec = _record("x**2 + 2*x + 1")
    set_current(session, current_rec)
    candidate_rec = _record("(x+1)**2")
    result = verify_equivalent(current_rec.text, candidate_rec.text, ["x"])
    record_step(session, _step(1, current_rec, candidate_rec, result))

    rehydrated = load_session(str(tmp_path), session.run_id)
    assert rehydrated.run_id == session.run_id
    assert rehydrated.current is not None
    assert rehydrated.current.text == current_rec.text
    assert len(rehydrated.steps) == 1
    assert rehydrated.steps[0].verdict == ZERO
    assert rehydrated.steps[0].candidate_text == "(x+1)**2"
