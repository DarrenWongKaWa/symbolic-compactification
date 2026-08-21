"""v0.3 skill + operating-contract: configurable proposer.

The project skill and AGENTS.md must agree:

* default proposer is main (the main agent writes candidates);
* isolated STRUCTURAL_PROPOSER subagent is optional, never the unique path;
* the verifier is mandatory and promotion requires exact ZERO.

Synthetic/docs contract only — no scientific workload.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".grok" / "skills" / "symbolic-compactification" / "SKILL.md"
AGENTS = ROOT / "AGENTS.md"
ROLE = ROOT / "roles" / "STRUCTURAL_PROPOSER.md"

# Shared operating sentences. Both the skill and AGENTS.md must carry them
# so a harness that reads only one file still gets the same defaults.
_SHARED = (
    "The proposer path is configurable.",
    "Subagent is never the unique path.",
    "working directory is noisy",
    "expression is extremely long",
    "Promote only on ZERO.",
)

# Unique-path recipe that v0.3 explicitly retires.
_RETIRED_UNIQUE_PATH = (
    "Ask the STRUCTURAL_PROPOSER for the next candidate"
)


def _norm(text: str) -> str:
    return " ".join(text.split())


def test_project_skill_exists_with_frontmatter():
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: symbolic-compactification\n" in text
    assert "argument-hint:" in text


def test_skill_and_agents_share_proposer_defaults():
    skill = _norm(SKILL.read_text(encoding="utf-8"))
    agents = _norm(AGENTS.read_text(encoding="utf-8"))
    for phrase in _SHARED:
        assert phrase in skill, f"skill missing: {phrase}"
        assert phrase in agents, f"AGENTS.md missing: {phrase}"


def test_default_is_main_and_subagent_is_optional():
    skill = SKILL.read_text(encoding="utf-8")
    agents = AGENTS.read_text(encoding="utf-8")
    assert "Default: `main`" in skill
    assert "Optional: `subagent`" in skill
    assert "Optional: `auto`" in skill
    assert "Default is **main**" in agents
    assert "Optional (`auto`)" in agents or "`auto`" in agents
    assert "Use `auto` only when the user asked" in skill
    assert _RETIRED_UNIQUE_PATH not in agents
    assert _RETIRED_UNIQUE_PATH not in skill


def test_subagent_child_receives_only_expression_and_structure_summary():
    skill = _norm(SKILL.read_text(encoding="utf-8"))
    role = _norm(ROLE.read_text(encoding="utf-8"))
    for text in (skill, role):
        assert "current expression" in text
        assert "structure_summary" in text
        assert "working tree" in text
        assert any(ban in text for ban in (
            "Do not give", "Do not pass", "Do not paste"))


def test_skill_contains_copy_paste_cli():
    skill = _norm(SKILL.read_text(encoding="utf-8"))
    for fragment in (
        "symbolic-compactification inspect",
        "symbolic-compactification init-session",
        "symbolic-compactification step",
        "symbolic-compactification finalize",
        "record_proposal",
        "harness_task_or_subagent_id",
    ):
        assert fragment in skill, f"skill missing CLI/API fragment: {fragment}"


def test_readme_states_scope_and_default_main():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "not a CAS replacement" in readme.lower() or "not a CAS" in readme
    assert "theorem" in readme.lower()
    assert "default" in readme.lower() and "main" in readme
    assert "Promote only on ZERO" in readme or "exact ZERO" in readme
