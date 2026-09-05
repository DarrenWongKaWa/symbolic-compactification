# Codex portable-skill test

Harness: Codex CLI
Version: 0.151.0 (model `gpt-5.6-terra`)
Source commit/tag: `bcb7863` on `release/portable-skill`
  (`github-tree-sha` 7f29c63569e9a9fc77cb36981f82e05004d63848)
Starting directory: `/tmp/sc-test-codex` (fresh, unrelated; not the
development repository)
Skill acquisition method:

```bash
gh skill install DarrenWongKaWa/symbolic-compactification symbolic-compactification \
  --agent codex --scope project --pin release/portable-skill --force
```

Skill installed location: `/tmp/sc-test-codex/.agents/skills/symbolic-compactification/`
Minimal prompt: `Audit https://arxiv.org/abs/2604.04520.`

Visible to the harness: the installed skill folder only (SKILL.md,
scripts, references). No Anan V1/V2/V3 outputs, no `audit.json` answer
key, no development conversation, no Guo ledger copy.

G1 Acquire: PASS
G2 Discover: PASS (`discover.txt` named `symbolic-compactification`)
G3 Trigger: PASS (minimal prompt; agent opened SKILL.md unprompted)
G4 Execute: PASS (`audit/inventory.json`, `audit.json`, `audit.html`,
`audit.md`; inventory 93 = 11 + 82, appendices A–E)
G5 Scientific fidelity: PARTIAL

Overall: PARTIAL

Failures:
- G5. Codex reconstructed Eq. (4) → Appendix C → Appendix D → Eq. (5)
  as a spine, and named TR / antisymmetrization in one collapsed edge
  (`E-7`). It did not emit separate edges for TR identities,
  antisymmetrization, and the shift-vector rewrite.

Cause: SKILL_DEFECT (coarse grain). METHOD now says not to collapse a
multi-step appendix into one edge. That instruction was **not** in the
installed `0.3.2` skill. Not a harness-runtime block.

Skill defects found:
- Missing “split distinct transformations” instruction (fixed in tree;
  not in this install).
- Installed renderer was V3.1 without the later judgment-strip UI.

Fixes required:
- Reinstall from a commit that contains METHOD grain + UI renderer.
- Rerun the same minimal prompt in a new `/tmp` workspace.

Classification: PARTIAL / SCIENTIFIC_FAILURE (coarse Appendix D) /
SKILL_DEFECT
