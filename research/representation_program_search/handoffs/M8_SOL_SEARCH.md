# M8 / E handoff — frozen-SOL-conditioned search (S3)

## Implementation

- Branch: `work/rps-sol-search`
- Implementation commit: `0ea7bb0`
- Scope: method implementation plus synthetic controls only.
- No scientific DEV/TEST run, benchmark/package/manifest mutation, LLM call,
  verifier call, parser change, verifier change, or SOL execution was made.

## Frozen SOL authority finding

The repository's SOL implementation is the Structural Observation Layer v1 at
commit `0a2905b`. Its callable interface is
`symbolic_compactification.observations`, while the committed historical Guo
`research/preprocessing_integration/guo/RELATION_GRAPH.json` contains only
aggregate packet statistics and no source-bound relation rows. Guo is sealed,
and that aggregate artifact is not eligible for S3.

`authority.py` freezes SHA-256 hashes for all SOL files plus the parser,
structure, budget, shared-model, frozen LGG, and LGG-scoring dependencies at
`0a2905b`. The canonical authority-manifest hash is:

```text
6678002a8038ea7cc79ed75d428c669946c67ae66272f1999d4e9d95db8f1595
```

The loader verifies these exact local bytes. A replay artifact must repeat
the exact source manifest and include a replay attestation binding the
canonical observation-bundle hash, public proposer-view hash, and authority
manifest hash. The attestation is a replayable integrity record, not a digital
signature or independent proof that a process executed; exact reproduction
remains the audit mechanism.

## Delivered surface

`research/representation_program_search/sol_search/` provides:

- `load_sol_projection()`: a read-only, caller-hash-bound loader for
  `RPSSOLArtifactV1`;
- exact case binding to the proposer-view SHA and every public source-member
  SHA;
- a recursive evaluator/gold-field firewall and forbidden package-path gate;
- validation of frozen SOL provenance, bundle/relation/node schemas,
  epistemic classes, node structural hashes, and backend attestations;
- deterministic projection only when every relation node occurs as an exact
  parsed subexpression of a public source member;
- explicit `UNAVAILABLE` for malformed/drifting/leaking authority or
  artifacts, and `NO_ELIGIBLE_SOL` when no source-bound routable relation is
  present;
- `RPSSOLPriorityPolicyV1`, a task-invariant integer routing policy for legal
  member-grouping, latent, parameter, derivative, Newton, recurrence,
  permutation, repeated-node/Hermite, linear-reuse, basis, reconstruction,
  and composition actions;
- `sol_conditioned_search()`, which calls the exact M2
  `extract_candidate_pool()` and `expand_state()` surfaces under the same
  `SearchPolicy`, grammar ablations, and budgets `10/50/100/500/1000`;
- deterministic ordering by descending cumulative SOL units, then frozen
  complexity, depth, and canonical state hash;
- an audit row for every legal child considered and every SOL relation used:
  parent/child state hash, structured action and hash, source artifact hash,
  relation id/type, rule id, and integer contribution;
- zero LLM-token accounting, no private reasoning, and
  `ordering_uses_verifier_outcomes=false`.

A derivative relation can prioritize a repeated-node or Hermite action only
when the repeated node label occurs among the exact public symbols on that
relation. This is explicitly a hypothesis-routing rule, not proof of node
multiplicity or a certified Hermite representation.

## Controls

The synthetic tests cover:

- exact artifact, authority-source, replay, case, member, relation-node, and
  public-subexpression binding;
- rejection of wrong hashes, self-declared wrong authority manifests, local
  authority drift, case drift, node drift, evaluator/gold fields, and
  forbidden evaluator/reference paths;
- explicit no-run `NO_ELIGIBLE_SOL` for aggregate/orphan and source-bound but
  unroutable relations;
- identical M2 candidate-pool hash and root legal-child frontier for S1/S3;
- deterministic S3 semantic trace and fixed state-expansion budget;
- derivative operator selection, member grouping, repeated-node routing, and
  Hermite routing;
- a misleading `RECURRENCE_CANDIDATE` anchoring control that deterministically
  routes recurrence ahead of an unsupported derivative action;
- absence of imports for SOL execution, verifier execution, or evaluator-side
  package loaders.

The tests use a manually constructed synthetic frozen-replay fixture. They do
not call SOL and do not establish a scientific S3 result.

## Verification

- Focused S3 controls: `14 passed`
- M2 + S3 controls: `31 passed`
- Full repository suite with bytecode writes disabled:
  `1784 passed in 214.62s`

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 \
  /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m pytest -q
```

## Scientific gate

There is deliberately no S3 program-search result yet. A scientific S3 run is
`UNAVAILABLE` until a fresh case-bound read-only SOL replay is produced from
the exact frozen authority and separately frozen with its full artifact hash.
Do not reconstruct relation edges from the historical Guo summary, use old
TEST artifacts, or treat the synthetic anchoring/operator controls as method
success.
