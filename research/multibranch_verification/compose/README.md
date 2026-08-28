# Owner: V2-D — family composition

Pairwise ZERO is not FAMILY_ZERO. Majority vote is forbidden.

`FAMILY_ZERO` iff the required graph is connected, every required edge is
ZERO, every recurrence verdict is ZERO, path consistency is ZERO,
multiplicities are consistent, and the latent is compatible. Any required
NONZERO ⇒ `FAMILY_NONZERO`. Otherwise `FAMILY_UNKNOWN`.

The global rule is imported from `schema.compose_family_verdict` (do not
edit `schema.py`). This package computes those inputs.

## Path consistency

If two directed paths from A to B exist, their composed operators must
agree. Algebraic limit/substitution maps that differ are NONZERO. Opaque
or uncomposable operators (including mixing Hermite recurrence with a
plain limit) are UNKNOWN, never ZERO. Vacuous (≤1 path) is ZERO.

Operators compose in a common name basis: later targets are not rewritten
through earlier identifications.

```python
from research.multibranch_verification.compose import (
    certify_family,
    path_consistency,
    compose_operators,
)

result = certify_family(
    member_ids=["G", "M", "L", "D"],
    edges=edges,                  # LocalEdge or dicts
    recurrence_verdicts=["ZERO"],
    latent_compatible=True,
)
# result.family_verdict: FAMILY_ZERO | FAMILY_NONZERO | FAMILY_UNKNOWN
```
