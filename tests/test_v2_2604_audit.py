"""Frozen V2 Anan audit baseline: HTML and Markdown share one evidence model."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "examples" / "2604.04520"
sys.path.insert(0, str(CASE / "tools"))

from render_v2 import check_rendered, render_html, render_markdown  # noqa: E402

pytestmark = pytest.mark.derivation_audit_release_critical


def _data() -> dict:
    return json.loads((CASE / "evidence" / "audit.json").read_text(encoding="utf-8"))


def test_inventory_is_93_not_v1_94():
    data = _data()
    assert data["inventory"]["v1_claimed"]["total"] == 94
    assert data["inventory"]["v2"]["total"] == 93
    assert data["inventory"]["v2"]["main"] == 11
    assert data["inventory"]["v2"]["appendix"] == 82
    assert data["inventory"]["v2"]["by_appendix_letter"] == {
        "A": 18, "B": 18, "C": 28, "D": 10, "E": 8,
    }


def test_claims_and_eq4_to_eq5_present():
    data = _data()
    ids = {c["id"] for c in data["claims"]}
    assert ids == {"C1", "C2", "C3", "C4", "C5"}
    assert any(e["to_eq"] == "(5)" for e in data["edges"])
    assert any("(4)" in e["from_eq"] or e["from_eq"] == "(4)" or e["id"] == "E-green-kernel" for e in data["edges"])
    geom = next(c for c in data["claims"] if c["id"] == "C2")
    assert geom["status"] in {"GAP", "HUMAN_REVIEW"}
    assert geom["status"] != "EXACT"


def test_no_exact_on_asymptotics_or_numerics():
    data = _data()
    for e in data["edges"]:
        if e["status"] == "EXACT":
            assert "asymptotic" not in e["transformation"]
        if e["status"] == "NUMERICAL_SUPPORT":
            assert e["id"] == "E-numeric-RM"
    c5 = next(c for c in data["claims"] if c["id"] == "C5")
    assert c5["status"] == "NUMERICAL_SUPPORT"


def test_html_and_markdown_match_canonical_model():
    data = _data()
    html_page = render_html(data)
    md_page = render_markdown(data)
    err = check_rendered(data, html_page, md_page)
    assert err == []
    committed_html = (CASE / "v2" / "audit.html").read_text(encoding="utf-8")
    committed_md = (CASE / "v2" / "audit.md").read_text(encoding="utf-8")
    assert committed_html == html_page
    assert committed_md == md_page
    assert "0*" not in html_page
    assert r"\sigma^{\alpha\alpha\alpha}" in md_page or "sigma2" in md_page
    assert "| ID | From | To |" in md_page
    assert 'id="claim-C2"' in html_page
    assert 'id="edge-E-D-to-sigma2"' in html_page
    assert 'id="ob-O1"' in html_page


def test_v1_preserved():
    v1_html = CASE / "v1" / "audit.html"
    v1_md = CASE / "v1" / "audit.md"
    assert v1_html.is_file() and v1_md.is_file()
    text = v1_md.read_text(encoding="utf-8")
    assert "Inventoried numbered lines: 94" in text
    assert "ZERO_UNDER_SUBSTITUTION" in text
