# HANDOFF — Track V3 Subagent V3-C (spectator split)

Parent: `dcfb90cac087a47241aced2dc0c3b851f1a12e21`
Branch: `work/v3-spectator-split`

Commit message: `Add exact spectator split with reconstruction for V3 edges.`

## Owned

- `research/iterated_confluence/spectator/**`
- `tests/test_ic_spectator.py`

Did not edit `schema.py`, `FROZEN_INPUTS_V3.json`, freeze scripts,
historical runs, or Track V `factor/`. No LLM. No Guo gold identities.

## What was implemented

`split_edge(A, B)` under `research/iterated_confluence/spectator/`.

Wraps Track V:

```python
from research.scalable_verification.factor import split_multiplicative, split_additive
```

Track V peels common `AppliedUndef` factors then `gcd` with ops cap 80.
This wrapper **extends** that split with an independent reconstruction
gate and ops accounting. It does not copy the gcd implementation.

Certification is fail-closed:

1. call Track V multiplicative, then additive
2. reject units (`±1`) and zero as spectators
3. require exact reconstruction **before** returning a local kernel
   - multiplicative: `S * A_local == A` and `S * B_local == B`
   - additive: `S + A_local == A` and `S + B_local == B`
4. if reconstruction fails, `certified=False` and the Track V kernel is
   discarded (`mode="none"`, `S=1`, locals = originals)
5. size-guard / gcd failure does not invent `S`

`count_ops` is `sympy.count_ops(..., visual=False)`.
`split_report` is a JSON-serializable view (`str` of expressions).

False decomposition acceptance = 0.

This package provides the splitter only. It does not claim success on
Guo; 573-op family kernels belong to `eval/`.

## Tests

`tests/test_ic_spectator.py`

Command: `.venv/bin/python -m pytest tests/test_ic_spectator.py -q`
Result: **25 passed**

## Remaining risks

- Track V skips polynomial gcd when `count_ops(A)+count_ops(B) > 80`.
  AppliedUndef peel still runs first on that path; polynomial spectators
  above the cap stay uncertified rather than guessed.
- Reconstruction uses `cancel` / `together`, not `sympy.simplify`.
  Expressions that are equal only after a named identity stay uncertified.
- Additive constant `±1` is treated as a unit spectator and rejected even
  if Track V additive would report it as a common addend.
- Callers must honor `certified`. Uncertified payloads are not proving
  kernels.

## COMMIT SHA

Parent `dcfb90cac087a47241aced2dc0c3b851f1a12e21`.
Branch `work/v3-spectator-split`.
