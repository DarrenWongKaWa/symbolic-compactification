# Evidence hierarchy

Certificate class is **provenance type**, not mathematical truth ranking.
`DIRECT_EXACT` residuals are unsubstituted engine ZERO.
`SUBSTITUTION_EXACT` residuals are ZERO after a declared upstream identity.
`RULE_CERTIFICATE` is local child ZERO plus a declared theorem/domain;
it is **not** engine ZERO for the global claim.
`ASYMPTOTIC` remainder claims stay UNKNOWN without a remainder certificate.

This table cannot create ZERO. Engine ZERO rows are copied from
`verification_table.json` (`may_appear_in_verified_table`).

| Paper step | Certificate class | Machine child | Rule / assumption | Status |
| --- | --- | --- | --- | --- |
| Eq. (D-74) | `DIRECT_EXACT` | `expressions/R_A_antisym.txt` ZERO | — | `ZERO` |
| Eq. (D-74) → Eq. (D-75) | `SUBSTITUTION_EXACT` | `expressions/R_A_to_Omega.txt` ZERO | Omega_ab^1 := I (A12^a A21^b - A12^b A21^a) | `ZERO` |
| Eq. (D-71) → Eq. (D-72) | `DIRECT_EXACT` | `expressions/R_C12_regroup.txt` ZERO | — | `ZERO` |
| Eq. (D-60) | `SUBSTITUTION_EXACT` | `expressions/R_K1A_metric.txt` ZERO | two-band metric-velocity pair for g_ab and g_ac | `ZERO` |
| Eq. (D-59) → Eq. (D-60) | `DIRECT_EXACT` | `expressions/R_K1A_regroup.txt` ZERO | — | `ZERO` |
| Eq. (D-77) → Eq. (D-78) | `SUBSTITUTION_EXACT` | `expressions/R_Omega2_relabel.txt` ZERO | Omega^2 = -Omega^1 | `ZERO` |
| Eq. (D-119) (local members only) | `DIRECT_EXACT` | `expressions/R_T0_local_sign.txt` ZERO | — | `ZERO` |
| Eq. (D-120) → Eq. (D-121) | `DIRECT_EXACT` | `expressions/R_T0T1_regroup.txt` ZERO | — | `ZERO` |
| Eq. (D-61) + Eq. (D-67) → Eq. (D-68) | `DIRECT_EXACT` | `expressions/R_TA_TBgeo.txt` ZERO | — | `ZERO` |
| Eq. (D-60) → Eq. (D-61) | `DIRECT_EXACT` | `expressions/R_TA_prefactor.txt` ZERO | — | `ZERO` |
| Eq. (D-66) → Eq. (D-67) | `SUBSTITUTION_EXACT` | `expressions/R_TBgeo_eps21.txt` ZERO | epsilon_21 = -epsilon_12 | `ZERO` |
| Eq. (D-73) | `DIRECT_EXACT` | `expressions/R_Vab_eps21.txt` ZERO | — | `ZERO` |
| Eq. (D-73) | `DIRECT_EXACT` | `expressions/R_Vab_expand.txt` ZERO | — | `ZERO` |
| Eq. (D-126) → Eq. (D-127) | `SUBSTITUTION_EXACT` | `expressions/R_compact_nbar.txt` ZERO | f_n' = 2 f_{0,n}' | `ZERO` |
| Eq. (D-125) → Eq. (D-126) | `SUBSTITUTION_EXACT` | `expressions/R_eps21_symmetrize.txt` ZERO | epsilon_21 = -epsilon_12 | `ZERO` |
| Eq. (D-122) + declared Eq. (D-124) → Eq. (D-125) | `DIRECT_EXACT` | `expressions/R_geo_T2_subst.txt` ZERO | — | `ZERO` |
| local Leibniz rule for Eq. (D-114)→(D-119) and Eq. (D-123)→(D-124) | `DIRECT_EXACT` | `expressions/R_leibniz_product_rule.txt` ZERO | — | `ZERO` |
| metric-velocity pair (unnumbered) → Eq. (D-60) | `DIRECT_EXACT` | `expressions/R_metric_pair.txt` ZERO | — | `ZERO` |
| Eq. (D-70) → Eq. (D-77) | `DIRECT_EXACT` | `expressions/R_sigma_m1_Ii.txt` ZERO | — | `ZERO` |
| Eq. (D-114) → Eq. (D-119) | `RULE_CERTIFICATE` | `D.leibniz-product-rule` ZERO | BZ torus periodicity | `CERTIFIED_BY_RULE` |
| Eq. (D-123) → Eq. (D-124) | `RULE_CERTIFICATE` | `D.leibniz-product-rule` ZERO | BZ torus periodicity | `CERTIFIED_BY_RULE` |
| Eq. (D-57) | `ASYMPTOTIC` | coefficient children not claimed as remainder | remainder absent | `UNKNOWN` |
