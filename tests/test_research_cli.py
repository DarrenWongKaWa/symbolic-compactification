"""Focused CLI tests for the external researcher workflow."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import symbolic_compactification.cli as cli


def _source_snapshot(root: Path) -> dict[str, tuple[bytes, int, int]]:
    return {
        path.relative_to(root).as_posix(): (
            path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode)
        for path in root.rglob("*")
        if path.is_file() and "runs" not in path.relative_to(root).parts
    }


def _initialize(tmp_path: Path, capsys, name: str = "workspace") -> Path:
    root = tmp_path / name
    assert cli.main(["init", str(root), "--json"]) == cli.EXIT_ZERO
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "WORKSPACE_INITIALIZED"
    assert payload["workspace"] == str(root.resolve())
    return root


def _set_candidate(root: Path, expression: str) -> None:
    (root / "expressions/candidate.txt").write_text(
        expression, encoding="utf-8")


def test_init_creates_minimal_workspace_and_never_overwrites(
        tmp_path, capsys):
    root = _initialize(tmp_path, capsys)
    assert (root / "project.yaml").is_file()
    assert (root / "expressions/current.txt").is_file()
    assert (root / "hypotheses/hypothesis.json").is_file()
    before = _source_snapshot(root)

    assert cli.main(["init", str(root)]) == cli.EXIT_ERROR
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.splitlines() == ["error: WORKSPACE_ALREADY_EXISTS"]
    assert "Traceback" not in captured.err
    assert _source_snapshot(root) == before


def test_workspace_inspect_reports_project_assumptions_and_structure_read_only(
        tmp_path, capsys):
    root = _initialize(tmp_path, capsys)
    before = _source_snapshot(root)

    assert cli.main(["inspect", str(root), "--json"]) == cli.EXIT_ZERO

    payload = json.loads(capsys.readouterr().out)
    assert payload["project"]["project_name"] == "workspace"
    assert payload["assumptions"]["symbols"][0]["name"] == "x"
    assert payload["hypothesis"]["hypothesis_type"] == "equivalence"
    assert len(payload["expressions"]) == 2
    current = next(item for item in payload["expressions"]
                   if item["entrypoint"])
    assert current["path"] == "expressions/current.txt"
    assert current["text"] == "x**2 + 2*x + 1"
    assert current["parsed_expression"]
    assert current["structure_summary"]["count_ops"] == current["count_ops"]
    assert len(current["sha256"]) == 64
    assert _source_snapshot(root) == before


@pytest.mark.parametrize(
    ("candidate", "expected_result", "expected_exit"),
    [
        ("(x + 1)**2\n", "ZERO", cli.EXIT_ZERO),
        ("x**2 + 2*x + 2\n", "NONZERO", cli.EXIT_NONZERO),
    ],
)
def test_workspace_verify_maps_exact_statuses_and_preserves_sources(
        tmp_path, capsys, candidate, expected_result, expected_exit):
    root = _initialize(tmp_path, capsys, expected_result.lower())
    _set_candidate(root, candidate)
    before = _source_snapshot(root)

    assert cli.main(["verify", str(root), "--json"]) == expected_exit

    payload = json.loads(capsys.readouterr().out)
    assert payload["result"] == expected_result
    assert payload["obligations"][0]["verdict"] == expected_result
    assert Path(payload["provenance_path"]).is_file()
    assert Path(payload["report_path"]).is_file()
    assert _source_snapshot(root) == before


def test_workspace_verify_unknown_is_first_class_not_success(tmp_path, capsys):
    root = _initialize(tmp_path, capsys)
    (root / "assumptions/assumptions.yaml").write_text(
        "symbols:\n"
        "  - name: x\n"
        "    real: true\n"
        "    nonzero: false\n"
        "functions:\n"
        "  - f\n"
        "  - g\n",
        encoding="utf-8",
    )
    (root / "expressions/current.txt").write_text(
        "f(x)\n", encoding="utf-8")
    _set_candidate(root, "g(x)\n")
    before = _source_snapshot(root)

    assert cli.main(["verify", str(root), "--json"]) == cli.EXIT_UNKNOWN

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["result"] == "UNKNOWN"
    assert payload["obligations"][0]["verdict"] == "UNKNOWN"
    assert "success" not in output.lower()
    assert _source_snapshot(root) == before


@pytest.mark.parametrize(
    ("mutation", "expected_result", "expected_code"),
    [
        ("parse", "PARSE_FAILURE", "EXPRESSION_PARSE_FAILURE"),
        ("compile", "COMPILE_FAILURE", "UNSUPPORTED_HYPOTHESIS_TYPE"),
        ("assumption", "ASSUMPTION_REQUIRED",
         "DECLARED_ASSUMPTIONS_OMITTED"),
    ],
)
def test_workspace_verify_maps_parse_and_compile_failures_to_exit_four(
        tmp_path, capsys, mutation, expected_result, expected_code):
    root = _initialize(tmp_path, capsys, mutation)
    if mutation == "parse":
        _set_candidate(root, "x + undeclared_name\n")
    else:
        path = root / "hypotheses/hypothesis.json"
        hypothesis = json.loads(path.read_text(encoding="utf-8"))
        if mutation == "compile":
            hypothesis["hypothesis_type"] = "recurrence"
        else:
            hypothesis["assumptions_used"] = []
        path.write_text(json.dumps(hypothesis), encoding="utf-8")
    before = _source_snapshot(root)

    assert cli.main(["verify", str(root), "--json"]) == cli.EXIT_ERROR

    payload = json.loads(capsys.readouterr().out)
    assert payload["result"] == expected_result
    assert payload["error_code"] == expected_code
    assert payload["error_source"]
    assert payload["action_hint"]
    assert Path(payload["provenance_path"]).is_file()
    assert _source_snapshot(root) == before


def test_workspace_parse_and_compile_hints_are_safe_specific_and_stable(
        tmp_path, capsys):
    parse_root = _initialize(tmp_path, capsys, "safe-parse")
    _set_candidate(parse_root, "x + undeclared_name\n")

    assert cli.main(["inspect", str(parse_root)]) == cli.EXIT_ERROR
    parse_error = capsys.readouterr().err
    assert "error: EXPRESSION_PARSE_FAILURE" in parse_error
    assert "source: expressions/candidate.txt" in parse_error
    assert "hint:" in parse_error
    assert "undeclared_name" not in parse_error

    compile_root = _initialize(tmp_path, capsys, "safe-compile")
    hypothesis_path = compile_root / "hypotheses/hypothesis.json"
    hypothesis = json.loads(hypothesis_path.read_text(encoding="utf-8"))
    hypothesis["proof_obligations"][0]["relation"] = "secret-relation-value"
    hypothesis_path.write_text(json.dumps(hypothesis), encoding="utf-8")

    assert cli.main(["verify", str(compile_root)]) == cli.EXIT_ERROR
    compile_error = capsys.readouterr().out
    assert "error_code:  UNSUPPORTED_RELATION" in compile_error
    assert ("source:      hypotheses/hypothesis.json#/proof_obligations/0/relation"
            in compile_error)
    assert "hint:" in compile_error
    assert "secret-relation-value" not in compile_error


def test_cli_version_distinguishes_release_engine_and_protocol(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--version"])

    assert excinfo.value.code == 0
    output = " ".join(capsys.readouterr().out.split())
    assert "0.3.0-alpha" in output
    assert "PEP 440 0.3.0a0" in output
    assert "engine 0.3.0" in output
    assert "protocol 0.3.0" in output


def test_report_uses_explicit_or_latest_safe_research_run(tmp_path, capsys):
    root = _initialize(tmp_path, capsys)
    assert cli.main(["verify", str(root), "--json"]) == cli.EXIT_ZERO
    first_run_id = json.loads(capsys.readouterr().out)["run_id"]
    _set_candidate(root, "x**2 + 2*x + 2\n")
    assert cli.main(["verify", str(root), "--json"]) == cli.EXIT_NONZERO
    run_id = json.loads(capsys.readouterr().out)["run_id"]

    assert cli.main(["report", str(root), "--json"]) == cli.EXIT_ZERO
    latest = json.loads(capsys.readouterr().out)
    assert latest["run_id"] == run_id
    assert latest["run_id"] != first_run_id
    assert latest["result"] == "NONZERO"
    assert "Git commit" in latest["text"]

    assert cli.main([
        "report", str(root), "--run", run_id, "--json",
    ]) == cli.EXIT_ZERO
    explicit = json.loads(capsys.readouterr().out)
    assert explicit == latest


def test_report_skips_symlink_run_and_fails_concisely_when_no_real_run(
        tmp_path, capsys):
    root = _initialize(tmp_path, capsys)
    outside = tmp_path / "outside-run"
    outside.mkdir()
    (root / "runs" / "fake-run").symlink_to(outside, target_is_directory=True)

    assert cli.main(["report", str(root)]) == cli.EXIT_ERROR

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.splitlines() == ["error: NO_RECORDED_RUNS"]
    assert "Traceback" not in captured.err


def test_legacy_file_inspect_and_verify_remain_compatible(tmp_path, capsys):
    current = tmp_path / "current.txt"
    candidate = tmp_path / "candidate.txt"
    symbols = tmp_path / "symbols.json"
    current.write_text("x**2 + 2*x + 1\n", encoding="utf-8")
    candidate.write_text("(x + 1)**2\n", encoding="utf-8")
    symbols.write_text('{"symbols":["x"]}\n', encoding="utf-8")

    assert cli.main([
        "inspect", str(current), "--symbols", str(symbols), "--json",
    ]) == cli.EXIT_ZERO
    inspection = json.loads(capsys.readouterr().out)
    assert inspection["text"] == "x**2 + 2*x + 1"

    assert cli.main([
        "verify", "--current", str(current), "--candidate", str(candidate),
        "--symbols", str(symbols), "--json",
    ]) == cli.EXIT_ZERO
    verification = json.loads(capsys.readouterr().out)
    assert verification["result"]["verdict"] == "ZERO"


def test_mixed_verify_modes_fail_with_stable_code_only(tmp_path, capsys):
    root = _initialize(tmp_path, capsys)

    assert cli.main([
        "verify", str(root), "--current", "current.txt",
    ]) == cli.EXIT_ERROR

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.splitlines() == ["error: VERIFY_MODES_MIXED"]
    assert "Traceback" not in captured.err


def test_unexpected_default_error_has_no_traceback_or_exception_text(
        tmp_path, capsys, monkeypatch):
    secret = "sk-this-must-not-leak-123456789"

    def explode(_path):
        raise RuntimeError(secret)

    monkeypatch.setattr(cli, "initialize_workspace", explode)
    assert cli.main(["init", str(tmp_path / "workspace")]) == cli.EXIT_ERROR

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.splitlines() == ["error: INTERNAL_ERROR"]
    assert "Traceback" not in captured.err
    assert secret not in captured.err


def test_debug_may_reraise_for_developer_diagnostics(
        tmp_path, monkeypatch):
    def explode(_path):
        raise RuntimeError("developer diagnostic")

    monkeypatch.setattr(cli, "initialize_workspace", explode)
    with pytest.raises(RuntimeError, match="developer diagnostic"):
        cli.main(["init", str(tmp_path / "workspace"), "--debug"])
