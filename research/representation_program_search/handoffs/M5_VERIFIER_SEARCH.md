# M5 / H handoff — verifier-in-the-loop controller (S6)

## Implementation

- Branch: `work/rps-verifier-search`
- Implementation commit: `618dc20`
- Required pre-contract dependency already in branch: `b2eb430` (equivalent
  to coordinator commit `5216f77`, exposing the already-declared `COMPOSE`
  operator through legal `ADD_COMPOSE`)
- Scope is infrastructure and evaluator controls only. No DEV scientific run,
  benchmark freeze, package mutation, parser change, or verifier change was
  performed.

## Delivered surface

`research/representation_program_search/verifier_search/` provides:

- a method-neutral `VerifierFrontierNode` boundary over the M1 typed program
  and compile context;
- a deterministic heap controller with fixed state budgets
  `10/50/100/500/1000`;
- a successor callback that receives only `ZERO`, `NONZERO`, `UNKNOWN`, or
  `COMPILE_FAILURE` for adjudicated states (`None` means a partial state was
  structurally expanded without verifier feedback);
- exact M1 compilation for complete, explicitly leakage-cleared programs;
- one fresh persisted symbolic-compactification session per compiled equality
  (`init_session` -> `set_current` -> `adjudicate_candidate`);
- atomic staging/publication of each equality's candidate, run directory, and
  evidence receipt;
- pre-verifier exclusion of tautological programs and conservative dominated
  states;
- complete-member required-obligation coverage as a hard gate;
- UNKNOWN retention with a frozen lower successor-priority band and no success;
- NONZERO pruning of only the exact state. Its method-neutral expander may
  still return legal repair states after seeing only the NONZERO label;
- exact state/obligation/receipt hashes, wall-time diagnostics, state and
  obligation verdict counts, states/time to first success, SUCCESS checkpoints,
  and zero LLM-token accounting.

The conservative dominance rule requires identical member coverage and
byte-identical compiled equality identities (source hash, candidate expression,
required flag) plus a strictly lower frontier-supplied frozen complexity. It
does not use algebraic resemblance, hidden gold, or an unverified score.

## Reproducibility hash split

Exact-run `decision_hash`, `evidence_record_hash`, and `trace_hash` values are
receipt-bound integrity hashes. They intentionally change with verifier wall
times, randomized session IDs, timestamps, and the resulting engine receipt
hashes.

Separate `semantic_evidence_hash`, `semantic_decision_hash`, and
`semantic_trace_hash` values exclude timings, run IDs/paths, and receipt hashes.
They bind the public state/frontier order, legal action provenance, aggregate
four-label feedback, exact obligation identities, and obligation verdicts.
The tests execute the same search twice and require semantic hashes to match
while receipt hashes differ.

## Controls exercised

- exact ZERO produces `PROGRAM_SUCCESS`, a CERTIFIED/PROVEN step, and promotion;
- exact NONZERO records its residual and exact rational counterexample only in
  the verifier step, prunes the state, then permits an explicit legal repair;
- actual polygamma recurrence proof gap produces UNKNOWN/PROOF_REQUIRED,
  remains retained, and never succeeds;
- the M10 wrong-Hermite evaluator trap is translated to M1 without changing
  its node structure and fails exactly with
  `HERMITE_REPEATED_NODE_REQUIRED:N0`; no verifier session is created;
- independent VALUE-self wrappers are pre-verifier tautologies;
- a strictly more complex program with the exact same obligations is
  pre-verifier dominated after a lower-complexity witness;
- partial programs expand with no scientific feedback and do not invoke the
  verifier;
- `COMPOSE` executes successfully under `G_PRIMITIVE`;
- forbidden evaluator/gold keys are rejected at the public frontier boundary;
- private reasoning and residual/counterexample material are absent from the
  decision/order records. Residual/counterexample evidence remains available
  in the exact session step.

## Verification

- Focused S6 controls: `8 passed`
- Full repository suite with bytecode writes disabled:
  `1744 passed in 197.18s`

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 \
  /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m pytest -q
```

An earlier full run reported `1741 passed, 3 failed` because importing the
matrix/differentiable-physics validator created
`packages/matrix_diffphys/__pycache__/`, while three existing package tests
iterate every directory under that package root as if it were a case. The
three tests pass independently after the generated cache is absent, and the
clean no-bytecode full run above is green. No test or package code was changed
to mask this pre-existing directory-enumeration sensitivity.

## Integration note

M2/M4 subsequently froze the expected compatible surface:
`SearchState.to_program(...)`, `canonical_hash`, `complexity`, `depth`,
`parent_hash`, `action_from_parent`, `PublicCase.compile_context(...)`, and
aligned `FrontierExpansion.children/actions`. The coordinator has M2 commits
`74f1cc6` and follow-up `d86e0c7`. A thin adapter can wrap those fields into
`VerifierFrontierNode` and call `expand_state`; S6 deliberately does not import
or duplicate M2's candidate extraction, legal-action generation, or
enumeration policy.
