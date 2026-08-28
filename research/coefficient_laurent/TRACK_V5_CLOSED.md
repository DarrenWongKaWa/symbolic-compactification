# Track V5 closed — coefficient-space-laurent-v1

## Generic suite

false ZERO = 0. t^0 match with surviving t^{-1} is NONZERO.
LEVEL A atom-series is not hop ZERO. Cache: G0014 keys ≠ G0016 keys.

## Frozen generic→diagonal hops

18 hops (6 families × 3 siblings). **No 27k-op together.**

```
ZERO:     0
NONZERO:  0
UNKNOWN: 18
case: **L-D**
```

Primary `G0016→G0013`: process timeout 40 s in rescore (LEVEL_A).
Direct sparse run: negative Laurent coeffs **expand to 0** (LEVEL B);
`C_0` vs G0013 is **not** `expand==0` (990 vs 327 ops). Unbounded
`cancel` is forbidden (>400 ops). Numeric probe at a regular point
agrees to ~1e-27 relative error — **not ZERO**.

Analog `G0023→G0020`: LEVEL_B, negatives ZERO, C_0 UNKNOWN,
max core ops 1696.

Sibling ell-hops: negatives UNKNOWN, cores ~10k ops.

Families remain FAMILY_UNKNOWN. Track D2 **LOCKED**.

## Decision

**STOP_VERIFICATION_LINE** for coefficient-space LEVEL C on this hop.
Bottleneck is **C_0 algebraic identity** (coefficient simplification),
not atom expansion and not 27k together. Do not open D2.
