# Final Scientific Verdict — Iterated Confluence Certification

## 1. Could five-branch Guo kernels be decomposed into one-parameter paths?

**Yes, as graphs.** Every frozen 5-branch family has three two-step covering
paths generic → diagonal → triple coincidence, plus the six one-step covering
edges, using only source `G####` members. Two-parameter star edges are
rejected as not one-parameter. No invented intermediates (I-E does not hold).

**No, as certificates.** Those edges stay UNKNOWN.

## 2. What op-count reduction was achieved?

Exact mul-args AppliedUndef peel (`h1*h2*h3` on 5-branch, `h1*h2` on
2-member), reconstruction `S*K = E`:

| class | full ops | local ops | vs 176 |
|---|---:|---:|---:|
| 2-member generic | 176 | 172 | 0.98 |
| 5-branch diagonal | 333 | 327 | 1.86 |
| 5-branch generic | 573 | 567 | 3.22 |
| 5-branch triple | 33 | 27 | 0.15 |

Spectator peel does **not** bring 5-branch kernels to the certified
two-member scale. Cancel-expansion peel (Track V) was rejected here
because it increased ops (176 → 1355).

## 3. How many local edges became ZERO/NONZERO/UNKNOWN?

Across the 7 families' unique covering edges:

- ZERO: **2** (s2-i4 G0005→G0004 and G0009→G0008, series, ~13 s)
- NONZERO: **0**
- UNKNOWN: all 5-branch one-parameter hops (timeout at 25 s; the 327-op
  hop also timed out at 90 s) plus s2-i4 substitution

## 4. Did order of limits commute where required?

**Not decided on Guo 5-branch.** No PATH_ZERO covering path, so
consistency is UNKNOWN. Toys: cubic commute CONSISTENT_ZERO;
`x/(x+y)` INCONSISTENT_NONZERO. Order-dependent families are never
FAMILY_ZERO (schema + falsifier).

## 5. Did any frozen family become FAMILY_ZERO?

**No.**

## 6. Did any become FAMILY_NONZERO?

**No.**

## 7. What exact obligations remained UNKNOWN?

One-parameter confluence `lim_{ε(a)→ε(b)} K_src = K_tgt` on 327–567-op
polygamma kernels after h1 peel. Substitution `b↔c` on s2-i4. Hermite
recurrence still not instantiated (no explicit F).

## 8. Was the bottleneck local symbolic complexity or multiparameter consistency?

**Local symbolic complexity (I-D).** Not I-C.

## 9. Did this produce new V_GAIN?

**No family-level V_GAIN.** The two ZERO edges reuse Track V two-member
certificates with a non-expanding peel. PATH_ZERO ≠ FAMILY_ZERO remains
enforced (s2-i4: 2 PATH_ZERO one-step paths + UNKNOWN substitution →
FAMILY_UNKNOWN).

## 10. Was Track D2 unlocked?

**No.**

## 11. If unlocked, what did new discovery experiments show?

Not run.

## 12. What remains of the Guo G1→G3 gap?

G1 (two-member local confluence) still the only certified scientific-scale
relation. G3 (Hermite / 5-branch family) unverified. Iterated 1-parameter
decomposition does not close G3 with this cascade.

## 13. Strongest positive result

Sound family composition: PATH_ZERO is not FAMILY_ZERO; order-dependent
toys FAMILY_NONZERO; false FAMILY_ZERO = 0; 176-op Guo pairs still ZERO
after mul-args peel + series.

## 14. Strongest counterexample

Frozen 5-branch hops, including the “small” diagonal→triple 333-op edge
designed to match the 176-op pattern, timeout as UNKNOWN at 25 s and 90 s.

## 15. False-promotion audit

false FAMILY_ZERO = 0 (generic suite + falsifier 10 cases).

## 16. Claims supported

- Five-branch source lattices admit one-parameter covering paths.
- Iterated limit ≠ joint limit unless consistency is certified.
- Majority PATH_ZERO is not FAMILY_ZERO.
- Spectator peel without expansion is exact on these Guo Muls.

## 17. Claims falsified

“Decomposing 573-op 5-branch obligations into iterated one-parameter
edges comparable to the certified 176-op case will decide FAMILY_ZERO
or FAMILY_NONZERO with the Track V cascade.” Local ops stay ~327–567;
series times out.

## 18. Publication decision

**E** — promising on toys and composition rules; scientific-scale 5-branch
certificates do not exist. No paper directory.

## 19. Exact commits / tags / artifacts

| | |
|---|---|
| Track V close | `38d6d4a` |
| V2 freeze | `4dee916` |
| V2 close | `fe53ebc` |
| V3 freeze | `dcfb90c` |
| V3 inputs sha256 | `e1fc6df85b0d293f3251ec87c1827409f402c01752a73251be8899f5b00c41db` |
| Tag intent | `iterated-confluence-verifier-v1` |

## 20. Recommended next scientific question

Not a new Hermite proposer. Not a longer series timeout.

> Can a *generic* polygamma / repeated-argument local identity engine
> decide the 327-op diagonal-to-triple hop without Guo-specific tables?

Until that exists, **do not** test a new Hermite proposer on Guo.
**STOP_VERIFICATION_LINE** for iterated-path V3 increments.
See `CAPABILITY_BOUNDARY.md`.
