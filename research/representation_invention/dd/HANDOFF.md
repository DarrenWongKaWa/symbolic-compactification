# HANDOFF — Subagent A (DD / Hermite)

Parent: `45b2b4dc7c823901f4b79713d279c6be7bae2859`
Branch: `work/representation-dd`

## What was implemented

Generic Newton / Hermite divided-difference constructors under
`research/representation_invention/dd/`. No source instantiation, no
source-specialized identities.

Public API (import `research.representation_invention.dd`):

| symbol | layer | formula |
|---|---|---|
| `newton_first(F, z, x, y)` | definition | `(F(x)-F(y))/(x-y)` via `xreplace` |
| `newton_table(F, z, nodes)` | recurrence | `F[x0..xk] = (F[x1..xk]-F[x0..x_{k-1}])/(xk-x0)` |
| `repeated_diagonal(F, z, x)` | definition | `F.diff(z).xreplace({z:x})` |
| `hermite_dd(F, z, [(v,m),...])` | confluent recurrence | all-equal window `F^{(k)}(a)/k!`; else Newton step |
| `limit_generic_to_degenerate(generic, var, point)` | confluence identity | `sympy.limit`; `ConfluenceLimitError` on failure |

`newton_table` does **not** rewrite coincident nodes to derivatives
(0/0 stays 0/0). `hermite_dd` is the confluent path.

## Formulas

Definition:

\[
F[x,y]=\frac{F(x)-F(y)}{x-y},\qquad F[x,x]=F'(x)
\]

Recurrence (distinct endpoints):

\[
F[x_0,\ldots,x_k]=\frac{F[x_1,\ldots,x_k]-F[x_0,\ldots,x_{k-1}]}{x_k-x_0}
\]

Confluent diagonal (`k+1` copies of `a`):

\[
F[\underbrace{a,\ldots,a}_{k+1}]=F^{(k)}(a)/k!
\]

so `F[x,x,x]=F''(x)/2`. For `F(z)=z^3` that is `3x` (unit probe `3`).

Confluence identity (not a definition, not instantiation):

\[
\lim_{y\to x} F[x,y]=F[x,x]
\]

Source instantiation (`A_i = O_i[F]` on catalog members) is G/C.

## Tests

`tests/test_representation_dd.py`

- cubic `F=z^3`: closed form `F[x,y]=x^2+xy+y^2`, `F[x,x]=3x^2`, `F[x,x,x]=3x` with unit probe `3`
- Hermite `F[x,x,y]=2x+y`, `F[x,y,y]=x+2y`
- `exp(z)` / `log(z)` identities and numeric probes
- confluence of `F[x,y]` and of `F[x,x,y]`
- negatives: wrong sign, wrong denominator, coincident-node 0/0 ≠ derivative, wrong derivative order
- typed errors: failed `sympy.limit`; mixed `F[x,y,x]` is not guessed

Command: `.venv/bin/python -m pytest tests/test_representation_dd.py -q`
Result: **15 passed**

Equality uses `research.llm_abstraction.constructor._equal` (imported, not copied).

## Remaining risks

- Mixed non-blocked sequences such as `F[x,y,x]` raise `HermiteDDError` rather than a mixed confluence limit. Callers should pass consecutive multiplicity blocks or use `limit_generic_to_degenerate`.
- `sympy.limit` fail-closed: unevaluated `Limit` and CAS exceptions become `ConfluenceLimitError`. Some special-function limits may therefore stay uncertified even if a closed form exists.
- Node equality in the tableau is structural (`==`), not `simplify(a-b)==0`. Mathematically equal but unsimplified node expressions are treated as distinct and take the generic recurrence.
- Constructors do not `simplify`. Residual ZERO is a verifier / `_equal` job.
- This package does not bind catalog IDs or reconstruct source members. A compiler that substitutes coincident nodes into `newton_first` will get `nan`, not `F'(x)`.
- No live API; no source-gold expressions in constructors or tests.

## COMMIT SHA

COMMIT_SHA=PENDING
