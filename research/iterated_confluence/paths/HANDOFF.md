# HANDOFF — Track V3-B (one-parameter path enumerator)

Parent: `dcfb90cac087a47241aced2dc0c3b851f1a12e21`
Branch: `work/v3-path-enumerator`
Owned: `research/iterated_confluence/paths/**`, `tests/test_ic_paths.py`

No LLM. No Guo identities. Does not edit `schema.py`, frozen inputs, or
historical runs. Does not adjudicate path or family verdicts.

## What was implemented

Covering paths among **existing** `G####` members of each frozen V3
family (`FROZEN_INPUTS_V3.json`, n=7). Written to `PATH_CANDIDATES.json`.

A step exists only when the target partition is a coarsening of the
source by **exactly one** declared index equality, using V2 Equality
regex parsing plus `piecewise.classify_condition` for roles. Same-parent
conds only. Incomparable diagonals (`Eq(m,n)` vs `Eq(ell,n)`) are not
joined. Intermediate expressions are not invented.

Public API:

```python
from research.iterated_confluence.paths import enumerate_family, enumerate_all, write
from research.iterated_confluence.schema import PathStep, PathCertificate

fam = enumerate_family(hyp)
# family_id, paths, rejected_multi_parameter
```

`PathStep` / `PathCertificate` verdicts stay `UNKNOWN` / `PATH_UNKNOWN`.

## Graph shape

- Six 5-member families: three 2-step covering paths generic → And, plus
  six one-step covering edges.
  - generic --{m,n}--> Eq(m,n) --{ell,n}--> And
  - generic --{ell,n}--> Eq(ell,n) --{m,n}--> And
  - generic --{ell,m}--> Eq(ell,m) --{m,n}--> And
  After `Eq(ell, m)` the remaining free coordinate is `Eq(m, n)`
  (`epsilon(m) -> epsilon(n)`).
- V2 two-parameter star `generic -> And` is listed under
  `rejected_multi_parameter` with `reason="not_one_parameter"`.
- `guo-p2-s2-i4`: confluence one-steps `G0005 -> G0004` and
  `G0009 -> G0008`. Substitution `G0005 -> G0009` is recorded separately
  (`substitutions`), not as a degeneracy path.

## Ranking

1. `n_steps` ascending
2. max source/target op count ascending
3. True→`Eq(m,n)` one-step (Track V pair shape) ahead of other ties
4. `path_id` lexicographic

Ranking does not read expected or certified edge verdicts.

## Tests

`tests/test_ic_paths.py`

Command: `.venv/bin/python -m pytest tests/test_ic_paths.py -q`

## Remaining risks

- Coordinate choice after a diagonal uses the preferred pair order
  `(m,n)`, `(ell,n)`, `(ell,m)`. A different spanning equality that
  imposes the same merge is not emitted as a second path.
- Cross-parent links are operator-only (substitution). Compose-of
  substitution+limit is not flattened into a confluence edge.
- Condition parser accepts sympy srepr `Equality` / `And` (V2 regex).

## COMMIT SHA

Parent `dcfb90cac087a47241aced2dc0c3b851f1a12e21`.
Branch `work/v3-path-enumerator`.
Message: `Enumerate one-parameter confluence paths for frozen V3 families.`
