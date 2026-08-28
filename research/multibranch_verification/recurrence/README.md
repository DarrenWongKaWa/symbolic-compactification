# Owner: V2-C — Hermite / Newton recurrence checks

False ZERO = 0. No source-member hard-coding.

Requires an explicit latent `F`. Verdicts are `ZERO` | `NONZERO` | `UNKNOWN`
with provenance. Size-guard, missing `F`/nodes/multiplicities, and ill-posed
tableaux are `UNKNOWN`, never `ZERO`. Algebraic mismatch is `NONZERO`.

Constructors: `research.representation_invention.dd` (`newton_first`,
`newton_table`, `repeated_diagonal`, `hermite_dd`). Not copied.

## Public API

```python
from research.multibranch_verification.recurrence import check_recurrence

check_recurrence("F[x,x]", F, z, x)                    # F[x,x] = F'(x)
check_recurrence("F[x,x,y]", F, z, x, y)               # (F[x,x]-F[x,y])/(x-y)
check_recurrence("F[x,y,y]", F, z, x, y)               # (F[x,y]-F[y,y])/(x-y)
check_recurrence("F[x,x,x]", F, z, x)                  # F''(x)/2
check_recurrence("newton_step", F, z, nodes=[x, y, w])
check_recurrence("hermite_step", F, z, nodes=[(x, 2), (y, 1)])
check_recurrence("F[x,x,y]", F, z, x, y, claimed=2 * x + y)
check_recurrence("F[x,x,y]", F, z, x, y, rhs=wrong_formula)
```

`claimed` is a claimed value of the left-hand DD. `rhs` overrides the
definitional right-hand side (orientation / factorial / derivative attacks).

## Formulas

- `F[x,x] = F'(x)` via `hermite_dd` multiplicity 2 vs `repeated_diagonal`
- `F[x,x,y] = (F[x,x] - F[x,y]) / (x - y)` (equals Newton `(F[x,y]-F[x,x])/(y-x)`)
- `F[x,y,y] = (F[x,y] - F[y,y]) / (x - y)`
- `F[x,x,x] = F''(x) / 2` (`k!` for `k+1` coincident nodes)

Coincident Newton `x=y` stays 0/0, not `F'(x)`. Mixed `F[x,y,x]` is UNKNOWN.
