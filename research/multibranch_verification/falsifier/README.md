# Owner: V2-H — adversarial family falsifier

Attack only. Do not improve the verifier, `schema.py`, or sibling V2
packages.

Eight toy polynomial families look like Hermite confluence of `F(t)=t**3`
and are wrong. Local exact checks fill required / recurrence / path
verdicts; `compose_family_verdict` is the only family rule. None of the
attacks may be `FAMILY_ZERO`.

False `FAMILY_ZERO` count must stay 0. Do not weaken a checker into an
always-NONZERO gate: `V2H_TRUE_HERMITE_FAMILY` must remain `FAMILY_ZERO`.

| id | kind | trap |
|---|---|---|
| V2H_01 | corrupted_branch_coefficient | generic Newton drops `xy`; 4/5 branches true |
| V2H_02 | wrong_factorial | `F[x,x,x]` uses `/3!` not `/2!` |
| V2H_03 | broken_branch | `F[x,y,y]` copied from `F[x,x,y]` |
| V2H_04 | mixed_latent_F | `t**3` and `t**2` glued; all local edges ZERO |
| V2H_05 | path_inconsistent_recurrence | both recurrences claimed to equal `2x+y` |
| V2H_06 | wrong_derivative_order | triple node filled with `F'` not `F''/2!` |
| V2H_07 | wrong_degeneracy_variable | claimed `y→x`, listed member is `y→w` |
| V2H_08 | pole_sensitive_false_confluence | `(x³-y³)/(x-y)²` claimed → `3x²` |
