# Owner: V7 — adversarial verifier reviewer

Attack only. Do not improve the verifier. No LLM.

Eight claims in `cases.py` must not certify as ZERO. Local sympy checks
run unconditionally. If `confluence`, `dd_cert`, or `factor` later expose
verify/certify/limit/factor callables, `engines.py` calls them; a ZERO on
an attack is a false certification.

False ZERO count must stay 0. Do not weaken a checker into an
always-NONZERO gate: `V7_TRUE_LIMIT_CONTROL` and `V7_TRUE_NEWTON_CONTROL`
must remain ZERO.

| id | kind | trap |
|---|---|---|
| V7_01 | wrong_limit_target | `(sin x-sin y)/(x-y)` claimed → `sin x` (true: `cos x`) |
| V7_02 | false_removable_singularity | `1/(x-y)` claimed → `F'(x)=1` |
| V7_03 | pole_sensitive | trigamma shift with the digamma sign |
| V7_04 | wrong_branch | `log(-1)` claimed `-I*pi` (principal `I*pi`) |
| V7_05 | nonuniform_limit_sketch | generic `eps→0` sketch used as `y→x` data |
| V7_06 | coefficient_corruption | `x³-y³` claimed `(x-y)(x²+y²)` |
| V7_07 | hidden_assumption | `sqrt(x²)=x` without `x>=0` |
| V7_08 | fake_dd_structure | `F[x,y]` claimed as `F[x,x]=F'(x)` |
