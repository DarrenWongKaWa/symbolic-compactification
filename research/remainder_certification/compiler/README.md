# Atom-local remainder compiler (R8)

Parent: `adbfd9f`. Branch `work/r-cert-compiler`. Not Track V6.
No LLM. Track D2 LOCKED.

Compiles one function atom, an affine argument, a domain certificate,
and a Taylor order into a `RemainderCertificate`. This is **not** a
hop certificate: `verdict == CERTIFIED` is not hop ZERO and does not
restore retracted LEVEL C.

```python
from research.remainder_certification.compiler import compile_remainder

cert = compile_remainder(
    atom,
    affine_argument,
    domain_certificate,
    taylor_order,
    affine=...,          # optional
    neighborhood=...,    # optional
    cauchy=...,          # optional
    polygamma=...,       # optional
    analysis=...,        # optional
)
```

## Fail closed

Sibling packages `affine`, `neighborhood`, `cauchy`, `polygamma`,
`analysis` may be absent in this worktree. Missing import or missing
`compile_step` is UNKNOWN. The compiler does not fake CERTIFIED from
a family name (including entire functions).

Unit tests inject callables for those steps. Each callable receives a
payload dict and returns a dict (or an object with `to_dict`).

Package entrypoint, when present: `compile_step(payload) -> dict`.

CERTIFIED requires:

1. nonnegative integer Taylor order
2. affine argument (`ok`, from the affine step or structured fields)
3. domain verdict CERTIFIED (input and/or analysis/polygamma)
4. neighborhood step present with `CERTIFIED_NEIGHBORHOOD`
5. Cauchy step present and `ok`
6. assumptions only class A/B
7. nonempty `domain_conditions`

Neighborhood must use `CERTIFIED_NEIGHBORHOOD`, not remainder
`CERTIFIED`. Class C/D (and unclassified) cannot validate as
CERTIFIED. Empty domain conditions are filled with an explicit
unproved condition and cannot stay CERTIFIED.

NONANALYTIC from the domain is preserved (path hits a singularity).
Missing neighborhood/Cauchy is UNKNOWN, not CERTIFIED.

## What this package does not do

- Global kernel logic, hop composition, or hop ZERO
- Silent genericity or physics positivity
- Unlock Track D2
- Substitute for R1–R7 proofs; it only assembles their results
