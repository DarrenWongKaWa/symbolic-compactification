# HANDOFF — Track V3 (confluence / limit engine)

Parent: `329c49c22c7d68d0192a59f04bf3ba8ad12c9b48`
Branch: `work/v-confluence`

## What was implemented

Typed check ``lim_{y -> x} F = G`` under
`research/scalable_verification/confluence/`. No LLM. No Guo-specific
identities. Cubic ``F[x,x,x]`` confluence is out of scope here.

Public API:

```python
from research.scalable_verification.confluence import check_limit

result = check_limit(F, y, x, G)
# result.verdict      ZERO | NONZERO | UNKNOWN
# result.provenance   deciding step name
# result.steps        full cascade trace
```

Cascade (each step records a provenance string):

1. `substitution` — `F.xreplace({y:x})` finite and equals `G`
2. `together_cancel` — `together`/`cancel` then substitute
3. `valuation` — numerator/denominator order at `y = x`
4. `series` — expansion in `(y - x)`
5. `lhopital` — derivative reduction on `0/0`
6. `newton_first_dd` — first Newton DD via `repeated_diagonal` (`F[x,x] = F'(x)`)
7. guarded `sympy.limit` (`dir="+-"`, process, `seconds<=8`), else `UNKNOWN`

`sympy.limit` is skipped when `count_ops(F) > 80`. `BudgetExceeded` and
non-positive budgets are UNKNOWN, never ZERO.

## Tests

`tests/test_sv_confluence.py`

- `(x**2-y**2)/(x-y) -> 2x` via `together_cancel` (no `sympy.limit`)
- exp first DD `-> exp(x)` via cascade
- continuous substitution `x+y -> 2x`
- negatives: wrong target `3x`, pole `1/(x-y)`, wrong-sign exp DD
- timeout (`BudgetExceeded`) is UNKNOWN, never ZERO
- `count_ops > 80` skips `sympy.limit` and stays UNKNOWN
- Newton helper uses `repeated_diagonal`

Command: `.venv/bin/python -m pytest tests/test_sv_confluence.py -q`

## Remaining risks

- Cheap steps do not cover essential singularities; two-sided `sympy.limit`
  may raise "does not exist" (treated as not equal to a finite `G`).
- Valuation/series/L'Hôpital are capped (order 8 / four rounds); higher-order
  removable zeros can stay UNKNOWN.
- Piecewise / one-sided confluence is not a special case here.
- Cubic `F[x,x,x]` is not certified by this engine.

## COMMIT SHA

COMMIT_SHA=PENDING
