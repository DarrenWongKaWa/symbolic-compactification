# HANDOFF — Track-V5 Subagent V5-M (literature)

Parent: `7102e8a3884e4f24da453c54f72263fbbb28f2ea`
Branch: `work/v5-literature`

## SHA

Parent `7102e8a3884e4f24da453c54f72263fbbb28f2ea`.
Live tip: `git rev-parse work/v5-literature`.

## Files (owned: `research/coefficient_laurent/literature/**`)

- `README.md` (index; does not rewrite frozen `research/literature/`,
  representation-invention literature, Track V, Track V2, Track V3,
  or Track V4 literature)
- `METHODS.md`
- `CLASSIFICATION.md`
- `REFERENCES.bib`
- `HANDOFF.md` (this file)
- `__init__.py` (package stub)

## Tests

None required. No live tests added. Shared contracts
(`schema.py`, `cache.py`, `PROTOCOL.md`, `FROZEN_INPUTS_V5.json`,
`freeze_v5.py`, `STATUS.md`, `OWNERS.md`,
`research/PROGRAM_STATUS_V5.md`) were not edited.
Frozen run trees were not edited. SOL was not retuned.
No paper directory. No LLM API.

## What this pack asserts

- Sparse Laurent series is standard math / standard CAS, not
  novelty.
- Polygamma Taylor expansion (and the derivative identity
  \(\mathrm{polygamma}(n+1)=d/dz\,\mathrm{polygamma}(n)\)) is
  standard special functions, not novelty. Track V4 already
  said this; Track V5 does not lift the ban.
- Laurent series, residues, removable singularities (Riemann),
  truncated CAS series (Gruntz / `sympy.series`), and sparse
  polynomial arithmetic (Geddes–Czapor–Labahn; FORM) remain
  known standard.
- Linearity of \([t^k]\), LEVEL A/B/C IR, reconstruction, and
  full-text cache keys are engineering adaptations, not new
  theorems.
- `LEVEL_A` is not hop `ZERO`. A \(t^0\) match with a surviving
  \(t^{-1}\) is `NONZERO`. Only `LEVEL_C` may return `ZERO`.
- Timeout / size-guard stays `UNKNOWN`. Numeric agreement is
  never ZERO. Majority of atoms or coefficients is forbidden.
- Never reuse G0014→G0012 certificates for G0016→G0013.
- Interpolation confluence ≠ rewriting confluence. Sparse
  Laurent ≠ sparse interpolation ≠ Puiseux.
- Truncated `series`+`removeO()` without remainder is not
  LEVEL C. Coefficient matching on expanded series is not
  Level-1 ZERO (`CERTIFICATION_SCOPE.md`).
- **Potential system contribution is coefficient-space routing
  at scientific-expression scale. That cell is a GAP until
  G0016→G0013 is `LEVEL_C` `ZERO`.** This pack is not that
  experiment. Do not claim a system-level combination until
  that hop exists with false hop `ZERO` = 0.
- Even a later hop ZERO is V_GAIN only. It is not
  `FAMILY_ZERO` and does not auto-`CONSISTENT_ZERO`. Track D2
  stays locked.
- This repo has **not** discovered \(\Phi_\Gamma\) or L4–L7.
- V4 CASE J-C (`248d247`) diagonal ZERO is not G0016→G0013.
- Publication status E.

## Residual risks

1. **Neighbor coverage is not exhaustive.** Proposer–verifier
   crowding lives in frozen `research/literature/`. Pair-scale
   limits / special-function tables live in Track V literature.
   Iterated-limit / removable-singularity classification lives
   in Track V3 literature. Track V4’s one-pager already banned
   polygamma Taylor as novelty. This pack cites those paths
   instead of duplicating FunSearch/Lean/Moxia/Gruntz rows in
   full.
2. **2025–2026 preprints** (LGuess, Moxia, O-Forge) still block
   “first certificate / first LLM+CAS” slogans even with weaker
   venue signal.
3. **egg / Lean / Wolfram / Maple `series`** are not assumed
   available on this host. Lack of a runtime is not novelty.
   Presence of published series/coeff primitives elsewhere is
   prior work, not a gap we fill.
4. **Other subagents (V5-A..L) may later land verifiers.** This
   audit must not be reread as evidence that G0016→G0013 is
   `LEVEL_C` `ZERO`. Status remains literature-only until those
   gates fire with false hop `ZERO` = 0.
5. **Two meanings of “sparse.”** Sparse Laurent *representation*
   (store nonzero \((k,a_k)\)) vs sparse *interpolation*
   (recover a polynomial from evaluations). Mixing them in a
   paper draft would be a reviewer-kill.
6. **Two meanings of “series.”** Laurent / Taylor of a germ vs
   Gruntz hierarchical MRV series vs Puiseux vs transseries.
   Mixing them would also be a reviewer-kill.
7. **Two meanings of “confluence.”** Interpolation-node
   confluence vs rewriting confluence (already recorded in
   Tracks V–V3). Mixing them remains a reviewer-kill.
8. **Certificate overload.** WZ, LEDA, ITP kernels, and PIT all
   own the word. Track-V5 “certificates” are reconstruction
   witnesses under engine semantics, not formal proofs.
   PIT/numerics must not become a ZERO path.
9. **CERTIFICATION_SCOPE vs Laurent coeffs.** Frozen scope
   forbids “coefficient matching on expanded series” as
   Level-1 ZERO. LEVEL C must be an exact residual of
   \(a_0\) versus the target, after poles vanish, with
   remainder — not agreement of the first few \([t^k]\).
   A draft that ignores this will be cited against us by
   ourselves.
10. **Hartogs vs real kernels.** Citing Hartogs extension to
    skip polar checks on Guo Piecewise polygamma is a type
    error (holomorphic \(\mathbb C^n\) vs real CAS kernel).
11. **V4 cache defect class.** Missing `text_sha256` is not a
    license to treat two different member texts as one hop.
12. **Hop vs family.** G0016→G0013 `LEVEL_C` `ZERO`, if it
    later exists, still does not unlock D2 by itself.

## Do not

- Edit `research/literature/`, `research/representation_invention/`
  (except citing), `research/scalable_verification/` (except
  citing), `research/multibranch_verification/` (except citing),
  `research/iterated_confluence/` (except citing),
  `research/polygamma_confluence/` (except citing), frozen run
  JSON, SOL, `schema.py`, `cache.py`, `FROZEN_INPUTS_V5.json`,
  `PROTOCOL.md`, `STATUS.md`, `OWNERS.md`, or
  `research/PROGRAM_STATUS_V5.md`.
- Put Guo gold names in proposer-visible files or ZERO rules.
- Treat this documentation as a method result or as Track V5
  closed.
- Convert timeout, `LEVEL_A`, or \(t^0\)+surviving pole to hop
  `ZERO`.
- Relabel Track V4 diagonal ZERO as G0016→G0013.
- Relabel one hop ZERO as `FAMILY_ZERO` or as unlocking D2.
- Open Track D2 until a frozen family is `FAMILY_ZERO` or
  `FAMILY_NONZERO`.
- Claim sparse Laurent series as novelty.
- Claim polygamma Taylor as novelty.
- Claim Laurent series, residues, or Gruntz as novelty.
- Claim `LEVEL_A` is hop ZERO.
- Upgrade the GAP cell to “potential novel contribution” while
  G0016→G0013 is not `LEVEL_C` `ZERO`.
- Call an LLM API.
