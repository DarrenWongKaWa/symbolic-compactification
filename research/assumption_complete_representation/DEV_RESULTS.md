# DEV matrix results (CORE_COMPARABLE n=6, 135 runs)

Model `deepseek-v4-pro`. Scorer `ac-score-v1.3`. Compiler `ac-compile-v1.1`.
Operational success requires two-point F (or F*F) with ZERO obligations.
PACKAGING_GAP tasks were not in this matrix.

## Per-task operational ZERO / 5 seeds

| task | R | P0 | P1 | P2 | P3 | P4 |
|---|---|---|---|---|---|---|
| mp-resolvent-dd-01 | R2 | 4 | 2 | 3 | 3 | 4 |
| ac-r01 | R2 | 2 | 3 | 0 | 1 | 0 |
| sciml-phi-hermite-01 | R3 | 0 | 0 | 0 | 0 | 0 |
| thermal-01 | R5 | 0 | 0 | 0 | 0 | — |
| thermal-03 | R5 | 0 | 0 | 0 | 0 | — |
| thermal-05 | R5 | 0 | 0 | 0 | 0 | — |

P4 type-correct on phi: 5/5; certified R3: 0.

Highest CERTIFIED_DEPTH: **R2**. Highest proposed: R6 slogans without certification.

Blocked API: 0/135.

GENERAL_FINAL: P0. See DEV_METHOD_SELECTION.md.
