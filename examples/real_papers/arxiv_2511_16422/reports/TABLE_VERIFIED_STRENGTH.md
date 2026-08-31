# Machine-verified identities (with verification strength)

Generated from `reports/verification_table.json` plus
`verification_strength.yaml`. This file **cannot create ZERO**.
A row appears here only if the machine table already lists it as
integrity-PASS engine ZERO.

**19 machine ZERO** = **13 DIRECT_EXACT** + **6 SUBSTITUTION_EXACT**.

18 executable equation-level identities were machine-verified as exact ZERO under the declared symbolic semantics. One asymptotic remainder claim remained UNKNOWN, and two global integration-by-parts steps remained NOT_LOWERED.

## Strength legend

| Strength | Meaning |
| --- | --- |
| `DIRECT_EXACT` | The displayed residual is an unsubstituted local identity. |
| `SUBSTITUTION_EXACT` | Exact *given* a declared upstream identity written into the residual. Does not independently prove that identity. |
| `CERTIFIED_BY_CHILDREN` | Split parent (never a ZERO row; none in this verified table). |

`SUBSTITUTION_EXACT` means: given the declared upstream identity, the downstream transformation is exact. It does **not** mean the tool independently proved $\epsilon_{21}=-\epsilon_{12}$, $\Omega_2=-\Omega_1$, $f'=2f_0'$, or the metric-velocity theorem.

## DIRECT_EXACT

| Paper equation(s) | Transformation | Type | Strength | Result | Evidence |
| --- | --- | --- | --- | --- | --- |
| Eq. (D-74) | A21^a A12^b - A12^a A21^b equals -(A12^a A21^b - A12^b A21^a) for commuting scalars | `ALGEBRAIC_EQUIVALENCE` | `DIRECT_EXACT` | `ZERO` | `expressions/R_A_antisym.txt` |
| Eq. (D-71) → Eq. (D-72) | C1 and C2 factor by regrouping commuting velocity products | `ALGEBRAIC_EQUIVALENCE` | `DIRECT_EXACT` | `ZERO` | `expressions/R_C12_regroup.txt` |
| Eq. (D-59) → Eq. (D-60) | K_{1A} factors by regrouping commuting velocity products | `ALGEBRAIC_EQUIVALENCE` | `DIRECT_EXACT` | `ZERO` | `expressions/R_K1A_regroup.txt` |
| Eq. (D-119) (local members only) | after the chain rule, the last two written members of the T0 display are algebraically equal | `ALGEBRAIC_EQUIVALENCE` | `DIRECT_EXACT` | `ZERO` | `expressions/R_T0_local_sign.txt` |
| Eq. (D-120) → Eq. (D-121) | T0+T1 regroups by f1' and f2' | `ALGEBRAIC_EQUIVALENCE` | `DIRECT_EXACT` | `ZERO` | `expressions/R_T0T1_regroup.txt` |
| Eq. (D-61) + Eq. (D-67) → Eq. (D-68) | geometric pieces T_A^{(-2)} + T_{B,geo}^{(-2)} cancel | `ALGEBRAIC_EQUIVALENCE` | `DIRECT_EXACT` | `ZERO` | `expressions/R_TA_TBgeo.txt` |
| Eq. (D-60) → Eq. (D-61) | the T_A^{(-2)} prefactor 2 e12^2 / (8 e12) equals e12/4 and the two written T_A forms agree | `ALGEBRAIC_EQUIVALENCE` | `DIRECT_EXACT` | `ZERO` | `expressions/R_TA_prefactor.txt` |
| Eq. (D-73) | using e12 e21 = -e12^2 converts the factored V_ab prefactor into e12^2 | `ALGEBRAIC_EQUIVALENCE` | `DIRECT_EXACT` | `ZERO` | `expressions/R_Vab_eps21.txt` |
| Eq. (D-73) | the Feynman-Hellmann substituted V_ab product expands to (-1)(e12 e21) times the A bilinear | `ALGEBRAIC_EQUIVALENCE` | `DIRECT_EXACT` | `ZERO` | `expressions/R_Vab_expand.txt` |
| Eq. (D-122) + declared Eq. (D-124) → Eq. (D-125) | substituting the declared T2 IBP result into sigma^geo and grouping by f_n' reproduces Eq. (D-125) | `ALGEBRAIC_EQUIVALENCE` | `DIRECT_EXACT` | `ZERO` | `expressions/R_geo_T2_subst.txt` |
| local Leibniz rule for Eq. (D-114)→(D-119) and Eq. (D-123)→(D-124) | local Leibniz rule d_k(u v) = (d_k u) v + u (d_k v) | `ALGEBRAIC_EQUIVALENCE` | `DIRECT_EXACT` | `ZERO` | `expressions/R_leibniz_product_rule.txt` |
| metric-velocity pair (unnumbered) → Eq. (D-60) | the metric-velocity pair in paper index order equals the pair appearing in regrouped K_{1A} | `PAIRWISE_REDUCTION` | `DIRECT_EXACT` | `ZERO` | `expressions/R_metric_pair.txt` |
| Eq. (D-70) → Eq. (D-77) | (-I)/(4 e12^2) * (I e12^2) cancels to 1/4 on the sigma^{(-1)} kernel | `ALGEBRAIC_EQUIVALENCE` | `DIRECT_EXACT` | `ZERO` | `expressions/R_sigma_m1_Ii.txt` |

## SUBSTITUTION_EXACT

| Paper equation(s) | Transformation | Substituted identity | Type | Strength | Result | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Eq. (D-74) → Eq. (D-75) | after inserting Omega_ab^1 = I (A12^a A21^b - A12^b A21^a), the A bilinear equals I Omega | Omega_ab^1 := I (A12^a A21^b - A12^b A21^a) | `ALGEBRAIC_EQUIVALENCE` | `SUBSTITUTION_EXACT` | `ZERO` | `expressions/R_A_to_Omega.txt` |
| Eq. (D-60) | after substituting the declared metric-velocity pair for g_ab and g_ac, regrouped K_{1A} equals 2 e12^2 (v1^c g_ab + v1^b g_ac) | two-band metric-velocity pair for g_ab and g_ac | `ALGEBRAIC_EQUIVALENCE` | `SUBSTITUTION_EXACT` | `ZERO` | `expressions/R_K1A_metric.txt` |
| Eq. (D-77) → Eq. (D-78) | using Omega^2 = -Omega^1, the two-band sigma^{(-1)} compactifies to a sum over n=1,2 | Omega^2 = -Omega^1 | `INDEX_RELABELING` | `SUBSTITUTION_EXACT` | `ZERO` | `expressions/R_Omega2_relabel.txt` |
| Eq. (D-66) → Eq. (D-67) | two-band T_{B,geo}^{(-2)} with e21 rewritten by e21=-e12 matches the e12 form | epsilon_21 = -epsilon_12 | `ALGEBRAIC_EQUIVALENCE` | `SUBSTITUTION_EXACT` | `ZERO` | `expressions/R_TBgeo_eps21.txt` |
| Eq. (D-126) → Eq. (D-127) | the n=1,2 form with e_{n nbar} and f_n' = 2 f_{0,n}' matches the compact rewrite | f_n' = 2 f_{0,n}' | `INDEX_RELABELING` | `SUBSTITUTION_EXACT` | `ZERO` | `expressions/R_compact_nbar.txt` |
| Eq. (D-125) → Eq. (D-126) | rewriting the band-2 denominator with e21=-e12 yields the symmetric two-band form | epsilon_21 = -epsilon_12 | `ALGEBRAIC_EQUIVALENCE` | `SUBSTITUTION_EXACT` | `ZERO` | `expressions/R_eps21_symmetrize.txt` |

## Outside this table (soundness, not failure)

See `TABLE_UNCERTIFIED.md`:

- Eq. (D-57) full $\Gamma$ expansion: `ASYMPTOTIC_CLAIM` / `UNKNOWN`
- Eq. (D-114) → (D-119) global BZ IBP: `INTEGRAL_ARGUMENT` / `NOT_LOWERED`
- Eq. (D-123) → (D-124) global BZ IBP: `INTEGRAL_ARGUMENT` / `NOT_LOWERED`

The machine-authoritative residual table remains `TABLE_VERIFIED.md`.
