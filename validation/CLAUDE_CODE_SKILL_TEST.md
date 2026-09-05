# Claude Code portable-skill test

Harness: Claude Code
Version: 2.1.231 (session warned that `deepseek-v4-pro` is not a
recognized model name; run completed anyway)
Source commit/tag: `bcb7863` on `release/portable-skill`
  (`github-tree-sha` 7f29c63569e9a9fc77cb36981f82e05004d63848)
Starting directory: `/tmp/sc-test-claude` (fresh, independent of the
Codex workspace and of the development repository)
Skill acquisition method:

```bash
gh skill install DarrenWongKaWa/symbolic-compactification symbolic-compactification \
  --agent claude-code --scope project --pin release/portable-skill --force
```

Skill installed location: `/tmp/sc-test-claude/.claude/skills/symbolic-compactification/`
Minimal prompt: `Audit https://arxiv.org/abs/2604.04520.`

Visible to the harness: the installed skill folder only. Codex’s Anan
run was not copied in. No golden `examples/2604.04520/v3/` tree.

G1 Acquire: PASS
G2 Discover: PASS (front matter matched “audit a paper” / arXiv URL;
the audit run invoked SKILL.md scripts without the user naming the skill)
G3 Trigger: PASS
G4 Execute: PASS (`audit/audit.json|html|md`, inventory 93 = 11 + 82)
G5 Scientific fidelity: PARTIAL

Overall: PARTIAL

Failures:
- G5. Claude reconstructed `(4) → C-2 → (5)` and stated TR
  antisymmetrization plus shift-vector in `E-4`, with obligation O4
  pointing at D-8 / D-10. It still collapsed Appendix D internals into
  one edge rather than TR identity / antisymmetrization / geometric
  rewrite as separate reconstructed steps.

Cause: SKILL_DEFECT (same coarse-grain gap as Codex) plus
HARNESS_BEHAVIOR (unknown-model warning; did not block artifacts).

Skill defects found:
- Same missing split-edge instruction as Codex (fixed in tree after
  this run).
- Installed renderer lacked the later judgment-strip UI.

Fixes required:
- Reinstall from the grain+UI commit in a new directory.
- Rerun the same minimal prompt. Do not reuse the Codex workspace.

Classification: PARTIAL / SCIENTIFIC_FAILURE (coarse Appendix D) /
SKILL_DEFECT; unknown-model warning is HARNESS_BEHAVIOR, not BLOCKED
