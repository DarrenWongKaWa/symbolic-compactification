# Track V3 independent reviews

Reviewers did not communicate before filing.

| id | role | file | commit |
|---|---|---|---|
| R1 | symbolic algebra | `R1_ALGEBRA.md` | `d13b287` |
| R2 | mathematical analysis | `R2_ANALYSIS.md` | `92b29a3` |
| R3 | theoretical physics | `R3_PHYSICS.md` | `c981ac8` |
| R4 | PL / verification | `R4_VERIFICATION.md` | `05e72b0` |
| R5 | benchmark skeptic | `R5_SKEPTIC.md` | `203d359` |
| R6 | reproducibility | `R6_REPRO.md` | `1cca059` |

Coordinator patches after reviews (not changing frozen Guo verdicts):

1. **R2:** two PATH_ZERO paths to the same source member are not
   `CONSISTENT_ZERO`. Rescore `_endpoint_consistency` stays UNKNOWN
   unless a PATH_NONZERO conflict is seen. Counterexample
   `xy/(x^2+y^2)` would have been a false family promotion.
2. **R1:** do not peel spectators that depend on the degeneration
   variable (`lim y·f(y)` is not `y·lim f`). Control
   `y(y+3)` vs `3y` as `y→0` is not ZERO.

Frozen Guo case remains **I-D**. Track D2 locked.
