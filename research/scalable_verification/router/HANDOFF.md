# HANDOFF — Track V Subagent V6 (size / complexity router)

Parent: `329c49c22c7d68d0192a59f04bf3ba8ad12c9b48`
Branch: `work/v-router`
Owned: `research/scalable_verification/router/**`, `tests/test_sv_router.py`

The router **does not decide truth**. It never returns `ZERO` or `NONZERO`.
Strategy `UNKNOWN` means no local strategy, not a verification verdict.

## What was implemented

Frozen complexity router under `research/scalable_verification/router/`.

| symbol | role |
|---|---|
| `measure(expr)` | `op_count`, `tree_depth`, `piecewise_count`, `sum_count`, `special_function_count`, `n_free_symbols` |
| `route(obligation_kind, measures)` | one of `api.STRATEGIES` |
| `THRESHOLDS.json` | frozen numeric policy |

`op_count` is `sympy.count_ops(..., visual=False)`. Structural counts use
preorder traversal (top-level `Sum` / `Piecewise` included).
`special_function_count` counts applications named in the frozen list
(polygamma family).

## Frozen policy (first hit)

1. `op_count > 400`, or `Sum ≥ 1` and `op_count > 400` → `UNKNOWN`
2. polygamma/special ≥ 1 and `op_count < 80` → `SPECIAL_FUNCTION_LOCAL`
3. Piecewise ≥ 1 and kind `LIMIT` → `FACTOR_LOCAL` if `Sum ≥ 1` else `SERIES_LOCAL`
4. `op_count < 40` and kind `NEWTON_DD` / `HERMITE_DD` / `DIVIDED_DIFFERENCE` → `DD_CERTIFICATE`
5. `op_count < 40` and kind `EQUALITY` → `DIRECT`
6. else `UNKNOWN`

Bounds are exclusive (`< 40`, `< 80`, `> 400`). `tree_depth` is measured
and is not a routing predicate in this freeze.

## Tests

`.venv/bin/python -m pytest tests/test_sv_router.py -q`

Result: **17 passed**. Deterministic. No network. No engine verifier import.

## Remaining risks

- Router sees kind + measures only, not left/right payloads. A bad measure
  yields a bad strategy, never a false ZERO (the router cannot emit ZERO).
- Unlisted specials (Bessel, hypergeometric, …) do not trip
  `SPECIAL_FUNCTION_LOCAL` unless added to the frozen name list.
- `FACTOR_LOCAL` vs `SERIES_LOCAL` is frozen as “LIMIT + Piecewise, split
  on Sum present”. Mixed kernels may want the other local engine.
- `huge_sum_ops` equals `huge_ops` (400) in this freeze, so the two huge
  gates coincide numerically.
- Callers must not treat strategy `UNKNOWN` as a verification `UNKNOWN`.

## COMMIT SHA

Tip of `work/v-router`. Parent `329c49c22c7d68d0192a59f04bf3ba8ad12c9b48`.
