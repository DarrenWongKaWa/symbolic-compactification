# T Handoff — Thermal Machine Packages

## Scope

Built six `RPSCasePackageV1` candidates under
`packages/thermal/`, sourced only from the new thermal-09, thermal-10,
thermal-11, and thermal-13 dossiers. No old AC identity, Guo artifact,
benchmark partition, shared contract, parser, or verifier was changed.

Each package contains immutable `members/*.txt`, `symbols.json`, a
SHA-bound source catalog and source manifest, a complete package-local
ScientificAssumptionContract, a proposer-only projection, an evaluator-only
reference program and obligations, and the original recorded session files.
`package.json` hashes every artifact except itself (self-hashing is
impossible), with relative paths.

## Results

| Package | Lowering | Audited depth | Status | Required verdicts |
|---|---|---|---|---|
| `thermal-09-digamma-newton` | symbolic source identity | R2 Newton DD | `PROOF_REQUIRED` | 1 ZERO, 1 UNKNOWN |
| `thermal-09-digamma-newton-z1` | fixed `z=1` | R0 | `PACKAGE_READY` | 2 ZERO |
| `thermal-10-polygamma-order2-recurrence` | fixed `n=2`, symbolic `z` | R1 | `PROOF_REQUIRED` | 1 ZERO, 1 UNKNOWN |
| `thermal-11-digamma-duplication` | fixed `n=2`, symbolic `z` | R1 | `PROOF_REQUIRED` | 1 ZERO, 1 UNKNOWN |
| `thermal-13-alternating-digamma` | symbolic source identity | R5 | `PROOF_REQUIRED` | 1 ZERO, 1 UNKNOWN |
| `thermal-13-alternating-digamma-z1` | fixed `z=1` | R5 fixed instance | `PACKAGE_READY` | 2 ZERO |

Totals: **8 ZERO, 4 UNKNOWN, 0 NONZERO**. Only the two all-ZERO fixed
instances are `PACKAGE_READY`. The four symbolic identities remain
`PROOF_REQUIRED`; none was promoted after UNKNOWN.

## Depth and assumption audit

- Thermal-10 is a shift recurrence, not Hermite structure. Its reference
  program contains neither repeated `NODES` nor `HERMITE_DD`; audited depth is
  R1, not the dossier's proposed R3.
- Thermal-11 with fixed `n=2` is one finite parameter-family reconstruction,
  not an R7 master library; audited depth is R1.
- Thermal-09 at fixed `z=1` parses to an already evaluated special value, so
  it is R0 operationally even though a Newton quotient can be written.
- Thermal-10's original dossier remains unchanged and assumption-audit
  rejected. The package-local contract explicitly declares the entire
  nonpositive-integer polygamma pole exclusion, sourced to DLMF 5.2.2; this
  repairs the package contract without rewriting the dossier or adding a
  physical assumption.

## Parser boundary

No fake undefined-function semantics were used. Thermal-12 (`Integral`),
thermal-14 (Hurwitz `zeta` and symbolic `factorial`), thermal-15 (theta), and
thermal-16 (`gamma`) remain `PACKAGING_GAP` under the frozen parser. They are
not fair search packages and are not counted as method failures.

## Leakage firewall

Every `proposer_view.json` exposes only opaque member IDs, relative member
paths and hashes, plus the assumption-contract reference and hash. It excludes
audited depth, package status, dossier ID, target/operator sequence, reference
program, member roles, and verifier verdicts. Evaluator-only content lives
under `reference/`.

## Authoritative sources

The exact formula sources and retrieved TeX bytes are recorded and SHA-bound
in each `source_manifest.json`:

- NIST DLMF 5.5.2: `https://dlmf.nist.gov/5.5.E2`
- NIST DLMF 5.15.5: `https://dlmf.nist.gov/5.15.E5`
- NIST DLMF 5.5.9: `https://dlmf.nist.gov/5.5.E9`
- NIST DLMF 5.7.7: `https://dlmf.nist.gov/5.7.E7`

## Reproduction

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m research.representation_program_search.packages.thermal.validate --check

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m pytest -q tests/test_rps_thermal_packages.py
```

Observed: validator reports 6 packages, 2 `PACKAGE_READY`, 4
`PROOF_REQUIRED`, verdict totals ZERO=8/UNKNOWN=4/NONZERO=0; tests report
`5 passed`.

## Limits

These artifacts are unpartitioned candidate packages, not DEV or TEST. The
two ready fixed instances do not establish symbolic-family generalization or
AI/search advantage. The symbolic UNKNOWN outcomes are proof gaps, not
counterexamples and not human-assumption gates.
