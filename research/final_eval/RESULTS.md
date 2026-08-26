# ssc-bench-v0.2-hard evaluation

Date: 2026-08-27
Method v2 frozen before this run (DEV_DECISION keep).
v0.1 test unused. n=11 (dev 8, **test 3**). One seed. One model
(deterministic packager + engine). B2/Lean/egg unavailable.

## Test (n=3)

| id | M1 ZERO steps | named-aux ZERO | M1 FP | B4-CAS verdict | B4 would FP |
|---|---:|---:|---:|---|---:|
| D3-thermal-pair | 2 | 1 | 0 | ZERO | 0 |
| H-D2-triple-channel | 2 | 1 | 0 | ZERO | 0 |
| H-D5-swap-pair | 2 | 1 | 0 | ZERO | 0 |

M1 false promotions: **0**. B4 (SymPy simplify, no gate) also did not
false-promote on these three: simplify stayed equivalent.

## B4 vs Method v2 (mandatory)

On this **small CAS-tractable** set, B4 did not ship a non-ZERO form.
The reliability contrast vs **blank LLM** (bottleneck R1) remains the
one that shows false claims: drop-Piecewise `claimed_proven` with engine
UNKNOWN; Fermi `-1/z` not ZERO.

Method v2 vs B4-CAS: **not a reliability win** on v0.2-hard test.
Method v2 vs B3-blank: **reliability win** (from search_bottleneck, not
re-seeded here).

Method v2 vs M0: packaging/named-aux after first ZERO, as designed.

## Multi-model

Not run. Only Grok packager + this session. C3 still inconclusive.

## Pareto (qualitative)

- Blank LLM: higher narrative D-level, low reliability.
- CAS B4: high reliability on this set, no named scientific objects.
- M0: D1/D2 ZERO, then stop.
- M1: D1/D2 ZERO plus named closed auxiliaries; still no D4 confluence
  ZERO.

No expert pairwise ratings.
