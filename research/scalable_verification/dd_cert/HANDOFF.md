# HANDOFF — V4 Newton / Hermite compositional certificates

Parent: `329c49c22c7d68d0192a59f04bf3ba8ad12c9b48`
Branch: `work/v-hermite-cert`
Owned: `research/scalable_verification/dd_cert/**`, `tests/test_sv_dd_cert.py`

No LLM. No catalog-member hard-coding. Constructors imported, not copied.

## What was implemented

Generic compositional certificates under `research/scalable_verification/dd_cert/`.

| function | claim | constructor |
|---|---|---|
| `newton_first_ok(F,z,x,y,member)` | `F[x,y]=(F(x)-F(y))/(x-y)` | `dd.newton_first` |
| `repeated_ok(F,z,x,member)` | `F[x,x]=F'(x)` | `dd.repeated_diagonal`, cross-check `hermite_dd` multiplicity 2 |
| `hermite_ok(F,z,[(v,m),...],member)` | blocked Hermite tableau | `dd.hermite_dd` |
| `hermite_xxy_ok` | `F[x,x,y]` | multiplicities `(2,1)` |
| `hermite_xyy_ok` | `F[x,y,y]` | multiplicities `(1,2)` |
| `hermite_xxx_ok` | `F[x,x,x]=F''(x)/2` | multiplicity `3` |

Each returns `Certificate` with verdict `ZERO` / `NONZERO` / `UNKNOWN` and provenance (`constructor`, `formula`, explicit `F`, nodes, multiplicities, reconstruction, residual).

Missing `F`, missing member, missing Hermite multiplicities, size-guard, constructor failure, and `HermiteDDError` (mixed endpoints) are **UNKNOWN**, never ZERO. Algebraic mismatch is **NONZERO**. Coincident Newton `x=y` stays 0/0, not `F'(x)`.

## Tests

`.venv/bin/python -m pytest tests/test_sv_dd_cert.py -q`

- cubic/quadratic Newton first DD ZERO
- `F[x,x]=F'(x)` ZERO and agrees with `hermite_dd` multiplicity 2
- `F[x,x,y]`, `F[x,y,y]`, `F[x,x,x]` ZERO (`2x+y`, `x+2y`, `3x` for `z**3`)
- `exp` / `log` probes ZERO
- fail-closed UNKNOWN: missing F, missing member, bare node list, mixed `F[x,y,x]`
- adversarial NONZERO (false ZERO = 0): wrong sign, wrong denom, wrong derivative order, wrong factorial, wrong multiplicity, wrong node-block order, coincident Newton claimed as derivative

## Remaining risks

- Residual identity is `expand` / `cancel` / `together` / `simplify`. Polynomials and the explicit `exp`/`log` probes are decided. Hard special-function rewrites may stay NONZERO or UNKNOWN, never a false ZERO.
- Mixed non-blocked sequences such as `F[x,y,x]` are UNKNOWN via `HermiteDDError`. Confluence limits are V3, not this package.
- Node coincidence is structural (`==` / `expand(a-b)==0`). Unsimplified but equal node expressions are treated as distinct.
- Size guard (`count_ops > 200`) is UNKNOWN, not ZERO.
- Does not bind catalog IDs, instantiate source members, or pair generic/degenerate catalog entries.

## Out of scope

Did not edit `research/scalable_verification/api.py`, frozen runs, SOL, or `research/representation_invention/dd/`.
