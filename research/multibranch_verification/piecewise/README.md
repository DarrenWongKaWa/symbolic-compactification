# Owner: V2-F — piecewise family normalizer

Condition-only roles for a Piecewise family. No LLM. No branch collapse.
No confluence inference.

## Public API

```python
from research.multibranch_verification.piecewise import (
    normalize_piecewise_family,
    classify_condition,
)

out = normalize_piecewise_family(members)  # {cond, text} per member
```

Roles (from the condition only):

| condition | role |
|---|---|
| `True` | `generic` |
| pairwise `Eq` of two index symbols (`Eq(m, n)`, `Eq(ell, n)`, …) | `diagonal` |
| `Eq` / `And` of equalities involving three or more index symbols | `higher-degeneracy` |
| anything else (`Ne`, inequalities, unparsed) | `unknown` |

A common AppliedUndef spectator is reported only when it **exactly**
divides every member (`factor._peel_applied_undef` / explicit `Mul` args,
checked against `split_multiplicative` on two-member families). Units
and polynomial-only gcds are not spectators here.

Output is structure only: per-member roles, the spectator if certified,
`collapsed=False`, `confluence_inferred=False`. It does not emit
`FAMILY_ZERO`, limit edges, or a reconstruction rule.
