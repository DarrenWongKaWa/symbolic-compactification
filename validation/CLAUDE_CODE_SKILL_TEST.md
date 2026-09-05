# Claude Code portable-skill test

Harness: Claude Code
Version: 2.1.231 (session warned that `deepseek-v4-pro` is not a
recognized model name; run completed and wrote artifacts)
Source commit/tag: `98f6a5b` on `release/portable-skill`
  (`github-tree-sha` c99bb39558b0d0bcc5361a0a3d12d735465b22b4, skill 0.3.3)
Starting directory: `/tmp/sc-test-claude2` (fresh; independent of Codex
and of `/tmp/sc-test-claude`)
Skill acquisition method:

```bash
gh skill install DarrenWongKaWa/symbolic-compactification symbolic-compactification \
  --agent claude-code --scope project --pin release/portable-skill --force
```

Skill installed location: `/tmp/sc-test-claude2/.claude/skills/symbolic-compactification/`
Minimal prompt: `Audit https://arxiv.org/abs/2604.04520.`

Visible to the harness: installed skill only. Codex replay was not copied
in. No golden `examples/2604.04520/v3/` tree.

G1 Acquire: PASS
G2 Discover: PASS (named `symbolic-compactification` and quoted the
description)
G3 Trigger: PASS
G4 Execute: PASS (inventory 93 = 11 + 82; `audit.json` / `audit.html` /
`audit.md`; `#judge-strip` and map on the first screen; `CHECK_OK`)
G5 Scientific fidelity: PARTIAL

Overall: PARTIAL

G5 evidence:

- Inventory and claim neighbourhood are right: TR-symmetric
  dissipation-enabled nonreciprocity, Γ² / Γ scaling, injection/shift and
  Drude/BCD/QMD limits, Rice–Mele as numerical support.
- Central spine is reconstructed:
  `(4) → C-1 → C-2 → D-1 → (5)`.
- Appendix D internals are still one edge (E-6): TR identities,
  antisymmetrization, and shift-vector rewrite are named in that edge and
  in O1, not split as separate reconstructed steps.
- No Exact stamps, no `0*`, no Guo leak.

Failures:
- G5. Did not split Appendix D despite SKILL.md / METHOD.md (“do not
  collapse a whole appendix into one step”). Codex, given the same
  installed skill, did split those steps.

Cause: HARNESS_BEHAVIOR (skill was sufficient; another competent agent
succeeded). Unknown-model warning is also HARNESS_BEHAVIOR, not BLOCKED.

Skill defects found: none required for this G5 miss.
Fixes required: none on the skill for Claude’s coarse D; a stronger
harness or a second pass would be needed.

Earlier `/tmp/sc-test-claude` run on `bcb7863` was the same G5 shape
without the judgment-strip UI.
