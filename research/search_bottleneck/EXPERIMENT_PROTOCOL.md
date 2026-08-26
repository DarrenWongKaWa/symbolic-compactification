# Bottleneck-localization protocol (DEV only)

Freeze: 2026-08-26. Does **not** modify `ssc-bench-v0.1` test files.
Architecture choices here cannot be justified on frozen test numbers.

## D-levels (scientific abstraction)

| Level | Meaning |
|---|---|
| D0 | local algebra: factor, cancel, together, trig/exp rewrite |
| D1 | identical-sum merge or numeric/common-factor fold (`2*Sum`, `a*(...)`) |
| D2 | repeated-kernel extraction (shared analytic summand named or factored as a kernel, not merely `2*expr`) |
| D3 | auxiliary / master-function definition |
| D4 | confluence, generating function, or Piecewise-as-one-analytic-object |
| D5 | symmetry orbit or geometric / physically meaningful generator |

Primary diagnostic: **D2–D5**. D0–D1 are a floor, not a win for this phase.

Syntactic `count_ops` is secondary. Do not declare a winner on ops alone.

## Arms (matched)

| ID | Search | Certification during search | Role |
|---|---|---|---|
| R1 | blank: expression + `scientific_context`; CAS allowed; no skill | none | unsafe search-power reference |
| R2 | **same candidates as R1** | every candidate through `verify_equivalent` (definitions expanded) | isolates search vs verify |
| R3 | main-agent skill path: locally checkable transforms, protocol language, no isolated proposer | yes | production-like |
| R4 | isolated `STRUCTURAL_PROPOSER` + expression + `structure_summary` (+ same `scientific_context` for matching) | yes, main verifies | H1 |
| R5 | isolated `SCIENTIFIC_STRUCTURE_PROPOSER` + same inputs + abstraction objective | yes, main verifies | H3 |

R6 (3 specialist proposers) is optional and skipped unless R5 is cheap and H6 is the remaining question.

R2 does not get a second LLM call. It reuses R1 text.

## Budgets (matched)

Per item, per arm, per seed:

- LLM calls: 1 (up to 3 candidates in that call)
- Verifier calls: ≤ 3 (one per candidate)
- Wall clock (proposer): 180 s target; record actual
- CAS: R1 may use SymPy; R3–R5 should propose structure, not "run simplify"
- Hidden gold: never in proposer context
- Model: Grok (this harness), same version for all LLM arms

Unavoidable mismatch: R3 is a subagent given the **skill excerpt**, not a
full dirty worktree (the 2026-08-21 skill arm had a git worktree). Recorded
as `R3_context=skill_excerpt_not_full_worktree`.

## Hard DEV set

Files under `research/search_bottleneck/dev_hard/` plus selected
`benchmark/dev/` items listed in `manifest.json`. **Not** `benchmark/test/`.

Guo `C-guo-sigma-abc` is a **case study** in this set, contaminated, not
held-out evidence.

## Seeds

Seed 0 on the full hard DEV set. Seeds `{0,1,2,3,4}` on two flagship
items if cost allows: `D2-shared-kernel` and Guo.

## Metrics

Search: n_hypotheses, max D-level *attempted*, families, time-to-first-D2+.
Certification: ZERO / NONZERO / UNKNOWN counts, false promotions (must be
0 if we only promote on ZERO), UNKNOWN among D2+ attempts.
Scientific: max *certified* D-level, kernel/Piecewise/auxiliary counts.
Syntactic: Δops, Δchars (secondary).

Hypothesis definitions are expanded before verify. Failure to expand is
UNKNOWN/parse, not ZERO.

## Regimes (filled in DECISION.md)

- A proposer/architecture: (R2 or R4 or R5) ≫ R3 on certified D-level or
  D2+ hypothesis rate, and verifier accepts some of those.
- B scientific-objective: R5 ≫ R4 on D2–D5.
- C verifier: R1 strong D2+ and R2 mostly UNKNOWN with unsupported/timeout
  evidence.
- D search-space: all proposers stay at D0–D1.
- E metric mismatch: ops prefers CAS, D-level prefers structured forms.

"≫" on this small n: at least **+1 certified D-level** on ≥2 items, or
≥2× D2+ hypothesis rate with non-overlapping interpretation (count
table, not a p-value theatre). If neither fires, say **no material
difference**.

## Leakage

Any proposer payload containing hidden gold or L4–L7 gold names as
*instructions* discards that run (`F_LEAK`).
