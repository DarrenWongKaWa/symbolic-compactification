# Audit claim for Supplement / Code Availability

The algebraic backbone of the manuscript has been machine-audited.

Exact algebraic, coefficient-level, permutation, and local symmetry identities
that were lowered to executable residuals were checked under the declared
symbolic semantics; all currently executable residuals evaluate to ZERO and
none to NONZERO. Definitions, integral-level arguments, and asymptotic
remainder claims are tracked separately rather than being misreported as
algebraic identities.

This does **not** say that every derivation has been formally proven.

Reproduce with `verification/reproduce.sh`. The reviewer table is
`verification/reports/TABLE_S_VERIFICATION.md`.
