# Owner: V3-H — local kernel complexity reduction

Algebraically equivalent forms of a local kernel that lower `count_ops`
without changing verifier semantics.

Allowed: `factor`, `cancel`, `together`, `collect`, exact child
substitution, common-subexpression names in the trace.

Forbidden: CAS-global simplifier as a silent proof, truncated expansions,
dropping Piecewise branches, undeclared identities.

## Public API

```python
from research.iterated_confluence.complexity import reduce_kernel, count_ops

reduce_kernel(expr) -> {
    "original_ops": int,
    "reduced_ops": int,
    "expr_reduced": expr,
    "trace": [str, ...],
    "equivalent": bool,
}
```

- `equivalent` is True only if `expr_reduced == original` or
  `cancel(original - reduced) == 0`, and Piecewise / Sum / Product shape
  is preserved.
- If a rewrite is not certified, the original expression is returned and
  `equivalent` is False.
- `count_ops` is `sympy.count_ops(..., visual=False)`.
- This module does not decide ZERO.

Piecewise nodes are reduced branchwise and rebuilt with `evaluate=False`.
Let bindings from common-subexpression extraction are trace notes only;
they are not substituted into `expr_reduced`.
