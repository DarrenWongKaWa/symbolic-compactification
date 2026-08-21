"""Operational proposer-mode intent (skill config), distinct from A/B arms.

``requested_proposer_mode`` records the user's skill setting
(main / subagent / auto). It must not become a promotion path, and it must
not overwrite evidence-derived ``run_summary['proposer_mode']``.
"""
from __future__ import annotations

import json

import pytest

from symbolic_compactification import (
    ZERO,
    AdapterError,
    adjudicate_candidate,
    init_session,
    load_expression,
    load_session,
    run_summary,
    set_current,
)
from symbolic_compactification.cli import main as cli_main
from symbolic_compactification.session import set_requested_proposer_mode


def _run_root(tmp_path, session):
    return tmp_path / "runs" / session.run_id


def test_requested_proposer_mode_default_is_undeclared(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    assert session.requested_proposer_mode is None
    manifest = json.loads(
        (_run_root(tmp_path, session) / "manifest.json")
        .read_text(encoding="utf-8"))
    assert manifest["requested_proposer_mode"] is None
    summary = run_summary(_run_root(tmp_path, session))
    assert summary["requested_proposer_mode"] is None
    assert summary["proposer_mode"] == "UNKNOWN"


def test_requested_proposer_mode_persists_and_reloads(tmp_path):
    session = init_session(workspace_root=str(tmp_path),
                           requested_proposer_mode="SUBAGENT")
    assert session.requested_proposer_mode == "subagent"
    reloaded = load_session(str(tmp_path), session.run_id)
    assert reloaded.requested_proposer_mode == "subagent"
    summary = run_summary(_run_root(tmp_path, session))
    assert summary["requested_proposer_mode"] == "subagent"
    assert summary["proposer_mode"] == "UNKNOWN"


@pytest.mark.parametrize("value", ["main", "subagent", "auto"])
def test_requested_proposer_mode_vocabulary(tmp_path, value):
    session = init_session(workspace_root=str(tmp_path),
                           requested_proposer_mode=value)
    assert session.requested_proposer_mode == value


def test_requested_proposer_mode_rejected_when_unknown(tmp_path):
    with pytest.raises(AdapterError) as excinfo:
        init_session(workspace_root=str(tmp_path),
                     requested_proposer_mode="harness")
    assert excinfo.value.code == "PROPOSER_MODE_INVALID"


def test_set_requested_proposer_mode_clears(tmp_path):
    session = init_session(workspace_root=str(tmp_path),
                           requested_proposer_mode="auto")
    set_requested_proposer_mode(session, None)
    assert session.requested_proposer_mode is None


def test_requested_proposer_mode_does_not_gate_zero_promotion(tmp_path):
    session = init_session(workspace_root=str(tmp_path),
                           requested_proposer_mode="subagent")
    current = load_expression(
        str(_write(tmp_path, "cur.txt", "x**2 + 2*x + 1")), ["x"])
    candidate = load_expression(
        str(_write(tmp_path, "cand.txt", "(x+1)**2")), ["x"])
    set_current(session, current)
    outcome = adjudicate_candidate(session, candidate)
    assert outcome.result.verdict == ZERO
    assert outcome.promoted is True
    assert session.current.text == candidate.text


def test_cli_init_session_proposer_mode_smoke(tmp_path, capsys):
    code = cli_main([
        "init-session", "--workspace", str(tmp_path),
        "--proposer-mode", "auto", "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["requested_proposer_mode"] == "auto"
    manifest = json.loads(
        (tmp_path / "runs" / payload["run_id"] / "manifest.json")
        .read_text(encoding="utf-8"))
    assert manifest["requested_proposer_mode"] == "auto"


def test_inspect_json_includes_structure_summary(tmp_path, capsys):
    expr = _write(tmp_path, "e.txt", "Sum(f(n), (n, 1, N))")
    symbols = _write(tmp_path, "s.json",
                     '{"symbols": ["N", "n"], "functions": ["f"]}')
    code = cli_main(["inspect", str(expr), "--symbols", str(symbols), "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    summary = payload["structure_summary"]
    assert summary["sums"] == 1
    assert summary["indexed_names"] == ["f"]
    assert "count_ops" in summary
    assert payload["text"] == "Sum(f(n), (n, 1, N))"


def test_cli_summary_reads_run_records(tmp_path, capsys):
    init = cli_main(["init-session", "--workspace", str(tmp_path), "--json"])
    assert init == 0
    run_id = json.loads(capsys.readouterr().out)["run_id"]
    code = cli_main([
        "summary", "--run", run_id, "--workspace", str(tmp_path), "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["run_id"] == run_id
    assert "proposer_mode" in payload
    assert "requested_proposer_mode" in payload


def _write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path
