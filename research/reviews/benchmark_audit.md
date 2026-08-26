# Benchmark-paper-template audit (ssc-bench-v0.1)

Secondary perspective: could the **benchmark** be the paper?

## Five pillars

| Pillar | Covered? | Content | Gap |
|---|---|---|---|
| Research Gap | partial | no public bench for certified scientific compactification with false-promotion | must cite MATH, MiniF2F, Herbie/FPBench, amplitude-simplification sets as the three limits |
| Construction Pipeline | Y | generated identities + engine-confirmed labels; author-constructed Tier C; hash split | reverse-synthesis is thin; Tier C too small and too easy; Guo contaminated in dev |
| Evaluation Framework | Y | correctness / compactness / ladder / efficiency / taxonomy | human rubric empty; ladder auto-score only L0–L2 |
| Empirical Findings | partial | verifier 35/35 test match; C2 negative vs B1 | no model-family boundary plot |
| Companion Method | NA | engine is companion; it did not dominate CAS compactness | |

## Design goals

G1 coverage: families exist but n_C test = 1 compactify item. Fail.
G2 diagnostics: yes (UNKNOWN vs NONZERO vs false ZERO).
G3 reproducibility: generator + hashes yes.
G4 contamination: Guo correctly parked in dev; still a case-study leak.

## Verdict

A NeurIPS D&B benchmark paper is **not** supported at v0.1 scale
(128 items, easy compactify, 1 held-out scientific compactify item).
The verifier-stress split (Tier A) is the only part that currently
behaves like a real evaluation dimension.

Do not rebrand the method failure as a benchmark success without
growing Tier C from public physics expressions and hardening compactify
tasks until B1 does not saturate them.
