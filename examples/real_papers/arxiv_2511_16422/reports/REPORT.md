# Derivation Audit Report

Narrative is non-authoritative; machine numbers come from records.
Markdown cannot create ZERO, VERIFIED, or CERTIFIED status.

## Scope

- Schema version: `DerivationAuditV1`
- Protocol version: `0.2.0`
- Audit name: `arxiv-2511-16422-v2-field-validation`
- Audit id: `arxiv-2511-16422-v2-field-validation`
- Run id: `20260831T224354Z-5082de88`
- Record count: `25`
- Verifier profile: `python_sympy_exact_v1`

## Declared semantics

Exact algebraic and local structural identities that were lowered to executable residuals were evaluated under the declared symbolic semantics. Only obligations returning exact ZERO are listed as machine-verified.

- ZERO is exact symbolic simplification of an executable residual to 0 under the declared namespace.
- NONZERO is an exact probe proving the residual is not 0.
- UNKNOWN and other non-ZERO statuses are not machine-verified.
- Split parents are never engine ZERO; CERTIFIED_BY_CHILDREN is displayed as `SPLIT — all children certified` and is never displayed as ZERO.
- Verified-table inclusion uses `schema.may_appear_in_verified_table` only. Other tables use `schema.table_bucket`.
- VERIFIED TABLE IS GENERATED, NOT AUTHORED.

## Source snapshot

- config_sha256: `39c74759b1bb5f6dfdd63345089f9bdc7f19f8e10f7fa87308182d9eed2ad22c`
- manuscript_sha256: `356f644c736b2dabebec651c88265133a060ab566755a32e4f2460c519e3a35a`
- equation_manifest_sha256: `f838690d679a0522cb2d73b676be0cc5d19e8f063759bf82e792f2d892a6ab95`
- edge_manifest_sha256: `935c1455cf3a3f712d3696729373fa1f73c3adae8d11356ccbf3b028ec51f2be`
- assumptions_sha256: `4fe1705cd8c427b2d989836d35dcc035366091569e7094925baf7f8bbaefa91a`
- record source_snapshot_hash values: `9df8f5e011cae94b406ebe2d955d08c24c1fa8e2e8f1bac6d19e4bd600f53df5`
- record engine_version values: `0.3.0`

## Verification summary

| Table | Rows |
| --- | --- |
| `TABLE_VERIFIED` | 18 |
| `TABLE_STRUCTURAL` | 4 |
| `TABLE_NONZERO` | 0 |
| `TABLE_UNCERTIFIED` | 3 |

| Status | Public label | Count |
| --- | --- | --- |
| `DEFINITION` | DEFINITION | 2 |
| `NOT_LOWERED` | NOT_LOWERED | 2 |
| `RECORDED` | RECORDED | 1 |
| `SPLIT` | SPLIT | 1 |
| `UNKNOWN` | UNKNOWN | 1 |
| `ZERO` | ZERO | 18 |

- integrity FAIL records: `0`

## Machine-verified identities

Exact algebraic and local structural identities that were lowered to executable residuals were evaluated under the declared symbolic semantics. Only obligations returning exact ZERO are listed as machine-verified.

| Edge ID | Manuscript equation reference(s) | Claim / transformation | Executable residual | Derivation type | Declared assumptions | Verifier | Result | Artifact link |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D.A-antisym | eq.D-74, expressions/A_pair.txt, expressions/A_pair_swapped.txt, expressions/R_A_antisym.txt | A21^a A12^b - A12^a A21^b equals -(A12^a A21^b - A12^b A21^a) for commuting scalars | (A21a*A12b - A12a*A21b) - (-(A12a*A21b - A12b*A21a))  | ALGEBRAIC_EQUIVALENCE | A21a, A12b, A12a, A21b | python_sympy_exact_v1 | ZERO | expressions/R_A_antisym.txt |
| D.A-to-Omega | eq.D-74, eq.D-75, expressions/A_pair_swapped.txt, expressions/i_Omega.txt, expressions/R_A_to_Omega.txt | after inserting Omega_ab^1 = I (A12^a A21^b - A12^b A21^a), the A bilinear equals I Omega | (-(A12a*A21b - A12b*A21a)) - (I*(I*(A12a*A21b - A12b*A21a)))  | ALGEBRAIC_EQUIVALENCE | A12a, A21b, A12b, A21a, Oab1 | python_sympy_exact_v1 | ZERO | expressions/R_A_to_Omega.txt |
| D.C12-regroup | eq.D-71, eq.D-72, expressions/C12_expanded.txt, expressions/C12_regrouped.txt, expressions/R_C12_regroup.txt | C1 and C2 factor by regrouping commuting velocity products | ((v21a*(v12b*v1c + v1b*v12c) - v12a*(v21b*v1c + v1b*v21c)) - (v1c*(v21a*v12b - v12a*v21b) + v1b*(v21a*v12c - v12a*v21c))) + ((-v21a*(v2b*v12c + v12b*v2c) + v12a*(v2b*v21c + v21b*v2c)) - (v2c*(v12a*v21b - v21a*v12b) + v2b*(v12a*v21c - v21a*v12c)))  | ALGEBRAIC_EQUIVALENCE | v21a, v12b, v1c, v1b, v12c, v12a, v21b, v21c, v2b, v2c | python_sympy_exact_v1 | ZERO | expressions/R_C12_regroup.txt |
| D.K1A-metric-subst | eq.D-60, expressions/K1A_regrouped.txt, expressions/K1A_metric.txt, expressions/R_K1A_metric.txt | after substituting the declared metric-velocity pair for g_ab and g_ac, regrouped K_{1A} equals 2 e12^2 (v1^c g_ab + v1^b g_ac) | (v1c*(v21a*v12b + v12a*v21b) + v1b*(v21a*v12c + v12a*v21c)) - (v1c*(v12a*v21b + v12b*v21a) + v1b*(v12a*v21c + v12c*v21a))  | ALGEBRAIC_EQUIVALENCE | v1c, v21a, v12b, v12a, v21b, v1b, v12c, v21c, e12, gab, gac | python_sympy_exact_v1 | ZERO | expressions/R_K1A_metric.txt |
| D.K1A-regroup | eq.D-59, eq.D-60, expressions/K1A_expanded.txt, expressions/K1A_regrouped.txt, expressions/R_K1A_regroup.txt | K_{1A} factors by regrouping commuting velocity products | (v21a*(v12b*v1c + v1b*v12c) + v12a*(v21b*v1c + v1b*v21c)) - (v1c*(v21a*v12b + v12a*v21b) + v1b*(v21a*v12c + v12a*v21c))  | ALGEBRAIC_EQUIVALENCE | v21a, v12b, v1c, v1b, v12c, v12a, v21b, v21c | python_sympy_exact_v1 | ZERO | expressions/R_K1A_regroup.txt |
| D.Omega2-relabel | eq.D-77, eq.D-78, expressions/sigma_m1_simplified.txt, expressions/sigma_m1_band_sum.txt, expressions/R_Omega2_relabel.txt | using Omega^2 = -Omega^1, the two-band sigma^{(-1)} compactifies to a sum over n=1,2 | ((1/4)*((v1c*Oab1 + v1b*Oac1)*f1p - (v2c*Oab1 + v2b*Oac1)*f2p)) - ((1/4)*((v1c*Oab1 + v1b*Oac1)*f1p + (v2c*(-Oab1) + v2b*(-Oac1))*f2p))  | INDEX_RELABELING | v1c, Oab1, v1b, Oac1, f1p, v2c, v2b, f2p, Oab2, Oac2 | python_sympy_exact_v1 | ZERO | expressions/R_Omega2_relabel.txt |
| D.T0-local-sign | eq.D-119, expressions/T0_chain.txt, expressions/T0_surface.txt, expressions/R_T0_local_sign.txt | after the chain rule, the last two written members of the T0 display are algebraically equal | (-(f1p*v1a - f2p*v2a)*(gbc/e12)) - (gbc*(v2a*f2p - v1a*f1p)/e12)  | ALGEBRAIC_EQUIVALENCE | f1p, v1a, f2p, v2a, gbc, e12 | python_sympy_exact_v1 | ZERO | expressions/R_T0_local_sign.txt |
| D.T0T1-regroup | eq.D-120, eq.D-121, expressions/T0T1_mixed.txt, expressions/T0T1_grouped.txt, expressions/R_T0T1_regroup.txt | T0+T1 regroups by f1' and f2' | ((1/e12)*(gbc*(v2a*f2p - v1a*f1p) + (v1c*gab + v1b*gac - v1a*gbc)*f1p - (v2c*gab + v2b*gac - v2a*gbc)*f2p)) - ((1/e12)*(f1p*(v1c*gab + v1b*gac - 2*v1a*gbc) - f2p*(v2c*gab + v2b*gac - 2*v2a*gbc)))  | ALGEBRAIC_EQUIVALENCE | e12, gbc, v2a, f2p, v1a, f1p, v1c, gab, v1b, gac, v2c, v2b | python_sympy_exact_v1 | ZERO | expressions/R_T0T1_regroup.txt |
| D.TA-TBgeo-cancel | eq.D-61, eq.D-68, expressions/TA_plus_TBgeo.txt, expressions/zero.txt, expressions/R_TA_TBgeo.txt | geometric pieces T_A^{(-2)} + T_{B,geo}^{(-2)} cancel | (e12/4)*((gab*v2c + gac*v2b)*f2p - (gab*v1c + gac*v1b)*f1p) + (e12/4)*((gac*v1b + gab*v1c)*f1p - (gac*v2b + gab*v2c)*f2p)  | ALGEBRAIC_EQUIVALENCE | e12, gab, v2c, gac, v2b, f2p, v1c, v1b, f1p | python_sympy_exact_v1 | ZERO | expressions/R_TA_TBgeo.txt |
| D.TA-prefactor | eq.D-60, eq.D-61, expressions/TA_unreduced.txt, expressions/TA_reduced.txt, expressions/R_TA_prefactor.txt | the T_A^{(-2)} prefactor 2 e12^2 / (8 e12) equals e12/4 and the two written T_A forms agree | ((2*e12**2)/(8*e12)*(-(v1c*gab + v1b*gac)*f1p + (v2c*gab + v2b*gac)*f2p)) - ((e12/4)*((gab*v2c + gac*v2b)*f2p - (gab*v1c + gac*v1b)*f1p))  | ALGEBRAIC_EQUIVALENCE | e12, v1c, gab, v1b, gac, f1p, v2c, v2b, f2p | python_sympy_exact_v1 | ZERO | expressions/R_TA_prefactor.txt |
| D.TBgeo-eps21 | eq.D-66, eq.D-67, expressions/TBgeo_e21.txt, expressions/TBgeo_e12.txt, expressions/R_TBgeo_eps21.txt | two-band T_{B,geo}^{(-2)} with e21 rewritten by e21=-e12 matches the e12 form | ((1/4)*(e12*(gac*v1b + gab*v1c)*f1p + (-e12)*(gac*v2b + gab*v2c)*f2p)) - ((e12/4)*((gac*v1b + gab*v1c)*f1p - (gac*v2b + gab*v2c)*f2p))  | ALGEBRAIC_EQUIVALENCE | e12, gac, v1b, gab, v1c, f1p, e21, v2b, v2c, f2p | python_sympy_exact_v1 | ZERO | expressions/R_TBgeo_eps21.txt |
| D.Vab-eps21 | eq.D-73, expressions/Vab_factored_subst.txt, expressions/Vab_e12sq.txt, expressions/R_Vab_eps21.txt | using e12 e21 = -e12^2 converts the factored V_ab prefactor into e12^2 | ((-1)*(e12*(-e12))*(A21a*A12b - A12a*A21b)) - (e12**2*(A21a*A12b - A12a*A21b))  | ALGEBRAIC_EQUIVALENCE | e12, A21a, A12b, A12a, A21b | python_sympy_exact_v1 | ZERO | expressions/R_Vab_eps21.txt |
| D.Vab-expand | eq.D-73, expressions/Vab_FH.txt, expressions/Vab_factored.txt, expressions/R_Vab_expand.txt | the Feynman-Hellmann substituted V_ab product expands to (-1)(e12 e21) times the A bilinear | ((-I*e12*A21a)*(-I*e21*A12b) - (-I*e21*A12a)*(-I*e12*A21b)) - ((-1)*(e12*e21)*(A21a*A12b - A12a*A21b))  | ALGEBRAIC_EQUIVALENCE | e12, A21a, e21, A12b, A12a, A21b | python_sympy_exact_v1 | ZERO | expressions/R_Vab_expand.txt |
| D.compact-nbar | eq.D-126, eq.D-127, expressions/geo_eps21_fprime.txt, expressions/geo_nbar.txt, expressions/R_compact_nbar.txt | the n=1,2 form with e_{n nbar} and f_n' = 2 f_{0,n}' matches the compact rewrite | ((2*f01p)*(-Rational(1,2)*dagbc + (1/e12)*(gab*v1c + gac*v1b - 2*gbc*v1a)) + (2*f02p)*(-Rational(1,2)*dagbc + (1/e21)*(gab*v2c + gac*v2b - 2*gbc*v2a))) - (2*f01p*(-Rational(1,2)*dagbc + (1/e12)*(gab*v1c + gac*v1b - 2*gbc*v1a)) + 2*f02p*(-Rational(1,2)*dagbc + (1/e21)*(gab*v2c + gac*v2b - 2*gbc*v2a)))  | INDEX_RELABELING | f1p, dagbc, e12, gab, v1c, gac, v1b, gbc, v1a, f2p, e21, v2c, v2b, v2a, f01p, f02p | python_sympy_exact_v1 | ZERO | expressions/R_compact_nbar.txt |
| D.eps21-symmetrize | eq.D-125, eq.D-126, expressions/geo_fnp_subst.txt, expressions/geo_eps21.txt, expressions/R_eps21_symmetrize.txt | rewriting the band-2 denominator with e21=-e12 yields the symmetric two-band form | (f1p*(-Rational(1,2)*dagbc + (1/e12)*(v1c*gab + v1b*gac - 2*v1a*gbc)) + f2p*(-Rational(1,2)*dagbc - (1/e12)*(v2c*gab + v2b*gac - 2*v2a*gbc))) - (f1p*(-Rational(1,2)*dagbc + (1/e12)*(gab*v1c + gac*v1b - 2*gbc*v1a)) + f2p*(-Rational(1,2)*dagbc + (1/(-e12))*(gab*v2c + gac*v2b - 2*gbc*v2a)))  | ALGEBRAIC_EQUIVALENCE | f1p, dagbc, e12, v1c, gab, v1b, gac, v1a, gbc, f2p, v2c, v2b, v2a, e21 | python_sympy_exact_v1 | ZERO | expressions/R_eps21_symmetrize.txt |
| D.geo-T2-subst | eq.D-122, eq.D-125, expressions/geo_T2_plus_T0T1.txt, expressions/geo_fnp.txt, expressions/R_geo_T2_subst.txt | substituting the declared T2 IBP result into sigma^geo and grouping by f_n' reproduces Eq. (D-125) | ((-Rational(1,2)*dagbc*(f1p + f2p)) + (1/e12)*(f1p*(v1c*gab + v1b*gac - 2*v1a*gbc) - f2p*(v2c*gab + v2b*gac - 2*v2a*gbc))) - (f1p*(-Rational(1,2)*dagbc + (1/e12)*(v1c*gab + v1b*gac - 2*v1a*gbc)) + f2p*(-Rational(1,2)*dagbc - (1/e12)*(v2c*gab + v2b*gac - 2*v2a*gbc)))  | ALGEBRAIC_EQUIVALENCE | dagbc, f1p, f2p, e12, v1c, gab, v1b, gac, v1a, gbc, v2c, v2b, v2a | python_sympy_exact_v1 | ZERO | expressions/R_geo_T2_subst.txt |
| D.metric-pair | eq.D-key-identities, eq.D-60, expressions/mv_pair_paper_order.txt, expressions/mv_pair_K1A_order.txt, expressions/R_metric_pair.txt | the metric-velocity pair in paper index order equals the pair appearing in regrouped K_{1A} | (v12a*v21b + v12b*v21a) - (v21a*v12b + v12a*v21b)  | PAIRWISE_REDUCTION | v12a, v21b, v12b, v21a | python_sympy_exact_v1 | ZERO | expressions/R_metric_pair.txt |
| D.sigma-m1-Ii | eq.D-70, eq.D-77, expressions/sigma_m1_with_i.txt, expressions/sigma_m1_simplified.txt, expressions/R_sigma_m1_Ii.txt | (-I)/(4 e12^2) * (I e12^2) cancels to 1/4 on the sigma^{(-1)} kernel | ((-I)/(4*e12**2)*(I*e12**2)*((v1c*Oab1 + v1b*Oac1)*f1p - (v2c*Oab1 + v2b*Oac1)*f2p)) - ((1/4)*((v1c*Oab1 + v1b*Oac1)*f1p - (v2c*Oab1 + v2b*Oac1)*f2p))  | ALGEBRAIC_EQUIVALENCE | e12, v1c, Oab1, v1b, Oac1, f1p, v2c, v2b, f2p | python_sympy_exact_v1 | ZERO | expressions/R_sigma_m1_Ii.txt |

## Structural steps

DEFINITION, RECORDED, SPLIT, and CERTIFIED_BY_CHILDREN records. CERTIFIED_BY_CHILDREN is never displayed as ZERO.

| Edge ID | Manuscript equation reference(s) | Claim / transformation | Executable residual | Derivation type | Declared assumptions | Verifier | Result | Artifact link |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B.j2-to-sigma | eq.B-24, eq.B-25 | the four current channels are translated into the frequency-space conductivity kernel |  | BOOKKEEPING |  | python_sympy_exact_v1 | RECORDED |  |
| B.split-j2 | eq.B-23, eq.B-24 | second-order current j_a^{(2)} is decomposed into four O(A^2) channels (I)-(IV) |  | SPLIT_PARENT |  | python_sympy_exact_v1 | SPLIT |  |
| D.mv-identity | eq.D-key-identities, expressions/mv_velocity_pair.txt, expressions/mv_metric_form.txt | two-band metric-velocity relation is introduced as a stated identity | (v12a*v21b + v12b*v21a ) - (2*e12**2*gab ) | DEFINITION_INSERTION | v12a, v21b, v12b, v21a, e12, gab | python_sympy_exact_v1 | DEFINITION |  |
| E.diag-2nd | eq.E-128 | multiband diagonal second-derivative identity is introduced as a stated key identity |  | DEFINITION_INSERTION |  | python_sympy_exact_v1 | DEFINITION |  |

## Nonzero residuals

### POTENTIAL DERIVATION MISMATCHES

The encoded residual is NONZERO under the declared symbolic semantics. Check transcription, assumptions, conventions, and the derivation step.

No NONZERO records in this run.

## Uncertified / asymptotic / integral

Definitions, integral-level arguments, asymptotic remainder claims, and unsupported transformations are tracked separately rather than being misreported as exact algebraic identities.

| Edge ID | Manuscript equation reference(s) | Claim / transformation | Executable residual | Derivation type | Declared assumptions | Verifier | Result | Artifact link |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D.T0-ibp-global | eq.D-114, eq.D-119 | integration by parts in k-space converts the T0 Fermi-sea form into a Fermi-surface form |  | INTEGRAL_ARGUMENT |  | python_sympy_exact_v1 | NOT_LOWERED |  |
| D.T2-ibp-global | eq.D-123, eq.D-124 | integration by parts converts T2 ~ g ∂_a(f') into a - (∂_a g) f' Fermi-surface term |  | INTEGRAL_ARGUMENT |  | python_sympy_exact_v1 | NOT_LOWERED |  |
| D.gamma-asymptotic | eq.D-57 | DC conductivity admits a Gamma expansion through O(Gamma^0) with remainder O(Gamma) |  | ASYMPTOTIC_CLAIM |  | python_sympy_exact_v1 | UNKNOWN |  |

- asymptotic/limit/integral records: `3`

## Assumptions

- workspace assumptions_sha256: `4fe1705cd8c427b2d989836d35dcc035366091569e7094925baf7f8bbaefa91a`
- Declared assumptions on records:
- `D.mv-identity`: `v12a`, `v21b`, `v12b`, `v21a`, `e12`, `gab`
- `D.K1A-regroup`: `v21a`, `v12b`, `v1c`, `v1b`, `v12c`, `v12a`, `v21b`, `v21c`
- `D.metric-pair`: `v12a`, `v21b`, `v12b`, `v21a`
- `D.K1A-metric-subst`: `v1c`, `v21a`, `v12b`, `v12a`, `v21b`, `v1b`, `v12c`, `v21c`, `e12`, `gab`, `gac`
- `D.TA-prefactor`: `e12`, `v1c`, `gab`, `v1b`, `gac`, `f1p`, `v2c`, `v2b`, `f2p`
- `D.TBgeo-eps21`: `e12`, `gac`, `v1b`, `gab`, `v1c`, `f1p`, `e21`, `v2b`, `v2c`, `f2p`
- `D.TA-TBgeo-cancel`: `e12`, `gab`, `v2c`, `gac`, `v2b`, `f2p`, `v1c`, `v1b`, `f1p`
- `D.C12-regroup`: `v21a`, `v12b`, `v1c`, `v1b`, `v12c`, `v12a`, `v21b`, `v21c`, `v2b`, `v2c`
- `D.Vab-expand`: `e12`, `A21a`, `e21`, `A12b`, `A12a`, `A21b`
- `D.Vab-eps21`: `e12`, `A21a`, `A12b`, `A12a`, `A21b`
- `D.A-antisym`: `A21a`, `A12b`, `A12a`, `A21b`
- `D.A-to-Omega`: `A12a`, `A21b`, `A12b`, `A21a`, `Oab1`
- `D.sigma-m1-Ii`: `e12`, `v1c`, `Oab1`, `v1b`, `Oac1`, `f1p`, `v2c`, `v2b`, `f2p`
- `D.Omega2-relabel`: `v1c`, `Oab1`, `v1b`, `Oac1`, `f1p`, `v2c`, `v2b`, `f2p`, `Oab2`, `Oac2`
- `D.T0-local-sign`: `f1p`, `v1a`, `f2p`, `v2a`, `gbc`, `e12`
- `D.T0T1-regroup`: `e12`, `gbc`, `v2a`, `f2p`, `v1a`, `f1p`, `v1c`, `gab`, `v1b`, `gac`, `v2c`, `v2b`
- `D.geo-T2-subst`: `dagbc`, `f1p`, `f2p`, `e12`, `v1c`, `gab`, `v1b`, `gac`, `v1a`, `gbc`, `v2c`, `v2b`, `v2a`
- `D.eps21-symmetrize`: `f1p`, `dagbc`, `e12`, `v1c`, `gab`, `v1b`, `gac`, `v1a`, `gbc`, `f2p`, `v2c`, `v2b`, `v2a`, `e21`
- `D.compact-nbar`: `f1p`, `dagbc`, `e12`, `gab`, `v1c`, `gac`, `v1b`, `gbc`, `v1a`, `f2p`, `e21`, `v2c`, `v2b`, `v2a`, `f01p`, `f02p`

Assumptions are those declared on the workspace and records. None were inferred.

## Reproduction

Tables and this report are regenerated from immutable machine records. Existing markdown is not evidence and is overwritten.

```
symbolic-compactification audit table <workspace> --run 20260831T224354Z-5082de88
symbolic-compactification audit report <workspace> --run 20260831T224354Z-5082de88
```

## Limitations

Definitions, integral-level arguments, asymptotic remainder claims, and unsupported transformations are tracked separately rather than being misreported as exact algebraic identities.

Finite coefficient identities do not certify an enclosing asymptotic remainder. Integral-level arguments are not local executable residuals. Split parents are never engine ZERO.
This report does not certify a manuscript as a whole.

