# Protocol v0 analysis (deterministic + one Grok seed)

Date: 2026-08-26
Engine: 0.3.0 / commit recorded in run JSONs
Benchmark: ssc-bench-v0.1 (128 items; test 42; compactify test 7)

UNKNOWN was never scored as success. No test item was edited after freeze.

## Engine adjudication (Tier A) — checker soundness

| Split | n | match | false_promotion | ZERO/ZERO | NONZERO/NONZERO | UNKNOWN/UNKNOWN |
|---|---:|---:|---:|---:|---:|---:|
| test | 35 | 35/35 | 0 | 6 | 28 | 1 |
| dev | 68 | 68/68 | 0 | 18 | 46 | 4 |

The frozen labels match the engine. This is a **necessary** condition for C1
(the verifier does not false-promote labelled corruptions). It is **not**
C1 versus unconstrained LLM/CAS agents (B3/B4), which were not batch-run.

## Compactify (Tier B/C) — compactness, not trivial certified_success

`certified_success` is near 1 for B0 because the input is equivalent to
itself. C2 is read from **deltas** and promotions that change structure.

Frozen **test** compactify (n=7, easy items):

| Arm | mean Δcount_ops | mean Δn_sums | false_promotion |
|---|---:|---:|---:|
| B0 | 0.000 | 0.000 | 0 |
| B1-cert | 0.143 | 0.000 | 0 |
| B6 | 0.429 | 0.000 | 0 |
| B7-det | 0.429 | 0.143 | 0 |
| B7-agent Grok seed0 | 0.714 | (1 sum-merge) | 0 |

B7-det's only structural (sum) win on test is `B-sum-common-factor`.
B1 skips global CAS on structured input by documented policy.

Frozen **dev** compactify (n=17, excludes wolfram Guo ingest):

| Arm | mean Δcount_ops | any sum-count reduction |
|---|---:|---|
| B0 | 0.000 | 0 |
| B1-cert | 0.824 | 0 |
| B6 | 0.647 | 0 |
| B7-det | 0.353 | 0 |

B1 **beats** B7-det on unstructured ops reduction on dev. C2 in the
strong form ("more compact than conventional CAS") is **not supported**
on this benchmark. Combined with the 2026-08-21 Guo probe (skill
certified-shallow vs blank CAS narratively deeper), C2 is at least
threatened and, on v0.1 easy items, empirically reversed on ops.

## LLM arms

B3/B4/B5/B7-agent batch: skipped (no batch client). One Grok main-proposer
seed on the 7 test compactify items: all ZERO, 0 false promotions, trivial
difficulty. Not a 5-seed, not multi-model. C3 inconclusive.

## Guo flagship

Not in this runner (Wolfram source). Prior report remains the case study:
certified L2 only; PRB L4–L7 absent.

## Claim status

- C1 vs B3/B4: **untested** in v0 batch; checker half holds (0 false ZERO
  on labelled test).
- C2: **not supported** (B1 ≥ B7-det on ops; Guo shallow).
- C3: **inconclusive**.
