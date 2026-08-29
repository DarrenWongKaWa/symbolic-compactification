# Final Scientific Verdict — Coefficient-Space Laurent Verification

Independent reviews R1–R6 at `fb3b929`. Coordinator remainder
fail-close after R2/R4. Ell-hops not retuned. D2 locked.

## 1. Was G0016->G0013 decided?

**No hop ZERO.** After remainder fail-close the hop is **UNKNOWN
LEVEL_B**. Negatives vanish. C0 matches G0013 by per-polygamma
rational coefficients (`pg_atoms`). Remainder is UNKNOWN:
`remainder_ok` is False on 14/14 atoms (symbolic α). Runtime ~2 s
on the m→n hop, max intermediate ops 1696.

The `fb3b929` LEVEL_C ZERO is retracted. It hardcoded remainder
ZERO (falsifier trap `forbidden_ignore_remainder`).

## 2. What was its exact Laurent pole order?

Order-1 removable pole of the extracted window. `C_{-6}`…`C_{-2}`
= 0; `C_{-1}` expands to 0. This is the negative-coefficient lemma,
not a remainder certificate that extra polygamma poles cannot sit
below `PMIN`.

## 3. Which negative coefficients vanished?

All `t^{-6}` through `t^{-1}` on the m→n hop (live rerun after
the patch).

## 4. Did the constant term match G0013?

**Yes, exactly**, after grouping 12 shared polygamma keys and proving
each rational coeff difference has together-numerator 0. Not via 27k
together. This is **not** hop ZERO: schema LEVEL C also requires
remainder ZERO.

## 5. Was a full `together()` avoided?

**Yes.** Per-atom series + sparse coeff sums + per-polygamma together
only (coeff-pair ops ≲ 2000, not 27327). `used_full_together=False`.

## 6. Maximum intermediate op count?

**1696** on the m→n hop (unchanged after remainder fail-close).

## 7. Runtime vs whole-kernel methods?

Sparse m→n: ~2 s. Whole together: size-guard 27k. Whole series:
30–90 s timeout. Ell-hops: 40 s process timeout (not rerun).

## 8. What happened on G0016->G0014/G0015?

UNKNOWN (40 s process timeout). Algorithm not retuned.

## 9. How many frozen UNKNOWN edges became ZERO/NONZERO?

**0 ZERO, 0 NONZERO, 18 UNKNOWN** after remainder fail-close.
Six m→n hops carry a C0 lemma (c0=ZERO) with remainder UNKNOWN.
Twelve ell-hops remain timeout UNKNOWN.

## 10. Did any path become PATH_ZERO?

No covering path is PATH_ZERO after the hop retraction. V4
diagonal→triple edges remain ZERO; the generic→diagonal step is
UNKNOWN.

## 11. Did any family become FAMILY_ZERO/NONZERO?

**No.** Consistency is never auto-CONSISTENT_ZERO. Reconstruction
is not hardcoded ZERO (R4). 7/7 FAMILY_UNKNOWN.

## 12. Was Track D2 unlocked?

**No.**

## 13. Exact V_GAIN vs no-gain accounting

**No hop V_GAIN and no family V_GAIN.** C0 per-polygamma matching
on G0016→G0013 is a non-hop lemma (exact rational identity of 12
keys) and must not be billed as LEVEL C ZERO. Not D_GAIN.

## 14. False ZERO audit

false ZERO = 0 on generic suite and falsifier. Unbounded cancel of
the 1317-op blob still forbidden. Per-atom together of coeff diffs
is scoped. Engine remainder no longer ignores `remainder_ok`.

## 15. Cache/provenance audit

Full text hashes in keys. G0014 cannot alias G0016. Timeout payload
now carries UNKNOWN neg/c0/remainder fields (JSON `provenance` kept
on live timeouts; committed ell rows were not rerun).

## 16. Strongest positive result

Generic→diagonal **m→n** C0 matches G0013 without combining the
kernel. Negatives in `t^{-6}…t^{-1}` vanish. Remainder is not
certified for symbolic thermal arguments.

## 17. Strongest counterexample

LEVEL C cannot be minted by skipping remainder (R2 live toy `f+u`
vs `f` was the hole). Frozen Guo α is symbolic, so `remainder_ok`
refuses. Ell-hops still timeout. Numeric agreement was never ZERO.

## 18. Remaining verification bottleneck

(1) Remainder certificate for affine polygamma arguments with
symbolic α that are not identically nonpositive integers — without
a kernel-specific identity. (2) Ell-hops G0016→G0014/G0015 runtime.
(3) Path independence for FAMILY_ZERO.

## 19. Publication decision

**E.** C0 routing evidence is stronger than V4 on this hop class;
LEVEL C and family certificates are missing. No paper directory.

## 20. Exact commits/tags/artifacts

V5 freeze `7102e8a`. First close L-D `ba2a0ce`. Unsound L-A
`fb3b929`. Reviews `work/v5-review-r1`…`r6`. Remainder fail-close
and rescore on `research/coefficient-space-laurent-v1`. Tag
`coefficient-space-laurent-v1` still points at `ba2a0ce` (not moved).
Case **L-D**. D2 LOCKED.
