# Method v2 DEV results

Date: 2026-08-27
Workloads: `research/search_bottleneck/dev_hard/` (not frozen v0.1 test)
M0 = stop-at-first-transform-ZERO
M1 = Method v2 (continue + expand names + isolated packager)

| id | m0 ZERO | m1 ZERO | named-aux ZERO (M1−M0) | extra after first ZERO | FP |
|---|---:|---:|---:|---:|---:|
| D2-weighted-kernel | 1 | 2 | +1 | 1 | 0 |
| D2-shared-denominator | 1 | 2 | +1 | 1 | 0 |
| D3-thermal-pair | 1 | 2 | +1 | 1 | 0 |
| D4-piecewise-generic-kernel | 0 | 0 | 0 | 0 | 0 |
| D5-index-pair | 1 | 2 | +1 | 1 | 0 |
| C-fermi-poly-piecewise | 1 | 1 | 0 | 0 | 0 |

False promotions: **0**. D2 ZERO did not regress. Four items gained a
**closed named auxiliary that expands to ZERO** after the first D1/D2
step. D4 drop-Piecewise was **not** promoted.

Honest limit: extra ZEROs are **definition expansion of already-certified
algebra** (packaging), not new D4/D5 identities the engine could not
prove before.
