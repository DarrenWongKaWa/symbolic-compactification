# Post-package admission, depth, and leakage audit

Policy: `RPS_PACKAGE_ADMISSION_AUDIT_V1`.

This is a fail-closed admission audit, not a benchmark split or method result. `PACKAGE_READY` remains necessary but is not treated as `ADMISSION_READY`.

## Outcome

- Packages audited: 13
- `ADMISSION_READY`: 0
- Fair-comparison eligible: 0
- Frozen reference documents checked: 79

| package | package status | claimed | independent | scope | dispositions | fair? |
|---|---|---:|---:|---|---|---:|
| `dp-oscillator-confluent-fixed-r4` | `PROOF_REQUIRED` | R4 | R4 | `FIXED_SCIENTIFIC_INSTANCE` | `PROOF_REQUIRED`, `SCHEMA_GAP`, `DUPLICATE_REVIEW` | no |
| `mx-abba-exp-fixed-r6` | `PACKAGE_READY` | R6 | R2 | `FIXED_SCIENTIFIC_INSTANCE` | `SCHEMA_GAP`, `DEPTH_DOWNGRADED` | no |
| `mx-sqrt-hermite-fixed-r3` | `PACKAGE_READY` | R3 | R3 | `FIXED_SCIENTIFIC_INSTANCE` | `SCHEMA_GAP`, `DUPLICATE_REVIEW` | no |
| `mx-sqrt-newton-fixed-r2` | `PACKAGE_READY` | R2 | R2 | `FIXED_SCIENTIFIC_INSTANCE` | `SCHEMA_GAP`, `DUPLICATE_REVIEW` | no |
| `rps-r-feshbach-optical-heff` | `PACKAGE_READY` | R6 | R0 | `FIXED_SCIENTIFIC_INSTANCE` | `SCHEMA_GAP`, `DEPTH_DOWNGRADED` | no |
| `rps-t-barnes-rivers-dn` | `PACKAGE_READY` | R8 | DIAGNOSTIC_ONLY | `FINITE_INDEX_DIAGNOSTIC` | `DIAGNOSTIC_ONLY`, `SCHEMA_GAP`, `DEPTH_DOWNGRADED` | no |
| `rps-t-stf-son-rank3` | `PACKAGE_READY` | R8 | DIAGNOSTIC_ONLY | `FINITE_INDEX_DIAGNOSTIC` | `DIAGNOSTIC_ONLY`, `SCHEMA_GAP`, `DEPTH_DOWNGRADED` | no |
| `thermal-09-digamma-newton` | `PROOF_REQUIRED` | R2_NEWTON_DD | R2 | `SYMBOLIC_SOURCE_OBJECT` | `PROOF_REQUIRED`, `SCHEMA_GAP`, `LEAKAGE_REVIEW`, `DUPLICATE_REVIEW` | no |
| `thermal-09-digamma-newton-z1` | `PACKAGE_READY` | R0_REPEATED_STRUCTURE | R0 | `FIXED_SCIENTIFIC_INSTANCE` | `SCHEMA_GAP`, `LEAKAGE_REVIEW`, `DUPLICATE_REVIEW` | no |
| `thermal-10-polygamma-order2-recurrence` | `PROOF_REQUIRED` | R1_PARAMETER_FAMILY | R1 | `FIXED_SCIENTIFIC_INSTANCE` | `HUMAN_REQUIRED`, `PROOF_REQUIRED`, `SCHEMA_GAP`, `LEAKAGE_REVIEW`, `DEPTH_DOWNGRADED` | no |
| `thermal-11-digamma-duplication` | `PROOF_REQUIRED` | R1_PARAMETER_FAMILY | R1 | `FIXED_SCIENTIFIC_INSTANCE` | `PROOF_REQUIRED`, `SCHEMA_GAP`, `DUPLICATE_REVIEW`, `DEPTH_DOWNGRADED` | no |
| `thermal-13-alternating-digamma` | `PROOF_REQUIRED` | R5_SPECIAL_FUNCTION_REPRESENTATION | R5 | `SYMBOLIC_SOURCE_OBJECT` | `PROOF_REQUIRED`, `SCHEMA_GAP`, `DUPLICATE_REVIEW` | no |
| `thermal-13-alternating-digamma-z1` | `PACKAGE_READY` | R5_SPECIAL_FUNCTION_FIXED_INSTANCE | R5_FIXED_INSTANCE | `FIXED_SCIENTIFIC_INSTANCE` | `SCHEMA_GAP`, `DUPLICATE_REVIEW` | no |

## Decisive findings

- All six thermal packages load through M1 but fail compilation at the first missing executable output; the audit records every loader schema delta and never repairs links.
- All four matrix/differentiable-physics packages and all three response/tensor packages fail the M1 loader with `PACKAGE_ARTIFACT_MANIFEST_INVALID` because they use `artifacts`, not the contract's `artifact_hashes` list.
- The oscillator's required complex-domain Piecewise obligation is `UNKNOWN`; its real-domain ZERO replay remains explicitly ineligible.
- Both tensor packages are `FINITE_INDEX_DIAGNOSTIC` and cannot enter R8 fair comparison.
- The fixed AB/BA package is independently R2 (one Newton divided difference plus linear reconstruction), not R6.
- The scalar Feshbach package is independently R0/CSE-baseline class (one exposed denominator kernel plus linear combinations), not R6.
- Thermal-10 is `HUMAN_REQUIRED`: it repairs a previously rejected domain contract without a recorded human decision.
- Schema repair alone cannot admit the pool: proof, assumption, depth, duplicate, leakage, and diagnostic-scope gates remain independent.

## DEV calibration recommendation

No package is recommended. Missing slots are reported rather than filled from ineligible artifacts:

| slot | status | candidate packages | missing gate |
|---|---|---|---|
| R2 | `MISSING` | `mx-abba-exp-fixed-r6`, `mx-sqrt-newton-fixed-r2`, `thermal-09-digamma-newton` | `ALL_CANDIDATES_FAIL_ADMISSION_GATES` |
| R3 | `MISSING` | `mx-sqrt-hermite-fixed-r3` | `ALL_CANDIDATES_FAIL_ADMISSION_GATES` |
| R4_R5 | `MISSING` | `dp-oscillator-confluent-fixed-r4`, `thermal-13-alternating-digamma`, `thermal-13-alternating-digamma-z1` | `ALL_CANDIDATES_FAIL_ADMISSION_GATES` |
| R6 | `MISSING` | none | `NO_INDEPENDENT_DEPTH_CANDIDATE` |

The M10 adversarial negative trap remains an evaluator-only falsifier, separate from benchmark admission; it is not a benchmark candidate. No TEST task was selected.

## Interpretation boundary

Depth review is independent of package labels. Duplicate similarity is a review gate, not an automatic scientific rejection. ZERO receipts certify only their exact current/candidate texts and declared lowering scope; they do not repair Program IR, source-provenance, leakage, or depth defects.
