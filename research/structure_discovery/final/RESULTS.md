# Held-out results — ssc-structure-bench-v0.1 TEST

Frozen method: observe → typed H → construct → verify (deterministic B9).
n_test = 12 (8 positive, 4 negative). One seed (deterministic). No LLM.

## Headline (B9_full vs B1 vs B6)

| Method | pos type-hit | pos gold-type ZERO | neg unsafe merge | false promotion |
|---|---:|---:|---:|---:|
| B0 raw | 0/8 | 0/8 | 0 | 0 |
| B1 SymPy transforms | 0/8 | 0/8 | 0 | 0 |
| B6 direct Method v2 | 0/8 | 0/8 | 0 | 0 |
| **B9 full** | **8/8** | **8/8** | **0** | **0** |
| B9 no observations | 0/8 | 0/8 | 0 | 0 |

D3–D5 gold subset (dd, master, orbit, green-two, tensor): B9 **5/5**, B1 **0/5**, B6 **0/5**.

B6 still emits tautological named auxiliaries with self-labeled D3/D5; those
labels do not match gold *types*. C1/C2 are scored on gold type-hit.

## Claims on this split

- **C1** supported (typed discovery vs CAS/direct).
- **C2** supported on the type axis (decomposition vs E→E').
- **C3** supported (0 forbidden ZEROs; aggressive merges NONZERO or incomplete).

## What this does *not* show

- An LLM invents D3–D5 structure (no usable model API).
- Multi-seed / multi-model generalization.
- Guo PRB L4–L7 (case study: D2 kernels only, Piecewise unused because of the 8-H cap).
- Human physicist D6 utility (slots unfilled; not fabricated).
- Superiority on `count_ops`.

Raw: `RESULTS.csv`, `SUMMARY.json`, `FAILURES.md`. Freeze: `FREEZE_MANIFEST.json`.
