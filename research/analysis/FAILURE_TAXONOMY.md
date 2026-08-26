# Failure taxonomy

Mandatory labels for every unsuccessful or shallow run. Applied both
automatically (when a detector fires) and manually on case studies.

| Code | Name | Detector / note |
|---|---|---|
| F_PARSE | parser failure | AdapterError / construction_or_parse_failed |
| F_SYNTAX | unsupported syntax | adapter `UNSUPPORTED_*` / DISALLOWED_CHARACTERS |
| F_TIMEOUT | verifier timeout | evidence kind TIME_BUDGET_EXCEEDED |
| F_INTUITION | false structural intuition | NONZERO after a structure-motivated proposal |
| F_LOCALMIN | local minimum / shallow simplification | certified but ladder below human reference − 2 |
| F_HALLUC | answer hallucination | claimed ZERO/proven without engine ZERO |
| F_ASSUME | assumption error | HUMAN_REQUIRED or invented assumptions |
| F_BRANCH | branch-cut / Piecewise issue | mutation_type changed_branch or piecewise UNKNOWN |
| F_RESOURCE | resource exhaustion | budget cap hit with no ZERO |
| F_USELESS | valid but scientifically useless rewrite | certified, compactness delta ≤ 0 on scientific axes |
| F_ABSTRACTION | failure to discover abstraction | no kernel naming / confluence / geometry on Tier C |
| F_LEAK | hidden-answer leakage | proposer context contained hidden fields (invalidate run) |
| F_UNKNOWN | honest unresolved | UNKNOWN without promotion (not a protocol failure) |

A run may carry multiple codes. `F_HALLUC` on B7 is an engine-contract
bug if promotion occurred; on B3/B4 it is the expected unconstrained
failure mode.

Manual labels for case studies live in `research/analysis/case_studies/`
after those runs exist.
