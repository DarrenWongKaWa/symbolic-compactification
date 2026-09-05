"""Portable skill package: layout, scripts, no hidden repo paths."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "symbolic-compactification"
SCRIPTS = SKILL / "scripts"


def test_canonical_skill_frontmatter_and_triggers():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: symbolic-compactification\n" in text
    lowered = text.lower()
    for needle in (
        "audit a paper",
        "numbered equations",
        "evidence ledger",
        "arxiv",
        "reviewer html",
        "llm judgment is never proof",
    ):
        assert needle in lowered, needle
    assert "2604.04520" not in text
    assert "eq. (4)" not in lowered
    assert "split distinct transformations" in lowered
    method = (SKILL / "references" / "METHOD.md").read_text().lower()
    assert "do not collapse a multi-step" in method


def test_skill_scripts_exist_and_are_stdlib():
    for name in ("inventory.py", "fetch_arxiv.py", "render.py", "check_audit.py"):
        path = SCRIPTS / name
        assert path.is_file(), name
        src = path.read_text(encoding="utf-8")
        assert "import sympy" not in src
        assert "symbolic_compactification" not in src
        assert "/Users/" not in src
        assert "/private/tmp" not in src


def test_inventory_and_render_on_fixture(tmp_path: Path):
    tex = ROOT / "tests" / "fixtures" / "skill" / "mini.tex"
    inv_out = tmp_path / "inventory.json"
    subprocess.run(
        [sys.executable, str(SCRIPTS / "inventory.py"), "--tex", str(tex), "--out", str(inv_out)],
        check=True,
    )
    inv = json.loads(inv_out.read_text(encoding="utf-8"))
    assert inv["v2"]["main"] == 2
    assert inv["v2"]["appendix"] == 1
    assert inv["v2"]["total"] == 3

    audit = ROOT / "tests" / "fixtures" / "skill" / "mini_audit.json"
    out = tmp_path / "audit"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "render.py"),
            "--audit",
            str(audit),
            "--out",
            str(out),
            "--check",
        ],
        check=True,
    )
    html = (out / "audit.html").read_text(encoding="utf-8")
    md = (out / "audit.md").read_text(encoding="utf-8")
    assert "C1" in html and "C1" in md
    assert "E-sum" in html
    assert 'id="map-sec"' in html.split('id="main"')[0]
    assert "Local certification is not a paper-level certificate." in html
    assert "Need your judgment" in html.split('id="main"')[0]
    assert "Equation map" in html
    assert "Main + appendix map A–E" not in html
    assert "Source: Eq. (2)" in html
    assert "tex-fallback" in html
    assert "<h2>E. Equation detail</h2>" not in html
    assert '["$","$"]' not in html
    assert "0*" not in html
    assert "paper-audit-v3:2604.04520" not in html
    subprocess.run(
        [sys.executable, str(SCRIPTS / "check_audit.py"), "--audit", str(audit)],
        check=True,
    )


def test_agents_and_claude_point_at_canonical_skill_without_duplicating_method():
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    for blob in (agents, claude):
        assert "skills/symbolic-compactification/SKILL.md" in blob
        assert "gh skill install" in blob
        assert "Audit https://arxiv.org/abs/2604.04520." in blob
        assert "Do not duplicate the method" in blob or "not defined here" in blob.lower()


def test_readme_install_then_minimal_prompt():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "gh skill install DarrenWongKaWa/symbolic-compactification" in readme
    assert "--agent codex" in readme
    assert "--agent claude-code" in readme
    assert "Audit https://arxiv.org/abs/2604.04520." in readme
    assert "audit/audit.html" in readme
