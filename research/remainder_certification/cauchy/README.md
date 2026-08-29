# R4 — Cauchy remainder order bound

Generic Cauchy-estimate remainder certificate **when a pole-free disk
is already certified**. This package does **not** certify a disk
(that is R3). A missing neighborhood is `UNKNOWN`, including for
entire families such as `exp`.

No LLM. Not a hop verifier. Remainder `CERTIFIED` is not hop `ZERO`.
Track D2 stays **LOCKED**. Do not revive retracted LEVEL_C ZERO.

```python
from research.remainder_certification.cauchy import cauchy_remainder_bound
```

## Estimate

Let `f` be holomorphic on a certified open disk `|z - z0| < rho`.
Choose a Cauchy contour `0 < r < rho` and a perturbation `|c t| < r`.
Taylor remainder `R_N` of `f(z0 + c t)` satisfies

```
|R_N(t)| <= M * q(t)**(N+1)
```

with `q = |c t|/r = |c| |t| / r`, or equivalently `|c| |t| / rho'`
for a strict subradius `rho' = r`. The integral form

```
|R_N(t)| <= M_r * q**(N+1) / (1-q)     (|c t| < r)
```

is equivalent for order control: on `|c t| <= r/2` one has
`1/(1-q) <= 2`, which is absorbed into a still-finite `M`.

Goal: `R_N(t) = O(t**(N+1))`, not a sharp number.

If `r` is omitted and `rho` is a proved finite positive radius, the
contour `r = rho/2` is used. That is a contour choice inside the
certified disk, not a new neighborhood claim.

## Finiteness of `M`

`M` may remain symbolic if **finiteness is certified**: holomorphic on
a compact disk `|z - z0| <= r` contained in the certified open disk
implies bounded (`M < infinity`, class B derived).

`M < infinity` without that lemma is class C/D
(`ASSUMPTION_POLICY.md`). Verdict is `UNKNOWN` or
`ASSUMPTION_REQUIRED`, never `CERTIFIED`.

## Fail-closed cases (not `CERTIFIED`)

| input | verdict |
|---|---|
| neighborhood missing / not `CERTIFIED_NEIGHBORHOOD` | `UNKNOWN` |
| neighborhood `ASSUMPTION_REQUIRED` | `ASSUMPTION_REQUIRED` |
| `r >= rho` (closed disk not strictly inside) | `UNKNOWN` |
| `N` missing | `UNKNOWN` |
| `M` finiteness unproved | `UNKNOWN` / `ASSUMPTION_REQUIRED` |

Positive control: `exp` on **any certified disk** (R3 may certify
every finite radius; R4 still requires that certificate).

Small-`t` is an existence certificate `|c t| < r`, and `|t| < r/|c|`
when `|c|` is proved positive — not an undeclared “sufficiently small t”.
