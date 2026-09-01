# Derivation-audit edge types

Frozen catalogue (`schema.EDGE_TYPES`). Do not invent parallel names.
Lowering applicability is `SUPPORTED`, `PARTIAL`, or `NOT_APPLICABLE`.
Default status is the typed non-proof starting point before a successful
executable `ZERO`.

Finite coefficient identities never certify an enclosing remainder claim.

## Catalogue

| Type | Lowering | Default | Notes |
|---|---|---|---|
| `ALGEBRAIC_EQUIVALENCE` | SUPPORTED | `NOT_LOWERED` | Scalar or expression equality residual `lhs - rhs`. |
| `DEFINITION_INSERTION` | NOT_APPLICABLE | `DEFINITION` | Name or definition introduction; not a proof claim. |
| `INDEX_RELABELING` | SUPPORTED | `NOT_LOWERED` | Dummy-index or dummy-variable relabeling of an identity. |
| `PERMUTATION_IDENTITY` | SUPPORTED | `NOT_LOWERED` | Finite permutation symmetry of a local kernel. |
| `COEFFICIENT_IDENTITY` | SUPPORTED | `NOT_LOWERED` | Exact coefficient comparison; not a remainder proof. |
| `LAURENT_COEFFICIENT` | SUPPORTED | `NOT_LOWERED` | Exact Laurent coefficient identity. Finite coefficients do not prove an asymptotic remainder. |
| `SERIES_COEFFICIENT` | SUPPORTED | `NOT_LOWERED` | Exact series coefficient identity, not a remainder certificate. |
| `SYMMETRY_LOCAL` | SUPPORTED | `NOT_LOWERED` | Local algebraic symmetry of a kernel or matrix element. |
| `PROJECTOR_IDENTITY` | SUPPORTED | `NOT_LOWERED` | Projector algebra such as `P^2 - P = 0` under declared relations. |
| `COMPLETENESS_RECONSTRUCTION` | PARTIAL | `RECORDED` | Executable only when the completeness rule is an explicit assumption and a residual is supplied. |
| `PAIRWISE_REDUCTION` | PARTIAL | `NOT_LOWERED` | Local pair identity is lowerable; a global sum is not swallowed as one residual. |
| `DIVIDED_DIFFERENCE` | SUPPORTED | `NOT_LOWERED` | Exact divided-difference algebraic identity. |
| `SPECIAL_FUNCTION_IDENTITY` | PARTIAL | `NOT_LOWERED` | Only identities inside the declared verifier catalogue. |
| `SPLIT_PARENT` | NOT_APPLICABLE | `SPLIT` | Parent delegated to child obligations. Never itself `ZERO`. |
| `ASYMPTOTIC_CLAIM` | NOT_APPLICABLE | `UNKNOWN` | Global remainder claim. Coefficient children may be `ZERO`; the claim is not `ZERO` without a remainder certificate. |
| `LIMIT_CLAIM` | PARTIAL | `UNKNOWN` | Naked limit differences are not identities. Coefficient or residue children may be lowered separately. |
| `INTEGRAL_ARGUMENT` | NOT_APPLICABLE | `NOT_LOWERED` | Integral-level pairing or contour argument is not a local residual. |
| `GLOBAL_SYMMETRY_PAIRING` | PARTIAL | `NOT_LOWERED` | Global pairing over a domain. Local pair kernels may be lowered. |
| `BOOKKEEPING` | NOT_APPLICABLE | `RECORDED` | Assembly or reconstruction bookkeeping, not an exact residual. |
| `CUSTOM_EXACT` | SUPPORTED | `NOT_LOWERED` | Explicit user-supplied residual with declared semantics. |
| `BZ_PERIODIC_INTEGRATION_BY_PARTS` | PARTIAL | `NOT_LOWERED` | Global BZ-torus IBP. Local Leibniz children may be `ZERO`. Parent is `CERTIFIED_BY_RULE` only with declared `BZ_TORUS_PERIODICITY` on `BRILLOUIN_ZONE_TORUS`. Never engine `ZERO`. |

`NON_RESIDUAL_CLAIM_TYPES` = `ASYMPTOTIC_CLAIM`, `LIMIT_CLAIM`,
`INTEGRAL_ARGUMENT`. Do not rewrite those as `F - A/gamma = 0`.

`COEFFICIENT_EDGE_TYPES` = `COEFFICIENT_IDENTITY`, `LAURENT_COEFFICIENT`,
`SERIES_COEFFICIENT`. Independently certifiable; they do not certify a
parent `ASYMPTOTIC_CLAIM`.

## Selection rules

- Use the most specific type that matches the scientific claim.
- A definition is `DEFINITION_INSERTION`, never `ZERO`.
- A global remainder is `ASYMPTOTIC_CLAIM`. Put finite coefficients on
  child edges.
- A parent that delegates proof is `SPLIT_PARENT` with `children`.
- If the engine has no residual, the honest status is `NOT_LOWERED` or
  `UNKNOWN`, not a nearby algebraic encoding.
- Brillouin-zone integration by parts is `BZ_PERIODIC_INTEGRATION_BY_PARTS`,
  not a local residual and not a fake integral `ZERO`. Put the Leibniz
  product rule on a child edge. Declare `BZ_TORUS_PERIODICITY` in
  `assumptions.yaml` `rules` and set `ibp_domain: BRILLOUIN_ZONE_TORUS`.
  Missing periodicity is `ASSUMPTION_REQUIRED`. The declared rule must apply
  to the **IBP integrand combination** (gauge-invariant / globally periodic).
  Do not treat a gauge-dependent Berry connection as automatically periodic
  because the BZ is a torus.

See [STATUS_SEMANTICS.md](STATUS_SEMANTICS.md).
