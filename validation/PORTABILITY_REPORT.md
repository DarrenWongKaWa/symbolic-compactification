# Portability report

Tested install: GitHub `release/portable-skill` @ `bcb7863`
(skill metadata version 0.3.2). Clean rooms `/tmp/sc-test-codex` and
`/tmp/sc-test-claude`. Minimal prompt only:

```text
Audit https://arxiv.org/abs/2604.04520.
```

| Gate                | Codex                         | Claude Code                   |
| ------------------- | ----------------------------- | ----------------------------- |
| Acquire             | PASS                          | PASS                          |
| Discover            | PASS                          | PASS                          |
| Trigger             | PASS                          | PASS                          |
| Execute             | PASS                          | PASS                          |
| Scientific fidelity | PARTIAL                       | PARTIAL                       |
| Overall             | PARTIAL                       | PARTIAL                       |

## Can a user install `symbolic-compactification`, start either supported harness from an unrelated directory, provide only a scientific paper, and obtain the intended reviewer-facing audit?

PARTIAL

Evidence:

- **Install is real.** `gh skill install DarrenWongKaWa/symbolic-compactification symbolic-compactification --agent {codex|claude-code} --scope project --pin release/portable-skill --force` populated `.agents/skills/` (Codex) and `.claude/skills/` (Claude Code) from GitHub, not from a manual copy of this repo.
- **Discovery and trigger work.** Neither harness was told the skill name or a script path. Both fetched arXiv:2604.04520, ran `inventory.py`, wrote `audit.json`, and rendered HTML+Markdown.
- **Inventory is correct** on both: 93 numbered rows, main 11, appendix 82, A–E only.
- **Claims are in the right scientific neighbourhood:** dissipation-enabled nonreciprocity under TR, geometric/shift-vector conductivity, low-T Γ², high-T/metallic Γ, Rice–Mele as numerical support — not Exact.
- **Central derivation is recognized but too coarse.** Both agents put Appendix D on the path from Eq. (4) to Eq. (5). Neither emitted the load-bearing TR / antisymmetrization / shift-vector steps as separate edges. That is short of the Anan semantic benchmark.
- **No Guo answer-key leak.** No `1508.00571` content. No `0*`.
- **HTML/Markdown exist** and were generated from the same `audit.json`. The UI judgment-strip pass landed **after** this install and is not in these artifacts.

## Skill vs harness

| Issue | Class |
|---|---|
| Coarse Appendix D grain | SKILL_DEFECT — METHOD now forbids collapsing a multi-step appendix; not in `bcb7863` |
| Claude unknown-model warning | HARNESS_BEHAVIOR — run still produced artifacts |
| Missing judgment-strip UI in this install | SKILL_DEFECT relative to the later UI pass; presentation only |

## Not done (release gates)

- Reinstall + replay after METHOD grain + UI renderer.
- PR / merge to `main`.
- Post-merge install from `main` or a tag.
- Tag.

Until G5 is replayed, this is not a PASS release.
