# Owner: V4 — Newton / Hermite certificate engine

False ZERO = 0. No Guo hard-coding.

Requires explicit latent `F` and, for Hermite, explicit multiplicities.
Verdicts are `ZERO` | `NONZERO` | `UNKNOWN` with provenance. Timeout,
size-guard, missing `F`/multiplicities, and ill-posed tableaux are
`UNKNOWN`, never `ZERO`.

## Public API

```python
from research.scalable_verification.dd_cert import (
    newton_first_ok,   # F[x,y] = (F(x)-F(y))/(x-y)
    repeated_ok,       # F[x,x] = F'(x)
    hermite_ok,        # hermite_dd on [(value, multiplicity), ...]
    hermite_xxy_ok,    # F[x,x,y]
    hermite_xyy_ok,    # F[x,y,y]
    hermite_xxx_ok,    # F[x,x,x] = F''(x)/2
)
```

Constructors: `research.representation_invention.dd.newton_first`,
`repeated_diagonal`, `hermite_dd`. Not copied. No catalog pairing.
