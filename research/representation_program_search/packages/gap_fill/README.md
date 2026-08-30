# Candidate-only R2/R6 gap fill

This directory contains two newly mined, source-backed
`RPSCasePackageV1` candidates. They are **not** in a DEV, TEST, CHALLENGE, or
shared admission manifest. `PACKAGE_READY` means only that the exact package
obligations are ZERO and the machine package is complete; a coordinator must
still run the independent source, depth, assumption, and leakage gates before
admission.

## Candidates

### `gf-cr3bp-2017-eq28`

An operational R2 family from Wan, Bihlo, and Nave's conservative scheme for
the planar restricted three-body problem. Four coordinate-wise gravitational
terms share the real scalar latent object

```text
F(z) = 1/sqrt(z)
```

at four pairs of distinct squared-distance nodes. Each member is reconstructed
by `NEWTON_DD` followed by its source chain-rule coefficient. This is not a
resolvent, Daleckii–Krein, phi-function, logarithm split, matrix-square-root
Sylvester coefficient, or a renamed historical identity. The source is a
peer-reviewed SIAM article, DOI `10.1137/16M110719X`.

Status: `CANDIDATE_ONLY_NOT_ADMITTED`. Four required obligations are exact
ZERO.

### `gf-vdw-2013-eq1`

A proposed R6 multi-operator family built from the real van der Waals Helmholtz
free energy at fixed particle number. Eight members cover the Helmholtz value,
pressure, entropy, internal energy, isochoric heat capacity, isothermal bulk
modulus, isothermal compressibility, and enthalpy. The typed program branches
from one `FUNCTION_2`, reuses intermediate outputs, and uses five operator
types (`VALUE`, `DERIVATIVE`, `SUBSTITUTE`, `LINEAR_COMBINATION`, `COMPOSE`).
All of those operators are in `G_PRIMITIVE`; no named MASTER primitive exists.

Status: `CANDIDATE_ONLY_DEPTH_REVIEW_REQUIRED`. Eight required obligations are
exact ZERO. This is intentionally not labeled admitted R6: the Helmholtz
source is an institutional scientific note, and an independent reviewer must
decide whether the branching thermodynamic reconstruction clears the R6
frontier rather than constituting a familiar derivative family.

## Reproduce the checks

```bash
PYTHONDONTWRITEBYTECODE=1 python -m \
  research.representation_program_search.packages.gap_fill.validate --json

PYTHONDONTWRITEBYTECODE=1 python -m \
  research.representation_program_search.packages.gap_fill.freshness_audit --json

PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
  tests/test_rps_gap_fill_candidates.py
```

`build_candidates.py --build` is a one-shot provenance builder and refuses to
overwrite committed evidence. It is not used by CI. The public proposer view
contains only the exact source catalog and assumption-contract links; the
program, operators, proposed depth, obligations, and receipts remain private.

No TEST or Guo case was read or run during package construction. No parser,
verifier, grammar, evaluator, benchmark manifest, or scientific method code was
changed.
