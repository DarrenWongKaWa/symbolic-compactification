# Owner: V6 — size / complexity router

Chooses strategy; does not decide ZERO.

Thresholds are frozen in `THRESHOLDS.json`. Do not retune in code.
`route` returns a name from `research.scalable_verification.api.STRATEGIES`
only. Strategy `UNKNOWN` is “no local strategy”, not a verification verdict.

## Public API

```python
from research.scalable_verification.router import measure, route

m = measure(expr)   # op_count, tree_depth, piecewise_count,
                    # sum_count, special_function_count, n_free_symbols
s = route(obligation_kind, m)
```

`op_count` is `sympy.count_ops(expr, visual=False)`. Structural counts use
preorder traversal (top-level `Sum` / `Piecewise` included).
`special_function_count` counts applications whose `func.__name__` is in
the frozen `special_function_names` list (polygamma family).

## Frozen policy (first hit wins)

Order is `policy_order` in `THRESHOLDS.json`.

| gate | predicate | strategy |
|---|---|---|
| HUGE_UNKNOWN | `op_count > 400`, or `sum_count ≥ 1` and `op_count > 400` | `UNKNOWN` |
| SPECIAL_FUNCTION_LOCAL | `special_function_count ≥ 1` and `op_count < 80` | `SPECIAL_FUNCTION_LOCAL` |
| PIECEWISE_LIMIT | `piecewise_count ≥ 1` and kind `LIMIT` | `FACTOR_LOCAL` if `sum_count ≥ 1`, else `SERIES_LOCAL` |
| SMALL_DD_CERTIFICATE | `op_count < 40` and kind `NEWTON_DD` / `HERMITE_DD` / `DIVIDED_DIFFERENCE` | `DD_CERTIFICATE` |
| SMALL_DIRECT | `op_count < 40` and kind `EQUALITY` | `DIRECT` |
| DEFAULT_UNKNOWN | otherwise | `UNKNOWN` |

Bounds are exclusive as written: `ops < 40`, `ops < 80`, `ops > 400`.
`tree_depth` is measured and not a routing predicate in this freeze.
