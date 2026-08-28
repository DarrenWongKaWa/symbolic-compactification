# HANDOFF — Track V3-A (degeneracy coordinates)

Parent: `dcfb90cac087a47241aced2dc0c3b851f1a12e21`
Branch: `work/v3-degeneracy-coordinates`
Owned: `research/iterated_confluence/coordinates/**`, `tests/test_ic_coordinates.py`

No new proposer calls. No Guo-specific identities. Does not edit
`schema.py`, frozen inputs, or historical runs. Does not infer a
representation. Does not emit a family verdict.

## What was implemented

Per-family degeneracy coordinate tables from `FROZEN_INPUTS_V3.json`,
written to `DEGENERACY_COORDINATES.json`.

Coordinates are undirected index equalities already implied by:

- piecewise branch conditions (`True`, `Eq`, `And` of `ell`, `m`, `n`)
- hypothesis operators (`epsilon(m)->epsilon(n)`, `{ell: n}`, `x -> y`, …)

Operator epsilon presentations are recorded as `epsilon(m)-epsilon(n)`
style pairs on the same coordinates, not as extra coordinates.
Substitution `b<->c` is stored under `substitution_operators` and is not
a degeneracy coordinate.

Roles reuse `classify_condition` (generic / diagonal / higher-degeneracy).
Active equalities are the pairs written in the member condition. Free
coordinates are family pairs not yet imposed, using transitivity so
`{ell,n}` is not free on `And(ell=m, m=n)`.

The three pairwise equalities among `{ell,m,n}` are linearly dependent:
`(ell=m)` follows from `(ell=n and m=n)`. Dependence is not treated as a
new representation.

Public API:

```python
from research.iterated_confluence.coordinates import (
    analyze_family,
    analyze_all,
    write as write_coordinates,
)
```

Equality parsing reuses Track V2 `_parse_equalities` / `_pairs_from_args`.

## Tests

`tests/test_ic_coordinates.py`

- 7 families present; no invented members
- True branch has empty active equalities
- `And(ell=m, m=n)` is higher-degeneracy with two equalities
- `analyze_family` does not call an external model
- `coordinates/*.py` source-ban: `Phi_Gamma`, Guo gold, family verdicts

Command: `.venv/bin/python -m pytest tests/test_ic_coordinates.py -q`
Result: **11 passed**

## Remaining risks

- Operator argument layouts are heterogeneous (`source/target`, `var/to`,
  `limits`, `{ell: n}`, `constraint: x -> y`). An unseen key is ignored
  (fail closed: no invented coordinate).
- Condition parser accepts sympy srepr `Equality` / `And` only (V2 regex).
- Free coordinates close under transitivity of the *condition* equalities.
  A member whose operator writes `{ell,n}` while the condition writes
  `{ell,m}` and `{m,n}` still reports those two as active; the third is
  not free because it follows.
- `x,y,z` in constraints map through the V2 reconstruction default
  `epsilon(m), epsilon(n), epsilon(ell)`. A different positional
  convention would mis-name the epsilon form, not add members.

## COMMIT SHA

`18ab1d630feb66b7ab6ac4018e918834af2745be`
Parent `dcfb90cac087a47241aced2dc0c3b851f1a12e21`.
Branch `work/v3-degeneracy-coordinates`.
Message: `Add degeneracy coordinate tables for frozen V3 families.`
