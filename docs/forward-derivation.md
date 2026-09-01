# Forward derivation

Give the engine a current expression, a candidate, and declared symbols.
It checks whether the candidate is exactly equal to the current expression.

```
current + assumptions + candidate
    -> verify
    -> ZERO | NONZERO | UNKNOWN | PARSE_FAILURE | ...
```

Promote only on `ZERO`. `NONZERO` keeps the residual and a counterexample.
`UNKNOWN` does not promote.

A human, a CAS, or an LLM may write `candidate.txt`. None of those sources
is a certificate. The proposer path is optional.

## Accepted step

```bash
cp -R examples/forward/exact-step /tmp/ssc-exact
symbolic-compactification verify /tmp/ssc-exact
```

`x**2 + 2*x + 1` versus `(x + 1)**2` is `ZERO`.

## Refused step

```bash
cp -R examples/forward/refused-step /tmp/ssc-refused
symbolic-compactification verify /tmp/ssc-refused
```

The sign-flipped candidate is `NONZERO`. Do not promote it.

## Loop

`inspect` → write a candidate → `verify` or `step` → on `ZERO`, the
candidate becomes current → next step. See `AGENTS.md` for the agent
contract.
