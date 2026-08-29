# Owner: R3 — pole-free affine neighborhood

Existence of some `delta > 0` such that `|t| < delta` keeps the path
`z0 + c t` inside a pole-free disk. Not an optimal delta. Not remainder
`CERTIFIED`. Not hop ZERO. Track D2 stays LOCKED. No LLM.

## Public API

```python
from research.remainder_certification.neighborhood import (
    certify_neighborhood,
    empty_pole_set,
    nonpositive_integer_poles,
)

cert = certify_neighborhood(z0, c, assumptions=..., pole_set=..., function_family=...)
# cert.verdict  CERTIFIED_NEIGHBORHOOD | ASSUMPTION_REQUIRED | UNKNOWN
```

`pole_set` is a callback `z0 -> PoleQuery` (or a dict with `kind`,
`distance`, `isolated`, `name`) so R2 can plug in a polygamma domain
query later.

Shipped defaults:

| family / `pole_set` | poles |
|---|---|
| `exp` / `entire` / `empty_pole_set` | empty (entire) |
| `polygamma` (and the meromorphic default) / `nonpositive_integer_poles` | `{0,-1,-2,…}` |

Unknown families without a callback are UNKNOWN, not certified.

## Theorem

Let `P ⊂ C` be closed and discrete (or empty). If `dist(z0, P) = rho > 0`
(equivalently: `P` isolated and `z0 ∉ P`), the open disk `|z - z0| < rho`
is pole-free. The affine path satisfies `|z0 + c t - z0| = |c||t|`. Any
choice with `0 < |c| * delta < rho` keeps the path inside the disk. An
explicit sufficient choice is

```
delta = rho / (2 * (|c| + 1))
```

because `|c| / (|c|+1) < 1`, hence `|c| * delta < rho/2 < rho`. If `P`
is empty, `rho = ∞` and `delta = 1` is sufficient. If `c = 0` the path
is the point `z0`; the neighborhood reduces to `z0` itself and any
`delta > 0` works once `z0 ∉ P`.

Existence of some delta is the certificate. The formula is not claimed
optimal.

## Assumptions

Declared class-A pole-exclusion (or Im(z0) ≠ 0 / Re(z0) > 0 for
`Z_<=0`) plus isolation is class B and may yield
`CERTIFIED_NEIGHBORHOOD`. Symbolic `z0` with no pole-exclusion is
`ASSUMPTION_REQUIRED` or `UNKNOWN` per ASSUMPTION_POLICY. Class C/D is
not inserted and cannot mint `CERTIFIED_NEIGHBORHOOD`. A proved pole at
`z0` is UNKNOWN (no pole-free disk about `z0`).
