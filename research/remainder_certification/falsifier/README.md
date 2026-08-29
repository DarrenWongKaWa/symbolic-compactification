# Owner: R9 — adversarial remainder-certificate falsifier

Attack only. Do not improve `schema.py`, sibling certifiers, or hop
engine timeouts. Track D2 stays LOCKED. Not Track V6. No LLM.

Remainder `CERTIFIED` is not hop ZERO. Composition under test is
`research.coefficient_laurent.schema.compose_hop_verdict`. If
`compile_remainder` is importable it is probed; it must not CERTIFIED
an attack.

False remainder `CERTIFIED` count must stay 0. Do not weaken a checker
into an always-UNKNOWN gate: entire `exp`, holomorphic `polygamma(0,1+t)`,
and `t^{-2} exp` with `N+1-m > 0` remain CERTIFIED.

Public API: `from research.remainder_certification.falsifier import run_cases`.

| id | kind | trap |
|---|---|---|
| RC9_01 | expansion_point_at_pole | Taylor of polygamma at t=0 |
| RC9_02 | symbolic_point_may_be_pole | generic a ∉ Z_≤0 |
| RC9_03 | affine_path_cross_pole | 1/2 + b t, pole at t = -1/(2b) |
| RC9_04 | insufficient_taylor_order | N=2 claimed as O(t^6) |
| RC9_05 | divergent_prefactor | t^{-4} O(t^3), N+1-m ≤ 0 |
| RC9_06 | hidden_denominator_zero | (1+t)/(t(1+t)) cancelled to 1 |
| RC9_07 | complex_path_real_only | real Lagrange on 1+I t |
| RC9_08 | incorrect_boundedness | Cauchy disk \|t\|<3 contains pole |
| RC9_09 | symbolic_M_unproved | Cauchy M < ∞ unproved |
| RC9_10 | ignore_remainder | neg ZERO + C0 ZERO + rem UNKNOWN |

`ignore_remainder` is the V5 regression: LEVEL B coefficients plus
remainder UNKNOWN must not compose to hop ZERO.

Class-C/D claimed certificates cannot `validate_certificate` as
CERTIFIED. Expansion at a pole is NONANALYTIC, not CERTIFIED.
