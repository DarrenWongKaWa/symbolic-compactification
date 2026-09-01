# Rule certificates

Frozen product principles (do not silently weaken):

1. `ZERO` is never `CERTIFIED_BY_RULE`.
2. Certificate class describes **provenance**, not a ranking of mathematical
   truth. `DIRECT_EXACT`, `SUBSTITUTION_EXACT`, and `RULE_CERTIFICATE` tell
   a reviewer what the conclusion depends on.
3. Rule growth is **field-driven**. Add a named rule only when a real public
   derivation exposes a missing adapter with explicit fail-closed conditions.
   Do not pre-load TRACE_CYCLICITY, STOKES, HERMITICITY, COMPLETENESS, or
   similar catalogues.

Lineage (immutable tags; do not move the old release tags):

```text
derivation-audit-v0.2.0-alpha
    → archive/guo-selected-edge-validation-v1
    → derivation-audit-v0.2.1-alpha  (generic BZ IBP adapter)
    → archive/guo-full-paper-audit-flagship-v1
```

Product code and case evidence stay separate. Unpublished local manuscripts
never enter public provenance.

`ZERO` is never the same as `CERTIFIED_BY_RULE`.

```
engine certificates  +  rule certificates
```

An engine certificate is an executable residual that the deterministic
verifier simplifies to exact `ZERO`.

A rule certificate is:

```
local child ZERO
  + declared theorem / domain condition
  → typed parent status CERTIFIED_BY_RULE
```

The parent is **not** an engine ZERO. SymPy did not evaluate the global
object (integral, completeness sum, contour, …).

## Recorded certificate

```text
status: CERTIFIED_BY_RULE
rule_id: BZ_TORUS_PERIODICITY
local_children:
  - edge_id: D.leibniz-product-rule
    status: ZERO
requirements:
  domain: BRILLOUIN_ZONE_TORUS
  integrand_periodic: declared
conclusion: integral_of_total_derivative = 0
```

## Field-driven rule growth

Do **not** build a theorem-prover rule library.

Add a named rule only when all of these hold:

1. a real public derivation used the step;
2. the existing taxonomy cannot express it without a fake residual ZERO;
3. the mathematical conditions are explicit and fail-closed
   (`ASSUMPTION_REQUIRED` when undeclared).

Current catalogue:

| Rule | Domain | Local child | Conclusion |
|---|---|---|---|
| `BZ_TORUS_PERIODICITY` | `BRILLOUIN_ZONE_TORUS` | Leibniz product rule | integral of a total $k$-derivative vanishes |

The next rule is added only when another real paper hits the same wall.

Completeness, symmetry projection, trace cyclicity, Hermiticity, Stokes, and
similar operations stay untyped until field use exposes them. Do not invent
a pseudo-ZERO for “everyone knows this.”

## Gauge caution

Declaring BZ torus periodicity does **not** make every intermediate object
periodic. The declared rule must apply to the **IBP integrand combination**.
A gauge-dependent Berry connection is not automatically allowed.
