# Track V3 generic iterated-confluence suite

false FAMILY_ZERO = 0
pass = True

| id | expect | got | ok | note |
|---|---|---|---|---|
| A-joint-iterated-agree | FAMILY_ZERO | FAMILY_ZERO | True | edges ZERO,ZERO |
| B-order-matters | FAMILY_NONZERO | FAMILY_NONZERO | True | y-then-1=ZERO x-then-0=ZERO; must not FAMILY_ZERO |
| C-one-path-invalid | FAMILY_NONZERO | FAMILY_NONZERO | True |  |
| D-pairwise-zero-inconsistent | FAMILY_NONZERO | FAMILY_NONZERO | True |  |
| E-hermite-cubic-consistent | FAMILY_ZERO | FAMILY_ZERO | True | Fxx ZERO |
| F-hidden-pole | not FAMILY_ZERO | FAMILY_NONZERO | True | pole verdict NONZERO |
| G-spectator-small-kernel | FAMILY_ZERO | FAMILY_ZERO | True | certified=True local=ZERO note=exact_applied_undef_factor |
| neg-majority-unknown | FAMILY_UNKNOWN | FAMILY_UNKNOWN | True |  |
