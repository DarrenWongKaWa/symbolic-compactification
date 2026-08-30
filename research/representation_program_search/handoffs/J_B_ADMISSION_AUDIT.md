# J-B admission audit handoff

Owner: J-B / C6 admission auditor

Branch: `work/rps-admission-audit`

Commit: this handoff's commit (exact SHA reported to the coordinator)

## Scope completed

Independently audited every newly mined non-skeptic dossier under:

- `cases/matrix/` (8)
- `cases/thermal/` (8)
- `cases/response/` (8)
- `cases/tensor/` (8)
- `cases/diffphys/` (7)

The audit checks machine-source/member availability, frozen-parser fit,
ScientificAssumptionContract structure and manual domain gaps, source
provenance, fabrication signals, nontriviality/exactness, depth plausibility,
and historical/intra-new duplicate risk. It does not edit dossiers, select a
partition, change grammar/search/scoring/parser/verifier, run Guo, or touch
shared manifests/`STATUS.md`.

## Deterministic outputs

- `audits/admission/audit.py`: discovers the five indexed miner clusters,
  enforces exact review coverage, hashes every dossier, reads explicit future
  member files through `load_expression()`, and fails closed.
- `audits/admission/reviews.json`: bounded per-case scientific/depth/parser
  review policy, itself SHA-256 bound in the output.
- `audits/admission/ADMISSION_AUDIT.json`: complete machine-readable result.
- `audits/admission/ADMISSION_AUDIT.md`: human table and interpretation
  boundaries.
- `tests/test_rps_admission_audit.py`: focused coverage, precedence,
  provenance, parser-ingestion, path-scope, and reproducibility tests.

Regeneration/check:

```bash
PYTHONPATH=src:. /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m research.representation_program_search.audits.admission.audit --check
```

## Fail-closed result

| exclusive primary status | count |
|---|---:|
| `ADMISSION_CANDIDATE` | 0 |
| `PACKAGING_GAP` | 27 |
| `PROBLEM_UNDERSPECIFIED` | 1 |
| `DUPLICATE_REVIEW` | 8 |
| `REJECT` | 3 |
| total | 39 |

Precedence is `REJECT` → `PROBLEM_UNDERSPECIFIED` → `DUPLICATE_REVIEW` →
`PACKAGING_GAP` → `ADMISSION_CANDIDATE`. Thus scientific/depth/duplicate
failures remain visible even though all 39 dossiers also lack an explicit
machine package.

Key packaging facts:

- parseable admission packages: 0;
- frozen source artifact references with matching repository bytes/hash: 0;
- citations present: 39/39;
- `expression_sketch` is prose/context and is never treated as verifier input;
- direct parser fit after packaging: 4;
- fixed-instance-only lowering route: 15;
- no frozen-parser/verifier route for the required obligation: 20.

Absence of a fabrication signal is reported only as
`NO_FABRICATION_SIGNAL_CITATIONS_NOT_SOURCE_AUTHENTICATED`; it is not
overclaimed as source verification.

## Non-packaging dispositions

`PROBLEM_UNDERSPECIFIED`:

- `rps-r-birman-schwinger-kernel`: compactness/boundedness depends on an
  unspecified “regularity assumptions on V” placeholder rather than a concrete
  potential class.

`REJECT`:

- `rps-r-fano-beutler-profile`: approximate physical formula and shallow
  q-family/rescaled limit do not provide an exact R4 obligation.
- `rps-r-lorentz-causal-poles`: asymptotic dominance regimes are not exact
  Piecewise branches; omega0/tau domain predicates are also incomplete.
- `rps-r-schrieffer-wolff-denom`: the claimed effective Hamiltonian is
  truncated at `O(V^3)`, outside this explicitly non-remainder experiment.

`DUPLICATE_REVIEW` covers eight dossiers: the two new Rodrigues dossiers,
Dirac and SU(3) completeness versus historical Pauli completeness, the (2,2)
Young projector versus historical S3 Young, self-dual Weyl versus historical
Ricci-Weyl, second-Fréchet block exponential versus historical Mathias/Van
Loan block packaging, and phi doubling versus the historical phi-Hermite
family. This is a review gate, not an instruction to reject or select.

Depth review counts:

- plausible as proposed: 34;
- downgrade needed: 3 (`mx-log-richter-01`,
  `thermal-11-gauss-multiplication-psi`, `thermal-15-theta-modular-heat`);
- not operational at proposed depth: 2 (Fano and Lorentz).

Depth plausibility is not certification and cannot count as a representation
result before a complete program and ZERO obligations.

## Validation

- focused admission tests: `11 passed`;
- admission + existing RPS contract/skeptic tests: `26 passed`;
- deterministic `--check`: passed;
- repository-wide suite was stopped at coordinator wrap-up request after
  `1366 passed` with no failures observed; it is not claimed as a complete
  full-suite pass.

All `__pycache__`, `.pyc`, and `.pyo` artifacts were removed before commit.
