# Owner: V9 — verification literature

Newton/Hermite divided-difference mathematics is **not** novelty.

This directory is the literature pack for **Track V** (scalable
compositional verification of already-proposed hypotheses). It does
**not** rewrite frozen compactification literature under
`research/literature/` or the representation-invention pack under
`research/representation_invention/literature/`. Cite those paths.

No tests required. No LLM calls. Do not mutate frozen runs, SOL, or
`FROZEN_INPUTS.json`.

## Documents

| file | role |
|---|---|
| `METHODS.md` | verification techniques: limits, confluent DD, Hermite, compositional proof, factoring, certificates, e-graphs, special-function identities |
| `CLASSIFICATION.md` | each method: known standard \| engineering adaptation \| potential novel contribution |
| `REFERENCES.bib` | citations used here |
| `HANDOFF.md` | SHA, files, residual risks |
| `__init__.py` | package stub |

## Frozen priors (not this line's novelty)

- Compactification proposer–verifier survey: `research/literature/` (freeze `13814ba`)
- Representation-invention novelty: `research/representation_invention/literature/NOVELTY.md`
- Certification scope: `research/verification/CERTIFICATION_SCOPE.md` (engine semantics, not formal proof)
- DD constructors (textbook, not discovery): `research/representation_invention/dd/`
- Local confluence baseline (G1, not DD-OK): Grounded-Proposer-v1 `3fea222`

Do not claim this repo discovered \(\Phi_\Gamma\) or human ladder L4–L7.
Do not claim Track V closed; that requires `TRACK_V_CLOSED.md` after
false ZERO = 0 on the generic suite and frozen rescore.
