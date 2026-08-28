# HANDOFF — Track V3-I (multiparameter series CONTROL)

Parent: `dcfb90cac087a47241aced2dc0c3b851f1a12e21`
Branch: `work/v3-series-control`

Commit message: `Add multivariate series control for iterated-limit toys.`

## Owned

- `research/iterated_confluence/series/**`
- `tests/test_ic_series.py`

Did not edit `schema.py`, freeze inputs, run JSON, or Track V/V2
verifiers.

## What was implemented

Public API:

```python
from research.iterated_confluence.series import multivariate_control, iterated_limits

iterated_limits(expr, steps)           # value or None
multivariate_control(expr, vars_and_points)
# commuting: bool | None
# order_a, order_b results
# note
```

This is a **control, not a verifier**. It never emits a family
certificate. Iterated limits are not joint limits.

One-parameter cascade (no `sympy.limit`): substitution, cancel,
valuation, explicit series in `(var - point)`, L'Hôpital. Ops cap 40.
Failure → `None` / `commuting is None` (UNKNOWN).

Audits: mixed partials of the formula, truncated iterated series (cross
terms), order swap of iterated limits.

## Tests

`tests/test_ic_series.py`

- removable `(x**3-y**3)/(x-y)` at `y=x` is `3x**2`
- noncommuting `x/(x+y)` at `(0,0)` order swap disagrees
- commuting polynomial `(x+y)` both orders 0
- large expr UNKNOWN
- source-ban: no gold names
- README states control, not a verifier

Command: `.venv/bin/python -m pytest tests/test_ic_series.py -q`

Result: **14 passed**. Deterministic. No network. No engine verifier import.

## Remaining risks

- Iterated agreement is not a joint-limit certificate
  (`xy/(x**2+y**2)` both orders 0). Callers must not promote COMPARED.
- Mixed partials of a rational formula can commute while iterated
  limits at a singularity do not (Schwarz needs a C² neighborhood).
- Laurent / essential singularities stay UNKNOWN when series or
  substitution is non-finite.
- Cap 40 is small; moderate polynomials are UNKNOWN by design.

## COMMIT SHA

`git rev-parse --short HEAD` on `work/v3-series-control`.
