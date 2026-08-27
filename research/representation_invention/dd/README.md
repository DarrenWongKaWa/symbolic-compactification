# Owner: Subagent A — Newton / Hermite DD

Implement generic divided-difference constructors and identities.

Do not specialize to Guo gold. Import V2 schema; do not edit it.

Required public API (implement in this package):

- `newton_first(F, z, x, y) -> Expr`  # (F(x)-F(y))/(x-y)
- `repeated_diagonal(F, z, x) -> Expr`  # dF/dz at x
- `hermite_nodes(F, z, nodes: list[(expr, multiplicity)]) -> Expr`
- `confluence_identity(generic, degenerate, var, point) -> Expr residual`

Distinguish definition / recurrence / confluence / source instantiation.

Negative controls: wrong sign, wrong denominator, wrong multiplicity.
