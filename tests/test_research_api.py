"""Focused release tests for the stable researcher Python API."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from symbolic_compactification import (
    ASSUMPTION_REQUIRED,
    COMPILE_FAILURE,
    NONZERO,
    PARSE_FAILURE,
    UNKNOWN,
    ZERO,
    HypothesisVerificationResult,
    generate_report,
    initialize_workspace,
    load_workspace,
    verify_hypothesis,
)


def _source_snapshot(root: Path) -> dict[str, tuple[bytes, int, int]]:
    return {
        path.relative_to(root).as_posix(): (
            path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode)
        for path in root.rglob("*")
        if path.is_file() and "runs" not in path.relative_to(root).parts
    }


def _read_run(root: Path, result: HypothesisVerificationResult):
    provenance = json.loads(result.provenance_path.read_text(encoding="utf-8"))
    details = json.loads(result.result_path.read_text(encoding="utf-8"))
    report = result.report_path.read_text(encoding="utf-8")
    assert result.run_directory.parent == root / "runs"
    assert result.run_directory == root / "runs" / result.run_id
    assert provenance["run_id"] == details["run_id"] == result.run_id
    assert provenance["result"] == details["result"] == result.result
    return provenance, details, report


def _set_candidate(root: Path, text: str) -> None:
    (root / "expressions/candidate.txt").write_text(text, encoding="utf-8")


def test_zero_api_persists_provenance_result_and_report_without_source_mutation(
        tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    before = _source_snapshot(root)

    result = verify_hypothesis(root, run_id="zero-run",
                               timestamp="2026-08-31T01:02:03Z")

    assert result.result == result.verdict == ZERO
    assert len(result.obligations) == 1
    assert result.obligations[0].verdict == ZERO
    provenance, details, report = _read_run(root, result)
    assert provenance["expression_hashes"] == {
        "expressions/candidate.txt": hashlib.sha256(
            (root / "expressions/candidate.txt").read_bytes()).hexdigest(),
        "expressions/current.txt": hashlib.sha256(
            (root / "expressions/current.txt").read_bytes()).hexdigest(),
    }
    assert details["schema_version"] == "ResearchHypothesisVerificationV1"
    assert "Result: **ZERO**" in report
    assert "exactly certified" in report
    assert _source_snapshot(root) == before


def test_nonzero_api_records_exact_counterexample(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    _set_candidate(root, "x**2 + 2*x + 2\n")

    result = verify_hypothesis(root, run_id="nonzero-run")

    assert result.result == NONZERO
    exact = result.obligations[0].result
    assert exact.counterexample is not None
    _, details, report = _read_run(root, result)
    assert details["obligations"][0]["verification"]["counterexample"]
    assert "Result: **NONZERO**" in report
    assert "Exact counterexample" in report


def test_unknown_is_first_class_and_never_promoted_to_success(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    (root / "assumptions/assumptions.yaml").write_text(
        "symbols:\n  - name: x\n    real: true\n    nonzero: false\n"
        "functions:\n  - f\n  - g\n",
        encoding="utf-8",
    )
    (root / "expressions/current.txt").write_text("f(x)\n", encoding="utf-8")
    _set_candidate(root, "g(x)\n")

    result = verify_hypothesis(root, run_id="unknown-run")

    assert result.result == UNKNOWN
    assert result.obligations[0].verdict == UNKNOWN
    provenance, _, report = _read_run(root, result)
    assert provenance["result"] == UNKNOWN
    assert "does not permit scientific promotion" in report
    assert "success" not in report.lower()


def test_unsupported_hypothesis_and_relation_are_compile_failures(tmp_path):
    first = tmp_path / "unsupported-type"
    initialize_workspace(first)
    hypothesis_path = first / "hypotheses/hypothesis.json"
    hypothesis = json.loads(hypothesis_path.read_text(encoding="utf-8"))
    hypothesis["hypothesis_type"] = "recurrence"
    hypothesis_path.write_text(json.dumps(hypothesis), encoding="utf-8")

    unsupported_type = verify_hypothesis(first, run_id="compile-type")
    assert unsupported_type.result == COMPILE_FAILURE
    assert unsupported_type.error_code == "UNSUPPORTED_HYPOTHESIS_TYPE"
    provenance, details, report = _read_run(first, unsupported_type)
    assert provenance["result"] == COMPILE_FAILURE
    assert details["obligations"] == []
    assert "no scientific relation was checked" in report

    second = tmp_path / "unsupported-relation"
    initialize_workspace(second)
    hypothesis_path = second / "hypotheses/hypothesis.json"
    hypothesis = json.loads(hypothesis_path.read_text(encoding="utf-8"))
    hypothesis["proof_obligations"][0]["relation"] = "approximately_equal"
    hypothesis_path.write_text(json.dumps(hypothesis), encoding="utf-8")

    unsupported_relation = verify_hypothesis(second, run_id="compile-relation")
    assert unsupported_relation.result == COMPILE_FAILURE
    assert unsupported_relation.error_code == "UNSUPPORTED_RELATION"
    _read_run(second, unsupported_relation)


def test_parse_failure_is_persisted_without_raw_failure_content(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    secret = "sk-thismustnotberecorded123456789"
    _set_candidate(root, f"x + {secret}\n")
    before = _source_snapshot(root)

    result = verify_hypothesis(root, run_id="parse-run")

    assert result.result == PARSE_FAILURE
    assert result.error_code == "EXPRESSION_PARSE_FAILURE"
    provenance, details, report = _read_run(root, result)
    artifact_blob = result.provenance_path.read_text(encoding="utf-8")
    artifact_blob += result.result_path.read_text(encoding="utf-8")
    artifact_blob += report
    assert provenance["result"] == PARSE_FAILURE
    assert details["error_code"] == "EXPRESSION_PARSE_FAILURE"
    assert details["obligations"] == []
    assert secret not in artifact_blob
    assert "Result: **PARSE_FAILURE**" in report
    assert _source_snapshot(root) == before


def test_declared_assumption_omission_is_an_explicit_gate(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    hypothesis_path = root / "hypotheses/hypothesis.json"
    hypothesis = json.loads(hypothesis_path.read_text(encoding="utf-8"))
    hypothesis["assumptions_used"] = []
    hypothesis_path.write_text(json.dumps(hypothesis), encoding="utf-8")
    before = _source_snapshot(root)

    result = verify_hypothesis(root, run_id="assumption-run")

    assert result.result == ASSUMPTION_REQUIRED
    assert result.error_code == "DECLARED_ASSUMPTIONS_OMITTED"
    provenance, details, report = _read_run(root, result)
    assert provenance["result"] == ASSUMPTION_REQUIRED
    assert details["obligations"] == []
    assert "Result: **ASSUMPTION_REQUIRED**" in report
    assert "nothing was silently inferred" in report
    assert _source_snapshot(root) == before


def test_multiple_obligations_aggregate_nonzero_before_unknown(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    (root / "assumptions/assumptions.yaml").write_text(
        "symbols:\n  - name: x\n    real: true\n    nonzero: false\n"
        "functions:\n  - f\n  - g\n",
        encoding="utf-8",
    )
    (root / "expressions/current.txt").write_text("f(x)\n", encoding="utf-8")
    _set_candidate(root, "g(x)\n")
    (root / "expressions/refuted.txt").write_text("f(x) + 1\n", encoding="utf-8")
    hypothesis_path = root / "hypotheses/hypothesis.json"
    hypothesis = json.loads(hypothesis_path.read_text(encoding="utf-8"))
    hypothesis["members"].append("expressions/refuted.txt")
    hypothesis["proof_obligations"] = [
        {
            "obligation_id": "undecided",
            "relation": "equivalent",
            "left": "expressions/current.txt",
            "right": "expressions/candidate.txt",
        },
        {
            "obligation_id": "refuted",
            "relation": "equivalent",
            "left": "expressions/current.txt",
            "right": "expressions/refuted.txt",
        },
    ]
    hypothesis_path.write_text(json.dumps(hypothesis), encoding="utf-8")

    result = verify_hypothesis(root, run_id="aggregate-run")

    assert [item.verdict for item in result.obligations] == [UNKNOWN, NONZERO]
    assert result.result == NONZERO
    _read_run(root, result)


def test_generate_report_returns_existing_or_regenerates_missing_report(tmp_path):
    root = tmp_path / "workspace"
    loaded = initialize_workspace(root)
    result = verify_hypothesis(loaded, run_id="report-run")

    existing = generate_report(root, result.run_id)
    assert existing.result == ZERO
    assert existing.text == result.report_path.read_text(encoding="utf-8")

    result.report_path.unlink()
    regenerated = generate_report(load_workspace(root), result)
    assert regenerated.path == result.report_path
    assert regenerated.path.is_file()
    assert regenerated.text == existing.text


def test_result_persists_bounded_grounding_context_and_report_is_complete(
        tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    hypothesis_path = root / "hypotheses/hypothesis.json"
    hypothesis = json.loads(hypothesis_path.read_text(encoding="utf-8"))
    hypothesis.update({
        "latent_object": "F(z)",
        "operators": ["VALUE", "SUBSTITUTE"],
        "instance_maps": {"current": {"z": "x"}},
        "reconstruction_rule": "substitute the declared instance map",
    })
    hypothesis_path.write_text(json.dumps(hypothesis), encoding="utf-8")

    result = verify_hypothesis(root, run_id="rich-report-run")
    provenance, details, report = _read_run(root, result)

    summary = details["workspace_summary"]
    assert summary["project"]["project_name"] == "workspace"
    assert summary["project"]["objective"]
    assert summary["assumptions"]["symbols"][0]["name"] == "x"
    assert summary["assumptions"]["functions"] == []
    persisted_hypothesis = summary["hypothesis"]
    assert persisted_hypothesis["hypothesis_type"] == "equivalence"
    assert persisted_hypothesis["members"] == [
        "expressions/current.txt", "expressions/candidate.txt"]
    assert persisted_hypothesis["latent_object"] == "F(z)"
    assert persisted_hypothesis["operators"] == ["VALUE", "SUBSTITUTE"]
    assert persisted_hypothesis["instance_maps"] == {"current": {"z": "x"}}
    assert persisted_hypothesis["reconstruction_rule"]
    assert persisted_hypothesis["assumptions_used"] == ["x"]
    assert summary["grounding"]["notes"][0]["path"] == (
        "notes/research_notes.md")
    assert summary["grounding"]["references"][0]["path"] == (
        "references/README.md")
    assert {item["path"] for item in details["artifact_inventory"]} == {
        "provenance.json", "result.json", "REPORT.md"}

    for required in (
        "Workspace and grounded hypothesis",
        "Declared symbols",
        "Declared functions",
        "Notes/references grounding inventory",
        "Dependency versions",
        "Warnings",
        "Input files",
        "Expression members",
        "Generated artifact inventory",
        provenance["input_hashes"]["project.yaml"],
        provenance["expression_hashes"]["expressions/current.txt"],
        "pyyaml",
    ):
        assert required in report

    result.report_path.unlink()
    regenerated = generate_report(root, result.run_id)
    assert regenerated.text == report


def test_all_zero_multiple_obligations_aggregate_zero(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    (root / "expressions/second.txt").write_text(
        "1 + 2*x + x**2\n", encoding="utf-8")
    hypothesis_path = root / "hypotheses/hypothesis.json"
    hypothesis = json.loads(hypothesis_path.read_text(encoding="utf-8"))
    hypothesis["members"].append("expressions/second.txt")
    hypothesis["proof_obligations"].append({
        "obligation_id": "equivalence-2",
        "relation": "equivalent",
        "left": "expressions/current.txt",
        "right": "expressions/second.txt",
    })
    hypothesis_path.write_text(json.dumps(hypothesis), encoding="utf-8")

    result = verify_hypothesis(root, run_id="all-zero-run")

    assert result.result == ZERO
    assert [item.verdict for item in result.obligations] == [ZERO, ZERO]
    _read_run(root, result)
