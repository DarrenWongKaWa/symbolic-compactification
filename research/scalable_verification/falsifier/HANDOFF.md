# HANDOFF — V7 (adversarial verifier reviewer)

Branch: `work/v-falsifier`
Owned: `research/scalable_verification/falsifier/**`, `tests/test_sv_falsifier.py`
Tests: `.venv/bin/python -m pytest tests/test_sv_falsifier.py -q`
Spawn freeze: `329c49c22c7d68d0192a59f04bf3ba8ad12c9b48`
Commit parent: `ba2326238df9e395cce0000a6ec2d46a9708d9e7`
SHA: this commit on `work/v-falsifier`.

False ZERO: **0**. True confluence and Newton controls remain ZERO.

`dd_cert` / `factor` are empty stubs on the parent. `confluence.check_limit`
is probed when importable (`check_limit(F, y, x, G)`); V7_01/02/05 come
back NONZERO and the true-limit control stays ZERO. Missing API is not
ZERO. A later ZERO on an attack is a false certification, not a pass.

## Attacks (must not be ZERO)

| id | local verdict | note | trap |
|---|---|---|---|
| V7_01_wrong_limit_target | NONZERO | `limit_vs_claimed` | `(sin x-sin y)/(x-y)` claimed → `sin x` (true `cos x`) |
| V7_02_false_removable_singularity | NONZERO | `no_finite_two_sided_limit` | `1/(x-y)` claimed → `F'(x)=1`; dirs `oo`/`-oo` |
| V7_03_pole_sensitive | NONZERO | `expand_func_nonzero` | trigamma shift with digamma sign; polar `-2/z**2` |
| V7_04_wrong_branch | NONZERO | `equality_vs_claimed` | `log(-1)` claimed `-I*pi` (principal `I*pi`) |
| V7_05_nonuniform_limit_sketch | NONZERO | `diagonal_neq_claimed_sketch` | generic `eps→0` sketch `=1` used as `y→x` data; diagonal is `0` |
| V7_06_coefficient_corruption | NONZERO | `equality_vs_claimed` | `x**3-y**3` claimed `(x-y)(x**2+y**2)` (dropped `xy`) |
| V7_07_hidden_assumption | NONZERO | `equality_vs_claimed` | `sqrt(x**2)=x` without `x>=0`; `x=-1` witnesses |
| V7_08_fake_dd_structure | NONZERO | `member_vs_repeated_node` | `F[x,y]` for `z**3` claimed as `F[x,x]=3x**2` |

## Remaining risks

- Empty engines are not ZERO. Once V2–V4 land, this suite is the false-ZERO gate.
- `sympy.limit` of `(x-y)/((x-y)+eps)` as `eps→0` is generically `1`. That
  must not certify the diagonal member. The claim probed is `y→x` → `1`.
- `repeated_diagonal` / `hermite_dd` rebuild the claimed RHS from `F`; they
  are not treated as member verdicts (that would false-ZERO V7_08).
- Do not declare `x` positive to discharge V7_07. Do not convert timeout
  or missing API to ZERO.
- Do not weaken residuals to always-NONZERO: true limit and Newton
  controls must stay ZERO.
