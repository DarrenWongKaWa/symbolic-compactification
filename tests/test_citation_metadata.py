"""Citation metadata stays in step with the package and the README."""
from __future__ import annotations

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


def test_readme_points_to_citation_and_keeps_model_verdict_split():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "(CITATION.cff)" in readme
    assert "```mermaid" in readme
    lowered = " ".join(readme.lower().split())
    assert "a model may propose but only the program may certify" in lowered
    assert "name the language model" in lowered
