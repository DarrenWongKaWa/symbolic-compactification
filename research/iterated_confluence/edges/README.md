# Owner: V3-D — one-parameter edge verifier

Typed check of one local one-parameter confluence edge **after** spectator
split. Timeout and size-guard are UNKNOWN, never ZERO. Reuses Track V
`check_limit` / `split_multiplicative` and Track V2 `certify_edge`. No Guo
pairing. No LLM.

## Public API

```python
from research.iterated_confluence.edges import certify_one_parameter

result = certify_one_parameter(
    source, target, variable, target_value, symbols, functions=None,
)
# result.verdict           ZERO | NONZERO | UNKNOWN
# result.provenance        deciding step
# result.full_ops          max count_ops of the unsplit pair
# result.local_ops         max count_ops after certified split
# result.reduction_ratio   local_ops / full_ops
# result.steps             full cascade trace
```

## Cascade (provenance per step)

1. spectator split first (`split_edge` if importable, else
   `split_multiplicative` / AppliedUndef peel) — **not** skipped when full
   ops > 250
2. size-guard on **local** kernels (`OPS_CAP=200`); uncertified split and
   full ops > 250 → UNKNOWN without running the unsplit pair
3. local special-function identities (`prove_local`) when polygamma/gamma
   are present
4. `check_limit` on local kernels (`sympy.limit` only under budget, and
   skipped when `count_ops > 80`)
5. `certify_edge` fallback (substitution, cancel/together, series,
   derivative reduction)
6. else UNKNOWN
