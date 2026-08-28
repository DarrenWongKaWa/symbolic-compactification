# HANDOFF — Track V2 Subagent V2-I (obligation router)

Parent: `4dee916170f0282f8b0e5fee171a8bf4a3934646`
Branch: `work/v2-router`
Owned: `research/multibranch_verification/router/**`, `tests/test_mb_router.py`

The router **does not decide truth**. It never returns `ZERO`, `NONZERO`,
`FAMILY_ZERO`, or `FAMILY_NONZERO`. Strategy `UNKNOWN` means no local
strategy, not a family verdict.

## What was implemented

Frozen obligation router under `research/multibranch_verification/router/`.

| symbol | role |
|---|---|
| `measure(expr)` | `op_count`, `branch_count`, `sum_count`, `n_free_symbols`, `special_function_count`, `denom_complexity`, `multiplicity` |
| `route(obligation_kind, measures)` | one of `STRATEGIES` |
| `THRESHOLDS.json` | frozen numeric policy |

`op_count` is `sympy.count_ops(..., visual=False)`. Structural counts use
preorder traversal (top-level `Sum` / `Piecewise` included).
`branch_count` is Piecewise arm count. `special_function_count` counts
applications named in the frozen list (polygamma family).
`denom_complexity` is `count_ops` of the together-denominator.
`multiplicity` is `1 + max Derivative order` (0 if none).

## Frozen policy (first hit)

1. `op_count > 400`, or `Sum ≥ 1` and `op_count > 400`, or `denom_complexity > 80` → `UNKNOWN`
2. polygamma/special ≥ 1 and `op_count < 80` → `SPECIAL_FUNCTION`
3. `op_count < 40` and Hermite kind, or DD kind with `multiplicity ≥ 2` → `HERMITE_RECURRENCE`
4. `op_count < 40` and DD kind → `DD_RECURRENCE`
5. `branch_count ≥ 1` and confluence/limit kind → `FACTOR` if `Sum ≥ 1` else `SERIES`
6. `denom_complexity ≥ 2` and `op_count < 80` and direct/limit kind → `FACTOR`
7. `op_count < 40` and `n_free_symbols ≤ 8` and direct kind → `DIRECT`
8. else `UNKNOWN`

Bounds are exclusive (`< 40`, `< 80`, `> 400`, `denom > 80`).

## Tests

`.venv/bin/python -m pytest tests/test_mb_router.py -q`

Deterministic. No network. No engine verifier import. `THRESHOLDS.json`
is the frozen authority; do not retune in code.

## Remaining risks

- Router sees kind + measures only, not left/right payloads. A bad measure
  yields a bad strategy, never a false FAMILY_ZERO (the router cannot emit
  a verdict).
- Unlisted specials (Bessel, hypergeometric, …) do not trip
  `SPECIAL_FUNCTION` unless added to the frozen name list.
- `FACTOR` vs `SERIES` is frozen as “limit/confluence + branches, split
  on Sum present”. Mixed kernels may want the other local engine.
- `huge_sum_ops` equals `huge_ops` (400) in this freeze, so the two huge
  op gates coincide numerically. `huge_denom` is an independent gate.
- `multiplicity` is measured from `Derivative` only; callers must pass
  Hermite node multiplicity in `measures` when the obligation is not a
  derivative expression.
- Callers must not treat strategy `UNKNOWN` as a family `FAMILY_UNKNOWN`.

## COMMIT SHA

Tip of `work/v2-router`. Parent `4dee916170f0282f8b0e5fee171a8bf4a3934646`.
