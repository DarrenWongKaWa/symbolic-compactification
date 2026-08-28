# Owner: V2-G — special-function local prover

After spectators are removed, prove or refute local polygamma identities.

`prove_local(expr_or_pair, ...)` → `ZERO` | `NONZERO` | `UNKNOWN`.

Reuses `research.scalable_verification.special.classify_identity`. No masters.
No LLM. No `expand_func`. No `sympy.limit`.

## Admitted ZERO

1. `d/dz polygamma(n, z) = polygamma(n + 1, z)` (via `classify_identity`)
2. Newton first DD of `polygamma(0, ·)` vs `(psi(x) - psi(y))/(x - y)`
   (via `classify_identity`)
3. **Series** (not algebraic equality): Newton DD of `polygamma(n, ·)` as
   `y → x` has leading term `polygamma(n + 1, x)`. Requires `relation="series"`
   (or `limit` / `one_parameter_confluence`) or explicit `variable`/`target`.

Certified multiplicative/additive spectators are stripped first. Units and
zero are not spectators. Local ZERO implies original ZERO.

## Not ZERO

Polygamma recurrence, reflection, chain rule, iterated `d²/dz²`, Φ_Γ / L4–L7,
Guo-scale kernels, series truncation claimed as exact equality, numeric
agreement. Timeout / size-guard / unparsed input: `UNKNOWN`.
