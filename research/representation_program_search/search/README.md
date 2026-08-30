# S0/S1/S2 search kernel — versioned finite policy

This directory implements the no-LLM controls:

- **S1** deterministically enumerates states by `(frozen complexity, depth,
  canonical state hash)` and emits every child produced by the finite frontier;
- **S0** samples the next state with a seeded PRNG from that exact same
  frontier under the same state-expansion budget.

Neither condition calls the verifier or uses ZERO/NONZERO/UNKNOWN to order a
state. Compilation is recorded and may fail closed, but it does not alter S0
or S1 priority.

**S2** uses the same candidate pool, legal actions, child expansion, grammar
ablations, and state-expansion budgets. It applies a deterministic layer-wise
beam of width 32. Candidate states are ordered by
`(-symbolic_priority, complexity, canonical_hash)`, and ties therefore have a
stable replay order. Every expanded state still emits its complete frozen
generated child frontier before beam truncation.

`RPSSymbolicHeuristicV1` uses only proposer-visible syntax and partial-program
structure: pairwise anti-unification relations, shared call-argument and
denominator families, adjacent power profiles as weak derivative-edge
evidence, alpha-renaming symmetry, repeated public call arguments, member
coverage, latent reuse, cross-latent composition, and frozen program
complexity. Its integer weights are global and versioned in
`symbolic_heuristic.py`. These signals are routing evidence, not proof.
Compiled obligations, ZERO/NONZERO/UNKNOWN, reference programs, audited
depths, hidden roles, and target labels are absent from S2 ordering.
The priority is a routing policy distinct from the frozen scientific
`Score(H)` in `SCORING_POLICY.md`; it cannot make a state eligible and cannot
establish PROGRAM_SUCCESS.

## Public boundary

`load_public_case()` accepts only a `proposer_view.json`. It follows only
package-relative, hash-bound paths disclosed by that view. Evaluator fields
and `reference/`, `verification/`, `runs/`, `steps/`, and `final/` paths are
rejected before a file is opened. It deliberately does not import M1's
evaluator-side `load_case_package()`.

## Candidate-pool policy

`RPSCandidatePoolV2` is finite and gold-free:

- at most 16 public source members;
- at most 24 latent candidates;
- at most 64 pairwise anti-unification pairs;
- at most two anti-unified parameters;
- at most eight public node atoms;
- at most 24 reconstruction coefficients;
- source expressions capped at 4096 characters for candidate extraction;
- fixed coefficient atoms `-1, 0, 1, 2, Rational(1, 2)`, augmented by a
  bounded syntax-only inventory of public integers, simple symbol products,
  direct denominator reciprocals, and observed integer/reciprocal products;
- unary function-call schemas, complete-expression one/two-name
  parameterizations, and syntax-tree pairwise anti-unification come only from
  public member expressions;
- call arguments are ordered before remaining free names in the bounded node
  inventory. Reserved constants and function identifiers are excluded.

`SOURCE_LITERAL` objects are **tautology controls only**. They may instantiate
their byte-identical member through VALUE so the pre-verifier tautology gate
can be tested; they are not used as derivative, divided-difference,
composition, recurrence, permutation, basis, or linear-combination search
latents. A byte-identical one-member wrapper is marked `TAUTOLOGICAL` and is
ineligible before any verifier call.

Every pool and search result records `branching_incomplete=true` and the
specific caps. This implementation is exhaustive only over its generated
finite child frontier. It never claims global enumeration of the grammar's
expression space.

S2 is additionally incomplete because it retains only 32 states after each
completed depth layer. `beam_search_complete=false` is unconditional, and
`beam_states_pruned` plus every layer's candidate and selected hashes make
the truncation auditable. Reaching an empty beam means only that the frozen
beam policy exhausted its retained frontier.

## S4/S5 LLM heuristic controls

S4 ranks bounded legal child states; S5 ranks bounded legal typed actions.
Both generate the unchanged M2 frontier and then present only its first 32
children under one shared frozen batch/beam policy.
They accept only complete permutations of opaque IDs and atomically record
every decision. Invalid API or schema output is not repaired; a distinct
canonical fallback is recorded. They never read verifier/evaluator/SOL data
and never self-certify PROGRAM_SUCCESS. Full request, response-projection,
private-reasoning exclusion, audit, and incompleteness rules are in
[`LLM_SEARCH.md`](LLM_SEARCH.md).

This is **not** frontier-matched to current S2: S2 ranks every generated child
before layer-beam truncation. S4/S5 therefore record
`symbolic_comparison_requires_matched_batch_control=true`; no AI-advantage
comparison to S2 is valid unless the implemented `S2_MATCHED_BATCH32`
diagnostic is run on the same inputs and budget. That diagnostic ranks the
identical first-32-per-parent subset and uses the exact shared cross-parent
merge key and beam width. It is additive: full-frontier S2 remains the
strongest symbolic baseline.

S4/S5 also fail closed at run level. A run with any API/schema/parse fallback,
incomplete usage, or zero accepted LLM rankings is labeled
`INVALID_LLM_GUIDED_DIAGNOSTIC_ONLY` and
`llm_guided_scientific_run_eligible=false`; fallback output can be replayed
but cannot count as LLM-guided evidence. Numeric result seeds 0--4 are bound
deterministically to retained labels `seed-0`--`seed-4`.

## Search-policy bounds

`RPSSearchPolicyV2` fixes, without per-task tuning:

- maximum program complexity 48;
- at most two latent objects;
- at most twelve operators;
- at most four node structures;
- at most one member group;
- at most two parameters per latent;
- optional `latent_creation_enabled=false` ablation.

V2 also exposes one-input scaling, bounded two-input reconstruction with the
same public coefficient inventory, and both three-node multiplicity
orientations `[x,x,y]` and `[x,y,y]`. Reconstruction considers a deterministic
four-output split window: the earliest reusable outputs and the most recent
construction outputs. This prevents prefix truncation from making a new
operator output unusable while preserving a finite gold-free branch set.

The V1→V2 change occurred before any scientific search run or TEST freeze.
Public-source legal-path checks showed that V1 could not mechanically express
a complete multi-member recurrence or two repeated-node obligations: the
missing paths were candidate/action reachability defects, not adverse search
scores. No grammar operator, verifier rule, target label, or hidden reference
was added. V2 is the implementation candidate for the first DEV execution
gate; the gate, not these reachability tests, determines search success.

Legal children use the frozen action vocabulary, including `ADD_COMPOSE` for
the existing COMPOSE primitive. Its bounded input pool is the first three
eligible available outputs regardless of which latent produced them; this
permits an outer latent to compose VALUE/DERIVATIVE results from a distinct
inner latent. SOURCE_LITERAL control outputs remain ineligible composition
inputs. `REMOVE_REDUNDANT_OBJECT` is a validated
transition but is not generated: removing an unused object reaches a
canonical state already reachable without adding that object, so duplicate
canonical-state pruning subsumes it. This is a gold-free graph reduction.

Headline budgets are exactly 10, 50, 100, 500, and 1000 states. The root is
state expansion 1; no synthetic expansions are added if a frontier exhausts.

## Frozen score

`scoring.py` implements `SCORING_POLICY.md` with coefficients `(1, 1, 1, 2)`
and the exact listed complexity terms. SymPy `count_ops(F)` is computed through
the engine's inspection-only namespace; if that exact count is unavailable,
the candidate is rejected rather than assigned an approximate cost. Declared
case assumptions remain the separate compilation/evaluation authority. Required NONZERO,
COMPILE_FAILURE, and an IR-level tautology are hard ineligibility markers.
UNKNOWN is retained and adds no verified relation.

For multiple latents, `count_ops(F)` means the sum of their exact operation
counts before the single `ceil(total / 8)`. Reconstruction operations are the
dependency-closure lengths summed over assignments. An assigned member is a
member-specific exception exactly when none of its referenced latents is also
referenced by another assigned member. These rules are global, not task-tuned.
