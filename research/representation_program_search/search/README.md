# S0/S1 search kernel — frozen finite policy

This directory implements the no-LLM controls:

- **S1** deterministically enumerates states by `(frozen complexity, depth,
  canonical state hash)` and emits every child produced by the finite frontier;
- **S0** samples the next state with a seeded PRNG from that exact same
  frontier under the same state-expansion budget.

Neither condition calls the verifier or uses ZERO/NONZERO/UNKNOWN to order a
state. Compilation is recorded and may fail closed, but it does not alter S0
or S1 priority.

## Public boundary

`load_public_case()` accepts only a `proposer_view.json`. It follows only
package-relative, hash-bound paths disclosed by that view. Evaluator fields
and `reference/`, `verification/`, `runs/`, `steps/`, and `final/` paths are
rejected before a file is opened. It deliberately does not import M1's
evaluator-side `load_case_package()`.

## Candidate-pool policy

`RPSCandidatePoolV1` is finite and gold-free:

- at most 16 public source members;
- at most 24 latent candidates;
- at most 64 pairwise anti-unification pairs;
- at most two anti-unified parameters;
- at most eight public node atoms;
- source expressions capped at 4096 characters for candidate extraction;
- fixed coefficient atoms `-1, 0, 1, 2, Rational(1, 2)`;
- unary function-call schemas and syntax-tree pairwise anti-unification come
  only from public member expressions.

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

## Search-policy bounds

`RPSSearchPolicyV1` fixes, without per-task tuning:

- maximum program complexity 24;
- at most two latent objects;
- at most four operators;
- at most one node structure;
- at most one member group;
- at most two parameters per latent;
- optional `latent_creation_enabled=false` ablation.

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
