"""V3 Anan audit: V1 visual grammar on V2 scientific semantics."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "examples" / "2604.04520"
sys.path.insert(0, str(CASE / "tools"))

from render import check_rendered, render_html, render_markdown  # noqa: E402

pytestmark = pytest.mark.derivation_audit_release_critical


def _data() -> dict:
    return json.loads((CASE / "evidence" / "audit.json").read_text(encoding="utf-8"))


def test_inventory_and_statuses_unchanged_from_v2_model():
    data = _data()
    assert data["inventory"]["v2"]["total"] == 93
    assert data["inventory"]["v2"]["main"] == 11
    assert data["inventory"]["v2"]["appendix"] == 82
    assert data["inventory"]["v2"]["by_appendix_letter"] == {
        "A": 18, "B": 18, "C": 28, "D": 10, "E": 8,
    }
    ids = {c["id"] for c in data["claims"]}
    assert ids == {"C1", "C2", "C3", "C4", "C5"}
    geom = next(c for c in data["claims"] if c["id"] == "C2")
    assert geom["status"] in {"GAP", "HUMAN_REVIEW"}
    assert geom["status"] != "EXACT"
    c5 = next(c for c in data["claims"] if c["id"] == "C5")
    assert c5["status"] == "NUMERICAL_SUPPORT"
    for e in data["edges"]:
        if e["status"] == "EXACT":
            assert "asymptotic" not in e["transformation"]


def test_v3_html_and_markdown_match_canonical_model():
    data = _data()
    html_page = render_html(data)
    md_page = render_markdown(data)
    err = check_rendered(data, html_page, md_page)
    assert err == []
    committed_html = (CASE / "v3" / "audit.html").read_text(encoding="utf-8")
    committed_md = (CASE / "v3" / "audit.md").read_text(encoding="utf-8")
    assert committed_html == html_page
    assert committed_md == md_page
    assert "0*" not in html_page
    assert r"\sigma^{\alpha\alpha\alpha}" in md_page
    assert "| ID | From | To |" in md_page
    assert 'id="claim-C2"' in html_page
    assert 'id="edge-E-D-to-sigma2"' in html_page
    assert 'id="ob-O1"' in html_page


def test_v3_first_screen_has_colour_stack_and_map():
    html_page = (CASE / "v3" / "audit.html").read_text(encoding="utf-8")
    head = html_page.split('id="main"')[0]
    assert 'class="stack"' in head
    assert 'id="map-sec"' in head
    assert "Appendix A" in head
    assert "Appendix E" in head
    assert "Appendix F" not in html_page
    assert "Appendix G" not in html_page
    assert "Main text" in head
    assert ">→</span>" in head
    assert ">⋯</span>" in head
    # (4) and (5) are not a reconstructed adjacent edge.
    assert re.search(
        r'id="map-M-4"[^>]*>\(4\)</a><span class="dots">⋯</span>'
        r'<a class="eq-node [^"]+" id="map-M-5"',
        head,
    )


def test_v3_chip_routing_is_specific():
    html_page = (CASE / "v3" / "audit.html").read_text(encoding="utf-8")
    assert 'id="map-D-1" href="#edge-E-D-longitudinal"' in html_page
    assert 'id="map-D-8" href="#edge-E-D-shift"' in html_page
    assert 'id="map-M-5" href="#claim-C2"' in html_page
    hrefs = re.findall(r'id="map-[^"]+" href="([^"]+)"', html_page)
    assert hrefs
    assert "#obligation-table" not in hrefs
    assert len(set(hrefs)) >= 8


def test_v3_keeps_reviewer_queue_not_v1_sign():
    html_page = (CASE / "v3" / "audit.html").read_text(encoding="utf-8")
    assert "Accept assumption/reasoning" in html_page
    assert "Accept reasoning" in html_page
    assert "Needs derivation" in html_page
    assert "sign-btn" not in html_page
    assert ">Sign<" not in html_page
    assert "Human acceptance records reviewer judgment" in html_page
    assert "Accepting does not stamp Exact" not in html_page


def test_v3_does_not_introduce_third_colour_language():
    html_page = (CASE / "v3" / "audit.html").read_text(encoding="utf-8")
    assert "chip num" not in html_page
    assert "class=\"chip num\"" not in html_page
    # Numerical support is an orange inspect chip.
    assert "Numerical support" in html_page
    assert 'C5 <span class="chip inspect">Numerical support</span>' in html_page


def test_historical_v1_v2_preserved_and_index_points_at_v3():
    assert (CASE / "v1" / "audit.html").is_file()
    assert (CASE / "v2" / "audit.html").is_file()
    v1 = (CASE / "v1" / "audit.md").read_text(encoding="utf-8")
    assert "Inventoried numbered lines: 94" in v1
    index = (CASE / "index.html").read_text(encoding="utf-8")
    assert "v3/audit.html" in index
    assert 'http-equiv="refresh"' in index


def test_v31_five_visible_layers_without_redundant_dumps():
    html_page = (CASE / "v3" / "audit.html").read_text(encoding="utf-8")
    vis = re.sub(r"<details\b[^>]*>.*?</details>", "", html_page, flags=re.S | re.I)
    assert "Local certification is not a paper-level certificate." in vis
    assert "<ul class=\"warn\">" not in vis
    assert "<strong>Where.</strong>" not in vis
    assert "<strong>Downstream.</strong>" not in vis
    assert "<h2>Numerical evidence" not in html_page
    assert "<h2>E. Equation detail</h2>" not in html_page
    assert vis.count("Need to verify") >= 8
    assert html_page.count('id="eq-detail-') == 93
    assert 'id="eq-drawer"' in html_page
    assert '["$","$"]' not in html_page
    assert "processEnvironments:false" in html_page
    assert "This supports consistency; it does not prove Eq. (5)." in vis
    assert "Geometric conductivity follows from Eq. (4)" in vis
    assert "C-2 → D-1" in vis or "C-2 → D-1" in html_page
    assert "longitudinal restriction" in vis
    # Visible page should be the five layers, not the 93-row cue table.
    assert vis.count('class="eq-rec"') == 0
    assert html_page.count('class="eq-rec"') == 93


def test_v31_inventory_cues_render_as_mathjax_not_raw_tex():
    html_page = (CASE / "v3" / "audit.html").read_text(encoding="utf-8")

    def rec(eid: str) -> str:
        m = re.search(
            rf'<div class="eq-rec" id="{eid}".*?(?=<div class="eq-rec"|</details>)',
            html_page,
            flags=re.S,
        )
        assert m, eid
        return m.group(0)

    m1 = rec("eq-detail-M-1")
    assert r"\begin{pmatrix}" in m1
    assert r"\(" in m1
    assert "class=\"cue\"" not in m1
    assert r"\begin{array}" not in m1
    m8 = rec("eq-detail-M-8")
    assert r"\Gamma" in m8
    assert r"\(" in m8
    assert "<code class=\"cue\">" not in html_page


def test_v3_markdown_keeps_assumptions_and_obligations():
    md = (CASE / "v3" / "audit.md").read_text(encoding="utf-8")
    html_page = (CASE / "v3" / "audit.html").read_text(encoding="utf-8")
    data = _data()
    for c in data["claims"]:
        assert c["id"] in md and c["id"] in html_page
        assert f"`{c['status']}`" in md
        for a in c["assumptions"]:
            assert a.replace("\\", "")[:20] in md.replace("\\", "") or a in md
    for e in data["edges"]:
        assert f"`{e['id']}`" in md
        assert f"`{e['status']}`" in md
    for o in data["reviewer_obligations"]:
        assert o["id"] in md and f'id="ob-{o["id"]}"' in html_page
    assert "eq:currentbyExcitation" in md
    assert "eq:sigma2" in md
