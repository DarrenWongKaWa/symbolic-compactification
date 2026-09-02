"""Flagship reviewer HTML is a presentation of frozen RESULTS, without 0*."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.derivation_audit_release_critical

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "examples" / "guo-evidence-ledger" / "output" / "index.html"
REPORT = ROOT / "examples" / "guo-evidence-ledger" / "output" / "REPORT.md"
RESULTS = ROOT / "examples" / "guo-evidence-ledger" / "evidence" / "RESULTS.md"


def test_flagship_html_has_first_screen_appendix_map():
    page = HTML.read_text(encoding="utf-8")
    visible = re.sub(r"<script\b[^>]*>.*?</script>", "", page, flags=re.S | re.I)
    head = visible.split('id="main"')[0]
    assert 'id="map-sec"' in head
    assert re.search(r"<section[^>]*id=\"map-sec\"", page)
    assert not re.search(r"<details[^>]*id=\"map-sec\"", page)
    for letter in "ABCDEFG":
        assert f"Appendix {letter}" in head


def test_flagship_html_excludes_invalid_zero_star_overlay():
    page = HTML.read_text(encoding="utf-8")
    assert "0*" not in page
    assert "ws-zero" not in page


def test_flagship_markdown_matches_frozen_results_table():
    report = REPORT.read_text(encoding="utf-8")
    results = RESULTS.read_text(encoding="utf-8")
    assert "Presentation is not a certificate" in report
    assert "| Eq. relation |" in report
    assert "| Eq. relation |" in results
    # Same scientific table body.
    assert results.split("| Eq. relation |", 1)[1] in report.split("| Eq. relation |", 1)[1]
