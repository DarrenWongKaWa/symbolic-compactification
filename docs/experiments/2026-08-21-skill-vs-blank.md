# Local A/B: blank agent vs skill (σ_abc first cycle)

Date: 2026-08-21. Host: this machine. Engine commit: `a0560a6`
(`engineering/v0.3-consolidation`). This note is an experiment log, not a
certified compact form.

Workload: `examples/long/Guo_Sigma_abc_dc_exact.txt`
(SHA-256 `63742cc4e6bf401dd48e258ecb86676b0d7570cc075cae38b91dc188652afc44`).

## Arms

- **Blank (3):** isolated `/tmp/sigma-blank-{1,2,3}` containing only
  `expression.txt`. No skill, no `AGENTS.md`, no engine.
- **Skill (3):** isolated git worktrees of this repo. Instructed to follow
  `.grok/skills/symbolic-compactification/SKILL.md` with
  `--proposer-mode main`. User did not ask for `subagent`.

## Skill arm

All three stayed on **main**. None spawned a STRUCTURAL_PROPOSER.

| Agent | First cycle | Nested proposer | Verifier |
|---|---|---|---|
| Skill-1 | inspect Wolfram → native `text` → init-session → `combine_identical_sums` | none | `step` **ZERO**, promoted |
| Skill-2 | same path, same rewrite | none | `step` **ZERO**, promoted |
| Skill-3 | inspect + init only | none | no `step` |

Follow-up on Skill-1's run `20260821T130820Z-ba9709` (same machine):

| Candidate | Verdict |
|---|---|
| `collect_common_factor` | **ZERO**, promoted (`count_ops` 3932 → ~1986) |
| Drop every `Piecewise`, keep only the default branch (blank-style confluence) | **UNKNOWN** (`TIME_BUDGET_EXCEEDED`) |

That drop-Piecewise check was `verify` only. It was **not** promoted.

## Blank arm

| Agent | Wall | What they did | Claim |
|---|---|---|---|
| Blank-1 | ~22 min | WolframKernel; kernel-by-kernel `Together`/`Simplify`; 30-digit spots | treated compact form as proven |
| Blank-2 | ~31 min | Wolfram `Simplify`/`Series`/`PossibleZeroQ`; drop Piecewise as limits | **Proven** (Kubo 3-point not proven) |
| Blank-3 | ~19 min | local SymPy coefficient cancellation; two kernels | many “Proven” lines; would not publish without an independent verifier |

None called this repo's `verify` / `step`. None produced a ZERO residual
record.

## Difference (this run)

The skill path is ingest → inspect → optional `step` → promote only on
ZERO. The blank path opens a CAS, writes named kernels, and treats
`Simplify` / numerics / coefficient cancellation as proof. Bold structure
(two kernels, removable limits) appeared only on the blank arm; the engine
did not certify it.

Where each agent stopped versus the PRB Form I / Form II closed form is
tabulated in
[2026-08-21-progress-vs-prb-closed-form.md](2026-08-21-progress-vs-prb-closed-form.md).
None of the six agents reproduced that closed form.
