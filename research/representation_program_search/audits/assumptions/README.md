# Scientific Assumption Audit — Representation Program Search V1

## Scope and verdict semantics

This audit covers every non-skeptic JSON dossier under `cases/matrix`,
`cases/thermal`, `cases/response`, `cases/tensor`, and `cases/diffphys` at the
input hashes recorded in `AUDIT.json`.  It does not select DEV, TEST, or
CHALLENGE and does not change a dossier.

The audit uses the existing `ScientificAssumptionContract` labels:

- `DECLARED`: written in the contract, including an explicit domain or branch
  declaration.
- `DERIVED`: follows from declared predicates without adding scientific or
  physical assumptions.
- `NOT_DECLARED`: needed by a displayed member or source theorem but neither
  declared nor derivable.

One `NOT_DECLARED` verifier-domain predicate makes the case
`PROBLEM_UNDERSPECIFIED`.  This is an assumption-domain failure, not a search
failure, verifier failure, or packaging gap.  An `ASSUMPTION_COMPLETE` result
only makes a case eligible for the separate admission, leakage, duplicate,
packaging, and verification audits.

## Deterministic artifacts

- `REQUIRED_PREDICATES.json` freezes the source-backed reclassifications and
  required-but-absent predicates found by the audit.
- `audit.py` inventories every contract entry, binds each dossier by SHA-256,
  applies the frozen findings, and produces canonical JSON.
- `AUDIT.json` is the generated complete audit, including every predicate,
  the dossier label, the audited classification, the source basis for each
  gap, and the downstream fail-closed gate.

Reproduce or check the artifact with Python 3.12:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  -m research.representation_program_search.audits.assumptions.audit --write
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  -m research.representation_program_search.audits.assumptions.audit --check
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q \
  tests/test_rps_assumption_audit.py
```

## Results

| Cluster | Audited | Assumption-complete | `PROBLEM_UNDERSPECIFIED` |
|---|---:|---:|---:|
| matrix | 8 | 8 | 0 |
| thermal | 8 | 7 | 1 |
| response | 8 | 3 | 5 |
| tensor | 8 | 8 | 0 |
| diffphys | 7 | 4 | 3 |
| **Total** | **39** | **30** | **9** |

The nine fail-closed cases are:

- `thermal-10-polygamma-recurrence`: `z != 0` does not derive exclusion of
  every nonpositive-integer polygamma pole.
- `rps-r-birman-schwinger-kernel`: the required potential regularity is a
  placeholder, not an explicit function-space condition.
- `rps-r-fano-beutler-profile`: nonzero line width and the real domain of `q`
  used by the extrema claims are absent.
- `rps-r-lorentz-causal-poles`: `tau != 0` and the positive-real domain of
  `omega0` needed by strict lower-half-plane pole placement are absent.
- `rps-r-schrieffer-wolff-denom`: the displayed sums do not quantify their
  denominator exclusions, and Hermiticity/real spectral data needed by the
  anti-Hermitian/unitary claim are absent.
- `rps-r-weyl-titchmarsh-m`: the operator, coefficient regularity, realization,
  and endpoint choice underlying the mixed M-function/Green-kernel statements
  are not fixed.
- `rps-dp-dexpinv-bernoulli`: invertibility of `dexp` does not imply
  convergence of its Bernoulli Taylor series outside `|w| < 2*pi`; no operator
  series convergence predicate is imposed.
- `rps-dp-liouville-jacobi-cnf`: the nonlinear CNF vector field lacks the
  regularity needed for `Df`, its trace, and a differentiable flow.
- `rps-dp-stm-sensitivity-kernel`: forcing integrability and differentiability
  of parameter-dependent initial data are absent.

The artifact records 642 audited predicates: 559 `DECLARED`, 69 `DERIVED`,
and 14 `NOT_DECLARED`.  Two of the gaps reclassify existing dossier entries;
the others record verifier-needed predicates absent from the contracts.  No
gap is repaired here: the dossiers and their source hashes remain unchanged.

## Limitations

This is a contract sufficiency audit against the members presently written in
each dossier.  It does not independently certify the mathematical identities,
approve source extraction, establish parser support, assess novelty/leakage,
or determine a benchmark partition.  The public citations recorded by each
dossier and the exact local contract text are the evidence base; a downstream
source-extraction audit may still reject a case whose assumptions pass here.
