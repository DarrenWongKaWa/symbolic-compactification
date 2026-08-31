"""Focused regressions for the three immutable v0.1 release demos."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from symbolic_compactification import UNKNOWN, ZERO, load_workspace

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEMO_ROOT = REPOSITORY_ROOT / "engineering/release_v0_1/demos"
RUNNER_PATH = DEMO_ROOT / "run_demos.py"
EXPECTED = {
    "demo_a_zero": ZERO,
    "demo_b_grounded_newton_dd": ZERO,
    "demo_c_unknown": UNKNOWN,
}
REQUIRED_WORKSPACE_PATHS = {
    "project.yaml",
    "expressions",
    "notes",
    "assumptions",
    "references",
    "hypotheses/hypothesis.json",
    "runs/.gitkeep",
}


def _load_runner():
    spec = importlib.util.spec_from_file_location("release_demo_runner", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_demo_inventory_is_exact_and_all_workspaces_load():
    workspace_names = sorted(
        path.name
        for path in DEMO_ROOT.iterdir()
        if path.is_dir() and path.name.startswith("demo_")
    )
    assert workspace_names == sorted(EXPECTED)

    for name in workspace_names:
        root = DEMO_ROOT / name
        for relative in REQUIRED_WORKSPACE_PATHS:
            assert (root / relative).exists(), f"{name} missing {relative}"
        assert sorted(path.name for path in (root / "runs").iterdir()) == [
            ".gitkeep"
        ]
        workspace = load_workspace(root)
        assert workspace.project.project_name
        assert workspace.hypothesis.proof_obligations


def test_demo_runner_produces_zero_zero_unknown_with_complete_artifacts(tmp_path):
    runner = _load_runner()
    execution_root = tmp_path / "demo-execution"
    summaries = runner.run_all(execution_root)

    assert list(summaries) == list(EXPECTED)
    assert {
        name: summary["actual"]
        for name, summary in summaries.items()
    } == EXPECTED
    assert summaries["demo_a_zero"]["obligation_results"] == [ZERO]
    assert summaries["demo_b_grounded_newton_dd"]["obligation_results"] == [
        ZERO, ZERO, ZERO, ZERO
    ]
    assert summaries["demo_c_unknown"]["obligation_results"] == [UNKNOWN]

    for name, summary in summaries.items():
        assert summary["passed"] is True
        assert summary["source_files_unchanged"] is True
        assert summary["provenance_complete"] is True
        assert summary["report_generated"] is True
        assert len(summary["source_snapshot_sha256"]) == 64
        run_root = execution_root / name / "runs" / summary["run_id"]
        assert (run_root / "provenance.json").is_file()
        assert (run_root / "result.json").is_file()
        report = (run_root / "REPORT.md").read_text(encoding="utf-8")
        assert f"Result: **{EXPECTED[name]}**" in report
        provenance = json.loads(
            (run_root / "provenance.json").read_text(encoding="utf-8")
        )
        assert provenance["result"] == EXPECTED[name]


def test_demo_runner_refuses_to_overwrite_execution_root(tmp_path):
    runner = _load_runner()
    existing = tmp_path / "existing"
    existing.mkdir()

    try:
        runner.run_all(existing)
    except FileExistsError as exc:
        assert "refusing to overwrite" in str(exc)
    else:
        raise AssertionError("runner overwrote an existing execution root")


def test_demo_scientific_boundaries_are_explicit():
    newton_notes = (
        DEMO_ROOT / "demo_b_grounded_newton_dd/notes/research_notes.md"
    ).read_text(encoding="utf-8")
    unknown_notes = (
        DEMO_ROOT / "demo_c_unknown/notes/research_notes.md"
    ).read_text(encoding="utf-8")

    normalized_newton_notes = " ".join(newton_notes.split())
    assert "not** a discovery result" in normalized_newton_notes
    assert "does not show that an AI" in normalized_newton_notes
    assert "UNKNOWN" in unknown_notes
    assert "no scientific state may be promoted" in unknown_notes
