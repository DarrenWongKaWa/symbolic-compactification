# S6 verifier-in-the-loop controller

This package is the exact-adjudication layer for condition S6. It is not a
program generator and does not duplicate S0/S1 enumeration.

The controller consumes `VerifierFrontierNode` objects adapted from a
method-neutral legal frontier. Ordering uses only:

- a frozen verifier-feedback priority band;
- the node's public structural priority;
- frozen complexity;
- the canonical public-state hash.

Complete, explicitly leakage-cleared states are compiled through M1. Every
compiled equality is run through a fresh persisted symbolic-compactification
session (`init_session`, `set_current`, `adjudicate_candidate`). The complete
session directory and its evidence record are staged and published by atomic
directory rename. Success requires ZERO for every required member obligation.

Only `ZERO`, `NONZERO`, `UNKNOWN`, and `COMPILE_FAILURE` may be returned to a
successor expander. Residuals and exact counterexamples remain in the verifier
step artifact and never become ordering inputs. `UNKNOWN` states are retained
and their legal successors enter the lower-priority frozen band. `NONZERO` or
`COMPILE_FAILURE` prunes the exact state, not unseen siblings; a method-neutral
expander may still return legal repairs after receiving only the outcome label.

Tautological programs, explicitly uncleared/leaking states, and states with an
already-seen strictly lower-complexity exact-obligation witness are ineligible
before verifier invocation. Conservative dominance requires byte-identical
current hashes and candidate expressions, equal coverage, and no additional
obligations.

Headline budgets are restricted to 10, 50, 100, 500, or 1000 states expanded.
Output records structured actions, hashes, timings, and session provenance;
private reasoning is never stored. Receipt-bound `decision_hash` /
`trace_hash` values bind the exact run, including timing and randomized
session receipts. Separate `semantic_decision_hash` /
`semantic_trace_hash` values bind only state, frontier, legal action,
aggregate feedback, and exact obligation identities/verdicts. The semantic
hashes explicitly exclude wall times, run IDs and paths, and engine receipt
hashes, so identical executions are comparable even though their diagnostic
timings and session receipts differ.

`M2VerifierFrontierAdapter` is the frozen bridge to the S0/S1 generated
frontier. It calls the same `extract_candidate_pool`, `initial_state`, and
`expand_state` functions and owns no alternate action generator. Aggregate
verifier feedback changes only the controller's priority band. Leakage status
defaults to `UNKNOWN`; a complete program can be verified only when a separate
audit has explicitly supplied `CLEARED`.
