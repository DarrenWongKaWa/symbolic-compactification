# Evaluation aggregation V1

`model.py` and `aggregate.py` report search outcomes; they do not run search,
compile programs, or adjudicate mathematics. Each input record is bound to the
SHA-256 of its source result and, when available, its search and exact-evidence
trace hashes.

## Atomic condition jobs

`runner.py` is the pre-DEV execution boundary. It runs exactly one condition
per job, so methods, tasks, budgets, seeds, and grammar ablations can be
parallelized without mutating a shared manifest. Each job consumes:

- one hash-bound public `proposer_view.json`;
- one independent `RPSCaseClearanceV1` receipt binding `ADMISSION_READY`,
  complete assumptions, cleared leakage, and the three audit artifact hashes;
- the frozen grammar, budget, seed, and optional LLM model in an immutable
  `ExperimentJobSpec`;
- only for S3, one exact frozen-SOL replay artifact and hash;
- only for F0, one evaluator-only legacy authority object and hash.

The runner publishes `JOB_MANIFEST.json`, all method-native traces, and
`JOB_RESULT.json` by atomic directory rename. A method exception becomes a
preserved `METHOD_ERROR`, never a search failure or a PROGRAM_SUCCESS. Output
directories cannot be reused. S0--S7 scientific success still comes only from
exact persisted verifier sessions; F0 uses the separate strict sessioned
evaluator. F0 has no state-expansion budget and must not be copied across
search-budget points as if it had performed formal search.

One independent audit may cover multiple gates; in that case the receipt
repeats the same exact artifact SHA in the corresponding fields. This records
shared authority explicitly rather than inventing separate evidence.

An `AVAILABLE` record enters a denominator only when the case is independently
`ADMISSION_READY` and leakage is `CLEARED`. `UNAVAILABLE`, `PACKAGING_GAP`,
`PROBLEM_UNDERSPECIFIED`, and infrastructure diagnostics are never silently
converted into method failures.

The fixed state budgets are 10, 50, 100, 500, and 1000. Reports include both:

- task weighting: every available case/seed run has equal weight;
- cluster weighting: outcomes are averaged within each structural cluster,
  then every represented cluster has equal weight.

States/time/tokens to first success are conditional summaries. The number of
failed or censored runs is always adjacent; a conditional median is never
presented as an unconditional efficiency result. Token-to-first-success stays
missing unless decision-level audit records locate the exact successful LLM
decision. Total run tokens are not substituted.

This module does not declare `AI_SEARCH_ADVANTAGE`. That claim additionally
requires a matched-frontier comparison, replication across tasks/seeds, and
three independent reviewer passes under `SCORING_POLICY.md`.
