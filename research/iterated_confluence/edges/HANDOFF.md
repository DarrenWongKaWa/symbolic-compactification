# HANDOFF — Track V3-D (one-parameter edge verifier)

Parent: `dcfb90cac087a47241aced2dc0c3b851f1a12e21`
Branch: `work/v3-edge-verifier`
Owned: `research/iterated_confluence/edges/**`, `tests/test_ic_edges.py`

No LLM. No Guo-specific identities. Timeout and size-guard are UNKNOWN,
never ZERO. Numeric agreement is not exact.

## What was implemented

`certify_one_parameter(source, target, variable, target_value, symbols, functions=None)` under `research/iterated_confluence/edges/`.

```python
from research.iterated_confluence.edges import certify_one_parameter

result = certify_one_parameter(source, target, variable, target_value, symbols, functions)
# result.verdict           ZERO | NONZERO | UNKNOWN
# result.provenance        deciding step
# result.full_ops          max count_ops of the unsplit pair
# result.local_ops         max count_ops after certified split
# result.reduction_ratio   local_ops / full_ops
# result.steps             full cascade trace
```

Critical difference vs V2 rescore `OPS_SKIP=250` on FULL expressions:

1. Split spectators first (`research.iterated_confluence.spectator.split_edge`
   when importable, else `split_multiplicative` / AppliedUndef peel).
2. Size-guard and `check_limit` apply to LOCAL kernels, not the unsplit pair.
3. If split is not certified, `certify_edge` may still run on the original
   pair only when full ops ≤ 250; otherwise UNKNOWN (never ZERO).
4. Split is not skipped because full ops > 250.

Cascade on the local pair: special-function identities, `check_limit`
(substitution / cancel / together / series / L'Hôpital / budgeted
`sympy.limit`), then `certify_edge`. `sympy.limit` is not called from this
package; `check_limit` skips it when `count_ops(F) > 80` and otherwise
runs it under `run_with_budget`.

## Tests

`tests/test_ic_edges.py`

- cubic Newton: `lim_{y→x} (x**3-y**3)/(x-y) == 3*x**2` is ZERO
- corrupted: `== 4*x**2` is NONZERO
- timeout / size-guard / huge unsplit expr are UNKNOWN, never ZERO
- spectator: `h1(x)*((x**3-y**3)/(x-y))` vs `h1(x)*3*x**2` is ZERO via split+limit
- full ops > 250 with AppliedUndef spectators still ZERO on the local kernel
- source-ban: no `guo_map` pairing, no `Phi_Gamma`, no `if family_id == guo`
- no direct `sympy.limit` on `count_ops > 80` without budget

Command: `.venv/bin/python -m pytest tests/test_ic_edges.py -q`

Do not run the 573-op Guo 5-branch pair in unit tests.

## Remaining risks

- `split_edge` is optional; until V3-C merges, the path is
  `split_multiplicative`. Polynomial gcd on large pairs still fails closed
  at factor `_GCD_OPS_CAP=80`; AppliedUndef peel has no that cap.
- Local cascade is skipped when local `count_ops > 200` (`certify_edge`
  `OPS_CAP`). A still-huge kernel after peel stays UNKNOWN, not ZERO.
- `check_limit` series / valuation / L'Hôpital are capped; essential
  singularities time out as UNKNOWN.
- This package certifies one local edge. It does not emit `PATH_ZERO` or
  `FAMILY_ZERO`.

## COMMIT SHA

Parent `dcfb90cac087a47241aced2dc0c3b851f1a12e21`.
Branch `work/v3-edge-verifier`.
Message: `Add one-parameter edge verifier with split-first cascade.`
