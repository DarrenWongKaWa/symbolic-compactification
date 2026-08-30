# Handoff — candidate-only R2/R6 gap fill

## Scope completed

Implemented two fresh, source-backed candidate packages under
`packages/gap_fill/` without changing shared manifests, parser, verifier,
grammar, search policy, evaluator, DEV/TEST inputs, or Guo artifacts.

## Candidate results

1. `gf-cr3bp-2017-eq28`
   - proposed depth: R2;
   - one reciprocal-square-root latent, four physical two-node instances;
   - operator profile: 4 `NEWTON_DD`, 4 `LINEAR_COMBINATION`;
   - 4/4 required obligations exact ZERO;
   - M1 schema deltas: none;
   - M1 program id:
     `d194d3532d65b3f7707995d78c35cce91995c323061e87435b9fa229f6031b5c`.

2. `gf-vdw-2013-eq1`
   - proposed depth: R6, explicitly independent-depth-review gated;
   - eight thermodynamic members, two latents, five operator kinds, branching
     and reuse;
   - 8/8 required obligations exact ZERO;
   - compiles under `G_PRIMITIVE` because it uses only `VALUE`, `DERIVATIVE`,
     `SUBSTITUTE`, `LINEAR_COMBINATION`, and `COMPOSE`;
   - M1 schema deltas: none;
   - M1 program id:
     `a9edbe98eae38051f4c43003f7cc8c806d2390d60cb9764aca2aa52fe0d67543`.

The R6 package is deliberately not called admitted. Its exact Helmholtz source
is institutional grey literature, although NIST and a peer-reviewed JCP source
bind the derivative and response semantics. An independent reviewer must
decide whether the branching graph is genuinely R6 or a familiar derivative
family.

## Audit result

Gold-free comparison covered 79 historical documents, 47 current mined cases,
and 13 existing packages. Both candidates had zero blocking duplicate/leakage
findings and remain `PASS_TO_INDEPENDENT_MANUAL_REVIEW`. This does not select a
partition.

## Reproduction

```bash
PYTHONDONTWRITEBYTECODE=1 python -m \
  research.representation_program_search.packages.gap_fill.validate --json

PYTHONDONTWRITEBYTECODE=1 python -m \
  research.representation_program_search.packages.gap_fill.freshness_audit --json

PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
  tests/test_rps_gap_fill_candidates.py
```

The one-shot builder refuses to overwrite the committed receipts. See
`packages/gap_fill/MINING_AUDIT.md` and each package's hash-bound source
dossier for source locations and domain contracts.
