# HANDOFF — Track-V2 Subagent V2-J (literature)

Parent: `4dee916170f0282f8b0e5fee171a8bf4a3934646`
Branch: `work/v2-literature`

## SHA

Parent `4dee916170f0282f8b0e5fee171a8bf4a3934646`.
Live tip: `git rev-parse work/v2-literature`.

## Files (owned: `research/multibranch_verification/literature/**`)

- `README.md` (index; does not rewrite frozen `research/literature/`,
  representation-invention literature, or Track V literature)
- `METHODS.md`
- `CLASSIFICATION.md`
- `HANDOFF.md` (this file)
- `__init__.py` (unchanged stub)

## Tests

None required. No live tests added. Shared contracts
(`schema.py`, `PROTOCOL.md`, `FROZEN_INPUTS_V2.json`,
`freeze_v2.py`, `research/PROGRAM_STATUS_V2.md`) were not edited.
Frozen run trees were not edited. SOL was not retuned.

## What this pack asserts

- Hermite recurrence is standard math, not novelty.
- Newton DD, confluent/repeated-node filling, and Hermite–Genocchi
  joint continuity are known standard.
- Limit decomposition, local-edge certificates, and the
  local-to-global `FAMILY_ZERO` glue are engineering adaptations,
  not new theorems.
- `FAMILY_ZERO` is never majority vote. Timeout / size-guard stays
  `FAMILY_UNKNOWN`. Numeric agreement is never ZERO.
- Interpolation confluence ≠ rewriting confluence. IBP “families”
  ≠ Newton tables.
- Potential novelty **only if** later `FAMILY_ZERO` on the frozen
  Guo 5-branch set with false `FAMILY_ZERO` = 0. This pack is not
  that experiment.
- This repo has **not** discovered \(\Phi_\Gamma\) or L4–L7.
- Track V pair-ZERO (`38d6d4a`, 3 two-member hyps) is not V2
  `FAMILY_ZERO`.
- P1 (`3fea222`) is local confluence (G1/R0), not DD-OK.
- Track D2 stays locked until CASE H-A or H-B.

## Residual risks

1. **Neighbor coverage is not exhaustive.** Proposer–verifier crowding
   lives in frozen `research/literature/`. Pair-scale Newton/Hermite
   classification lives in Track V literature. This pack cites those
   paths instead of duplicating FunSearch/Lean/Moxia/Gruntz rows in
   full.
2. **2025–2026 preprints** (LGuess, Moxia, O-Forge) still block
   “first certificate / first LLM+CAS” slogans even with weaker
   venue signal.
3. **egg / Lean / Wolfram** are not assumed available on this host.
   Lack of a runtime is not novelty.
4. **Other subagents (V2-A..I) may later land verifiers.** This audit
   must not be reread as evidence that `FAMILY_ZERO` already holds.
   Status remains literature-only until those gates fire with false
   `FAMILY_ZERO` = 0.
5. **Conti vs Conte.** The NA textbook is S. D. Conte and C. de Boor
   (1980). “Conti/de Boor” is that pair, not Costanza Conti’s spline
   papers.
6. **Two meanings of “confluence.”** Interpolation-node confluence vs
   rewriting confluence. Mixing them in a paper draft would be a
   reviewer-kill.
7. **Two meanings of “family.”** Newton/Hermite node table vs IBP
   master-integral vector space. Mixing them would also be a
   reviewer-kill.
8. **Certificate overload.** WZ, LEDA, ITP kernels, and PIT all own
   the word. Track-V2 “certificates” are reconstruction witnesses
   under engine semantics, not formal proofs. PIT/numerics must not
   become a ZERO path.
9. **Hermite–Genocchi path independence** must not be used to skip
   path-consistency obligations on untrusted Piecewise kernels
   (`AGENTS.md` rule 14).

## Do not

- Edit `research/literature/`, `research/representation_invention/`
  (except citing), `research/scalable_verification/` (except citing),
  frozen run JSON, SOL, `schema.py`, `FROZEN_INPUTS_V2.json`,
  `PROTOCOL.md`, or `research/PROGRAM_STATUS_V2.md`.
- Put Guo gold names in proposer-visible files or ZERO rules.
- Treat this documentation as a method result or as Track V2 closed.
- Convert timeout or 4-of-5 edges to `FAMILY_ZERO`.
- Relabel Track V pair-ZERO as family certification.
- Open Track D until CASE H-A or H-B.
- Claim the Hermite recurrence as novelty.
