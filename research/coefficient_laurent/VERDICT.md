# Final Scientific Verdict — Coefficient-Space Laurent Verification

## 1. Was G0016->G0013 decided?

**No.** Rescore: UNKNOWN (LEVEL_A, 40 s process timeout). Direct sparse
accumulation: negatives vanish; constant term not proven equal. Case **L-D**.

## 2. What was its exact Laurent pole order?

Denominator of the together'd diagnostic has **t^1**. After expand,
`C_{-6}`…`C_{-2}` are 0; `C_{-1}` is 93 ops and **expand==0**. Apparent
order-1 removable pole.

## 3. Which negative coefficients vanished?

`t^{-6}` through `t^{-1}` all expand to 0 on the m→n hop
(`G0016→G0013` / `G0023→G0020`).

## 4. Did the constant term match G0013?

Not by exact expand/cancel. `C_0` 990 ops vs target 327. Numeric
agreement ~1e-27 at one regular point is **not** ZERO.

## 5. Was a full `together()` avoided?

**Yes.** `used_full_together=False`. Per-atom series + sparse `coeff(t,p)`
sums. V4's 27327-op together was not built.

## 6. Maximum intermediate op count?

m→n analog: **1696** (G0023→G0020). Ell-hops: ~9770–10114 (still UNKNOWN).

## 7. Runtime vs whole-kernel methods?

Sparse m→n: ~7–40 s. Whole-kernel together: size-guard 27k. Whole-kernel
series: 30–90 s timeout.

## 8. What happened on G0016->G0014/G0015?

UNKNOWN LEVEL_A; negative coeffs not certified; larger cores.

## 9. How many frozen UNKNOWN edges became ZERO/NONZERO?

**0 ZERO, 0 NONZERO.** LEVEL B on two analog m→n hops is not edge ZERO.

## 10. Did any path become PATH_ZERO?

No new covering two-step PATH_ZERO (generic hop still UNKNOWN).
V4 diagonal→triple one-step PATH_ZERO unchanged.

## 11. Did any family become FAMILY_ZERO/NONZERO?

**No.** 7/7 FAMILY_UNKNOWN.

## 12. Was Track D2 unlocked?

**No.**

## 13. Exact V_GAIN vs no-gain accounting

No new **edge ZERO** V_GAIN. **Partial:** negatives of the generic→diagonal
m→n hop are exactly 0 without 27k together (LEVEL B, not LEVEL C).
Not D_GAIN. Not family V_GAIN.

## 14. False ZERO audit

false ZERO = 0 on generic suite. Unbounded `cancel` on 1317-op `C_0-target`
was **rejected** (cap 400). Cache regression tests pass (17).

## 15. Cache/provenance audit

V4 alias of G0014→G0012 onto G0016→G0013 cannot occur: keys include full
text hashes + method version + atom hash. Extra attacks in
`tests/test_cl_cache_audit.py`.

## 16. Strongest positive result

Sparse Laurent shows **all negative powers vanish** for generic→diagonal
m→n without combining the kernel.

## 17. Strongest counterexample

`C_0` numerically matches G0013 but exact expand does not; LEVEL C refused.
t^0-only would have been a false ZERO if negatives were skipped — falsifier
rule kept.

## 18. Remaining verification bottleneck

**Constant-term algebraic identity** (`C_0` vs 327-op diagonal), not
atom series and not together-size. Classification: coefficient
simplification / latent cancellation basis.

## 19. Publication decision

**E.** Optional F for “LEVEL C on G0016→G0013 with this cascade.”
Scoped strategy did not decide the hop. No paper directory.

## 20. Exact commits/tags/artifacts

| | |
|---|---|
| V4 close | `248d247` |
| V5 freeze | `7102e8a` |
| Freeze sha256 | `3d6a5bf2ba327b8b8b3f91609f185494ade3b0eeec303175ab7df98c014d16fc` |
| Case | L-D |
| D2 | LOCKED |
