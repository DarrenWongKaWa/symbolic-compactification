# Protocol — symbolic remainder certification

Parent: `9da52fb` (problem + assumption freeze). Not Track V6.
No LLM. No Guo identity table. Track D2 LOCKED.

## Shared files (orchestrator)

`PROBLEM_STATEMENT.md`, `ASSUMPTION_POLICY.md`, `schema.py`,
`PROTOCOL.md`, `OWNERS.md`, `STATUS.md`.

Do not edit frozen V3/V4/V5 runs, SOL, B9, LGG, or hop engine
timeouts. Do not retune ell-hops. Do not promote G0016→G0013 to
ZERO in this cluster.

## Order of evidence

1. Generic theorem/certificate for `f(z0 + c t)`.
2. Generic test suite. False CERTIFIED remainder = 0.
3. Symbolic affine class (motivating form, **not** Guo atoms).
4. Frozen G0016 14 atoms, independently, after the generic method
   is frozen. Do not reuse certificates across atoms without full
   text-hash identity.
5. LEVEL C reconstruction of the hop only if every required atom
   remainder is CERTIFIED **and** independent review passes.
6. Ell-hops only after the primary hop remainder is decided.

## Remainder vs hop

`RemainderCertificate.verdict == CERTIFIED` is not hop ZERO.
Hop composition remains `research.coefficient_laurent.schema.compose_hop_verdict`.
LEVEL B coefficients + remainder UNKNOWN must stay UNKNOWN
(`test_forbidden_ignore_remainder_regression`).
