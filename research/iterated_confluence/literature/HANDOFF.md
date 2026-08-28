# HANDOFF — Track-V3 Subagent V3-K (literature)

Parent: `dcfb90cac087a47241aced2dc0c3b851f1a12e21`
Branch: `work/v3-literature`

## SHA

Parent `dcfb90cac087a47241aced2dc0c3b851f1a12e21`.
Live tip: `git rev-parse work/v3-literature`.

## Files (owned: `research/iterated_confluence/literature/**`)

- `README.md` (index; does not rewrite frozen `research/literature/`,
  representation-invention literature, Track V literature, or
  Track V2 literature)
- `METHODS.md`
- `CLASSIFICATION.md`
- `REFERENCES.bib`
- `HANDOFF.md` (this file)
- `__init__.py` (package stub)

## Tests

None required. No live tests added. Shared contracts
(`schema.py`, `PROTOCOL.md`, `FROZEN_INPUTS_V3.json`,
`freeze_v3.py`, `STATUS.md`, `OWNERS.md`,
`research/PROGRAM_STATUS_V3.md`) were not edited.
Frozen run trees were not edited. SOL was not retuned.
No paper directory.

## What this pack asserts

- Iterated limits are standard math, not novelty.
- Joint limit ≠ iterated limit. Moore–Osgood / \(C^k\) /
  Hermite–Genocchi are extra hypotheses, not free.
- `PATH_ZERO` does not imply joint confluence and does not
  imply `FAMILY_ZERO`.
- Multivariate removable singularities (Riemann; Hartogs SCV;
  real 0/0) are standard. Hartogs is the wrong object for real
  Piecewise polygamma.
- Symbolic multivariate-limit algorithms (Gruntz; Cadavid;
  Xiao–Zeng; RegularChains; Strzeboński; Maple `limit/multi`)
  are published CAS. “First multivariate limit” is forbidden.
- Newton DD, confluent/repeated-node filling, Hermite
  interpolation, and the Hermite recurrence remain known
  standard (Track V, Track V2). Sequencing them along a path
  does not mint a theorem.
- PATH vs FAMILY glue, budgets, and fail-closed
  ZERO/NONZERO/UNKNOWN are engineering adaptations, not new
  theorems.
- `FAMILY_ZERO` is never majority vote. Timeout / size-guard
  stays `FAMILY_UNKNOWN`. Numeric agreement is never ZERO.
- Interpolation confluence ≠ rewriting confluence. IBP
  “families” ≠ Newton tables.
- **Potential novelty is a GAP.** V2 closed CASE H-C
  (`fe53ebc`). Frozen Guo 5-branch family certificates do not
  exist. This pack is not that experiment. Do not claim a
  system-level combination (proof decomposition / routing /
  scientific-expression-scale machine certification) until
  those certificates exist.
- This repo has **not** discovered \(\Phi_\Gamma\) or L4–L7.
- Track V pair-ZERO (`38d6d4a`, 3 two-member hyps) is not V3
  `FAMILY_ZERO`.
- P1 (`3fea222`) is local confluence (G1/R0), not DD-OK.
- Track D2 stays locked. Publication status E.

## Residual risks

1. **Neighbor coverage is not exhaustive.** Proposer–verifier
   crowding lives in frozen `research/literature/`. Pair-scale
   Newton/Hermite classification lives in Track V literature.
   Family-scale Hermite-recurrence classification lives in
   Track V2 literature. This pack cites those paths instead of
   duplicating FunSearch/Lean/Moxia/Gruntz rows in full.
2. **2025–2026 preprints** (LGuess, Moxia, O-Forge) still block
   “first certificate / first LLM+CAS” slogans even with weaker
   venue signal.
3. **egg / Lean / Wolfram / Maple `limit/multi`** are not
   assumed available on this host. Lack of a runtime is not
   novelty. Presence of a published multivariate-limit CAS
   elsewhere is prior work, not a gap we fill.
4. **Other subagents (V3-A..J) may later land verifiers.** This
   audit must not be reread as evidence that `PATH_ZERO` or
   `FAMILY_ZERO` already holds. Status remains literature-only
   until those gates fire with false `FAMILY_ZERO` = 0.
5. **Conti vs Conte.** The NA textbook is S. D. Conte and C. de
   Boor (1980). “Conti/de Boor” is that pair, not Costanza
   Conti’s spline papers.
6. **Two meanings of “confluence.”** Interpolation-node
   confluence vs rewriting confluence. Mixing them in a paper
   draft would be a reviewer-kill.
7. **Two meanings of “family.”** Newton/Hermite node table vs
   IBP master-integral vector space. Mixing them would also be
   a reviewer-kill.
8. **Two meanings of “path.”** Real-analysis path to a point vs
   an ordered list of one-parameter `PathStep`s. Mixing them
   would also be a reviewer-kill.
9. **Certificate overload.** WZ, LEDA, ITP kernels, and PIT all
   own the word. Track-V3 “certificates” are reconstruction
   witnesses under engine semantics, not formal proofs.
   PIT/numerics must not become a ZERO path.
10. **Hartogs vs real kernels.** Citing Hartogs extension to
    skip path-consistency on Guo Piecewise polygamma is a type
    error (holomorphic \(\mathbb C^n\) vs real CAS kernel).
11. **Hermite–Genocchi path independence** must not be used to
    skip path-consistency obligations on untrusted Piecewise
    kernels (`AGENTS.md` rule 14).
12. **Cadavid-style joint rational limits** must not be
    advertised as this engine’s algorithm. They are neighbors
    for a different object (isolated polynomial denominator).

## Do not

- Edit `research/literature/`, `research/representation_invention/`
  (except citing), `research/scalable_verification/` (except
  citing), `research/multibranch_verification/` (except citing),
  frozen run JSON, SOL, `schema.py`, `FROZEN_INPUTS_V3.json`,
  `PROTOCOL.md`, `STATUS.md`, `OWNERS.md`, or
  `research/PROGRAM_STATUS_V3.md`.
- Put Guo gold names in proposer-visible files or ZERO rules.
- Treat this documentation as a method result or as Track V3
  closed.
- Convert timeout or 4-of-5 paths to `FAMILY_ZERO`.
- Relabel Track V pair-ZERO as family certification.
- Relabel one `PATH_ZERO` as joint confluence.
- Open Track D2 until I-A or I-B.
- Claim iterated limits as novelty.
- Claim the Hermite recurrence as novelty.
- Claim Newton DD as novelty.
- Claim `PATH_ZERO` implies joint confluence.
- Upgrade the GAP cell to “potential novel contribution” while
  Guo family certificates do not exist.
