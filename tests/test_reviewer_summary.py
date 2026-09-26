"""Reviewer summary is a faithful, no-code view of machine records."""
from __future__ import annotations

import json
from pathlib import Path

from symbolic_compactification.audit.evidence import verify_audit
from symbolic_compactification.audit.summary import generate_reviewer_summary


def _copy_demo(tmp_path: Path, name: str) -> Path:
    import shutil

    source = Path(__file__).resolve().parents[1] / "tests/fixtures/audit_demos" / name
    destination = tmp_path / f"demo-{name}"
    shutil.copytree(source, destination)
    return destination


def test_summary_has_counts_queue_provenance_and_no_code_path(tmp_path):
    root = _copy_demo(tmp_path, "C")
    # Load the copied fixture through the normal immutable workspace loader.
    from symbolic_compactification.audit.workspace import load_audit_workspace

    workspace = load_audit_workspace(root)
    run = verify_audit(workspace, run_id="summary-run")
    artifacts = generate_reviewer_summary(workspace, run)

    html = artifacts.html.read_text(encoding="utf-8")
    markdown = artifacts.markdown.read_text(encoding="utf-8")

    assert artifacts.html.name == "REVIEWER_SUMMARY.html"
    assert artifacts.markdown.name == "REVIEWER_SUMMARY.md"
    assert "machine evidence" in html.lower()
    assert "reviewer queue" in html.lower()
    assert "declared equation inventory" in html.lower()
    assert "C.asymptotic-O" in html
    assert "C.asymptotic-O" in markdown
    assert "./reproduce.sh" in markdown
    assert "not a paper-level certificate" in html.lower()
    assert "ZERO" in markdown
    assert "ASYMPTOTIC" in markdown
    assert "Declared equation inventory" in markdown
    assert "AI proves your paper" not in html


def test_summary_is_generated_from_records_not_stale_tables(tmp_path):
    root = _copy_demo(tmp_path, "A")
    from symbolic_compactification.audit.workspace import load_audit_workspace

    workspace = load_audit_workspace(root)
    run = verify_audit(workspace, run_id="summary-run")
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "TABLE_VERIFIED.md").write_text("FORGED\n", encoding="utf-8")
    artifacts = generate_reviewer_summary(workspace, run)
    assert "FORGED" not in artifacts.markdown.read_text(encoding="utf-8")
    assert "Machine-verified local identities" in artifacts.markdown.read_text(
        encoding="utf-8")
