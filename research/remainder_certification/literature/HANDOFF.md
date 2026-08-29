# HANDOFF — Subagent R12 (literature / novelty audit)

Parent: `adbfd9f755546a82108f0464e5bcbe82df6d62e3`
Branch: `work/r-literature`
Worktree: isolated (`/private/tmp/wt-r-literature`)

Not Track V6. No LLM. Track D2 LOCKED. Do not revive retracted
LEVEL_C ZERO (`fb3b929`). Remainder `CERTIFIED` is not hop ZERO.

## SHA

Parent `adbfd9f755546a82108f0464e5bcbe82df6d62e3`.
Live tip: `git rev-parse work/r-literature`.

## Files (owned: `research/remainder_certification/literature/**`)

- `README.md`
- `METHODS.md`
- `CLASSIFICATION.md`
- `REFERENCES.bib`
- `HANDOFF.md` (this file)
- `__init__.py` (package stub)

## Tests

None required. No live tests added. Shared remainder-certification
contracts (`schema.py`, `PROTOCOL.md`, `PROBLEM_STATEMENT.md`,
`ASSUMPTION_POLICY.md`, `STATUS.md`, `OWNERS.md`) were not edited.
Frozen V3/V4/V5 runs, SOL, B9, LGG, hop engine timeouts were not
edited. `research/PROGRAM_STATUS_V5.md` and
`research/coefficient_laurent/literature/` were cited, not rewritten.
No paper directory. No LLM API. No publication letter.

## What this pack asserts

- Holomorphic Taylor remainder is **STANDARD MATHEMATICS**.
- Cauchy estimates are **STANDARD MATHEMATICS**.
- Polygamma meromorphic structure (poles at nonpositive integers;
  DLMF 5.15 recurrence, reflection, polar leading term) is
  **STANDARD MATHEMATICS**.
- Symbolic asymptotics (Gruntz / hierarchical series) and CAS
  `series` + `O(t^n)` notation are **STANDARD CAS TECHNIQUE**.
  The `O` token is not a remainder certificate.
- Interval / ball arithmetic and numeric certified series (Moore;
  van der Hoeven; Arb; Taylor models) are published validated
  numerics. They certify **numeric** enclosures, not symbolic
  affine arguments. **STANDARD CAS TECHNIQUE** (theory of
  interval analysis: **STANDARD MATHEMATICS**).
- Holonomic / D-finite tail bounds (Mezzarobba, NumGfun) are
  **STANDARD CAS TECHNIQUE**. They are the **wrong object** for
  polygamma in the argument \(z\): infinitely many poles ⇒ not
  D-finite.
- `RemainderCertificate` IR, assumption classes A/B/C/D, and
  fail-closed `validate_certificate` are **SYSTEMS INTEGRATION**.
- Track V5 C0 match is **not** this line’s contribution. Cite
  `research/coefficient_laurent/literature/`.
- The only candidate contribution is **machine-checkable remainder
  certificates for symbolic affine special-function arguments
  under explicit assumption classes**. That cell is a **GAP**
  until a generic suite exists with false `CERTIFIED` = 0.
  It is labelled POTENTIAL RESEARCH CONTRIBUTION only in that
  restricted, unclaimed sense.
- Remainder `CERTIFIED` ≠ hop `ZERO`. LEVEL B coefficients +
  remainder UNKNOWN stay hop UNKNOWN
  (`tests/test_forbidden_ignore_remainder_regression` /
  `tests/test_rc_schema.py`).
- Publication status E. Track D2 LOCKED.

## Residual risks

1. **Neighbor coverage is not exhaustive.** Proposer–verifier
   crowding lives in frozen `research/literature/`. Sparse Laurent,
   polygamma Taylor, and C0 routing live in Track V5 literature.
   This pack cites those paths instead of duplicating FunSearch /
   Lean / Gruntz rows in full.
2. **2025–2026 preprints** still block “first certificate / first
   LLM+CAS” slogans even with weaker venue signal.
3. **Arb / Isabelle / Maple `series` / COSY** are not assumed
   available on this host. Lack of a runtime is not novelty.
   Presence of published remainder primitives elsewhere is prior
   work, not a gap we fill.
4. **Other subagents (R1–R11, R13) may later land theorems.**
   This audit must not be reread as evidence that any remainder
   is `CERTIFIED`, that G0016→G0013 is LEVEL_C ZERO, or that
   the GAP cell has been filled.
5. **Two meanings of “certified series.”** Numeric ball enclosures
   of a truncated series at a number, versus a symbolic order
   certificate \(R_{N+1}(t)=O(t^{N+1})\) for a parametric germ.
   Mixing them is a reviewer-kill.
6. **Two meanings of “remainder.”** Lagrange/Cauchy integral
   remainder of a holomorphic Taylor polynomial, versus the
   Track V5 hop field `remainder_verdict` (ZERO/UNKNOWN on an
   atom, composed into LEVEL_C). Mixing them is a reviewer-kill.
7. **Two meanings of “certificate.”** WZ / LEDA / ITP kernels /
   PIT versus this engine’s `RemainderCertificate` under
   `CERTIFICATION_SCOPE.md` (engine semantics, not Lean).
8. **Holonomic confusion.** D-finite tail bounds are real,
   published, and irrelevant to polygamma(\(k,z\)) as a function
   of \(z\).
9. **`M<∞` without a proof.** ASSUMPTION_POLICY class C/D:
   a Cauchy bound that assumes a finite max on a circle without
   proving the circle avoids poles is not `CERTIFIED`.
10. **Silent genericity.** `α₀ ∉ {0,−1,−2,…}` is class C unless
    declared or derived. V5-G already returns UNKNOWN on
    symbolic α. This pack does not license inserting that
    predicate to restore `fb3b929`.
11. **Hop vs remainder vs family.** A later remainder `CERTIFIED`
    still does not unlock D2 and is not hop ZERO.

## Do not

- Edit `research/PROGRAM_STATUS_V5.md` or
  `research/coefficient_laurent/literature/` except by citing
  paths.
- Edit shared remainder-certification files owned by the
  orchestrator.
- Put Guo gold names in proposer-visible files or ZERO rules.
- Treat this documentation as a method result, a hop ZERO, or
  a publication letter.
- Convert timeout, LEVEL_A/B, C0 match, or numeric agreement
  to remainder `CERTIFIED` or hop `ZERO`.
- Restore retracted LEVEL_C ZERO.
- Open Track D2.
- Claim Taylor remainder, Cauchy estimates, or polygamma poles
  as novelty.
- Upgrade the GAP cell to a claimed contribution while the
  generic suite is unrun or while any false `CERTIFIED` exists.
- Call an LLM API.
