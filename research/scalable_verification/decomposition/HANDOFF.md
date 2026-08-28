# HANDOFF — Track V / V1 (proof decomposition)

Parent: `329c49c22c7d68d0192a59f04bf3ba8ad12c9b48`
Branch: `work/v-proof-decomposition`
Owned: `research/scalable_verification/decomposition/**`, `tests/test_sv_decomposition.py`

## What was implemented

Generic planner `decompose(A, B, relation)` for `EQUALITY`, `LIMIT`,
`NEWTON_DD`, `HERMITE_DD`. Returns typed steps with provenance and may
**suggest** `research.scalable_verification.api.STRATEGIES`. It does **not**
assign ZERO / NONZERO / UNKNOWN as a verdict and does **not** call
`sympy.limit` on a claim.

Exact composition (remainder-`0` polynomial division, never `A_loc := A/S`):

- Spectator: `A = S A_loc`, `B = S B_loc`. Residual `A_loc - B_loc` only if
  `S` is a nonzero constant or `Ne(S, 0)` is assumed.
- Identical cancel: `S` divides numerator and denominator of a rational.

False composition acceptance: **0**.

No Guo-specific identities. No LLM calls.

## Tests

`.venv/bin/python -m pytest tests/test_sv_decomposition.py -q`

Small polynomials only. `sympy.limit` is monkeypatched to explode on the
LIMIT path.

## Remaining risks

- Non-polynomial expressions fail closed (no split), they are not guessed.
- Mixed Hermite windows are not unfolded here (V4).
- Uncertified spectators are suggested (`FACTOR_LOCAL`) but not substituted
  for the original claim.
- `together` may already cancel some rationals; a vanishing denominator still
  yields `SERIES_LOCAL`, not a local evaluation.

## COMMIT SHA

(pending)
