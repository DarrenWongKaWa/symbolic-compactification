# Generic remainder suite (spec)

False CERTIFIED remainder = 0. Numeric agreement is not CERTIFIED.
Do not run Guo atoms here.

## Positive controls

| id | object | expected remainder |
|---|---|---|
| A-exp | `exp(z0 + c t)` | CERTIFIED (entire) |
| B-log | `log(z0 + c t)` with declared `z0` in a pole-free disk of `log` | CERTIFIED or ASSUMPTION_REQUIRED if disk missing |
| C-rational | rational analytic away from poles | CERTIFIED when disk proved |
| D-pg-safe | `polygamma(k, z0+c t)` with explicit safe `z0` (e.g. `1`) | CERTIFIED neighborhood + O(t^{N+1}) |
| E-pg-declared | symbolic `z0` with **declared** pole-exclusion | CERTIFIED only from A/B |
| F-prefactor | `t^{-m}` times analytic Taylor, `N >= m` | remainder vanishes through `t^0` |

## Negative / UNKNOWN controls

| id | object | expected |
|---|---|---|
| nA-pole | `z0` at a pole | NONANALYTIC, not CERTIFIED |
| nB-symbolic | symbolic `z0`, no pole-exclusion | ASSUMPTION_REQUIRED or UNKNOWN |
| nC-cross | path can hit a pole for arbitrarily small t | not CERTIFIED |
| nD-short | `N` insufficient vs `t^{-m}` | not CERTIFIED vanishing |
| nE-hidden | hidden denominator zero | not CERTIFIED |
| nF-unprovable | unprovable symbolic domain | UNKNOWN |

Runner lands after R1–R11 merge. `false_CERTIFIED` must be 0.
