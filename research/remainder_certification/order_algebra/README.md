# Order algebra — `O(t^k)` and `o(t^k)` as `t → 0`

No LLM. Typed Landau classes for remainder × prefactor. This package
does not decide hops and does not unlock Track D2. A remainder that
vanishes through `t^0` is **not** hop ZERO.

```python
from research.remainder_certification.order_algebra import (
    O, o, add, mul, div, exact_power, remainder_times_prefactor,
    sufficient_expansion_order, vanishes_through_constant,
)
```

## Landau rules (`t → 0`)

Smaller exponent dominates.

| operation | result |
|---|---|
| `O(t^a) + O(t^b)` | `O(t^{min(a,b)})` |
| `o(t^a) + o(t^b)` | `o(t^{min(a,b)})` |
| `O(t^a) + o(t^a)` | `O(t^a)` |
| `O(t^a) * O(t^b)` | `O(t^{a+b})` |
| `o(t^a) * O(t^b)` | `o(t^{a+b})` |
| `t^m * O(t^k)` | `O(t^{m+k})` |

No heuristic truncation: `O(t^2) + O(t^2) = O(t^2)`, never `o(t^2)`.
Two exact monomials of the same order are `O`, not cancelled.

## Remainder × prefactor

A holomorphic Taylor remainder after degree `N` is `O(t^{N+1})`.
Times a polar prefactor `t^{-m}` (coefficient 1, certified nonzero):

```
t^{-m} * O(t^{N+1}) = O(t^{N+1-m})
```

After keeping Laurent terms through `t^0`, that remainder vanishes as
`t → 0` iff `N+1-m >= 1`, i.e. `N >= m`.

Examples:

- `O(t^2) + O(t^3) = O(t^2)`
- `t^{-3} * O(t^4) = O(t)` → vanishes (`4-3 = 1 >= 1`)
- `t^{-3} * O(t^3) = O(1)` → does **not** vanish
- `N` insufficient vs pole order `m` (`N+1-m <= 0`) → not certified vanishing
  (`N = m-2` leaves a polar `O(t^{-1})`)

`KEEP_THROUGH = 0`. `O(t^k)` vanishes iff `k >= 1`. `o(t^k)` vanishes
iff `k >= 0` (`o(1) → 0`). `O(1)` does not vanish.

## Division

`div(numer, denom)` is `UNKNOWN` unless `denom` is an exact monomial
whose leading coefficient is certified nonzero. A bare `O(t^p)` or
`o(t^p)` denominator is not a certified leading order.

## Composition

`compose` / `compose_remainder` substitute a certified inner class into
a certified analytic expansion `f(w) = Σ c_n w^n + O(w^{N+1})`.
The inner must tend to 0. Negative outer exponents require a certified
exact inner valuation: an `O` upper bound on `w` does not bound `w^{-p}`.

Present expansion coefficients that are not certified nonzero stay as
`O` summands. They are never dropped.

## Fail-closed

Ill-typed operands, mixed variables, uncertified division, and inner
classes that need not tend to 0 return `UNKNOWN`. `UNKNOWN` is a
successful verifier outcome, not a license to truncate.
