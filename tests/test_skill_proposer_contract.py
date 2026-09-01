"""v0.3 skill contract: two workflows, optional proposer, mandatory verifier."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".grok" / "skills" / "symbolic-compactification" / "SKILL.md"
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"


def _norm(text: str) -> str:
    return " ".join(text.split())


def test_project_skill_exists_with_frontmatter():
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: symbolic-compactification\n" in text


def test_skill_and_agents_share_two_workflows_and_zero_gate():
    skill = _norm(SKILL.read_text(encoding="utf-8"))
    agents = _norm(AGENTS.read_text(encoding="utf-8"))
    for phrase in (
        "Forward derivation",
        "Paper audit",
        "LLM judgment is never proof",
        "no API key",
    ):
        assert phrase in skill, f"skill missing: {phrase}"
        assert phrase in agents, f"AGENTS.md missing: {phrase}"
    assert "Promote only on `ZERO`" in skill or "Promote only on ZERO" in skill
    assert "Promote only on `ZERO`" in agents or "Promote only on ZERO" in agents


def test_skill_contains_copy_paste_cli():
    skill = _norm(SKILL.read_text(encoding="utf-8"))
    for fragment in (
        "symbolic-compactification inspect",
        "symbolic-compactification verify",
        "symbolic-compactification audit verify",
    ):
        assert fragment in skill, f"skill missing CLI fragment: {fragment}"


def test_readme_states_scope_and_zero_gate():
    readme = README.read_text(encoding="utf-8")
    lowered = readme.lower()
    assert "verified symbolic reasoning for theoretical physics" in lowered
    assert "forward derivation" in lowered
    assert "paper audit" in lowered
    assert "promote only on `zero`" in lowered
    assert "no api key" in lowered
