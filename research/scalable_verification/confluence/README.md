# Owner: V3 — confluence / limit engine

Typed check ``lim_{y -> x} F = G``. Cascade; never convert timeout to ZERO.

## Cascade (provenance per step)

1. substitution: ``F.xreplace({y:x})`` finite and equals ``G``
2. ``together`` / ``cancel`` then substitute
3. numerator/denominator order (valuation) at ``y = x``
4. series in ``(y - x)`` to the order needed
5. L'Hôpital / derivative reduction on ``0/0``
6. Newton first DD: ``F[x,x] = F'(x)`` via ``repeated_diagonal``
7. guarded ``sympy.limit`` (process, ``<= 8s``, skip if ``count_ops > 80``), else UNKNOWN

Timeout and size-guard are UNKNOWN, never ZERO. No Guo-specific identities.

```python
from research.scalable_verification.confluence import check_limit

result = check_limit(F, y, x, G)
# result.verdict: ZERO | NONZERO | UNKNOWN
# result.provenance: deciding step
# result.steps: full cascade trace
```
