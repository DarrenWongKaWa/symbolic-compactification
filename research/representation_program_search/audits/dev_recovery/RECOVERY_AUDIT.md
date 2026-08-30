# J2 machine-package recovery audit

Policy: `RPS_DEV_RECOVERY_VALIDATOR_V1`.

## Outcome

No recovered package is admissible. The requested R2, R3, R4/R5, and R6
calibration slots remain missing. This is a fail-closed result, not a method
failure and not permission to alter the parser or scientific domains.

| slot | disposition | decisive reason |
|---|---|---|
| R2 | `MISSING` | available unused objects did not survive duplicate/grammar-bait/first-order-LGG screening |
| R3 | `PACKAGING_GAP` | source is arbitrary complex, while all eight receipts are restricted by the frozen `real:false` implementation to provably non-real symbols |
| R4/R5 | `PACKAGING_GAP` | the prioritized phi recurrence needs a sound arbitrary-complex namespace with a removable value; complex/nonzero parsing fails and the Piecewise zero stratum collapses |
| R6 | `MISSING` | parser-feasible scalar lowerings erase the matrix/block/integral master and independently downgrade to shallow structure |

## Retained R3 defect evidence

`rps-candidate-j2-001` is a strict M1-native `RPSCasePackageV1` artifact with:

- no loader schema deltas;
- canonical full-program id
  `951244f77df712e6c70211d48eda0c2bf6a993799c01f6deefd08cbe35352810`;
- canonical primitive-program id
  `9ebe78cf867af8f6969f6ccde878e8e4184f63dd9426464e0df2e119aa84036b`;
- explicit repeated-node structures `[x,x,y]` and `[x,y,y]`;
- a G_PRIMITIVE/G_NO_HERMITE reconstruction using only VALUE, DERIVATIVE,
  SUBSTITUTE, and LINEAR_COMBINATION;
- eight hash-bound recorded `init-session` + `step` receipts, all exact ZERO;
- an exact package-relative copy of the mined dossier;
- primary PDF locator and retrieved SHA-256
  `327111b07b62c9bb47982b615adcfccafe1c156094d49be49eccd465198817be`;
- an opaque proposer view with no target/operator/depth/verdict fields.

Those facts make the artifact useful contract-defect evidence. They do not
make it a scientific package: `real:false` does not cover the source's
arbitrary-complex domain under the frozen implementation. The package manifest
therefore says `PACKAGING_GAP`, `INELIGIBLE`, and
`REAL_FALSE_NAMESPACE_CONTRACT_DEFECT`. No ZERO is promoted into a DEV result.

The duplicate audit found no exact or alpha-renamed member match in the current
package pool. It nevertheless retains manual review for thematic overlap with
historical first-Fréchet/Daleckii--Krein and exponential divided-difference
tasks, plus a visible-CSE baseline risk. These risks are not used to rescue or
reinterpret the domain defect.

## Prioritized R5 attempt

Aceto--Gemignani equations (1)--(2) and (15) were inspected from the primary
PDF retrieved on 2026-08-30, SHA-256
`e289354365a188962f43e6203ec81661e90f3056bce379964cbb61e781fdb61e`.
The source declares an entire complex family. The frozen namespace cannot
soundly package both the quotient stratum and removable point without either
the recorded contract defect or a new domain restriction. No candidate package
or apparent ZERO receipt from a collapsed Piecewise branch was retained.

Machine report: `RECOVERY_AUDIT.json`.

Focused tests: `27 passed` across `test_rps_dev_recovery.py` and
`test_rps_program_ir.py`.
