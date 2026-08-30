# M3 + M9 handoff — S2 symbolic-heuristic beam

Date: 2026-08-30  
Branch: `work/rps-symbolic-beam`  
Base: `d0c0591`  
Scope: implementation and synthetic/evaluator-only controls; no scientific
DEV run

## Delivered

- `search/symbolic_heuristic.py`
  - `RPSSymbolicHeuristicV1`, a deterministic proposer-visible observation
    inventory and integer state priority;
  - public structural signals: candidate relation graph, shared call-argument
    families, denominator shapes, adjacent-power derivative hints,
    alpha-renaming symmetry, repeated public call arguments, partial-program
    coverage/reuse, and cross-latent composition;
  - fixed global coefficients:
    - coverage member `+16`
    - reuse member `+8`
    - relation support `+4`
    - repeated-node match `+6`
    - derivative-edge match `+5`
    - denominator/argument-family match `+4`
    - symmetry match `+4`
    - cross-latent COMPOSE `+3`
    - complexity unit `-2`
    - SOURCE_LITERAL tautology-control latent `-12`
- `search/symbolic_beam.py`
  - `RPSSymbolicBeamPolicyV1`, a layer-wise deterministic beam with frozen
    width 32;
  - ascending tie key
    `(-symbolic_priority, complexity, canonical_hash)`;
  - the same `extract_candidate_pool`, `expand_state`, `SearchPolicy`, frozen
    budgets, grammar ablations, and latent-object ablation as S0/S1;
  - exact expanded-state accounting, wall time, zero LLM tokens, full legal
    child hashes for each expanded state, layer candidate/selection hashes,
    priority records, and pruned-state counts.
- public exports and search README documentation.
- `tests/test_rps_symbolic_beam.py` with synthetic controls only.

## Firewall and causal separation

S2 accepts an already loaded `PublicCase`; it has no evaluator entry point.
The implementation does not import or call `load_case_package`, verifier
functions, SOL, LLM code, reference programs, hidden member roles, audited
depth, target labels, or verdicts. `verified_obligations` and
`compiled_obligations` are absent from priority calculation. Tests inject
UNKNOWN and NONZERO evidence into otherwise identical states and confirm the
priority and canonical identity are unchanged.

Compilation remains the method-neutral recording behavior inside the shared
M2/M4 `expand_state`; S2 does not use compile status for ordering. The S2
priority is a routing heuristic, not the frozen `Score(H)`, not an eligibility
decision, and not evidence of PROGRAM_SUCCESS.

## Incompleteness

This is not exhaustive search. It inherits the finite candidate-pool caps and
records `branching_incomplete=true`. It additionally truncates each completed
depth layer to 32 states, unconditionally records
`beam_search_complete=false`, and reports `beam_states_pruned`. The flag
`generated_frontier_exhaustive=true` means only that every expanded state was
passed through the complete shared frozen `expand_state` frontier. It is not a
claim of global grammar enumeration.

The derivative, confluence, and symmetry observations are deliberately weak
syntactic hints. They do not assert exact differentiation, equal nodes, or a
mathematical symmetry. Only later evaluator-side exact obligations can do so.

## Test evidence

Commands used with bytecode disabled and the root Python 3.12 environment:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q \
  tests/test_rps_symbolic_beam.py \
  tests/test_rps_enumerative_random.py \
  tests/test_rps_program_ir.py

50 passed in 12.47s
```

Repository-wide result:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q

1772 passed in 209.36s
```

The focused controls cover deterministic replay, matched root legal frontier,
budget validation/counting, evaluator/verifier blindness, structural controls
ranked over distractors, proof-verdict invariance, all three grammar
ablations, latent-object-disabled behavior, cross-latent COMPOSE under
`G_PRIMITIVE`, and explicit candidate-pool/beam incompleteness.

## Integration boundary

No package, benchmark manifest, parser, verifier, M1 program IR, M2/M4 action
generation, search-policy bound, or scientific result was changed. Do not
treat these tests as DEV success. The policy and weights are ready for the
coordinator's pre-DEV freeze/review, after which changing them requires a
version bump and cannot occur after TEST freeze.
