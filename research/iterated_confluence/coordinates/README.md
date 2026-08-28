# Owner: V3-A — degeneracy coordinates

Read frozen Track V3 families (`FROZEN_INPUTS_V3.json`, n=7). Output
`DEGENERACY_COORDINATES.json`.

Coordinates are undirected index equalities already implied by piecewise
branch conditions and hypothesis operators. Substitution (`b<->c`) is
not a degeneracy coordinate. Does not infer a representation and does
not emit a family verdict.

## Public API

```python
from research.iterated_confluence.coordinates import (
    analyze_family,
    analyze_all,
    write as write_coordinates,
)

row = analyze_family(hyp)
# family_id, coordinates,
# members: [{member_id, cond, role, active_equalities, free_coordinates}]
```

Roles come from `classify_condition` (conditions only):

| condition | role | active equalities | free (5-branch) |
|---|---|---|---|
| `True` | `generic` | none | `{ell,m}`, `{ell,n}`, `{m,n}` |
| `Eq(m,n)` | `diagonal` | `{m,n}` | `{ell,m}`, `{ell,n}` |
| `Eq(ell,n)` | `diagonal` | `{ell,n}` | `{ell,m}`, `{m,n}` |
| `Eq(ell,m)` | `diagonal` | `{ell,m}` | `{ell,n}`, `{m,n}` |
| `And(ell=m, m=n)` | `higher-degeneracy` | `{ell,m}`, `{m,n}` | none (`{ell,n}` follows) |

The three pairwise equalities are linearly dependent: `(ell=m)` follows
from `(ell=n and m=n)`. Dependence is not a new representation.

`guo-p2-s2-i4` has coordinate `{m,n}` only. The `b<->c` swap is stored
under `substitution_operators`.
