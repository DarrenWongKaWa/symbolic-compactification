# Reviewer-style overlay (experiment, not a product table)

`ZERO` below is engine exact `ZERO` on an exact-algebra child. Parent
approximation overlays are never called `ZERO`.

| Transition | Scientific move | Authority | Machine check | Overlay |
|---|---|---|---|---|
| AA-05 \(K_{1A}\) (D-59)\(\to\)(D-60) | algebra | — | `ZERO` | `ENGINE_ZERO` |
| AA-01 \(E_0\to\widetilde E_0\to E_1\) | weak-\(\Gamma\) truncation then regroup | author declared | naive `NONZERO`; downstream `ZERO` | `CERTIFIED_UNDER_DECLARED_APPROXIMATION` |
| AA-02 same truncation, sign error | weak-\(\Gamma\) then wrong algebra | author declared | downstream `NONZERO` | `REFUSED_DOWNSTREAM_NONZERO` |
| AA-03 Guo (D-57) | \(\mathcal{O}(\Gamma)\) remainder | author declared | remainder `UNKNOWN`; not lowered | `ASYMPTOTIC_DECLARED_ONLY` |
| AA-06 \(T_{B,\mathrm{geo}}\) (D-66)\(\to\)(D-67) | substitution \(e_{21}=-e_{12}\) | identity, not approx | naive `NONZERO` | `SUBSTITUTION_NOT_APPROXIMATION` |
| AA-04 \(E_0\to E_1\) undeclared | hidden truncation | **none** | naive `NONZERO`; hidden \(T_A\) `ZERO` | `UNDECLARED_APPROXIMATION_REQUIRED` |
| AA-07 model truncation | same \(T_A\) as AA-01 | model proposed | downstream `ZERO` | `MODEL_APPROX_NOT_AUTHORIZED` |
| AA-08 remainder as exact claim | naive \(E_0=\widetilde E_0\) | none | `NONZERO` | `NAIVE_REMAINDER_AS_EXACT_REFUSED` |
| AA-10 \(G^0\) coefficient | coefficient child | author declared | coeff `ZERO`; remainder not certified | `COEFFICIENT_ZERO_NOT_REMAINDER` |
