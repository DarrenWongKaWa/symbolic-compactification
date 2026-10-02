"""Citation, release and skill version metadata stay in step across the repo."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.release_critical

ROOT = Path(__file__).resolve().parents[1]


def _field(text: str, key: str) -> str:
    match = re.search(rf'^{key}\s*[:=]\s*"?([^"\n]+)"?\s*$', text, re.MULTILINE)
    assert match, f"{key} missing"
    return match.group(1).strip()


def test_citation_version_matches_pyproject():
    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert _field(cff, "cff-version") == "1.2.0"
    assert _field(cff, "version") == _field(pyproject, "version")
    assert _field(cff, "license") == "MIT"
    assert "github.com/DarrenWongKaWa/symbolic-compactification" in cff


def test_release_version_is_the_same_everywhere():
    """pyproject, models.py, README and the plugin manifests name one release."""
    from symbolic_compactification.models import (PACKAGE_VERSION,
                                                   RELEASE_VERSION)

    release = _field((ROOT / "pyproject.toml").read_text(encoding="utf-8"),
                     "version")
    assert RELEASE_VERSION == release
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"Package `{release}` (PEP 440: `{PACKAGE_VERSION}`)" in readme

    plugin = json.loads(
        (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert plugin["version"] == release
    marketplace = json.loads(
        (ROOT / ".claude-plugin" / "marketplace.json").read_text(
            encoding="utf-8"))
    assert [p["version"] for p in marketplace["plugins"]] == [release]


def test_skill_version_is_the_same_everywhere():
    """SKILL.md owns skill_version; README and the fetch User-Agent follow."""
    skill_dir = ROOT / "skills" / "symbolic-compactification"
    skill = _field((skill_dir / "SKILL.md").read_text(encoding="utf-8"),
                   r"\s*skill_version")
    assert re.fullmatch(r"\d+\.\d+\.\d+", skill), skill
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"`skill_version` `{skill}`" in readme
    fetch = (skill_dir / "scripts" / "fetch_arxiv.py").read_text(
        encoding="utf-8")
    assert f"symbolic-compactification-skill/{skill} " in fetch


def test_readme_points_to_citation_and_keeps_model_verdict_split():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "(CITATION.cff)" in readme
    assert "```mermaid" in readme
    lowered = " ".join(readme.lower().split())
    assert "a model may propose but only the program may certify" in lowered
    assert "name the language model" in lowered
