# HANDOFF — Track V2-A (branch graph builder)

Parent: `4dee916170f0282f8b0e5fee171a8bf4a3934646`
Branch: `work/v2-branch-graph`
Owned: `research/multibranch_verification/graph/**`, `tests/test_mb_graph.py`

No LLM. No Guo gold names. Does not edit `schema.py`, frozen inputs, or
historical runs. Does not adjudicate `FAMILY_ZERO`.

## What was implemented

Per-family graphs from `FROZEN_INPUTS_V2.json` plus obligation-map
member conditions, written to `BRANCH_GRAPHS.json` (evaluation-only).

Nodes are `G####` members. Edges exist only when implied by:

- hypothesis operators (`limit` source/target, `substitution`)
- piecewise conditions (`True` vs `Eq(m,n)` vs `Eq` involving `ell`)
- generic coalescence of coinciding nodes (one- vs two-parameter)

Allowed relations actually emitted: `one_parameter_confluence`,
`repeated_node_confluence`, `substitution`. `other` compose is a path,
not an edge. No `dd_recurrence` / `hermite_dd_recurrence` / `derivative`
tableau edges (not stated by operators or conds).

Public API (`from research.multibranch_verification.graph import ...`):

```python
from research.multibranch_verification.graph import build, build_certificates
from research.multibranch_verification.schema import LocalEdge, ConfluentFamilyCertificate

blob = build()                     # evaluation JSON
certs = build_certificates()       # list[ConfluentFamilyCertificate]
```

Edge verdicts stay `UNKNOWN`. `family_verdict` is `FAMILY_UNKNOWN`.
Recurrence / consistency obligation lists are empty (V2-C / V2-E).

## Graph shape (frozen n=7)

- Six 5-member families: star from the `True` branch — three
  `one_parameter_confluence` edges (`epsilon(m)->epsilon(n)`,
  `epsilon(ell)->epsilon(n)`, `epsilon(ell)->epsilon(m)`) plus one
  `repeated_node_confluence` onto the `And(ell=m, m=n)` branch.
- `guo-p2-s2-i4`: `G0005 -> G0004` confluence, `G0005 -> G0009`
  `b<->c` substitution, `G0009 -> G0008` confluence. No direct
  `G0005 -> G0008` (`other` compose is that path).

Incomparable one-parameter branches (`Eq(m,n)` vs `Eq(ell,n)`) are not
joined. Same-parent conds only; cross-parent links require an operator.

## Tests

`tests/test_mb_graph.py`

Command: `.venv/bin/python -m pytest tests/test_mb_graph.py -q`
Result: **14 passed**

## Remaining risks

- Operator argument layouts are heterogeneous (`source/target`, `var/to`,
  `limits`, `{ell: n}`, `constraint: x -> y`). An unseen key is ignored
  (fail closed: no invented edge).
- Condition parser accepts sympy srepr `Equality` / `And` only.
- `x,y,z` in constraints map to `epsilon(m), epsilon(n), epsilon(ell)`
  from the reconstruction `F(epsilon(m), epsilon(n), epsilon(ell))`
  default; a different positional convention would mis-name variables
  but not add extra members.
- Hermite-typed claims use the same cond/operator graph as
  `local_confluence`. Tableau recurrences are not hypothesized here.

## COMMIT SHA

Parent `4dee916170f0282f8b0e5fee171a8bf4a3934646`.
Branch `work/v2-branch-graph`.
Message: `Build branch graphs for frozen 5-branch/Hermite families.`
