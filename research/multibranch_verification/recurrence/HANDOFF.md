# HANDOFF — V2-C Hermite / Newton recurrence

Parent: `4dee916170f0282f8b0e5fee171a8bf4a3934646`
Branch: `work/v2-hermite-recurrence`
Owned: `research/multibranch_verification/recurrence/**`, `tests/test_mb_recurrence.py`

No LLM. No source-member hard-coding. Constructors imported from
`research.representation_invention.dd`, not copied. Did not edit `schema.py`.

## What was implemented

Generic recurrence checks under `research/multibranch_verification/recurrence/`.

Public API: `check_recurrence(kind, F, z, x=None, y=None, *, claimed=None, rhs=None, nodes=None)`
returns `RecurrenceResult` with verdict `ZERO` / `NONZERO` / `UNKNOWN` and
provenance (`constructor`, `formula`, `F`, nodes, multiplicities, lhs, rhs,
residual, checks).

| kind | identity | constructors |
|---|---|---|
| `F[x,x]` | `F[x,x]=F'(x)` | `hermite_dd` mult. 2 vs `repeated_diagonal` |
| `F[x,x,y]` | `F[x,x,y]=(F[x,x]-F[x,y])/(x-y)` | `hermite_dd` vs `repeated_diagonal`, `newton_first` |
| `F[x,y,y]` | `F[x,y,y]=(F[x,y]-F[y,y])/(x-y)` | `hermite_dd` vs `newton_first`, `repeated_diagonal` |
| `F[x,x,x]` | `F[x,x,x]=F''(x)/2` | `hermite_dd` mult. 3 vs `F''/2!` |
| `newton_step` / `dd_recurrence` | tableau step | `newton_table` |
| `hermite_step` / `hermite_dd_recurrence` | all-equal `F^{(k)}/k!` or Newton step | `hermite_dd` |

`claimed` is a claimed value of the left-hand DD. `rhs` overrides the
definitional formula (orientation / factorial / derivative-order attacks).
`to_obligation()` is a dict for `ConfluentFamilyCertificate.recurrence_obligations`.

Missing `F` / nodes / multiplicities, unknown kind, size-guard, constructor
failure, and `HermiteDDError` (mixed `F[x,y,x]`) are **UNKNOWN**, never ZERO.
Algebraic mismatch is **NONZERO**. Coincident Newton `x=y` stays 0/0, not
`F'(x)`. Substituting `y=x` into the `F[x,x,y]` formula is not ZERO.

Mission orientation `(F[x,x]-F[x,y])/(x-y)` and Newton orientation
`(F[x,y]-F[x,x])/(y-x)` both ZERO; a single sign flip is NONZERO.

## Tests

`.venv/bin/python -m pytest tests/test_mb_recurrence.py -q`

Result: **22 passed**

- cubic/quadratic identities ZERO, including closed forms `3x^2`, `2x+y`, `x+2y`, `3x`
- `exp` / `log` probes ZERO
- fail-closed UNKNOWN: missing F, missing y/nodes/multiplicities, mixed endpoints
- adversarial NONZERO (false ZERO = 0): wrong sign, wrong factorial, wrong
  derivative order, wrong multiplicity, wrong orientation (xxy vs xyy and
  flipped recurrence numerator), wrong node value, coincident Newton as derivative

## Remaining risks

- Residual identity is `expand` / `cancel` / `together` / `simplify`. Polynomials
  and the explicit `exp`/`log` probes are decided. Hard special-function
  rewrites may stay NONZERO or UNKNOWN, never a false ZERO.
- Mixed non-blocked sequences such as `F[x,y,x]` are UNKNOWN via `HermiteDDError`.
  Confluence limits (`y→x` of `F[x,x,y]`) are not this package.
- Node coincidence is structural (`==` / `expand(a-b)==0`). Unsimplified but
  equal node expressions are treated as distinct.
- Size guard (`count_ops > 200`) is UNKNOWN, not ZERO.
- Does not instantiate source members or pair generic/degenerate family edges.

## Out of scope

Did not edit `research/multibranch_verification/schema.py`, frozen V2 inputs,
SOL, or `research/representation_invention/dd/`.
