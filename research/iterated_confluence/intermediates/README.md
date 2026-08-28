# Owner: V3-G — intermediate expression builder

Exact one-parameter intermediates from a source parent plus a declared
substitution or Eq imposition. No LLM. No heuristic interpolation.

Limits are edges, not intermediates. `reconstruction_ok` is True only
when the constructed expression is the finite raw substitution image of
the parent.

## Public API

```python
from research.iterated_confluence.intermediates import (
    build_intermediate,
    IntermediateBuild,
)

built = build_intermediate(parent_expr, variable, target_value, parent_id, symbols=None)
# built.record            schema.IntermediateExpression
# built.expr              sympy expr if reconstruction_ok else None
# built.reconstruction_ok True only on exact finite reconstruction
```

Construction is `parent.xreplace({variable: target_value})`. An `Eq` in
`variable`, `target_value`, or `condition` is Eq imposition. A vanishing
denominator (`nan` / `zoo` / identically zero denom) is refused.

## Frozen 5-branch Guo lattice

The six frozen 5-member families already have source `G####` members at
every 3-index equality node (generic, three pairwise diagonals, triple).
`guo-p2-s2-i4` has source members for generic and `m=n` on each of two
parent sums. No intermediate expression is required for those families.
`constructed_intermediates` is always empty: missing nodes, if any, are
reported as index-sets, never as invented kernels.

## Forbidden

- `sympy.limit` / cancel / together / series as construction
- interpolating a missing branch
- gold names
