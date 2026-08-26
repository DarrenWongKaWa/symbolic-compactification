# Falsification conditions

Freeze date: 2026-08-26. Do not edit thresholds after seeing test results.
If a condition fires, write it in `research/STATUS.md` and stop optimizing
around the result.

Statistical procedures and n are in `EXPERIMENT_FREEZE.md`.

## C1 is falsified if

Any of the following holds on the frozen **test** split:

1. **Indistinguishable false-promotion.** The two-sided 95% interval on
   (false-promotion rate of B7 minus that of B4) contains 0, **and** the
   same holds versus B5, on the union of Tier A corruptions and Tier C
   labeled non-identities.
2. **B4/B5 safer and as complete.** B4 or B5 has false-promotion rate
   ≤ B7 **and** certified-success rate ≥ B7 on Tier A identities.
3. **UNKNOWN laundering.** Any condition converts UNKNOWN or numeric
   agreement into success; if that happens in code, C1 is invalid until
   the bug is fixed and the run is repeated. This is a protocol failure,
   not a scientific win.

C1 can still be **directionally supported** on Tier A and fail on Tier C.
Report both; do not pool into one headline if they disagree.

## C2 is falsified if

Any of the following holds under matched budgets on frozen **test**
Tier B ∪ Tier C:

1. **CAS dominates certified compactness.** For the majority of items,
   B1 (or B2 if available) produces a certified form with weakly better
   compactness vector than B7 **and** weakly higher certified ladder
   level where a ladder exists.
2. **Only syntactic wins.** B7 reduces `count_ops` or character length
   but does not reduce sums, Piecewise branches, or repeated kernels,
   and human-ladder level does not increase — i.e. "shorter soup", not
   scientific compactification.
3. **Uncertified CAS counted as our loss incorrectly inverted.** If the
   only way C2 "wins" is by declaring every uncertified CAS form a CAS
   failure while also refusing to compare the CAS form's structure, that
   is metric gaming. Pre-registered comparison: compactness is reported
   for (a) certified outputs only, and (b) a dashed "claimed but
   uncertified" series that is **not** used to accept C2.

Existing Guo probe is already a **threat** to C2, not a pass.

## C3 is falsified if

1. Gains on C1/C2 appear for only **one** model family, and the other
   available model(s) show intervals covering zero.
2. Gains appear only on Guo \(\sigma_{abc}\) and vanish on the other
   Tier C families and on Tier B.
3. Test-set prompt or budget was changed after seeing test numbers
   (automatic falsification of C3 by protocol breach).

If only two models are technically available, C3 may be reported as
**inconclusive**, not as confirmed. Inconclusive ≠ confirmed.

## Global stop conditions

- Core mechanism already beaten by B1/B4 on the pre-registered primary
  metrics (idea-evaluator data-refuted rule): stop, verdict C or D.
- Hidden human references leaked into proposer context: invalidate
  affected runs; do not replace them with lucky seeds.
- Benchmark test files mutated after freeze without a new version id:
  all later numbers are non-reportable.
