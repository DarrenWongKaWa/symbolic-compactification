# J-A Handoff — Scientific Assumption Audit

## Scope

Audited all 39 non-skeptic case dossiers in the five requested clusters:
matrix (8), thermal (8), response (8), tensor (8), and differentiable physics
(7).  The skeptic controls, shared manifests/contracts/STATUS, Guo, case
dossiers, parser, verifier, and benchmark partitions were not changed.

## Owned changes

- `audits/assumptions/audit.py`: deterministic canonical audit builder/checker.
- `audits/assumptions/REQUIRED_PREDICATES.json`: frozen, source-backed
  reclassifications and required-predicate gaps.
- `audits/assumptions/AUDIT.json`: complete predicate-level artifact bound to
  every dossier SHA-256.
- `audits/assumptions/README.md`: semantics, results, reproduction, limits.
- `tests/test_rps_assumption_audit.py`: focused coverage, determinism, hash,
  fail-closed, and no-partition-selection tests.

## Results

- `ASSUMPTION_COMPLETE`: 30/39.
- `PROBLEM_UNDERSPECIFIED`: 9/39.
- Predicate classifications: 559 `DECLARED`, 69 `DERIVED`, 14
  `NOT_DECLARED`.
- Fail-closed case IDs:
  `thermal-10-polygamma-recurrence`,
  `rps-r-birman-schwinger-kernel`,
  `rps-r-fano-beutler-profile`,
  `rps-r-lorentz-causal-poles`,
  `rps-r-schrieffer-wolff-denom`,
  `rps-r-weyl-titchmarsh-m`,
  `rps-dp-dexpinv-bernoulli`,
  `rps-dp-liouville-jacobi-cnf`, and
  `rps-dp-stm-sensitivity-kernel`.

These outcomes are audit gates only.  No case was selected for DEV or TEST,
and an assumption-complete case still requires the separate admission,
source, duplicate/leakage, packaging, and exact-verification checks.

## Commands and observed results

```text
PYTHONDONTWRITEBYTECODE=1 /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m research.representation_program_search.audits.assumptions.audit --check
exit 0

PYTHONDONTWRITEBYTECODE=1 /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m pytest -q tests/test_rps_assumption_audit.py
8 passed

PYTHONDONTWRITEBYTECODE=1 /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m pytest -q tests/test_rps_assumption_audit.py tests/test_ac_schema.py \
  tests/test_rps_skeptic.py tests/test_rps_contracts.py
25 passed

PYTHONDONTWRITEBYTECODE=1 /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m pytest -q
1671 passed in 204.42s
```

## Limitations

- Source support is the dossier's frozen public citation list and exact local
  contract text; this audit does not replace an independent extraction audit.
- It classifies assumptions needed by the currently displayed members, not
  identities or programs that future method agents may invent.
- `ASSUMPTION_COMPLETE` is deliberately not called `CERTIFIED` or `ADMITTED`.

## Provenance

- Parent baseline: `9e568b3` (`C1: eight assumption-complete matrix-function candidate dossiers.`)
- Implementation commit: supplied separately in the final handoff because a
  commit cannot contain its own SHA without changing that SHA.
