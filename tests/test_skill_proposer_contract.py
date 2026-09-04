"""Canonical portable skill is the method. Harness files stay thin."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "symbolic-compactification" / "SKILL.md"
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"


def _norm(text: str) -> str:
    return " ".join(text.split())


def test_project_skill_exists_with_frontmatter():
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: symbolic-compactification\n" in text


def test_skill_defines_paper_audit_and_zero_gate():
    skill = _norm(SKILL.read_text(encoding="utf-8"))
    for phrase in (
        "LLM judgment is never proof",
        "Human Accept never stamps Exact",
        "Adjacent numbers",
    ):
        assert phrase in skill, f"skill missing: {phrase}"
    assert "scripts/render.py" in skill
    assert "scripts/inventory.py" in skill


def test_agents_points_at_skill_not_a_second_method():
    agents = AGENTS.read_text(encoding="utf-8")
    assert "skills/symbolic-compactification/SKILL.md" in agents
    assert "Do not duplicate the method" in agents
    assert "Promote only on engine `ZERO`" in agents


def test_readme_states_scope_and_zero_gate():
    readme = README.read_text(encoding="utf-8")
    lowered = readme.lower()
    assert "verified symbolic reasoning for theoretical physics" in lowered
    assert "forward derivation" in lowered
    assert "paper audit" in lowered or "derivation-audit" in lowered
    assert "promote only on `zero`" in lowered
    assert "no api key" in lowered
