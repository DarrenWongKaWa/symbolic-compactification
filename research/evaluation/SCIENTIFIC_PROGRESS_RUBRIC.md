# Scientific progress rubric

Two independent axes. Do not declare a winner on `count_ops` alone.

## Syntactic compression

count_ops, char_len, ast_depth (secondary).

## Scientific abstraction (observable)

Score the **best certified** form (and, separately, the best *attempted*
hypothesis). Attempted ≠ certified.

| Code | Observable |
|---|---|
| S1 | repeated summands or identical limits merged |
| S2 | shared kernel extracted (named or factored summand, not `2*expr` only) |
| S3 | reusable named master whose **expansion** is ZERO |
| S4 | Piecewise branches reduced only with ZERO residual |
| S5 | symmetry / permute pairing named and expansion ZERO |
| S6 | physically labelled generator with closed reconstruction ZERO |

Task-local ladders (examples):

- D2 kernel tasks: L0 raw → L1 structure kept → L2 shared kernel ZERO
- D3 thermal: L0 → L1 factor → L2 named master expanding to ZERO
- D4 Piecewise: L0 keep branches → L1 named confluence hypothesis
  (not certified) → L2 ZERO unified object (usually absent)
- Guo (dev only): L0–L7 as in 2026-08-21 note; evaluation post-hoc

No human pairwise annotations were collected. Do not fabricate them.

Reconstruction exactness is mandatory for any certified level: engine ZERO
after definition expansion.
