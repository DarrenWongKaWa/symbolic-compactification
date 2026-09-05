# Codex portable-skill test

Harness: Codex CLI
Version: 0.151.0 (model `gpt-5.6-terra`)
Source commit/tag: `98f6a5b` on `release/portable-skill`
  (`github-tree-sha` c99bb39558b0d0bcc5361a0a3d12d735465b22b4, skill 0.3.3)
Starting directory: `/tmp/sc-test-codex2` (fresh; not the development
repository; not the earlier `/tmp/sc-test-codex` run)
Skill acquisition method:

```bash
gh skill install DarrenWongKaWa/symbolic-compactification symbolic-compactification \
  --agent codex --scope project --pin release/portable-skill --force
```

Skill installed location: `/tmp/sc-test-codex2/.agents/skills/symbolic-compactification/`
Minimal prompt: `Audit https://arxiv.org/abs/2604.04520.`

Visible to the harness: installed skill only. No Anan V3 answer key, no
Guo ledger, no previous Codex `audit.json`.

G1 Acquire: PASS
G2 Discover: PASS (named `symbolic-compactification` and quoted the
description without being told the skill name)
G3 Trigger: PASS (minimal prompt opened SKILL.md unprompted)
G4 Execute: PASS (`audit/{inventory.json,audit.json,audit.html,audit.md}`;
inventory 93 = 11 + 82, A–E; HTML has `#judge-strip`, map on first screen)
G5 Scientific fidelity: PASS

Overall: PASS

G5 evidence (semantic, not byte-identical to the golden Anan model):

- Claims cover dissipation/TR nonreciprocity, geometric/shift-vector
  conductivity, low-T Γ², high-T/metallic Γ, Rice–Mele numerical support.
- Central chain is reconstructed, not summarized:
  `(4) → C-1 → C-2 → D-1 → D-4…D-7 → D-8 → (5)`
  with separate edges for TR (E-8), antisymmetrization (E-9),
  shift-vector rewrite (E-10), and `H = ξ i A` (E-11).
- Statuses stay orange on remainders, numerics, and uncompiled algebra.
  No `0*`. No Guo content.
- Reviewer queue names the load-bearing human decisions (gauge,
  continuation, TR/shift-vector, remainders, constant-Γ, numerics).

Failures: none that block the gates.

Limitation (not a gate fail): E-3 is `EXACT_IF_ASSUMPTIONS` without a
compiled engine ZERO. The skill says to leave uncompiled algebra as
`GAP`. HARNESS_BEHAVIOR.

Earlier `/tmp/sc-test-codex` run on `bcb7863` was G5 PARTIAL (Appendix D
collapsed). The split-edge METHOD line in `98f6a5b` is the skill fix.

Skill defects found: none remaining for G1–G5 on this replay.
Fixes required: none for Codex gates.
