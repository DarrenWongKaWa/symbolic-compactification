# Owner: Subagent A — Newton / Hermite DD

Generic divided-difference constructors. No source-specialized identities.

Import V2 schema from the frozen contract if a caller needs types; this
package does not edit the contract and does not instantiate catalog members.

## Layers (do not mix)

| layer | what it is | where |
|---|---|---|
| definition | `F[x,y] = (F(x)-F(y))/(x-y)`; `F[x,x] := F'(x)` | `newton_first`, `repeated_diagonal` |
| recurrence | Newton / confluent tableau | `newton_table`, `hermite_dd` |
| confluence identity | `lim_{y→x} F[x,y] = F[x,x]` | `limit_generic_to_degenerate` |
| source instantiation | bind G#### members to `O[F]` | **not this package (G/C)** |

## Public API

```python
from research.representation_invention.dd import (
    newton_first,              # definition
    newton_table,              # recurrence
    repeated_diagonal,         # definition of F[x,x]
    hermite_dd,                # confluent recurrence
    limit_generic_to_degenerate,
    ConfluenceLimitError,
    HermiteDDError,
)
```

- `newton_first(F, z, x, y)` → `(F.xreplace({z:x}) - F.xreplace({z:y})) / (x - y)`
- `newton_table(F, z, nodes)` → recursive `F[x0,...,xk]`. Coincident nodes stay 0/0.
- `repeated_diagonal(F, z, x)` → `F.diff(z).xreplace({z:x})`
- `hermite_dd(F, z, nodes)` with `nodes: list[tuple[Expr, int]]`, multiplicity `>= 1`
- `limit_generic_to_degenerate(generic, var, point)` → `sympy.limit`; typed error on failure

## Hermite recurrence

Expand multiplicity blocks to a node sequence. For a window `z_i,...,z_j`:

- one node: `F(z_i)`
- all nodes equal to `a` (`k+1` copies): `F^{(k)}(a) / k!`
  so `F[x,x] = F'(x)` and `F[x,x,x] = F''(x)/2`
- distinct endpoints: `(F[z_{i+1}..z_j] - F[z_i..z_{j-1}]) / (z_j - z_i)`
- equal endpoints with unequal interior: `HermiteDDError` (do not guess 0/0)

Supported blocks: `F[x,y]`, `F[x,x]`, `F[x,x,y]`, `F[x,y,y]`, `F[x,x,x]`.

## Negative controls

- wrong sign: `-(F(x)-F(y))/(x-y)` is not `newton_first`
- wrong denominator: `(F(x)-F(y))/(x+y)`
- wrong multiplicity: `newton_first(F,z,x,x)` is 0/0, not `F'(x)`
- wrong derivative order: `F[x,x,x]` is `F''(x)/2`, not `F''(x)` or `F'''(x)`
