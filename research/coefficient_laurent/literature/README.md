# Owner: V5-M — coefficient-space Laurent literature

Sparse Laurent series is **not** novelty. Polygamma Taylor
expansion is **not** novelty. Both are textbook / published CAS.

`LEVEL_A` (atoms expanded) is not hop `ZERO`. A \(t^0\) match
with a surviving \(t^{-1}\) is `NONZERO`. Only `LEVEL_C` may
return hop `ZERO`.

G0016→G0013 is hop `UNKNOWN` (`LEVEL_B` after remainder
fail-close: C0 matches, `remainder_ok` False). The only
*candidate* system contribution — coefficient-space routing at
scientific-expression scale — is a **GAP** until that hop is
`LEVEL_C` `ZERO`. A C0 lemma is not hop ZERO.

This directory is the literature pack for **Track V5**
(coefficient-space Laurent certification of already-frozen
generic→diagonal hops). It does **not** rewrite frozen
compactification literature under `research/literature/`,
the representation-invention pack, Track V, Track V2, Track V3,
or Track V4 literature. Cite those paths.

No tests required. No LLM calls. Do not mutate frozen runs,
SOL, `schema.py`, `cache.py`, `FROZEN_INPUTS_V5.json`,
`PROTOCOL.md`, `STATUS.md`, `OWNERS.md`, or
`research/PROGRAM_STATUS_V5.md`.

## Documents

| file | role |
|---|---|
| `METHODS.md` | Laurent series, sparse coefficient arithmetic, polygamma Taylor, extraction, CAS series, removable poles, LEVEL A/B/C, routing |
| `CLASSIFICATION.md` | each method: known standard \| engineering adaptation \| **GAP** |
| `REFERENCES.bib` | citations used here |
| `HANDOFF.md` | SHA, files, residual risks |
| `__init__.py` | package stub |

## Frozen priors (not this line's novelty)

- Compactification proposer–verifier survey: `research/literature/`
- Representation-invention novelty: `research/representation_invention/literature/NOVELTY.md`
- Track V methods: `research/scalable_verification/literature/` (limits, special-function tables, `SERIES_LOCAL`)
- Track V2 methods: `research/multibranch_verification/literature/`
- Track V3 methods: `research/iterated_confluence/literature/` (iterated limits, removable singularities, series control)
- Track V4 one-pager: `research/polygamma_confluence/literature/CLASSIFICATION.md` (polygamma derivative, Taylor, Laurent \(t^0\) already **known standard**)
- Certification scope: `research/verification/CERTIFICATION_SCOPE.md` (engine semantics, not formal proof; truncated series-coefficient matching is not Level-1 ZERO)
- Track V4 close: CASE **J-C** (`248d247`): diagonal→triple hops ZERO by atom-series; generic→diagonal `UNKNOWN` (together 27327 / timeout)

Do not claim this repo discovered \(\Phi_\Gamma\) or human ladder L4–L7.
Do not claim Track V5 closed. Track D2 stays locked.
**Sparse Laurent is not novelty. Polygamma Taylor is not novelty.**
The packaged contribution is a GAP because G0016→G0013 is not
`LEVEL_C` `ZERO`.
