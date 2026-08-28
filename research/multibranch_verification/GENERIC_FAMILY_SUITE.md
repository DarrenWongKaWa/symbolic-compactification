# Generic multi-branch family suite

false FAMILY_ZERO: **0**
gate: PASS

| id | expect | got | ok |
|---|---|---|---|
| pos-3branch-confluence | FAMILY_ZERO | FAMILY_ZERO | True |
| pos-5branch-hermite-cubic | FAMILY_ZERO | FAMILY_ZERO | True |
| pos-two-paths | FAMILY_ZERO | FAMILY_ZERO | True |
| neg-corrupted-branch | FAMILY_NONZERO | FAMILY_NONZERO | True |
| neg-mixed-latent | FAMILY_UNKNOWN | FAMILY_UNKNOWN | True |
| neg-majority-not-zero | FAMILY_UNKNOWN | FAMILY_UNKNOWN | True |
