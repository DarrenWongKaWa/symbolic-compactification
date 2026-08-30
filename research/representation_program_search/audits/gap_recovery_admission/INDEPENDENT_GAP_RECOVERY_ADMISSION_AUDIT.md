# Independent gap-recovery admission audit

## Verdict

**ADMISSION_READY — DEV R2 calibration only.**

The repaired package passes the source, public-boundary, M1, exact-proof,
depth, primitive-control, and duplicate gates. It is not a new scientific
identity, search success, AI result, or R3+ result.

## Primary source

The audit independently downloaded arXiv `1612.02417v1`. The archive SHA-256
is `698a6b496e375aa6a31e0b4750dbe59a438f69bd205a807dca8913269b8a1d4a` and `CM_dynSys.tex` SHA-256 is
`59ad6a8047c13cd4a8dd1f7c595194f5734aa5049a0949828b23c55ccbcacbc3`. All six stored excerpts compare byte-for-byte with the
claimed upstream line ranges. Official metadata agrees between
[arXiv](https://arxiv.org/abs/1612.02417) and
[SIAM](https://epubs.siam.org/doi/10.1137/16M110719X).

The four retained identities are unnumbered lines 705--708. The later
`R3B_RHS` numbered environment starts after them; the predecessor's “Eq. 28”
name was inaccurate and is not repeated in the repaired public boundary.

## Public boundary and assumptions

`load_public_case()` reads exactly the proposer view, assumptions, catalog,
symbols, and four member files. It returns eight hash-bound real symbols and
the exact statuses `DECLARED, DECLARED, DECLARED, DERIVED`. Case/member IDs are
opaque. No source identity, target representation, operator name or sequence,
reference program, node role, or receipt is public.

The factorized formulas make the intended structure comparatively easy. P9A4
also uses the generic phrase “node difference”; this is recorded as an
easiness risk, not target leakage, because it identifies neither the paired
expressions' roles nor a target operator. This wording must not be cited as
evidence of search difficulty.

## Program and proof

M1 loads with no schema deltas. `G_FULL`, `G_NO_HERMITE`, and `G_PRIMITIVE`
all have canonical program hashes, compile non-tautologically, and produce four
obligations. All 12 stored sessions bind exact current/candidate hashes and
record `HYPOTHESIS -> ZERO/CERTIFIED/PROVEN`; independent replay returns 12
more exact ZERO verdicts.

The independent depth is `R2_NEWTON_DD`: one shared
`1/sqrt(z)` latent, four explicit two-node evaluations, and exact linear
reconstruction. The primitive control uses only `VALUE` and
`LINEAR_COMBINATION`, so the named `NEWTON_DD` primitive is not required.

## Duplicate disposition

The only exact current-package matches are the four predecessor member files;
there are no additional alpha-renamed matches. The predecessor tree remains
unchanged at `0943a6ae269d81af89daf96202303e183d7c75f8383a959f67c149501b04fdc0` (33
files).

These copies do not create a second case. They are a versioned package repair
of one identity newly mined in this experiment. The predecessor failed
admission and appears in no DEV/TEST manifest or method-run artifact. Admit at
most the repaired package and permanently alias/exclude the predecessor. Never
report the repair as a new mining success.

## Scope and limitations

- Admission is limited to DEV R2 calibration.
- The visible factorization can make the task easy.
- This does not bear on held-out generalization or the R3+ frontier.
- It is not AI, grammar, verifier-feedback, or search evidence until a frozen
  method run evaluates it.
- The audit used AI-assisted research tooling; all admission gates are backed
  by deterministic artifacts or exact source hashes.
