# M2/M4 handoff — enumerative and random search controls

Implementation commit: `74f1cc6d0e93ffae9a4f43341526d17bd4738d90`

Contract-access dependency: coordinator commit `5216f77` (present in this
worktree as cherry-pick `679d5e0`) added `ADD_COMPOSE` for the already-frozen
COMPOSE operator. The implementation commit assumes that action is in
`grammar_v1.ACTIONS`.

## Delivered

- typed immutable `SearchState`, `LegalAction`, proof-evidence, expansion, and
  result records;
- case-bound, ancestry-free canonical state hashing with M1 alpha-normalized
  program identity;
- a hardened proposer-only loader which never imports the evaluator-side M1
  package loader and rejects evaluator fields plus every `reference/`,
  `verification/`, `runs/`, `steps/`, or `final/` path;
- exact source-member path/hash binding and assumption statuses limited to
  public DECLARED/DERIVED predicates;
- `RPSCandidatePoolV1`: bounded public-expression unary schemas and pairwise
  syntax-tree anti-unification, with all caps and incompleteness recorded;
- SOURCE_LITERAL objects restricted to explicit tautology controls; their
  byte-identical VALUE-self maps receive a pre-verifier `TAUTOLOGICAL`
  ineligibility marker and cannot become PROGRAM_SUCCESS;
- executable typed transitions for every frozen action, including the repaired
  `ADD_COMPOSE` access path, bounded cross-latent composition inputs, and
  explicit repeated-node structures;
- hard G_FULL / G_NO_HERMITE / G_PRIMITIVE action filtering and the
  latent-object-disabled ablation;
- exact frozen complexity/score implementation, including exact SymPy
  `count_ops`, member exceptions, reconstruction depth, required-NONZERO hard
  ineligibility, and UNKNOWN retention;
- S1 exhaustive emission of every child in the **generated finite frontier**,
  ordered by increasing `(complexity, depth, canonical hash)`;
- S0 seeded sampling of the next state from that exact same frontier;
- exact headline expansion budgets 10/50/100/500/1000, plus wall time and zero
  LLM-token accounting.

Stable integration API:

```python
case = load_public_case(".../proposer_view.json")
pool = extract_candidate_pool(case)
root = initial_state(case, grammar_id="G_FULL")
actions = legal_actions(root, case, pool, SearchPolicy())
expansion = expand_state(root, case, pool, SearchPolicy())
program = root.to_program(
    source_members=case.source_members,
    assumption_statuses=case.assumption_statuses,
)
```

`FrontierExpansion.actions` and `.children` are aligned one-to-one in the same
deterministic order. Search-state hashes do not contain proof evidence, score,
parentage, or method priority. Consequently later S6/S7 methods can attach
feedback without changing mathematical state identity.

## Scientific boundary

No scientific DEV or TEST result was produced. S0/S1 compile public synthetic
states for constructor diagnostics but never invoke the verifier and never use
ZERO/NONZERO/UNKNOWN in frontier ordering. `branching_incomplete` is true in
every pool/result. The implementation makes no global expression-space or
global grammar-enumeration claim.

`REMOVE_REDUNDANT_OBJECT` is a validated transition but is not generated:
removing an unused object reaches the canonical state already reachable by not
adding it, so canonical duplicate pruning subsumes it without gold knowledge.

## Package compatibility finding

The four matrix/differentiable-physics and six thermal proposer views pass the
public loader. The three response/tensor proposer views fail closed with
`PUBLIC_SYMBOLS_HASH_MISSING`: each exposes a `symbols_path` without the exact
SHA-256 required by the public package contract. M2/M4 did not repair or read
around that boundary.

## Validation

Focused integration:

```text
53 passed in 7.33s
```

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q \
  tests/test_rps_enumerative_random.py \
  tests/test_rps_program_ir.py \
  tests/test_rps_contracts.py \
  tests/test_rps_matrix_diffphys_packages.py
```

Synthetic high-budget smoke (not a scientific case):

```text
S1 1000 states; frontier not exhausted; 5848 duplicate states pruned
S0 1000 states; seed 8675309; frontier not exhausted; 917 duplicates pruned
```

The first full-repository run reported `1745 passed, 3 failed in 187.81s`.
All three failures were the same pre-existing test-discovery defect:
`tests/test_rps_matrix_diffphys_packages.py` treats every directory under its
package root as a scientific package, including a generated `__pycache__`.
After deleting that generated cache and setting `PYTHONDONTWRITEBYTECODE=1`,
the affected package file passes `7/7`. No implementation test failed.

`git diff --check` and Python bytecode compilation passed before the
implementation commit.

## Deliberate limits

- Candidate-pool caps are method semantics, not a claim of complete grammar
  enumeration.
- Public namespace inference is inspection/compilation support only and never
  proof authority; evaluation must use the package's declared namespace.
- S0/S1 retain COMPILE_FAILURE states diagnostically and never convert them to
  proof outcomes.
- No hidden target program, target depth, package status, verifier receipt,
  or reference reconstruction is loaded.
- No parser, verifier, package, scientific dossier, or partition was changed.

## Pre-DEV V2 implementation amendment

Before any scientific method run or TEST freeze, public-source legal-path
checks exposed two mechanical limitations in the original finite frontier:
it could not retain enough operators/node structures for a complete
multi-member program, and it could not derive public reconstruction
coefficients or a complete one-parameter latent from source syntax. The
coordinator therefore versioned the policy to `RPSCandidatePoolV2` and
`RPSSearchPolicyV2`.

V2 adds bounded syntax-only full-expression parameterization, a bounded
public coefficient inventory, one-input scaling, bounded two-input
reconstruction, both repeated-node orientations, higher global complexity /
operator / node caps, and a deterministic earliest-plus-recent output window.
These are generic constructor/search paths over existing grammar operators.
They do not use evaluator programs or verifier verdicts, and they do not
constitute a scientific result. V1 provenance above is retained rather than
rewritten.
