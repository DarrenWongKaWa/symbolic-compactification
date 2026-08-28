# Track V3-I — multivariate series CONTROL

This package is a **control, not a verifier**.

It compares iterated one-parameter limits and local multivariate series
on **small toys**: removable singularities, order dependence, cross
terms, and mixed derivatives. It does **not** certify families and must
not be read as a family certificate.

Iterated limits are not joint limits. Two orders agreeing (for example
a commuting polynomial, or an iterated pair whose joint limit still
fails) is not a family certificate.

If `count_ops` exceeds 40 or a series/limit step fails, the control
returns UNKNOWN (`None` / `commuting is None`). Size-guard and series
failure are never a family certificate.

Do not apply this package to large source expressions.

```python
from research.iterated_confluence.series import multivariate_control, iterated_limits

# iterated_limits(expr, steps) -> value or None
# multivariate_control(expr, vars_and_points) -> dict
#   commuting: bool | None
#   order_a, order_b results
#   note
```

- `iterated_limits` applies `(variable, point)` steps in the given order
  via substitution, cancel, valuation, explicit series, then L'Hôpital.
- `multivariate_control` runs the given order (`order_a`) and the
  reversed order (`order_b`). `commuting` is True when both finite
  values agree, False when they disagree, and None when the comparison
  is UNKNOWN.
