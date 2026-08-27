# HANDOFF — Subagent F (adversarial falsifier)

Branch: `work/representation-falsifier`
Owned: `research/representation_invention/falsifier/**`, `tests/test_representation_falsifier.py`
Tests: `.venv/bin/python -m pytest tests/test_representation_falsifier.py -q`
SHA: this commit on `work/representation-falsifier` (parent `45b2b4dc7c823901f4b79713d279c6be7bae2859`).

False ZERO on local claim checks: **0**. True Newton first-DD control remains ZERO.

## Attacks currently checkable

| id | local claim verdict | obligations compile/verify (this worktree) | audit class |
|---|---|---|---|
| F01_fake_confluence | NONZERO (`limit((sin x-sin y)/(x-y),y→x)=cos x ≠ sin x`) | NONZERO CONFLUENCE | WRONG_CONFLUENCE |
| F02_wrong_repeated_node | NONZERO (`F[x,y]` for `z**3` ≠ `F[x,x]=3x**2`) | NONZERO HERMITE_DD | WRONG_DD_NODE_STRUCTURE |
| F03_pole_sensitive_recurrence | NONZERO (`expand_func` → `-2/z**2`; rational pole witness `-2/(z(z-1))`) | NONZERO RECURRENCE | NONZERO |
| F04_special_function_order | NONZERO (`polygamma(0,z) ≠ polygamma(1,z)`) | NONZERO EQUALITY | WRONG_OPERATOR |
| F05_invalid_limit | NONZERO (`1/(x-y)` y→x is `-oo` / dirs disagree, not `0`) | NONZERO LIMIT/CONFLUENCE | WRONG_CONFLUENCE |
| F06_sign_flipped_dd | NONZERO (member `(F(y)-F(x))/(x-y)` ≠ Newton) | NONZERO NEWTON_DD | WRONG_OPERATOR |
| F07_broken_symmetry_coefficient | NONZERO (`f(i,j)+f(j,i) ≠ 2 f(i,j)`) | NONZERO PERMUTATION | WRONG_OPERATOR |
| F08_tautological_master | COMPILE_FAILURE (`F:=A` used once). Residual A−A is ZERO and is **not** a claim ZERO. | residual ZERO (tautology leak) | TAUTOLOGICAL_MASTER |
| F09_overgeneralized_latent | COMPILE_FAILURE (identity `F(u)=u` absorbs any member) | residual ZERO (identity-template leak) | SHALLOW_REPACKAGING |
| F10_ambiguous_member_maps | PARSE_FAILURE (`S1_True`, `generic_branch`; G0001 generic+degenerate) | PARSE_FAILURE / COMPILE_FAILURE | UNGROUNDABLE |

JSON fixtures: `research/representation_invention/falsifier/fixtures/`.

## Remaining risks

- Obligations residual equality **will** ZERO F08/F09 (`A=A`, `F(u)=u`). That is the attack, not certification. Master quality (Subagent B) must refuse tautology / identity templates. The falsifier local audit already does.
- `sympy.limit` on a multivariate Piecewise raises `NotImplementedError`. F01 checks the **generic branch** against the degenerate branch, which is the confluence claim.
- `simplify` does not discharge polygamma recurrences; F03 requires `expand_func`.
- F07 via obligations is caught as a failed permutation, not as a coefficient audit. Local residual is the coefficient check.
- Do not weaken residual identity to always-NONZERO: `true_newton_dd_control` must stay ZERO.
