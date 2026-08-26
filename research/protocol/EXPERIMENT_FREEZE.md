# Experiment freeze (ssc-bench-v0.1 / protocol v0)

Freeze date: 2026-08-26
Engine: package 0.3.0, engine 0.3.0, agent protocol 0.3.0
Git: `73c127814af9b38db0cbeb48c4ca38b2e52c38a4` at protocol freeze
  (experiment artifacts record the **run** commit, which may add
  research/benchmark files but must not silently change verifier
  semantics; engine-semantic edits bump engine version and this freeze)

This file freezes definitions **before** large experiments. Changing a
bullet requires a new protocol version (`v1`) and a STATUS.md entry.

## Benchmark

- Name: `ssc-bench-v0.1`
- Schema: `benchmark/schema.json`
- Splits: `benchmark/dev/` (tuning, ablations-of-implementation, prompt
  drafting) vs `benchmark/test/` (frozen numbers).
- Test files are hashed. After freeze, do not edit test JSON except via
  `ssc-bench-v0.2`.
- Hidden fields (`human_reference`, `reference_text`, `target_compact`,
  `ladder_target`) are stripped by `proposer_view()` before any proposer
  call.
- Guo \(\sigma_{abc}\) is one Tier C flagship item, not the benchmark.

## Budgets (matched across B3–B7 and A0–A7)

Per item, whichever comes first:

| Resource | Cap |
|---|---|
| Wall clock | 600 s (Tier A), 1200 s (Tier B), 3600 s (Tier C flagship) |
| Verifier calls | 20 (A), 30 (B), 40 (C) |
| Candidate proposals | same as verifier-call cap |
| LLM calls | 20 (A), 30 (B), 40 (C) |
| Named transform applications | 20 |

Engine verify/transform **internal** budgets remain shipped defaults
(`VERIFY_POLICY`, `TRANSFORM_POLICY`, `budgets.py`). Do not raise them
after seeing UNKNOWN rates on test.

B0/B1/B6 use the same wall-clock cap. B1 may apply a **fixed** sequence
`simplify, factor, cancel, together, collect, combine_identical_sums,
collect_common_factor` once each, each passed through the verifier when
the arm is "certified CAS" (`B1-cert`). Unrestricted `simplify` without
verify is `B1-raw` and cannot score certified success.

## Seeds / repeats

- Deterministic arms (B0, B1, B2, B6, transform-only B7-det): 1 run.
- Stochastic LLM arms: **5 seeds** `{0,1,2,3,4}` where cost permits.
  Flagship C1/C2 comparison (B4 vs B7 on test Tier C): 5 seeds minimum.
- Report mean, median, sample SD, success counts. Never one lucky run.

## Models

Attempted, in order, using whatever is **actually callable** without
new secret collection:

1. Grok (this harness / xAI if API present)
2. Claude (Anthropic token if empirically valid)
3. A third distinct family if a key or local runtime exists at run time

If fewer than 3 families run, C3 is inconclusive. Do not pretend a
second Grok temperature is a second family.

## Hidden-answer policy

Proposer context may contain: current expression, declared symbols and
assumptions, `structure_summary`, this-step residual/counterexample,
role contract. Proposer context may **not** contain: human closed form,
ladder answers, test metadata, other items' targets, git history of
scientific-line certificates, `FINAL_EXACT_CLOSED_FORM`.

## Primary metrics (no single aggregate score)

See `research/metrics/METRICS.md`. Headline tables use:

- C1: false_promotion_rate, certified_success_rate, unknown_rate
- C2: certified compactness delta; certified_ladder_level
- C3: the same, sliced by model and family

"Substantial" for C1 (pre-registered): absolute drop in false-promotion
rate of **at least 20 percentage points** on labeled non-identities
**or** (if baseline false-promotion is <20%) a drop to ≤5% with
non-overlapping 95% intervals vs B4. Do not pick a new cutoff later.

## Baselines and ablations

B0–B7 as in `research/baselines/BASELINES.md`.
A0–A7 as listed in that file. Unavailable arms are skipped with an
explicit mismatch row, not silently replaced by a stronger cousin.

## Certification language

Default claim: **exact symbolic certification under declared SymPy
engine semantics**. "Formal proof" is forbidden unless a Lean/other
kernel subset is actually checked.

## What may still change after freeze

- Bugfixes that restore documented engine invariants (P0), with
  regression tests, without changing ZERO/NONZERO/UNKNOWN meanings.
- Additional **dev** items.
- Runners, logging, figure code.

## What may not change after seeing test results

- Test items, labels, expected verdicts
- Metrics, thresholds, budget caps
- Which arm is "ours"
- Splits
- Seed list
