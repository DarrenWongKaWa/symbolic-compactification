# Owner: V2 — local kernel factorization

Exact spectator-factor split. False decomposition acceptance = 0.

Only sympy `gcd` / `factor` / `cancel`. No physics inference. No `simplify`.

## Public API

```python
from research.scalable_verification.factor import (
    split_multiplicative,
    split_additive,
)

split_multiplicative(A, B) -> {S, A_local, B_local, certified, note}
split_additive(A, B)       -> {S, A_local, B_local, certified, note}
```

- Multiplicative: `A = S * A_local`, `B = S * B_local` with
  `S = gcd(num A, num B) / gcd(den A, den B)`.
- Additive: `A = S + A_local`, `B = S + B_local` with `S` the same-sign
  min-coefficient common part of additive terms.
- Units (`±1`) and zero are not spectators. If there is no exact common
  factor, `certified=False` and the function does not guess.

## Certification guards

A split is certified only if reconstruction holds **and**:

- multiplicative: `num(S)` divides both numerators and `den(S)` divides
  both denominators (no invented poles, no coefficient over-claim);
- additive: every coefficient of `S` is contained in both sides with the
  same sign and no larger magnitude.

## Negatives (must not certify the mismatched part)

| class | example | required behaviour |
|---|---|---|
| wrong sign | `(x+1)` vs `(x-1)`; `x` vs `-x` additively | `certified=False` or `S` omits the signed mismatch |
| factor missing from one side | `x*y` vs `z` | `certified=False`; extra factor never enters `S` |
| coefficient mismatch | `2*(x+1)` vs `3*(x-1)`; `2*x` vs `3*y` | do not put the larger/mismatched coeff into `S` |
| pole mismatch | `1/(x-1)` vs `1/(x+1)` | `certified=False`; dens must both be divisible by `den(S)` |
