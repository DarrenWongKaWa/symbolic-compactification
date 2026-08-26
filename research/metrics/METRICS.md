# Metrics (frozen with protocol v0)

No single aggregate score. Every metric below is implemented in
`evaluator.py` and written into a per-run JSON record.

UNKNOWN is never converted into success. Numeric agreement is never
treated as exact symbolic equivalence.

## Correctness

| Metric | Definition | Notes |
|---|---|---|
| certified_success | 1 iff final current is certified and, when a gold identity is labelled, verifier(current, gold) is ZERO | Tier A identities |
| false_promotion | 1 iff any promoted candidate has gold label NONZERO, or verifier(promoted, input) is not ZERO | primary C1 |
| nonzero_detection | 1 iff a labelled non-identity is reported NONZERO (not UNKNOWN) | refutation capability |
| unknown_rate | fraction of verifier calls with UNKNOWN | reported; not a win |
| parse_fail_rate | fraction of items that fail ingestion | separate from UNKNOWN |

## Compactness (measured on input vs certified output only)

All from `structure_summary` plus cheap extras:

- count_ops (SymPy `count_ops`)
- char_len (canonical text length)
- ast_depth (preorder max depth)
- n_sums, n_products, n_piecewise, n_piecewise_branches
- n_indexed_calls, n_indexed_names
- n_distinct_repeated_kernels (duplicate Sum bodies / duplicate
  undefined-function call patterns, count of patterns with freq≥2)
- repeated_subexpression_count (subexpr srepr frequency ≥2, capped
  traversal)

Deltas are `input - certified` so positive means smaller/simpler.
Uncertified arms report compactness of their **claimed** form in a
separate namespace `claimed_*` that cannot enter certified_success.

## Scientific progress

- certified_ladder_level: max L_k whose predicate holds on certified
  current (Guo ladder L0–L7 documented in
  `docs/experiments/2026-08-21-progress-vs-prb-closed-form.md`; other
  Tier C items define their own ladders in metadata). Missing ladder
  → metric omitted, not zero-filled as if L0 failure.
- distance_to_hidden_reference: 0 if verifier(certified, hidden) is
  ZERO; else compactness distance + 1000 if UNKNOWN/NONZERO. Hidden
  reference never enters proposer context.
- human_rubric: optional integer 0–3 filled only by a human later
  (0 none, 1 syntactic, 2 structural, 3 scientific abstraction).
  Agent runs must leave this null.

## Efficiency

wall_clock_s, verifier_calls, candidates_proposed, llm_calls,
token_usage (if harness exposes; else null), estimated_cost (else null),
time_to_first_zero_s, time_to_best_certified_s.

## Robustness

Sliced reports, not extra scores: by family, by count_ops bins, by
model, by seed. Failure taxonomy labels from
`research/analysis/FAILURE_TAXONOMY.md`.

## Aggregation

Per cell: n, mean, median, sample SD, count of binary successes.
No ranking score. Pareto plot uses x = scientific-progress proxy
(ladder or certified compactness z-score on Tier B) and y = 1 −
false_promotion_rate (or certified reliability on Tier A).
