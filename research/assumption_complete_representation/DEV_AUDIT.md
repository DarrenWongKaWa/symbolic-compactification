# DEV slice audit (14 tasks)

Partition **DEV**, not a TEST freeze. Guo excluded. Tags are frozen
before LLM runs. Easy tasks stay in DEV.

| case | tag | R | operator | B0 ZERO ⇒ discovery? | notes |
|---|---|---|---|---|---|
| mp-resolvent-dd-01 | SHALLOW | R2 | NEWTON_DD | no (algebra ≠ naming F[z,w]) | near-dup of ac-r01 |
| mp-daleckii-krein-01 | NONTRIVIAL | R3 | HERMITE_DD | no | Loewner kernel; dup of sciml-daleckii |
| mp-hermite-fA-01 | NONTRIVIAL | R3 | HERMITE_DD | no | Higham interpolant |
| mp-cauchy-dunford-01 | NONTRIVIAL | R6 | FUNCTIONAL_CALCULUS | no | contour master; sketch leaks |
| thermal-01-fermi-im-digamma | NONTRIVIAL | R5 | OTHER_EXPLICIT | no | DLMF 5.4.17; B0 numeric ZERO |
| thermal-03-digamma-reflection | NONTRIVIAL | R5 | RECURRENCE | no | DLMF 5.5.4; use `pi/tan(pi*z)` |
| thermal-05-trigamma-double-pole | SHALLOW | R5 | RECURRENCE | no | defining series |
| sciml-phi-hermite-01 | NONTRIVIAL | R3 | HERMITE_DD | no | φ_k = exp[0^{(k)},z] |
| sciml-vanloan-blockexp-01 | CHALLENGE | R6 | FUNCTIONAL_CALCULUS | no | block triangular exp |
| sciml-daleckii-krein-01 | NONTRIVIAL | R3 | HERMITE_DD | no | same H as mp-daleckii |
| ac-t-eps-delta | SHALLOW | R8 | BASIS_RECONSTRUCTION | identity residual is trivial | εε→δδ |
| ac-t-young-s3 | NONTRIVIAL | R8 | PERMUTATION | no | S₃ Young projectors |
| ac-r01-resolvent-hilbert-identity | SHALLOW | R2 | NEWTON_DD | residual trivial | opposite resolvent convention vs mp |
| ac-r03-helmholtz-outgoing-green | NONTRIVIAL | R5 | SUBSTITUTION | no | freeze n=3, k>0 declared |

Do not count two AI_UNIQUE_SUCCESS on a duplicate pair.

Raw `expression_sketch` often leaks gold names. Proposer packs must
use unlabeled members + declared domains only (`proposer_leak_risk`).

Counts: TRIVIAL 0, SHALLOW 4, NONTRIVIAL 9, CHALLENGE 1.
