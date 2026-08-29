# Polygamma domain (R2)

Parent: `adbfd9f`. Branch `work/r-polygamma-domain`. Not Track V6.
No LLM. Track D2 LOCKED. Domain CERTIFIED is **not** remainder CERTIFIED
and is **not** hop ZERO.

```python
from research.remainder_certification.polygamma import (
    classify_polygamma_domain,
    classify_motivating_form,
)
```

## Pole set (DLMF / SymPy, not a case-study table)

Integer order `k` of `polygamma(k, z)`:

| `k` | domain | poles of the argument |
|---|---|---|
| `k >= 0` | meromorphic | `{0, -1, -2, …}` (DLMF 5.15.1, 5.2, 5.15 chain) |
| `k = -1` | meromorphic / log-singular | same set (SymPy `loggamma(z) - log(2π)/2`) |
| `k <= -2` | **entire** | empty (SymPy Espinosa–Moll; `expand_func` is a polynomial in `z` plus `∂_s ζ(s,z)` at `s=k+1≤-1`; DLMF 25.11.2 Bernoulli) |

SymPy `polygamma.eval` returns `zoo` at nonpositive integers **for every**
`n`, including `k <= -2`. That eval is **not** a pole certificate for
entire orders and is not used here.

## Affine neighborhood

Poles on `Z_<=0` are isolated. If `z0` is certified not a pole and `c`
is finite, there exists `δ > 0` such that `|t| < δ` implies
`z0 + c t ∉ Z_<=0`. Existence of `δ` is a class-B isolation lemma, not
genericity. A real-only path is not assumed.

## Predicates (never silently inserted)

| predicate | CERTIFIED? |
|---|---|
| `z0` not identically in `{0,-1,-2,…}` | **no** (too weak) |
| `Im(z0)` identically nonzero | yes (then `dist ≥ \|Im\| > 0`) |
| `dist(z0, Z_<=0)` certified positive | yes |
| declared A: `z0 not in Z_<=0` | yes |
| `k <= -2` entire | yes (any finite `t`) |
| undeclared genericity / `β>0` physics | **no** → `ASSUMPTION_REQUIRED` |

## Domain verdicts

- **CERTIFIED** — predicates true from A/B; neighborhood usable for a
  later remainder CERTIFIED. This package does **not** emit remainder
  CERTIFIED (`as_remainder_fields` keeps remainder UNKNOWN on this branch).
- **ASSUMPTION_REQUIRED** — needs undeclared C/D. Successful fail-closed
  outcome. Genericity is listed under `missing_assumptions`, never inserted.
- **NONANALYTIC** — `z0` identically a pole (`k >= -1`).
- **UNKNOWN** — unparsed / unproved.

## Live check (declared assumptions only)

Form: `(βγ ± I β μ ∓ I β ε + π)/(2π)` with free **real** symbols
(`real=True`; not positive; not nonzero).

- not identically in `Z_<=0`: TRUE (B)
- `Im = ±β(μ−ε)/(2π)` identically nonzero: UNPROVED
- `dist` certified positive: UNPROVED
- `β=0` gives `z0=1/2` (regular); `μ=ε` still allows real poles

**Verdict: `ASSUMPTION_REQUIRED`, not CERTIFIED.**

`β>0` is class D unless declared, and even as declared A it is not
enough (`μ=ε` remains). Do not insert genericity.

## What this package does not do

- Emit remainder CERTIFIED or mint hop ZERO
- Restore retracted LEVEL C
- Unlock Track D2
- Treat “not identically a pole” as pole-exclusion
- Assume physics positivity
- Call CAS `series` / `limit` as a domain proof
