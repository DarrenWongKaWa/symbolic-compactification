# J/K/C6 handoff — post-package admission, depth, and leakage audit

Owner: independent package admission/depth/leakage auditor

Branch: `work/rps-package-admission`

The exact implementation commit is reported to the coordinator after commit;
the commit cannot contain its own SHA without changing that SHA.

## Scope and invariant

Audited all 13 package directories under `packages/thermal`,
`packages/matrix_diffphys`, and `packages/response_tensor`. The audit is
read-only with respect to package artifacts, scientific inputs, reference
programs, parser, verifier, grammar, and historical evidence. It selects no
DEV/TEST/CHALLENGE partition and records no method result.

Delivered:

- `audits/package_admission/audit.py`: deterministic mechanical gates;
- `audits/package_admission/reviews.json`: bounded independent scientific,
  depth, non-tautology, and primitive-giveaway judgments;
- `audits/package_admission/PACKAGE_ADMISSION_AUDIT.json`: complete evidence;
- `audits/package_admission/PACKAGE_ADMISSION_AUDIT.md`: human report;
- `tests/test_rps_package_admission.py`: focused regression tests.

## Decisive result

`ADMISSION_READY = 0/13`. `PACKAGE_READY` was not conflated with admission.
The initial DEV calibration pool therefore remains empty; R2, R3, R4/R5, and
R6 are all explicitly reported missing rather than force-filled.

Disposition counts (non-exclusive):

| disposition | packages |
|---|---:|
| `SCHEMA_GAP` | 13 |
| `DUPLICATE_REVIEW` | 8 |
| `DEPTH_DOWNGRADED` | 6 |
| `PROOF_REQUIRED` | 5 |
| `LEAKAGE_REVIEW` | 3 |
| `DIAGNOSTIC_ONLY` | 2 |
| `HUMAN_REQUIRED` | 1 |

Schema repair alone cannot cure the pool. Required UNKNOWN verdicts,
unauthorized assumptions, depth downgrades, duplicate review, public
projection leakage, and diagnostic-only scope remain independent gates.

## M1 and package-schema boundary

- All six thermal packages pass artifact hash/coverage validation and load
  through M1. Every one fails compilation with
  `OPERATOR_OUTPUT_MISSING:OP0`. The exact six M1 loader deltas are retained:
  exact catalog source injection, exact contract assumption injection,
  missing operator outputs, missing assignment outputs, missing
  obligation-output links, and a non-M1 legacy program id. No link was
  inferred or repaired.
- All four matrix/differentiable-physics packages and all three
  response/tensor packages use `artifacts` rather than the contract's
  `artifact_hashes` list. Their listed bytes and coverage validate, but the M1
  loader correctly stops at `PACKAGE_ARTIFACT_MANIFEST_INVALID`. Static
  schema observations are recorded without modifying those programs.
- All member/reference expression text parses under the frozen parser, all
  retained obligation artifacts and session verdicts match, and all source
  members are covered. Those passing axes do not override M1 failure.
- Strict source-provenance defects are also explicit: online retrieval dates
  are absent from thermal and matrix manifests; matrix dossier paths are
  repository-relative rather than package-relative; response/tensor packages
  do not path/hash-bind their source dossiers.

## Proof and assumption axes

- The oscillator remains `PROOF_REQUIRED`: four required obligations are
  ZERO and the complex-domain Piecewise obligation is UNKNOWN. Its later
  real-`w` ZERO replay is `INELIGIBLE_RESTRICTED_REPLAY` and cannot certify the
  source claim.
- Four thermal symbolic/special-function packages remain
  `PROOF_REQUIRED`; UNKNOWN was never promoted.
- Thermal-10 is additionally `HUMAN_REQUIRED`. It adds the full
  nonpositive-integer pole exclusion after its inherited dossier was rejected
  as `PROBLEM_UNDERSPECIFIED`; there is no recorded human authorization for
  that domain repair.

## Independent depth and falsification findings

- `mx-abba-exp-fixed-r6` is R2 operationally: one Newton divided difference
  plus linear reconstruction of fixed scalar entries. The shared quotient is
  itself proposer-visible as a source member. It is not an R6 master.
- `rps-r-feshbach-optical-heff` is R0/CSE-baseline class: one exposed scalar
  denominator kernel plus linear combinations. It satisfies the narrow IR
  shared-latent non-tautology rule, but it is not a fair R6 discovery task.
- The fixed square-root repeated-node package is plausibly R3, but the named
  Hermite primitive is a critical giveaway control; G_NO_HERMITE and
  G_PRIMITIVE ablations are mandatory if it is ever repaired and admitted.
- Both tensor packages are `FINITE_INDEX_DIAGNOSTIC`, independently
  `DIAGNOSTIC_ONLY`, and never R8 admission evidence.
- The M10 adversarial negative trap remains an evaluator-only falsifier. It is
  separate from benchmark admission and is not a benchmark candidate.

## Leakage and duplicate findings

- Thermal-09 symbolic and fixed packages expose `newton` in a public package
  id; thermal-10 exposes `recurrence`. The referenced thermal assumption files
  are expanded before value scanning, so the audit covers every file the
  proposer may receive rather than only the top-level JSON.
- Exact current-pool overlap is recorded between the R2 and R3 square-root
  siblings; fixed/symbolic thermal siblings are source-cluster review pairs.
- The frozen historical audit policy raises eight package-level manual-review
  rows. Similarity is never an automatic rejection.

## Reproduction

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. \
  /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m research.representation_program_search.audits.package_admission.audit --check

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. \
  /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m pytest -q tests/test_rps_package_admission.py
```

Observed focused result: `7 passed`.

The audit plus all package/M1 focused suites is reported with the final commit
handoff. No TEST identity or final method semantic was frozen.
