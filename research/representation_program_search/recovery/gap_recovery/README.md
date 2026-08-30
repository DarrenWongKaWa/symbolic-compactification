# Strict gap recovery

This collection contains one new, candidate-only R2 repair and one bounded R6
negative mining audit. It does not admit a case to DEV, modify a benchmark
manifest, or create a TEST identity.

## R2 replacement package

`rps-candidate-k9-001` preserves the scientific identity of the rejected
`gap_fill/gf-cr3bp-2017-eq28` package while replacing its package boundary and
all generated evidence. The rejected package remains unchanged.

The public search boundary is opaque (`C9H4`, `M9H1`–`M9H4`) and contains only
hash-bound assumptions, catalog, symbols, and member expressions. Calling
`load_public_case()` loads the exact eight-symbol namespace with every symbol
explicitly `real:true`; it does not infer `real:false`.

The primary evidence is Wan, Bihlo, and Nave, “Conservative methods for
dynamical systems,” DOI `10.1137/16M110719X`. Six exact byte excerpts from the
arXiv v1 TeX source are stored under `source/upstream/`. Their hashes bind:

- the Section 5.3 scientific context and four unnumbered coordinate identities;
- the following numbered source environment, which proves the old Eq. 28 name
  was wrong;
- the real-domain declaration;
- the divided-difference definition and exact rule hypotheses.

The source actually places the four retained identities in an unnumbered
`align*` block after source label `3bodySys` and before `R3B_RHS`. The new
dossier states that correction explicitly. It does not infer positivity of the
relative masses; only `alpha+beta=1` is source-declared there.

The M1 program compiles without schema deltas or tautology in:

- `G_FULL`: named two-node construction plus linear reconstruction;
- `G_NO_HERMITE`: the same legal program;
- `G_PRIMITIVE`: two values and linear combinations construct the quotients
  compositionally, without a named divided-difference operator.

All 12 compiled obligations have a recorded main-agent `HYPOTHESIS` followed
by exact `CERTIFIED`/`ZERO` evidence.

The fresh duplicate audit covers 79 historical documents, the current case
and package pools, and the sealed Guo diagnostic. The only exact member matches
are the four expected members of the rejected predecessor; there are no other
exact or alpha-renamed matches. This is a repair, not a claim of a new
scientific identity.

## R6 result

`R6_MINING_NEGATIVE.json` records `NO_DEFENSIBLE_R6_CANDIDATE`. Fresh
multi-operator objects found in Maxwell/Debye and Potts transfer-matrix sources
require vector curl/basis or matrix power/trace/determinant semantics absent
from frozen M1, and their sources directly expose the proposed representation.
Parser-feasible scalar alternatives are derivative/recurrence ladders,
duplicates, or previously depth-downgraded response graphs. No toy package was
forced.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python -m \
  research.representation_program_search.recovery.gap_recovery.validate \
  --root .

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. python -m pytest -q \
  tests/test_rps_gap_recovery.py
```

The builder is a one-shot provenance artifact and refuses to overwrite the
committed package.
