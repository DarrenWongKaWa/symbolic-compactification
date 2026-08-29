# Final Scientific Verdict — Symbolic Remainder Certification

Independent line, not Track V6. Parent V5 fail-close `84b412d`.
Retracted LEVEL_C ZERO is not restored. Track D2 LOCKED.

## 1. What theorem/certificate was implemented?

Holomorphic Taylor remainder on an affine path (R1 T7 / Ahlfors–Cauchy):
if `f` is holomorphic on `|z-z0|<ρ` and `|c|δ<ρ`, then

```
f(z0+c t) = Σ_{r=0}^N f^{(r)}(z0)(c t)^r/r! + O(t^{N+1})
```

plus Cauchy order bound on a **certified** disk (R4), polygamma pole-set
predicates (R2 / DLMF 5.15), neighborhood existence (R3), typed `O(t^k)`
algebra (R5), polygamma derivative chain (R6), exact affine normalizer
(R7), atom-local `RemainderCertificate` compiler (R8).

Taylor’s theorem is standard mathematics, not novelty.

## 2. What assumptions are required?

Class A/B only for `CERTIFIED`. For polygamma of order `k>=-1`, a
pole-free germ needs a declared or derived `z0 ∉ {0,-1,-2,…}` or
`Im(z0)` identically nonzero or a certified positive distance to that
set. Undeclared genericity is class C → `ASSUMPTION_REQUIRED`.

## 3. Can symbolic affine polygamma arguments be certified analytic?

Only with a **declared** pole-exclusion (or equivalent A/B). Without it:
`ASSUMPTION_REQUIRED`. Motivating form
`1/2 + β(γ ± i(μ-ε))/(2π)` is not identically a pole, but `Im(z0)` is
not identically nonzero under `real=True` symbols alone.

## 4. Can a pole-free neighborhood be proven?

Yes when `dist(z0,P)>0` or the pole set is empty (`exp`). Explicit
sufficient `δ = ρ/(2(|c|+1))`. Symbolic polygamma `z0` without
exclusion: no.

## 5. Can O(t^{N+1}) remainder be certified?

Yes on a certified disk (Cauchy / T7). Prefactor: `t^{-m} O(t^{N+1})`
vanishes through `t^0` iff `N+1-m >= 1`.

## 6. What fraction of generic tests pass?

Generic suite 12/12 with expected labels. Package tests 307 passed
before suite write; plus generic/engine regressions.

## 7. False remainder certificates?

**0.** Falsifier `false_certified_count()=0`. Generic `false_CERTIFIED=0`.

## 8. What happens on the 14 frozen G0016 atoms?

All 14: affine-normalizable; **ASSUMPTION_REQUIRED** (symbolic thermal
`z0`, missing `z0 not in Z_<=0`). 0 CERTIFIED, 0 NONANALYTIC.
Certificates are not reused across distinct `(z0,c)` without hashing;
identical `(z0,c)` share a domain query.

## 9. Does G0016→G0013 become LEVEL_C ZERO?

**No.** Even one required remainder UNKNOWN/ASSUMPTION_REQUIRED blocks
LEVEL C. Hop remains UNKNOWN LEVEL_B. Retracted ZERO is not restored.
Ell-hops were not rerun.

## 10. Is any additional assumption required?

**Yes (HUMAN_REQUIRED / class C):**

```
z0 not in {0, -1, -2, …}
```

or a stronger sufficient A/B condition (`Im(z0)` identically nonzero).
Declaring pole-exclusion certifies the motivating form (R2 live). It is
**not** in the frozen problem and is **not** inserted.

## 11. Was an external rigorous backend superior?

**No.** R13: CONTINUE_CUSTOM, not CASE R-E. Arb/flint not importable;
holonomic tools reject Γ/polygamma; SymPy `series` is not a bound;
V5 `remainder_ok` is a fail-closed gate only.

## 12. What happens to frozen family verdicts?

Unchanged: 7/7 FAMILY_UNKNOWN. Graph topology not edited.

## 13. Is Track D2 unlocked?

**No.**

## 14. What exact V_GAIN occurred?

**None on hops.** Method V_GAIN is a generic remainder certificate
with assumption classes; it does not change frozen Guo hop ZERO count.

## 15. Strongest positive example

`exp(z0+c t)` CERTIFIED (entire). `polygamma(k,1+c t)` domain CERTIFIED.
`polygamma(k,a+c t)` CERTIFIED **iff** pole-exclusion is declared.
`t^{-2} O(t^{4})` vanishes through `t^0`.

## 16. Strongest counterexample

Symbolic `α₀` with only `real=True`: `ASSUMPTION_REQUIRED`.
`z0=0`: NONANALYTIC. `t^{-3} O(t^{3})=O(1)` does not vanish.
LEVEL B coefficients + remainder UNKNOWN ≠ hop ZERO
(`test_forbidden_ignore_remainder_regression`).

## 17. What did independent reviewers find?

This close is CASE R-B: no LEVEL_C promotion, so the §18 LEVEL_C
review cluster was not launched. R1–R13 packages were isolated.
R2/R10: no silent genericity. R13: no backend pivot.

## 18. Publication decision

**E.** Generic remainder certificates exist; scientific-scale
polygamma affine arguments need an explicit domain assumption not
present in the frozen problem. No paper directory.

## 19. Exact commits/tags/artifacts

Contracts `9da52fb`. IR `adbfd9f`. R1–R13 merges on
`research/symbolic-remainder-certification-v1`.
Artifacts: `GENERIC_SUITE.json`, `MOTIVATING_CLASS.json`,
`FROZEN_G0016_ATOMS.json`. Case **R-B**. D2 LOCKED.

## 20. Recommended next scientific question

Should pole-exclusion `z0 ∉ Z_<=0` be **declared** from the thermal
field-theory source (class A), or must the verifier remain
`ASSUMPTION_REQUIRED` until a derived identity proves `Im(z0)≠0`?
Do not insert it silently. Do not recurse into Remainder V2 without
that scientific decision.
