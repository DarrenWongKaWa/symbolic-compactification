# HANDOFF — Track V2-B (local edge certifier)

Parent: `4dee916170f0282f8b0e5fee171a8bf4a3934646`
Branch: `work/v2-edge-certifier`
Owned: `research/multibranch_verification/edges/**`, `tests/test_mb_edges.py`

No LLM. No Guo-specific identities. Track V packages imported, not copied.

## What was implemented

`certify_edge(source_expr, target_expr, relation, variable, target_value, symbols, functions)` under `research/multibranch_verification/edges/`.

```python
from research.multibranch_verification.edges import certify_edge

result = certify_edge(source, target, relation, variable, target_value, symbols, functions)
# result.verdict      ZERO | NONZERO | UNKNOWN
# result.provenance   deciding step name
# result.steps        full cascade trace
```

Cascade (each step records a provenance string):

1. `substitution` — finite `xreplace({variable: target_value})`
2. `cancel` — `cancel`, then substitute when a point is given
3. `split_multiplicative` — Track V exact spectator split
4. `together` — `together` / `cancel` normalize
5. `check_limit` — Track V confluence, limit-like relations only
6. `derivative` — `F'(node)`; `F''(node)/2` on dd/hermite
7. `dd_cert` — Track V Newton / Hermite certificates, dd/hermite only
8. else `UNKNOWN`

`BudgetExceeded` and `count_ops > 200` are UNKNOWN, never ZERO.
Finite substitution / cancel-then-substitute may NONZERO only for
`substitution` and limit-like relations, so a Hermite claim `F` vs
`F[x,x,x]` is not refuted by `F(x) ≠ member`.

## Tests

`tests/test_mb_edges.py`

- cubic Newton closed form `(x**3-y**3)/(x-y) = x**2+xy+y**2`
- confluence `(x**2-y**2)/(x-y) → 2x`
- cubic Newton confluence → `3x**2`
- cubic Hermite `F[x,x,x] = 3x` and Newton first via `dd_cert`
- cubic derivative `F' = 3x**2`
- negatives: wrong target `3x`, pole `1/(x-y)`, wrong Hermite `6x`
- timeout / size-guard / parse failure are UNKNOWN, never ZERO

Command: `.venv/bin/python -m pytest tests/test_mb_edges.py -q`

## Remaining risks

- `check_limit` is used only for `limit` / `one_parameter_confluence` /
  `repeated_node_confluence`. Passing latent `F` as `source` on those
  relations asks `lim F = G`, not a Hermite tableau.
- `dd_cert` infers Newton nodes from `target` free symbols plus
  `target_value`. Unrelated extra symbols can select the wrong pair;
  that path stays UNKNOWN or NONZERO, not a false ZERO, when the
  reconstruction mismatches.
- Spectator split continues the cascade on certified locals for
  limit-like edges. An uncertified split is ignored (fail closed).
- Cheap algebraic identity uses `expand` / `cancel` / `together` /
  `equals(0)` under the ops cap, never `simplify` as a ZERO proof.

## COMMIT SHA

Parent `4dee916170f0282f8b0e5fee171a8bf4a3934646`.
Branch `work/v2-edge-certifier`.
Message: `Add local edge certifier cascade for Track V2.`
