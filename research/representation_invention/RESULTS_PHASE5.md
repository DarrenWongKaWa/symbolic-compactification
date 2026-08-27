# Phase 5 — generic DD validation

false ZERO: **0**
missed positives: 0
gate: PASS

| id | expect | got | ok |
|---|---|---|---|
| pos-newton-z2 | ZERO | ZERO | True |
| pos-newton-z3 | ZERO | ZERO | True |
| pos-repeated-diagonal | ZERO | ZERO | True |
| pos-hermite-xxy | ZERO | ZERO | True |
| pos-hermite-xxx | ZERO | ZERO | True |
| pos-piecewise-confluence | ZERO | ZERO | True |
| pos-polygamma-newton | ZERO | ZERO | True |
| neg-wrong-sign | NONZERO | NONZERO | True |
| neg-wrong-denominator | NONZERO | NONZERO | True |
| neg-wrong-derivative-order | NONZERO | NONZERO | True |
| neg-wrong-repeated-as-first-dd | NONZERO | NONZERO | True |
| neg-swapped-limit | NONZERO | NONZERO | True |
