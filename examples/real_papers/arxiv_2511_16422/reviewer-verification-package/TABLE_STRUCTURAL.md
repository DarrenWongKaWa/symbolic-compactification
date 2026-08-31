# TABLE_STRUCTURAL

Definitions, recorded bookkeeping, split parents, split parents whose children are all certified, and BZ-torus IBP parents certified by local ZERO plus a declared periodicity theorem.

CERTIFIED_BY_CHILDREN is displayed as `SPLIT — all children certified`. CERTIFIED_BY_RULE is displayed as `CERTIFIED_BY_RULE — local ZERO + declared BZ-torus IBP`. Neither is displayed as ZERO; SymPy did not evaluate the integral.

| Edge ID | Manuscript equation reference(s) | Claim / transformation | Executable residual | Derivation type | Declared assumptions | Verifier | Result | Artifact link |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B.j2-to-sigma | eq.B-24, eq.B-25 | the four current channels are translated into the frequency-space conductivity kernel |  | BOOKKEEPING |  | python_sympy_exact_v1 | RECORDED |  |
| B.split-j2 | eq.B-23, eq.B-24 | second-order current j_a^{(2)} is decomposed into four O(A^2) channels (I)-(IV) |  | SPLIT_PARENT |  | python_sympy_exact_v1 | SPLIT |  |
| D.T0-ibp-global | eq.D-114, eq.D-119 | BZ-torus IBP converts the T0 Fermi-sea density into a Fermi-surface density |  | BZ_PERIODIC_INTEGRATION_BY_PARTS |  | python_sympy_exact_v1 | CERTIFIED_BY_RULE — local ZERO + declared BZ-torus IBP |  |
| D.T2-ibp-global | eq.D-123, eq.D-124 | BZ-torus IBP converts T2 ~ g d_a(f') into a -(d_a g) f' Fermi-surface term |  | BZ_PERIODIC_INTEGRATION_BY_PARTS |  | python_sympy_exact_v1 | CERTIFIED_BY_RULE — local ZERO + declared BZ-torus IBP |  |
| D.mv-identity | eq.D-key-identities, expressions/mv_velocity_pair.txt, expressions/mv_metric_form.txt | two-band metric-velocity relation is introduced as a stated identity | (v12a*v21b + v12b*v21a ) - (2*e12**2*gab ) | DEFINITION_INSERTION | v12a, v21b, v12b, v21a, e12, gab | python_sympy_exact_v1 | DEFINITION |  |
| E.diag-2nd | eq.E-128 | multiband diagonal second-derivative identity is introduced as a stated key identity |  | DEFINITION_INSERTION |  | python_sympy_exact_v1 | DEFINITION |  |

