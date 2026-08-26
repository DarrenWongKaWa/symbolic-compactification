# Frozen claims (structure-discovery v1)

Frozen: 2026-08-27. At most three claims. Old compactness claims (protocol v0
C1–C3) are **not** reused and are **not** being rescued.

Input: exact expression \(E\) plus declared context \(C\).
Output: typed hypotheses \(H\), constructions \(R(E,H)\), verdicts
ZERO / NONZERO / UNKNOWN. Promotion iff ZERO.

---

## C1 — STRUCTURE DISCOVERY

A dedicated observe→hypothesis architecture proposes higher-level, scientifically
meaningful abstraction *types* (D2–D5) more often than generic CAS simplification
(B1) or direct compactification without a typed hypothesis (B6).

- **Positive prediction:** On gold-backed positive DEV+TEST items, B9 type-hit
  rate exceeds B1 and B6 by a margin that is not explained by tautological
  renaming of the whole expression.
- **Falsification:** B9 type-hit ≤ max(B1, B6) on the frozen test split.
- **Required experiment:** ssc-structure-bench-v0.1, methods B1, B6, B9.
- **Minimum evidence:** held-out test, both polarities, no gold leakage.

## C2 — DECOMPOSED SEARCH

Separating hypothesis discovery from candidate construction improves D3–D5
*type* discovery relative to asking only for a final compact expression.

- **Positive prediction:** B9 D3+ type-hit > B6 D3+ type-hit on positive items
  whose gold type is D3, D4, or D5.
- **Falsification:** no D3+ gap, or the gap is only D2 common-subexpression
  elimination (which CSE/FORM already do).
- **Required experiment:** mandatory DIRECT vs DECOMPOSED ablation.
- **Minimum evidence:** per-level table, not an aggregate win somewhere.

## C3 — VERIFIED UTILITY OF AGGRESSION

Exact fail-closed verification lets the discoverer propose aggressive
(possibly false) structure without those false merges becoming scientific state.

- **Positive prediction:** forbidden reconstructions on negative items are
  never ZERO; false_promotion = 0.
- **Falsification:** any ZERO on a forbidden reconstruction, or UNKNOWN treated
  as success.
- **Required experiment:** negative pole-merge, broken-orbit, invalid
  Piecewise, independent-function items.
- **Minimum evidence:** zero unsafe merges on DEV and held-out TEST.

D6 physicist utility is **not** a frozen claim (no human annotations).
