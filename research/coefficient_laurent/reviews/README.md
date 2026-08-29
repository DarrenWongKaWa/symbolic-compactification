# Track V5 independent reviews

Reviewers did not communicate before filing.

| id | role | file | commit |
|---|---|---|---|
| R1 | symbolic algebra | `R1_ALGEBRA.md` | `a51f768` |
| R2 | complex analysis / asymptotics | `R2_ANALYSIS.md` | `7b43572` |
| R3 | special functions | `R3_SPECIAL_FUNCTIONS.md` | `4818037` |
| R4 | PL / verification / cache | `R4_VERIFICATION.md` | `e27d2d3` |
| R5 | theoretical physics | `R5_PHYSICS.md` | `966593c` |
| R6 | reproducibility | `R6_REPRO.md` | `b745dc6` |

Coordinator patches after reviews (not retuning ell-hops, not unlocking D2):

1. **R2/R4 remainder:** `sparse_laurent_limit` must call `remainder_ok`.
   Hardcoded remainder ZERO is the falsifier trap `forbidden_ignore_remainder`.
   Live G0016 atoms: 14/14 `remainder_ok` False (symbolic α). After the
   patch, six m→n hops are LEVEL_B UNKNOWN (neg ZERO, C0 ZERO, rem UNKNOWN).
   Case **L-D**. The `fb3b929` LEVEL_C ZERO is retracted.
2. **R4 family compose:** do not hardcode `reconstruction_verdicts=["ZERO"]`;
   always inject `CONSISTENCY_UNKNOWN` and require path independence.
   Frozen families stay FAMILY_UNKNOWN.
3. **R4 timeout payload:** UNKNOWN neg/c0/remainder on live timeouts
   (committed ell-hops were not rerun).
4. **R1 hash hygiene:** atom_decomposition_hash is srepr of pref+terms,
   not an ops-count join. Rescore keys remain full-text SHA256.
5. **R3/R5/R6 docs:** literature GAP restored to “not LEVEL_C ZERO”;
   `PROGRAM_STATUS_V5.md` no longer claims L-A; `REPRODUCIBILITY_V5.md`
   added. Tag `coefficient-space-laurent-v1` was **not** moved off
   `ba2a0ce`.

C0 per-polygamma matching (R1/R3) remains sound as a **non-hop** lemma.
It is not hop ZERO and not FAMILY V_GAIN.

Frozen Guo case is **L-D**. Track D2 locked.
