# HANDOFF — Track V3-F (order-of-limits / path consistency)

Parent: `dcfb90cac087a47241aced2dc0c3b851f1a12e21`
Branch: `work/v3-path-consistency`
Owned: `research/iterated_confluence/consistency/**`, `tests/test_ic_consistency.py`

No LLM. Did not edit schema, freeze, or runs.

## What was implemented

Public API:

```python
from research.iterated_confluence.consistency import (
    check_two_paths,
    family_zero_blocked,
    CONSISTENT_ZERO,
    INCONSISTENT_NONZERO,
    CONSISTENCY_UNKNOWN,
)

result = check_two_paths(expr, path_a_steps, path_b_steps, symbols=None)
# result.verdict / result.provenance  (PathConsistencyObligation)
```

`check_two_paths` evaluates each path as an iterated one-parameter limit
(substitution → together/cancel → valuation → series → L'Hôpital → Newton
first DD → guarded `sympy.limit`). Cheap finite candidates are confirmed
with `check_limit`. The two results are compared with `_expr_equal`.

| verdict | meaning |
|---|---|
| `CONSISTENT_ZERO` | both iterated limits computed and equal |
| `INCONSISTENT_NONZERO` | both computed and unequal (or pole vs finite) |
| `UNKNOWN` | size-guard, timeout, parse/CAS failure, undecided compare, both non-finite |

`family_zero_blocked(consistency_verdicts, require_path_independence=True)`
is true unless all verdicts are `CONSISTENT_ZERO` when independence is
required. `INCONSISTENT_NONZERO` always blocks `FAMILY_ZERO`.

Size-guard is `count_ops > 80` (`LIMIT_OPS_CAP` from the confluence engine).
Large kernels are not evaluated.

## Tests

`tests/test_ic_consistency.py`

- commuting cubic Newton second DD (`F=z**3`) `y->x` then `w->x` vs swap,
  both `F''(x)/2 = 3x` → `CONSISTENT_ZERO`
- `x/(x+y)` order swap → `INCONSISTENT_NONZERO`
- `count_ops > 80` commuting substitutions → `UNKNOWN`, not `CONSISTENT_ZERO`
- schema: `PATH_ZERO+PATH_ZERO` + `UNKNOWN` + `require_path_independence` → `FAMILY_UNKNOWN`
- schema: `PATH_ZERO+PATH_ZERO` + `INCONSISTENT_NONZERO` → `FAMILY_NONZERO`
- source-ban: no catalog gold names or identity tables in this package

Command: `.venv/bin/python -m pytest tests/test_ic_consistency.py -q`

## Remaining risks

- Two-sided limits only (`check_limit` / `sympy.limit` with `dir="+-"`).
- Pole vs pole is `UNKNOWN`, not `CONSISTENT_ZERO`.
- Witness comparison uses the confluence `_expr_equal` budget; hard
  identities can stay `UNKNOWN`.
- Does not enumerate path pairs (that is the path enumerator).

## COMMIT SHA

COMMIT_SHA=b8df9da2992a2fbe93a2b92a2144477e4357dd1e
