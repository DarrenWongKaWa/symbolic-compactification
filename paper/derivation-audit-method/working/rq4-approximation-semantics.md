# RQ4 candidate — approximation-mediated derivation semantics

Status: **candidate**, not a core claim of draft-v2.
Experiment: `experiment/approximation-authority-v1`
Report: `experiments/approximation_authority_v1/FINAL_REPORT.md`
Verdict: `FOUR_DIAGNOSTIC_CASES_DISTINGUISHED`

Do not rewrite the main paper around this. One Discussion sentence is
enough until a decision is made: fourth experiment in this manuscript,
or a follow-on method note.

## Principle

Approximation may be authorized; its consequences must still be verified.

`ZERO` stays exact `ZERO`. A parent overlay
`CERTIFIED_UNDER_DECLARED_APPROXIMATION` is to `ZERO` as
`CERTIFIED_BY_RULE` is to `ZERO`.

Author authorization \(\neq\) approximation proof.

## Axes

provenance \(\times\) control \(\times\) downstream equality

## Four cases distinguished

1. `AUTHOR_DECLARED` + downstream `ZERO`
2. `AUTHOR_DECLARED` + downstream `NONZERO`
3. `AUTHOR_DECLARED` + remainder `DECLARED_ONLY` (Guo (D-57) `UNKNOWN`)
4. `NONE` + hidden \(T_A\) yields `ZERO` → `UNDECLARED_APPROXIMATION_REQUIRED`

Guo \(e_{21}=-e_{12}\) / \(f_n'=2f_{0,n}'\) remain substitution/assumption
gaps (Forward RQ1), not approximation.

## Product

Do not add the overlay status to `src/` in this pass.
See experiment `PRODUCT_GAPS.md`.
