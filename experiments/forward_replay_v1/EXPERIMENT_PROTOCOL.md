# Experiment protocol (frozen before proposers)

Product: tag `derivation-audit-v0.2.1-alpha` peel `783ec64`.
Engine: `python_sympy_exact_v1` / `0.3.0`.
No `src/` edits.

## Research question

Given candidate next transformations from an arbitrary proposer, can the
framework safely decide which candidates may become the next accepted
state?

Not: can an AI discover the right representation.

## Design (benchmark skill, targeted)

G1 Coverage: 8 recovery tasks across algebraic regroup, prefactor,
antisymmetry, substitution-conditioned algebra, compact rewrite; plus one
negative control; plus a 3-step rollout.

G2 Diagnostics: separate TargetRecovery@K (proposer quality) from
promotion / false-promotion (verifier safety).

G3 Reproducibility: frozen tasks, hashed contexts, frozen candidate JSON,
offline verifier replay.

G4 Quality: leakage scan; gold control is not counted as proposer success.

Out of scope: BZ global IBP as a recovery target; remainder ZERO; new
rules; parser expansion.

## Promotion policy (experiment-level, product semantics unchanged)

| Verifier result | Promotion |
|---|---|
| ZERO | eligible; promote |
| NONZERO | refuse |
| UNKNOWN | refuse |
| PARSE_FAILURE / COMPILE_FAILURE / ASSUMPTION_REQUIRED | refuse |

`CERTIFIED_BY_RULE` is not used in this forward Mode A workspace path.
Do not equate it with ZERO.

## Experiments

A. One-shot masked recovery, K=4, candidates frozen before verify.
B. Injected negatives mixed with gold.
C. Multi-step MS-01: FR-01 → FR-02 → FR-03.
D. Optional feedback: skipped unless time remains after A–C freeze.

## Metrics

Proposer: TargetRecovery@K.
Safety: false promotion rate on injected negatives; unsupported promotion
rate; status histogram.
Rollout: accepted steps / 3.
