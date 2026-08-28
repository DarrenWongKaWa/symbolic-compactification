# Proof decomposition — architecture (Track V / V1)

Replace one giant global `sympy.limit` / equality check with **small typed
obligations** plus **exact composition rules**. This package is a planner.
It does not certify ZERO.

## Layer split

| layer | owner | decides ZERO? |
|---|---|---|
| plan (typed steps + composition) | V1 `decomposition/` | **no** |
| spectator-factor engine | V2 `factor/` | no (split only) |
| confluence / limit engine | V3 `confluence/` | yes, locally |
| Newton / Hermite certificates | V4 `dd_cert/` | yes, locally |
| special-function localization | V5 `special/` | yes, locally |
| size / strategy router | V6 `router/` | **no** |
| engine verdict | existing verifier | yes |

V1 may **suggest** a route from `research.scalable_verification.api.STRATEGIES`.
It must not write a verdict field and must not call global `sympy.limit` on
the original claim.

```
STRATEGIES = DIRECT | FACTOR_LOCAL | SERIES_LOCAL | DD_CERTIFICATE
            | SPECIAL_FUNCTION_LOCAL | UNKNOWN
```

UNKNOWN as a strategy means “no plan”, not an engine UNKNOWN verdict.

## Claimed relations

The planner accepts two expressions `A`, `B` and one claimed relation:

| relation | meaning (still unproven) |
|---|---|
| `EQUALITY` | `A = B` |
| `LIMIT` | `lim_{var → to} A = B` |
| `NEWTON_DD` | `A` reconstructs a Newton divided difference claimed equal to `B` |
| `HERMITE_DD` | `A` reconstructs a Hermite / confluent DD claimed equal to `B` |

No other kinds are planned. An unknown relation yields a single `UNKNOWN`
strategy step. Guo-specific identities are forbidden.

## Exact composition

A spectator split is legal only as a **polynomial-ring (or exact rational)
identity**, never as the tautology `A_loc := A/S`.

### Spectator (both sides)

If there is an `S` such that

\[
A = S\cdot A_{\mathrm{loc}},\qquad B = S\cdot B_{\mathrm{loc}}
\]

**identically** (exact quotient, remainder `0` on numerators, checked by
`expand` / `_equal` on the reconstruction `S·(·)_{loc}`), then:

- if `S` is a **nonzero constant**, or
- if `S` is **certified nonzero-as-assumption** (`Ne(S, 0)` declared),

the residual obligation is

\[
A_{\mathrm{loc}} - B_{\mathrm{loc}}
\]

with relation `EQUALITY` (or the original relation’s local form). Suggested
strategy: `FACTOR_LOCAL`.

If `S` divides both sides exactly but is **not** certified nonzero, the
factoring is recorded as a suggested `FACTOR_LOCAL` route. The equivalent
residual is **not** substituted for the original claim.

### Identical cancellation (one rational)

If `A = (S·N)/(S·D)` identically (`S` divides numerator and denominator in
the polynomial ring), `S` is **identically cancelled** and

\[
A_{\mathrm{loc}} = N/D.
\]

The residual is `A_loc` versus `B` (and, for `LIMIT`, a further local
evaluation when the cancelled denominator does not vanish at the point).
This is not `sympy.limit`.

### False composition

Rejected (planner returns `None` from `certify_composition` /
`certify_identical_cancel`):

- `S` does not exactly divide the claimed side(s) (nonzero remainder)
- `S = 0`
- `A_loc := A/S` without a remainder-`0` quotient (tautological split)
- cancelling a factor present in only the numerator or only the denominator
  of a rational (not removable)

False composition acceptance must stay **0**.

Additive term matching (`A1+A2 = B1+B2` ⇒ `A1=B1`) is not a composition
rule. It is not exact.

## LIMIT without global `sympy.limit`

For `lim_{var → to} A = B`:

1. Identically cancel a common polynomial factor of `num(A)` and `den(A)`,
   preferring powers of `(var - to)` that divide **both**.
2. If the cancelled denominator is algebraically nonzero at `to`
   (`expand(den_loc.xreplace({var: to})) ≠ 0`), emit a local `EQUALITY`
   of `num_loc.xreplace({var: to}) / den_loc.xreplace({var: to})` versus `B`.
3. If the denominator still vanishes at `to`, emit a smaller `LIMIT` of
   the cancelled rational and suggest `SERIES_LOCAL`.
4. Never call `sympy.limit` on the original (or residual) claim.

## DD relations

`NEWTON_DD` / `HERMITE_DD` always suggest `DD_CERTIFICATE`.

If a latent `F(z)` and nodes are supplied, the planner may **unfold the
definition** into extra `EQUALITY` steps (still unproven):

- Newton: \(F[x,y]=(F(x)-F(y))/(x-y)\)
- Hermite diagonal: \(F[\underbrace{a,\ldots,a}_{k+1}]=F^{(k)}(a)/k!\)

Unfolding is a rewrite of the claim into local obligations. Comparing those
to `B` is V4’s job. V1 does not run the DD certificate.

## What a plan contains

`decompose(A, B, relation, ...)` → `DecompositionPlan`:

- original `A`, `B`, relation
- ordered `ObligationStep` list with provenance (`input_claim`,
  `spectator_factor`, `identical_cancel`, `limit_after_cancel`,
  `newton_definition`, `hermite_definition`, `residual_equality`, …)
- optional `Composition` (`spectator`, `a_loc`, `b_loc`, `residual`,
  status)
- `suggested_strategies` ⊆ `STRATEGIES`
- notes

No `verdict`. No `ZERO` / `NONZERO` assignment.

Each step names one `suggested_strategy` via `api.route_name`. Downstream
packages discharge steps; the engine remains the only ZERO authority.

## Provenance discipline

Composition identities (`A` vs `S·A_loc`) may use
`research.llm_abstraction.constructor._equal` / `parse_flex`. That check
certifies **the split**, not `A = B`.

The original pair `(A, B)` is never passed to `_equal` as a claim decision.

## Tests

Small polynomials only. See `tests/test_sv_decomposition.py`.
False composition must be 0.
