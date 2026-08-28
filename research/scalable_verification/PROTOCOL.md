# Track V — Scalable compositional verification

Question: are **already-proposed** representation hypotheses correct
once verification is no longer a giant global `sympy.limit`?

No new LLM calls on this track.

## Frozen inputs

`FROZEN_INPUTS.json` lists every hypothesis that may be rescored.
Historical run JSON under `research/grounded_proposer/runs/` and
`research/representation_invention/llm/runs/` is **read-only**.

## Causal labels

If the **same frozen output** changes UNKNOWN → ZERO because the
verifier improved: **V_GAIN**. Never D_GAIN.

COMPILE_FAILURE → ZERO because compilation improved: **C_GAIN**.

Timeout / size-guard is UNKNOWN, never ZERO.

## Gain accounting

| label | meaning |
|---|---|
| V_GAIN | new ZERO/NONZERO from the same compiled obligation |
| C_GAIN | previously uncompiled obligation now compiles then verifies |
| NO_GAIN | verdict unchanged |

## Do not

- Guo-specific ZERO identities
- mutate frozen runs
- retune SOL
- open Track D until `TRACK_V_CLOSED.md` exists
