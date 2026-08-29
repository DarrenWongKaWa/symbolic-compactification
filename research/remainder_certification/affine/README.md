# Affine argument normalizer

Not Track V6. No LLM. Track D2 stays LOCKED. This package does not
emit a remainder verdict and does not mint hop ZERO.

An argument is accepted only when it is exactly affine in the
perturbation `t`:

```
z = z0 + c t
```

including algebraically equivalent syntax (`z0 + t*c`, Add
rearrangements, `(2*z0 + 2*c*t)/2`). Extraction is proved by
reconstruction:

```
residual = expand(z - (z0 + c t))
```

Accept iff `residual == 0` and both `z0` and `c` are free of `t`.
Otherwise the result is `UNSUPPORTED`. A nonzero residual is never
returned.

```python
from research.remainder_certification.affine import normalize_affine, UNSUPPORTED
```

## UNSUPPORTED (fail closed)

- quadratic in `t`: `z0 + c t + d t^2` with `d ≠ 0`
- non-affine rational in `t`: `1/(a + t)` (this is an argument
  normalizer; the argument is not affine)
- transcendental `t` dependence: `exp(t)`, `sin(t)`
- inexact floats, non-expressions, size-guard failure

`c = 0` (argument independent of `t`) is affine.

The motivating polygamma class

```
z0 = 1/2 + β (γ ± i (μ − ε)) / (2 π)
z  = z0 + c t
```

is a test class, not a design oracle.

Callers that need a remainder certificate must use the remainder IR;
an affine split is not `CERTIFIED`.
