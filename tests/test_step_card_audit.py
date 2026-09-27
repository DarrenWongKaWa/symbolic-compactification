"""STEP_CARD edges through the derivation audit: demo S end to end."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from symbolic_compactification import cli
from symbolic_compactification.audit.evidence import verify_audit
from symbolic_compactification.audit.replay_compare import compare_records
from symbolic_compactification.audit.schema import (
    CERTIFIED_BY_RULE, SOURCE_TIED_STEP_CARD, UNKNOWN, integrity_issues,
    may_appear_in_verified_table)
from symbolic_compactification.audit.summary import generate_reviewer_summary
from symbolic_compactification.audit.workspace import load_audit_workspace
from symbolic_compactification.manybody.latex import locate_quote
from symbolic_compactification.manybody.mathml import expression_to_mathml, latex_to_mathml

pytestmark = pytest.mark.derivation_audit_release_critical

DEMO = Path(__file__).resolve().parents[1] / "tests/fixtures/audit_demos/S"


def _copy(tmp_path: Path) -> Path:
    destination = tmp_path / "demo-S"
    shutil.copytree(DEMO, destination)
    return destination


def _run(root: Path):
    return verify_audit(load_audit_workspace(root), run_id="cards-run")


def _expected() -> dict[str, str]:
    doc = yaml.safe_load((DEMO / "demo.yaml").read_text(encoding="utf-8"))
    return {row["edge_id"]: row["expected_status"] for row in doc["expected_edges"]}


def test_demo_s_statuses_and_certificates(tmp_path):
    run = _run(_copy(tmp_path))
    assert {r.edge_id: r.status for r in run.records} == _expected()
    certified = [r for r in run.records if r.status == CERTIFIED_BY_RULE]
    for record in certified:
        assert record.rule_certificate.rule_id == SOURCE_TIED_STEP_CARD
        assert not integrity_issues(record) and not may_appear_in_verified_table(record)
        assert "TRANSCRIPTION:MATCH" in record.warnings


def test_summary_renders_math_with_sources(tmp_path):
    root = _copy(tmp_path)
    run = _run(root)
    page = generate_reviewer_summary(load_audit_workspace(root), run).html.read_text()
    assert page.count("<math") >= 6 and "<script" not in page
    assert "From the manuscript:" in page and "eq. (5)" in page and "line 33" in page
    assert "Conventions to review once" in page and "Step cards" in page


def test_edited_quote_is_not_decided(tmp_path):
    root = _copy(tmp_path)
    card = root / "cards" / "eq_pair-wrong.yaml"
    text = card.read_text().replace(r"\psi(z_+(a))", r"\psi(z_-(a))").replace(r"\psi(z_+(b))", r"\psi(z_-(b))")
    card.write_text(text)                      # the "fixed" claim no longer quotes the paper
    by_id = {r.edge_id: r for r in _run(root).records}
    assert by_id["S.pair-wrong"].status == UNKNOWN
    assert "TRANSCRIPTION:NOT_IN_DOCUMENT" in by_id["S.pair-wrong"].warnings


def test_card_outside_workspace_is_refused(tmp_path):
    root = _copy(tmp_path)
    outside = tmp_path / "elsewhere.tex"
    outside.write_text("x")
    card = root / "cards" / "eq_split.yaml"
    card.write_text(card.read_text().replace("../manuscript/source.tex", str(outside)))
    by_id = {r.edge_id: r for r in _run(root).records}
    assert by_id["S.split"].status == UNKNOWN
    assert any(w.startswith("MANYBODY_INPUT_ERROR") for w in by_id["S.split"].warnings)


def test_package_replays_step_cards(tmp_path, capsys):
    root = _copy(tmp_path)
    assert cli.main(["audit", "verify", str(root)]) in (0, 2)
    assert cli.main(["audit", "package", str(root)]) == 0
    capsys.readouterr()
    replay = root / "reviewer-verification-package" / "replay"
    assert (replay / "cards" / "conventions.yaml").is_file()
    recorded = _run(root).records
    replayed = verify_audit(load_audit_workspace(replay), run_id="replay").records
    assert not compare_records(recorded, replayed)


def test_mathml_and_locator():
    macros = {"ii": (0, r"\mathrm{i}")}
    math = latex_to_mathml(r"\frac{\ii}{\omega - \ii\Gamma}", macros)
    assert "<mfrac>" in math and "Γ" in math and "−" in math
    assert "\\unknowncmd" in latex_to_mathml(r"x + \unknowncmd")      # visible, not dropped
    assert "&#968;" in expression_to_mathml("polygamma(1, z) + beta")
    raw = "\\begin{equation}a=b\\end{equation}\n\\begin{align}c&=d\\\\e&=f\\label{q}\\end{align}"
    assert locate_quote(raw, "e&=f") == {"line": 2, "environment": "align", "label": "q", "number": 3}
