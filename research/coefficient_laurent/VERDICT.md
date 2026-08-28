# Final Scientific Verdict — Coefficient-Space Laurent Verification

## 1. Was G0016->G0013 decided?

**Yes. ZERO (LEVEL C).** Negatives vanish; C0 matches G0013 by per-polygamma
rational coefficients. Runtime ~11 s direct, max intermediate ops 1696.

## 2. What was its exact Laurent pole order?

Order-1 removable pole. `C_{-6}`…`C_{-2}` = 0; `C_{-1}` expands to 0.

## 3. Which negative coefficients vanished?

All `t^{-6}` through `t^{-1}` on the m→n hop.

## 4. Did the constant term match G0013?

**Yes, exactly**, after grouping 12 shared polygamma keys and proving each
rational coeff difference has together-numerator 0. Not via 27k together.

## 5. Was a full `together()` avoided?

**Yes.** Per-atom series + sparse coeff sums + per-polygamma together only
(coeff-pair ops ≲ 2000, not 27327).

## 6. Maximum intermediate op count?

**1696** on the certified m→n hop.

## 7. Runtime vs whole-kernel methods?

Sparse LEVEL C: ~11 s. Whole together: size-guard 27k. Whole series: 30–90 s timeout.

## 8. What happened on G0016->G0014/G0015?

UNKNOWN (40 s process timeout). Algorithm not retuned.

## 9. How many frozen UNKNOWN edges became ZERO/NONZERO?

**6 ZERO, 0 NONZERO, 12 remain UNKNOWN.**

## 10. Did any path become PATH_ZERO?

The covering path `G0016→G0013→G0012` is PATH_ZERO (V5 hop + V4 diagonal hop).
Sibling covering paths that need ell-hops stay PATH_UNKNOWN.

## 11. Did any family become FAMILY_ZERO/NONZERO?

**No.** Consistency not auto-certified; ell-hops UNKNOWN.

## 12. Was Track D2 unlocked?

**No.**

## 13. Exact V_GAIN vs no-gain accounting

**Edge V_GAIN (LEVEL C)** on G0016→G0013 and five cached copies / second-sum analog.
Not family V_GAIN. Not D_GAIN.

## 14. False ZERO audit

false ZERO = 0 on generic suite. Unbounded cancel of the 1317-op blob still forbidden.
Per-atom together of coeff diffs is scoped and reconstruction-gated by grouping keys.

## 15. Cache/provenance audit

Full text hashes in keys. 17 cache tests. G0014 cannot alias G0016.

## 16. Strongest positive result

Generic→diagonal **m→n** confluence is LEVEL C ZERO without combining the kernel.

## 17. Strongest counterexample

Ell-hops still timeout. Full-blob expand of C0−G0013 is not 0; only atom grouping proves it.
Numeric agreement alone was never ZERO.

## 18. Remaining verification bottleneck

G0016→G0014/G0015 (ell degeneration) runtime; then path-independence for FAMILY_ZERO.

## 19. Publication decision

**E.** Edge-level method evidence is stronger; family certificate still missing.

## 20. Exact commits/tags/artifacts

V5 freeze `7102e8a`. Close update on `research/coefficient-space-laurent-v1`.
Case **L-A**. D2 LOCKED.
