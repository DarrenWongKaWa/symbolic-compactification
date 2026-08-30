# Evaluation aggregation V1

This layer reports search outcomes; it does not run search, compile programs,
or adjudicate mathematics. Each input record is bound to the SHA-256 of its
source result and, when available, its search and exact-evidence trace hashes.

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
