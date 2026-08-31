"""Fast release gate for the external fail-closed researcher workflow."""
from __future__ import annotations

import hashlib
import json
from importlib import metadata
from pathlib import Path

import pytest

import symbolic_compactification.cli as cli
from symbolic_compactification import (
    ASSUMPTION_REQUIRED,
    COMPILE_FAILURE,
    NONZERO,
    PARSE_FAILURE,
    AGENT_PROTOCOL_VERSION,
    ENGINE_VERSION,
    PACKAGE_VERSION,
    RELEASE_VERSION,
    UNKNOWN,
    ZERO,
    build_run_record,
    generate_report,
    initialize_workspace,
    load_workspace,
    sha256_file,
    verify_hypothesis,
)

pytestmark = pytest.mark.release_critical


def test_release_identity_keeps_engine_and_protocol_semantics_separate():
    assert RELEASE_VERSION == "0.1.0-alpha"
    assert PACKAGE_VERSION == metadata.version(
        "symbolic-compactification") == "0.1.0a0"
    assert ENGINE_VERSION == AGENT_PROTOCOL_VERSION == "0.3.0"


def _source_snapshot(root: Path) -> dict[str, tuple[bytes, int, int]]:
    """Capture researcher-owned files while excluding generated runs."""
    return {
        path.relative_to(root).as_posix(): (
            path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode)
        for path in root.rglob("*")
        if path.is_file() and "runs" not in path.relative_to(root).parts
    }


def _set_candidate(root: Path, expression: str) -> None:
    (root / "expressions/candidate.txt").write_text(
        expression, encoding="utf-8")


def _set_unknown_pair(root: Path) -> None:
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


def _artifact_blob(root: Path) -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((root / "runs").rglob("*"))
        if path.is_file()
    )


def test_workspace_init_clean_parse_and_cli_inspect_smoke(tmp_path, capsys):
    root = tmp_path / "workspace"

    assert cli.main(["init", str(root), "--json"]) == cli.EXIT_ZERO
    initialized = json.loads(capsys.readouterr().out)
    assert initialized["status"] == "WORKSPACE_INITIALIZED"

    before = _source_snapshot(root)
    loaded = load_workspace(root)
    assert loaded.current_expression.text == "x**2 + 2*x + 1"
    assert cli.main(["inspect", str(root), "--json"]) == cli.EXIT_ZERO
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["project"]["project_name"] == "workspace"
    assert len(inspected["expressions"]) == 2
    assert _source_snapshot(root) == before


@pytest.mark.parametrize(
    ("case", "expected", "exit_code"),
    [
        ("zero", ZERO, cli.EXIT_ZERO),
        ("nonzero", NONZERO, cli.EXIT_NONZERO),
        ("unknown", UNKNOWN, cli.EXIT_UNKNOWN),
    ],
)
def test_cli_exact_verdicts_are_distinct_and_sources_are_immutable(
        tmp_path, capsys, case, expected, exit_code):
    root = tmp_path / case
    initialize_workspace(root)
    if case == "nonzero":
        _set_candidate(root, "x**2 + 2*x + 2\n")
    elif case == "unknown":
        _set_unknown_pair(root)
    before = _source_snapshot(root)

    assert cli.main(["verify", str(root), "--json"]) == exit_code

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["result"] == expected
    assert payload["obligations"][0]["verdict"] == expected
    if expected == UNKNOWN:
        assert "success" not in output.lower()
        report = Path(payload["report_path"]).read_text(encoding="utf-8")
        assert "does not permit scientific promotion" in report
        assert "success" not in report.lower()
    assert _source_snapshot(root) == before


@pytest.mark.parametrize(
    ("case", "expected", "error_code"),
    [
        ("parse", PARSE_FAILURE, "EXPRESSION_PARSE_FAILURE"),
        ("compile", COMPILE_FAILURE, "UNSUPPORTED_HYPOTHESIS_TYPE"),
        ("assumption", ASSUMPTION_REQUIRED,
         "DECLARED_ASSUMPTIONS_OMITTED"),
    ],
)
def test_parse_compile_and_assumption_gates_never_verify_or_promote(
        tmp_path, case, expected, error_code):
    root = tmp_path / case
    initialize_workspace(root)
    hypothesis_path = root / "hypotheses/hypothesis.json"
    if case == "parse":
        _set_candidate(root, "x + undeclared_name\n")
    else:
        hypothesis = json.loads(hypothesis_path.read_text(encoding="utf-8"))
        if case == "compile":
            hypothesis["hypothesis_type"] = "unsupported_master_object"
        else:
            hypothesis.pop("assumptions_used")
        hypothesis_path.write_text(json.dumps(hypothesis), encoding="utf-8")
    before = _source_snapshot(root)

    result = verify_hypothesis(root, run_id=f"{case}-gate")

    assert result.result == expected
    assert result.error_code == error_code
    assert result.error_source
    assert result.action_hint
    assert result.obligations == ()
    assert json.loads(result.provenance_path.read_text(
        encoding="utf-8"))["result"] == expected
    report = result.report_path.read_text(encoding="utf-8")
    assert f"Result: **{expected}**" in report
    assert "no scientific relation was checked" in report.lower()
    assert _source_snapshot(root) == before


def test_provenance_hashes_are_exact_deterministic_and_bounded(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    before = _source_snapshot(root)

    result = verify_hypothesis(
        root,
        run_id="deterministic-provenance",
        timestamp="2026-08-31T01:02:03Z",
    )
    provenance = json.loads(result.provenance_path.read_text(encoding="utf-8"))
    candidate = root / "expressions/candidate.txt"
    assert provenance["expression_hashes"]["expressions/candidate.txt"] == (
        sha256_file(candidate)
    )
    assert provenance["hypothesis_hash"] == hashlib.sha256(
        (root / "hypotheses/hypothesis.json").read_bytes()).hexdigest()
    assert set(provenance["dependency_versions"]) == {"pyyaml", "sympy"}

    digest = hashlib.sha256(b"fixed input").hexdigest()
    kwargs = {
        "input_hashes": {"project.yaml": digest},
        "expression_hashes": {"expressions/current.txt": digest},
        "hypothesis_hash": digest,
        "assumptions_hash": digest,
        "verifier_route": "python_sympy_exact_v1",
        "result": UNKNOWN,
        "runtime_seconds": 0.125,
        "warnings": ["bounded warning"],
        "run_id": "fixed-run",
        "timestamp": "2026-08-31T01:02:03Z",
        "git_commit": "a" * 40,
        "installed_dependencies": {"sympy": "1.14.0"},
    }
    assert build_run_record(**kwargs) == build_run_record(**kwargs)
    assert _source_snapshot(root) == before


def test_parse_failure_artifacts_redact_secret_like_input(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    secret = "sk-proj-synthetic01234567890123456789"
    _set_candidate(root, f"x + {secret}\n")

    result = verify_hypothesis(root, run_id="redaction-gate")

    assert result.result == PARSE_FAILURE
    assert secret not in _artifact_blob(root)


def test_report_generation_uses_persisted_run_and_not_source_mutation(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    before = _source_snapshot(root)
    result = verify_hypothesis(root, run_id="report-gate")
    result.report_path.unlink()

    report = generate_report(root, result.run_id)

    assert report.result == ZERO
    assert report.path.is_file()
    assert "Result: **ZERO**" in report.text
    assert "Git commit" in report.text
    assert "Workspace and grounded hypothesis" in report.text
    assert "Declared symbols" in report.text
    assert "Dependency versions" in report.text
    assert "Expression members" in report.text
    assert "Generated artifact inventory" in report.text
    assert _source_snapshot(root) == before


def test_finite_laurent_coefficients_without_remainder_never_certify():
    """Permanent historical safety boundary; no new evaluator behavior."""
    from research.coefficient_laurent.schema import (
        LEVEL_B,
        UNKNOWN as HOP_UNKNOWN,
        compose_hop_verdict,
    )

    verdict, level = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=ZERO,
        constant_verdict=ZERO,
        remainder_verdict=HOP_UNKNOWN,
    )

    assert verdict == HOP_UNKNOWN
    assert verdict != ZERO
    assert level == LEVEL_B
