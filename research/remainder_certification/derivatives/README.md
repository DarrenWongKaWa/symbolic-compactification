# Polygamma derivative chain (R6)

Parent: `adbfd9f`. Branch `work/r-polygamma-derivatives`. Not Track V6.
No LLM. No case-study coefficient list. Track D2 LOCKED.

Taylor coefficients of `polygamma(k, z0 + c t)` from the derivative
identity supported by the symbolic backend (SymPy `diff` /
`polygamma.fdiff`, DLMF 5.15). Remainder CERTIFIED is **not** emitted
here. Holomorphicity at `z0` is owned by **R2** (polygamma domain) and
**R3** (neighborhood).

```python
from research.remainder_certification.derivatives import (
    polygamma_diff,
    polygamma_taylor_coefficient,
    polygamma_taylor_coefficients,
)
```

## Identity

```
d/dz polygamma(k, z) = polygamma(k+1, z)
```

Checked against `sympy.diff` for orders `k = 0, 1, 2`. Iterating in
the derivative order:

```
d^r/dz^r polygamma(k, z) = polygamma(k+r, z)
```

## Taylor coefficient

When `polygamma(k, ·)` is holomorphic at `z0`,

```
[t^r] polygamma(k, z0 + c t) = polygamma(k+r, z0) * c^r / r!
```

Construction differentiates with `sympy.diff` and scales by `c^r / r!`.
It does **not** call CAS `series`. Tests compare the result to
`Expr.series` for `k, r ∈ {0, 1, 2}`.

## Domain (R2/R3)

The formula is a holomorphic Taylor coefficient. Poles of polygamma
(`z0 ∈ {0, −1, −2, …}` for order `k ≥ 0`) and a disk around `z0` that
the path `z0 + c t` stays inside are **not** decided in this package.
`domain_owner` is `R2/R3`.

## What this package does not do

- Emit `RemainderCertificate.verdict == CERTIFIED`
- Mint hop ZERO or restore retracted LEVEL C
- Unlock Track D2
- Encode a case-study energy kernel or a hardcoded coefficient table
- Call the hop composer
