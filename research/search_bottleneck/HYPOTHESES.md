# Search-bottleneck hypotheses

Date: 2026-08-26
Guo sources: `docs/experiments/2026-08-21-skill-vs-blank.md`,
`docs/experiments/2026-08-21-progress-vs-prb-closed-form.md`.
Baseline diagnosis: `BASELINE_DIAGNOSIS.md`.

Blank-agent kernel names and confluence slogans are **not** certified
success. They are search-power observations.

---

## Reconstructing the Guo observation

| Arm | Certified | Search narrative | vs PRB ladder |
|---|---|---|---|
| Skill (main, n=3) | L0–L2 ZERO on 2/3 (`combine_identical_sums`, `collect_common_factor`; ops 3932→~1986). Skill-3: no `step`. | Did not name \(K_2,K_3\); did not invent \(\Phi\), divided differences, or geometry | **correct, shallow** |
| Blank (n=3) | **zero** engine ZERO records; treated Together/Simplify/Series/PossibleZeroQ/coefficient cancellation as proof | named two kernels; claimed removable Piecewise / limits | **directionally nearer to Form I's two-kernel story, different algebra, uncertified** |
| Drop-Piecewise vs Skill-1 current | engine `UNKNOWN` (`TIME_BUDGET_EXCEEDED`) | — | not promoted |

Nobody produced L4–L7. Blank bolder ≠ blank correct.

---

## Why might blank agents emit bolder hypotheses?

Candidate explanations (not mutually exclusive):

1. They were not also operating a git repo, CLI protocol, and fail-closed
   gate, so attention went to the formula.
2. They were rewarded (by their own prompting) for a compact *story*
   (named kernels, "drop Piecewise") rather than a locally checkable
   residual.
3. They used WolframKernel / Series, which suggest confluence narratives
   this engine does not prove.
4. They were willing to introduce names and limits without a promotion
   rule that punishes UNKNOWN.

---

## H1 — Main-agent context overload

The same agent does repository navigation, protocol compliance,
verification, persistence, and mathematical search.

**Falsify if:** R4 (isolated structural subagent, same model, matched
budget) does **not** produce more D2+ hypotheses or a higher certified
D-level than R3 (main-agent skill workflow) on the hard DEV set, within
the pre-registered noise rule in `EXPERIMENT_PROTOCOL.md`.

---

## H2 — Conservative proposer behavior

The skill and STRUCTURAL_PROPOSER emphasize locally checkable
transforms (`combine_identical_sums`, common factors) and therefore
suppress high-risk structural hypotheses.

**Falsify if:** R3 already emits D2+ hypotheses at a rate indistinguishable
from R1/R5, or if R4 (same isolation, generic structural role, no extra
scientific objective) matches R5.

---

## H3 — Missing scientific objective

The proposer optimizes generic simplification (ops, LeafCount-like
shortness) rather than kernels, master functions, symmetries, or
geometric generators.

**Falsify if:** R5 (scientific-abstraction objective + allowed context)
does **not** exceed R4 on D2–D5 attempts or certified D-level.

---

## H4 — Verifier incompleteness

Correct high-level transformations become UNKNOWN because the engine
lacks limits, series, special-function normalization, continuation, or
confluence proofs.

**Falsify if:** among R1 hypotheses that a human would call
"structurally serious", R2/R4/R5 UNKNOWN rate is **not** dominated by
`TIME_BUDGET_EXCEEDED` / unsupported operations, but by NONZERO (the
hypotheses were wrong) or by parse failures (the hypotheses were not
even well-formed).

---

## H5 — Non-monotonic search

A scientifically compact form may require auxiliary objects or a
temporary increase in syntactic complexity.

**Falsify if:** every D2+ certified success on the hard DEV set is a
monotone ops/char drop with no auxiliary definition, **and** forbidding
auxiliaries does not reduce certified D-level.

---

## H6 — Single-proposer local minimum

One proposer repeatedly explores the same transform family.

**Falsify if:** R6 (optional ensemble) is not run, **or** if it is run
and does not increase hypothesis-family diversity or certified D-level
over R5 at matched total LLM-call budget.

R6 is optional. If skipped, H6 remains **open**, not confirmed.

---

## Mapping to regimes (filled after results)

See `EXPERIMENT_PROTOCOL.md` § regimes. H1→A, H3→B, H4→C, H5/H6→D,
ops-vs-physics mismatch→E.
