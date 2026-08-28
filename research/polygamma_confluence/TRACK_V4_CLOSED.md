# Track V4 closed — polygamma-local-identity-v1

## Method

Per-atom series of polygamma rational terms, then Laurent `t^0`
comparison. No Guo identities. Timeout / together-ops cap → UNKNOWN.

## Generic tests

`tests/test_pg_engine.py`: Newton polygamma ZERO; wrong order not ZERO;
cubic Newton ZERO.

## Frozen Guo hops

After fixing a cache-key bug (must hash member *text*, not missing
`text_sha256`):

```
FAMILY_ZERO:     0
FAMILY_NONZERO:  0
FAMILY_UNKNOWN:  7
ZERO edges:     20
case: **J-C**
```

**V_GAIN (edge, not family):** every diagonal→triple one-parameter hop
is ZERO (`atom_series:t0`, 12 atoms, `c0` ops 47, together 1592–3845).
That is the 327-op class Track V3 timed out on as a whole kernel.

**Still UNKNOWN:** generic→diagonal hops (567-op G0016/G0023). Together
ops 27327 (size-guard) or 30 s process timeout.

Two-step covering paths therefore PATH_UNKNOWN. Families remain
FAMILY_UNKNOWN (R2: no auto path-consistency). Track D2 **LOCKED**.

s2-i4 two-member pairs ZERO by the same engine (2 atoms).

## Decision

**CONTINUE_VERIFICATION** only for generic→diagonal (567-op) comparison,
not another path enumerator. Do not open D2. Do not start a Hermite
proposer.
