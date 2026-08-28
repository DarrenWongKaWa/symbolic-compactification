# HANDOFF — V2-H (adversarial family falsifier)

Branch: `work/v2-falsifier`
Parent: `4dee916170f0282f8b0e5fee171a8bf4a3934646`
Owned: `research/multibranch_verification/falsifier/**`, `tests/test_mb_falsifier.py`
Tests: `.venv/bin/python -m pytest tests/test_mb_falsifier.py -q`

False FAMILY_ZERO: **0**. True five-member cubic Hermite control remains FAMILY_ZERO.

Did not edit `schema.py`, sibling V2 packages, or the composer. Local exact
checks fill edge / recurrence / path verdicts; `compose_family_verdict` is
the only family rule. Majority of Hermite-looking branches is recorded as a
trap, never as a certificate.

## Attacks (must not be FAMILY_ZERO)

| id | family verdict | trap | defect |
|---|---|---|---|
| V2H_01_corrupted_branch_coefficient | FAMILY_NONZERO | majority 4/5 reconstructions ZERO | generic Newton `x**2+y**2` drops `xy` |
| V2H_02_wrong_factorial | FAMILY_NONZERO | majority 4/5 ZERO | `F[x,x,x]` uses `F''/3!` (`x`) not `F''/2!` (`3x`) |
| V2H_03_broken_branch | FAMILY_NONZERO | majority 4/5 ZERO | `F[x,y,y]` copied from `F[x,x,y]` (`2x+y`) |
| V2H_04_mixed_latent_F | FAMILY_UNKNOWN | all local edges ZERO | `t**3` and `t**2` glued; disconnected; `latent_compatible=False` |
| V2H_05_path_inconsistent_recurrence | FAMILY_NONZERO | all 5 reconstructions ZERO | both recurrences claimed equal to `2x+y`; `(y,y)` path is `x+2y` |
| V2H_06_wrong_derivative_order | FAMILY_NONZERO | majority 4/5 ZERO | triple node filled with `F'(x)=3x**2` not `F''(x)/2!` |
| V2H_07_wrong_degeneracy_variable | FAMILY_NONZERO | majority 4/5 ZERO | claimed `y→x`; listed diagonal is `y→w` |
| V2H_08_pole_sensitive_false_confluence | FAMILY_NONZERO | majority 4/5 ZERO | polar `(x**3-y**3)/(x-y)**2` claimed → `3x**2`; dirs infinite |

Lying about connected/latent on V2H_04 makes `compose_family_verdict` return
FAMILY_ZERO. That is the attack, not a pass.

## Remaining risks

- Empty or UNKNOWN required edges are not FAMILY_ZERO (`4 ZERO + 1 UNKNOWN`
  stays FAMILY_UNKNOWN). A later composer that majority-votes branches is a
  false certification against this suite.
- Reconstruction compares members to the true DD from node multiplicities
  (`F^{(k)}/k!` with `k = multiplicity-1`), not the family's self-reported
  factorial or derivative order.
- Pole-sensitive generic is rational, not polynomial; directional `sympy.limit`
  must keep the infinite/disagreeing witness. Do not cancel one `(x-y)` and
  call the rest a derivative.
- Do not declare extra assumptions, convert timeout to ZERO, or weaken
  residuals to always-NONZERO: `V2H_TRUE_HERMITE_FAMILY` must stay FAMILY_ZERO.
