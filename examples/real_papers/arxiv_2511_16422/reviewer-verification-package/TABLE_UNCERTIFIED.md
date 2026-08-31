# TABLE_UNCERTIFIED

Unknown, assumption-required, not-lowered, parse/compile/grounding failures, invalid records, and other non-verified obligations.

Asymptotic remainder claims and integral arguments appear here. A remainder certificate does not place an enclosing ASYMPTOTIC_CLAIM in TABLE_VERIFIED.

| Edge ID | Manuscript equation reference(s) | Claim / transformation | Executable residual | Derivation type | Declared assumptions | Verifier | Result | Artifact link |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D.T0-ibp-global | eq.D-114, eq.D-119 | integration by parts in k-space converts the T0 Fermi-sea form into a Fermi-surface form |  | INTEGRAL_ARGUMENT |  | python_sympy_exact_v1 | NOT_LOWERED |  |
| D.T2-ibp-global | eq.D-123, eq.D-124 | integration by parts converts T2 ~ g ∂_a(f') into a - (∂_a g) f' Fermi-surface term |  | INTEGRAL_ARGUMENT |  | python_sympy_exact_v1 | NOT_LOWERED |  |
| D.gamma-asymptotic | eq.D-57 | DC conductivity admits a Gamma expansion through O(Gamma^0) with remainder O(Gamma) |  | ASYMPTOTIC_CLAIM |  | python_sympy_exact_v1 | UNKNOWN |  |

