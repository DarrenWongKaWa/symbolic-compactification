# Method v2 architecture

Frozen with `METHOD_DECISION.md`. Engine 0.3.0 semantics unchanged.

```
Human: scientific_context, symbols, assumptions
                ↓
     Orchestrator (state, expand, verify, continue)
                ↓
 Isolated SCIENTIFIC_STRUCTURE_PROPOSER  (one; not an ensemble)
                ↓
     expand definitions → closed candidate
                ↓
     verify_equivalent  ZERO | NONZERO | UNKNOWN
                ↓
     certified current  (promote only ZERO)
                ↓
     loop until step budget (do not stop at first D1/D2 ZERO)
```

Production `proposer=main` remains the default CLI. Method v2 lives under
`research/method_v2/` until DEV_DECISION promotes it.

## What v2 does not do

- No new ZERO rules for limits, series, polygamma recurrences, or
  Piecewise deletion.
- No three-proposer panel.
- No custom IR.
- No promotion of UNKNOWN.
