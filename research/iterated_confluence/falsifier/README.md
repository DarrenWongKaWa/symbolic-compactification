# Owner: V3-J — adversarial iterated-path falsifier

Attack only. Do not improve the verifier, `schema.py`, or sibling V3
packages. Composition under test is `schema.compose_path_verdict` and
`schema.compose_family_verdict`.

Eight toy families look pairwise-confluent along some one-parameter path
and are not a commuting family. None of the attacks may be `FAMILY_ZERO`.

False `FAMILY_ZERO` count must stay 0. Do not weaken a checker into an
always-NONZERO gate: the two commuting polynomial controls must remain
`FAMILY_ZERO` with path consistency `CONSISTENT_ZERO`.

Public API: `from research.iterated_confluence.falsifier import run_cases`.

| id | kind | trap |
|---|---|---|
| V3J_01 | one_path_zero_other_nonzero | y→x of x+y is 2x; x→y filled with 3y |
| V3J_02 | noncommuting_limits | x/(x+y): y then x is 1, x then y is 0 |
| V3J_03 | hidden_pole | (x²−y²)/(x−y)² claimed → 2x; sibling x+y is ZERO |
| V3J_04 | corrupted_intermediate | true diagonal 3x²; inserted mid 2x² |
| V3J_05 | wrong_equality_surface | x²+y claimed = x²+x; residual 0 only on y=x |
| V3J_06 | path_dependent_repeated_node | 2x+y → 3x ZERO; x+2y+1 → 3x+1 |
| V3J_07 | spectator_mismatch | local (x+y)→2x ZERO; K_xx uses n+2m not n+m |
| V3J_08 | majority_path_unknown | 2 PATH_ZERO + 1 size-guard PATH_UNKNOWN |
