# Owner: V2-I — obligation router

Chooses strategy; does not decide ZERO / FAMILY_ZERO.

Thresholds are frozen in `THRESHOLDS.json`. Do not retune in code.
`route` returns a name from `STRATEGIES` only. Strategy `UNKNOWN` is
“no local strategy”, not a family verdict.

## Public API

```python
from research.multibranch_verification.router import measure, route

m = measure(expr)   # op_count, branch_count, sum_count,
                    # n_free_symbols, special_function_count,
                    # denom_complexity, multiplicity
s = route(obligation_kind, m)
```

`op_count` is `sympy.count_ops(expr, visual=False)`. Structural counts use
preorder traversal (top-level `Sum` / `Piecewise` included).
`branch_count` is the number of Piecewise arms.
`special_function_count` counts applications whose `func.__name__` is in
the frozen `special_function_names` list (polygamma family).
`denom_complexity` is `count_ops` of the together-denominator.
`multiplicity` is `1 + max Derivative order` (0 if none).

## Frozen policy (first hit wins)

Order is `policy_order` in `THRESHOLDS.json`.

| gate | predicate | strategy |
|---|---|---|
| HUGE_UNKNOWN | `op_count > 400`, or `sum_count ≥ 1` and `op_count > 400`, or `denom_complexity > 80` | `UNKNOWN` |
| SPECIAL_FUNCTION | `special_function_count ≥ 1` and `op_count < 80` | `SPECIAL_FUNCTION` |
| HERMITE_RECURRENCE | `op_count < 40` and (Hermite kind, or DD kind with `multiplicity ≥ 2`) | `HERMITE_RECURRENCE` |
| DD_RECURRENCE | `op_count < 40` and DD kind | `DD_RECURRENCE` |
| BRANCH_FACTOR_OR_SERIES | `branch_count ≥ 1` and confluence/limit kind | `FACTOR` if `sum_count ≥ 1`, else `SERIES` |
| DENOM_FACTOR | `denom_complexity ≥ 2` and `op_count < 80` and direct/limit kind | `FACTOR` |
| SMALL_DIRECT | `op_count < 40` and `n_free_symbols ≤ 8` and direct kind | `DIRECT` |
| DEFAULT_UNKNOWN | otherwise | `UNKNOWN` |

Bounds are exclusive as written: `ops < 40`, `ops < 80`, `ops > 400`,
`denom_complexity > 80`.
