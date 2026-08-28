# Owner: V2-B — local edge certifier

Typed check of one family edge. Cascade; timeout and size-guard are
UNKNOWN, never ZERO. Reuses Track V packages. No Guo pairing. No LLM.

## Public API

```python
from research.multibranch_verification.edges import certify_edge

result = certify_edge(
    source_expr, target_expr, relation, variable, target_value,
    symbols, functions,
)
# result.verdict     ZERO | NONZERO | UNKNOWN
# result.provenance  deciding step
# result.steps       full cascade trace
```

Relations: `substitution`, `limit`, `one_parameter_confluence`,
`repeated_node_confluence`, `derivative`, `dd_recurrence`,
`hermite_dd_recurrence`.

## Cascade (provenance per step)

1. `substitution` — `source.xreplace({variable: target_value})` finite
2. `cancel` — `cancel` then (if a point is given) substitute
3. `split_multiplicative` — exact spectator split (Track V factor)
4. `together` — `together` / `cancel` / normalize
5. `check_limit` — Track V confluence, limit-like relations only
6. `derivative` — `F'(node)` (and `F''(node)/2` on dd/hermite)
7. `dd_cert` — Track V Newton / Hermite certificates, dd/hermite only
8. else `UNKNOWN`

Positives: cubic Newton / confluence toys. Negatives: wrong target, pole.
