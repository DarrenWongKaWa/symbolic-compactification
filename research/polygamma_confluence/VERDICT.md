# Final Scientific Verdict — Polygamma Local Confluence (Track V4)

## 1. Could five-branch Guo kernels be decomposed into one-parameter paths?

Yes (V3). V4 certifies the **second** hop of those paths.

## 2. What op-count reduction was achieved?

Not spectator peel (still 327 vs 176). The reduction is **term count**:
12 polygamma atoms of 13–51 ops instead of one 327-op series.

## 3. How many local edges became ZERO/NONZERO/UNKNOWN?

ZERO **20**, NONZERO **0**, UNKNOWN **18** (generic→diagonal, after
correct text-hash cache).

Diagonal→triple: **all ZERO**. Generic→diagonal: **all UNKNOWN**.

## 4. Did order of limits commute where required?

Not decided. Covering two-step paths are PATH_UNKNOWN. No
auto-CONSISTENT_ZERO (R2).

## 5. Did any frozen family become FAMILY_ZERO?

**No.**

## 6. Did any become FAMILY_NONZERO?

**No.**

## 7. What exact obligations remained UNKNOWN?

`G0016→G0013/G0014/G0015` and `G0023→G0020/G0021/G0022`: together/series
of the 14-atom generic kernel (ops 27k or timeout).

## 8. Was the bottleneck local symbolic complexity or multiparameter consistency?

**Local complexity on the generic (567-op) hop.** The 327-op diagonal hop
is no longer the bottleneck.

## 9. Did this produce new V_GAIN?

**Yes, edge-level V_GAIN.** V3's 327-op UNKNOWN is ZERO by atom-series.
Not family-level V_GAIN. Not D_GAIN.

## 10. Was Track D2 unlocked?

**No** (J-C).

## 11. If unlocked, what did new discovery experiments show?

Not run.

## 12. What remains of the Guo G1→G3 gap?

G1 two-member still ZERO. G1.5: diagonal→triple 5-branch hops ZERO.
G3 family still UNKNOWN (generic hop + consistency + no explicit F).

## 13. Strongest positive result

Per-atom series + Laurent `t^0` certifies `G0013/G0014/G0015 → G0012`
in seconds (`c0` 47 ops, `expand(c0-K12)==0`).

## 14. Strongest counterexample

Cache keyed on missing `text_sha256` reused G0014 certificates for
G0016 (would have been a false ZERO). Fixed before close. Generic hops
remain UNKNOWN, not silently ZERO.

## 15. False-promotion audit

Engine tests: wrong polygamma order is not ZERO. Cache bug caught.
false FAMILY_ZERO = 0 (families still UNKNOWN).

## 16. Claims supported

Compositional series of small polygamma atoms decides 327-op confluence
that whole-kernel series timed out on.

## 17. Claims falsified

“Atom-series immediately decides the full 5-branch family.” Generic
567-op hops still UNKNOWN; FAMILY_ZERO not reached.

## 18. Publication decision

**E.** Stronger evidence than V3, still not a family certificate.

## 19. Exact commits / tags / artifacts

V3 close `d2752f9`. V4 freeze `FROZEN_INPUTS_V4.json` n=7. Case **J-C**.

## 20. Recommended next scientific question

Can the **generic→diagonal** 14-atom kernel (G0016→G0013) be certified
by a Laurent comparison that does not `together` 27k ops — still without
Guo identities? Until FAMILY_ZERO or FAMILY_NONZERO, do not test a
Hermite proposer on Guo.
