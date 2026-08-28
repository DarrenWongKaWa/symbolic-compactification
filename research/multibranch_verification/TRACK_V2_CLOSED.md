# Track V2 closed — multibranch-hermite-verifier-v1

## Generic suite

`GENERIC_FAMILY_SUITE.md`: **false FAMILY_ZERO = 0**. Cubic 3-branch and
5-branch toys FAMILY_ZERO. Majority 4 ZERO + 1 UNKNOWN is FAMILY_UNKNOWN.
Corrupted branch FAMILY_NONZERO.

## Frozen Guo 5-branch / Hermite rescore

7 families, **no new LLM**.

```
FAMILY_ZERO:     0
FAMILY_NONZERO:  0
FAMILY_UNKNOWN:  7
```

**CASE H-C.** Verification remains insufficient for five-branch / Hermite
families. Local 2-member confluence edges inside the mixed 4-member family
(`guo-p2-s2-i4`) are ZERO (2 edges) but the family is UNKNOWN (one
substitution edge + composition rule). 5-branch star edges were not
discharged (ops skip on 573-op generic kernels; repeated-node edges
UNKNOWN). Recurrence without explicit F is UNKNOWN, not ZERO.

## Track D2

**LOCKED** for Guo. Do not run new Hermite proposers on Guo until a family
is FAMILY_ZERO or FAMILY_NONZERO.

## Freeze

Family schema, graphs, edge certifier, recurrence, composition, router,
generic suite, adversarial suite, Guo family rescore.
