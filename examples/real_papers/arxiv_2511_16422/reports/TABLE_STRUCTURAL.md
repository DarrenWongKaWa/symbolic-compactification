# TABLE_STRUCTURAL

Definitions, recorded bookkeeping, split parents, and split parents whose children are all certified.

CERTIFIED_BY_CHILDREN is displayed as `SPLIT — all children certified` via `public_status_label`. It is never displayed as ZERO.

| Edge ID | Manuscript equation reference(s) | Claim / transformation | Executable residual | Derivation type | Declared assumptions | Verifier | Result | Artifact link |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B.j2-to-sigma | eq.B-24, eq.B-25 | the four current channels are translated into the frequency-space conductivity kernel |  | BOOKKEEPING |  | python_sympy_exact_v1 | RECORDED |  |
| B.split-j2 | eq.B-23, eq.B-24 | second-order current j_a^{(2)} is decomposed into four O(A^2) channels (I)-(IV) |  | SPLIT_PARENT |  | python_sympy_exact_v1 | SPLIT |  |
| D.mv-identity | eq.D-key-identities, expressions/mv_velocity_pair.txt, expressions/mv_metric_form.txt | two-band metric-velocity relation is introduced as a stated identity | (v12a*v21b + v12b*v21a ) - (2*e12**2*gab ) | DEFINITION_INSERTION | v12a, v21b, v12b, v21a, e12, gab | python_sympy_exact_v1 | DEFINITION |  |
| E.diag-2nd | eq.E-128 | multiband diagonal second-derivative identity is introduced as a stated key identity |  | DEFINITION_INSERTION |  | python_sympy_exact_v1 | DEFINITION |  |

