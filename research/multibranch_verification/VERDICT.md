# Final Scientific Verdict — Multi-Branch Verified Representation Discovery

## 1. Could five-branch confluence be compositionally certified?

**Not on frozen Guo.** Toy cubics: yes (FAMILY_ZERO, false FAMILY_ZERO=0).
Guo 5-branch families: **FAMILY_UNKNOWN** (7/7).

## 2. How many frozen Guo UNKNOWNs became ZERO/NONZERO?

Family level: **0 FAMILY_ZERO, 0 FAMILY_NONZERO**.
Edge level: the mixed 4-member family has **2 ZERO** one-parameter edges
(already known 2-member V_GAIN) and 1 UNKNOWN substitution edge.

## 3. Did Hermite recurrence close the family?

**No.** Frozen hyps have no explicit polynomial F; recurrence is UNKNOWN.
Typed `hermite_divided_difference` families remain FAMILY_UNKNOWN.

## 4. What remained verifier-bound?

5-branch generic kernels (ops ~573) and repeated-node multi-parameter
limits. Not shown NONZERO.

## 5. Was Track D2 unlocked?

**No (CASE H-C).**

## 6. If unlocked, could DeepSeek discover HERMITE_OK?

Not run.

## 7. Could it discover MASTER_OK?

Not run.

## 8. Did SOL help or anchor?

Unchanged. SOL not retuned.

## 9. Did specialist proposers help?

Not run.

## 10. What did frozen symbolic baselines achieve?

Unchanged from `91a401b`.

## 11. What were AI_UNIQUE_SUCCESS cases?

Unchanged polygamma Newton. No new family-level unique success.

## 12. What happened on Guo?

G1 two-member confluence still the only certified scientific-scale
relation. 5-branch claims are connected graphs with UNKNOWN required
edges.

## 13. What highest G-level was reached?

**G1.** Not G3.

## 14. Which gains were D/G/C/V?

No D_GAIN. No family-level V_GAIN. Edge-level ZERO on s2-i4 reuses Track V
two-member V_GAIN, not a new family certificate.

## 15. Which results replicated across seeds?

All four 5-branch star families (s0 i3, s1 i2/i3, s2 i2/i3, s4 i1)
FAMILY_UNKNOWN.

## 16. Which generalized to held-out TEST?

No new TEST LLM. Toy FAMILY_ZERO is generic cubic, not Guo.

## 17. Strongest positive result

Composition rule soundness: 4 ZERO + 1 UNKNOWN ≠ FAMILY_ZERO; corrupted
cubic family FAMILY_NONZERO; toy 5-branch Hermite FAMILY_ZERO.

## 18. Strongest counterexample

Frozen Guo 5-branch `local_confluence` / Hermite-typed families stay
FAMILY_UNKNOWN. Naming Hermite + listing five G#### ids is not a family
certificate.

## 19. Which claims survived?

FAMILY_ZERO is not majority vote. Two-member confluence remains ZERO.
False FAMILY_ZERO = 0 on toys.

## 20. Which claims were falsified?

“Star of one-parameter limits plus Hermite recurrence would certify Guo
5-branch families in this scoped engine.” They remain UNKNOWN.

## 21. Publication decision

**E.** Track D2 locked. No paper directory.

## 22. Exact commits / tags / hashes

| | |
|---|---|
| Track V close | `38d6d4a` |
| V2 freeze | `4dee916` |
| V2 inputs | `FROZEN_INPUTS_V2.json` n=7 |
| Tag intent | `multibranch-hermite-verifier-v1` |

## 23. Next scientific question

Can a **single-parameter slice** of a 5-branch kernel (ops after spectator
split comparable to the 176-op 2-member case) be certified without
skipping on size, and can multi-parameter repeated-node limits be reduced
to iterated one-parameter ZERO edges — still without Guo-specific algebra?
