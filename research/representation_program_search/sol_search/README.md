# S3 frozen-SOL-conditioned search

This package adds a deterministic priority layer over the exact M2 legal
frontier. It does not run, modify, or retune SOL, create candidate programs,
call the verifier, or consume evaluator artifacts.

The separate `build_sol_replay_artifact()` surface performs the one allowed
read-only replay needed to prepare a future S3 input. It does not search,
verify, or promote a representation.

## Frozen authority and input contract

The repository's Structural Observation Layer v1 is frozen at commit
`0a2905b` and exposed by `symbolic_compactification.observations`. S3 accepts
only an immutable `RPSSOLArtifactV1` JSON envelope containing:

- the authority tuple `structural-observation-layer-v1@0a2905b`;
- the exact SHA-256 manifest of all SOL source files and its parser, structure,
  budget, model, and frozen LGG scoring dependencies at that commit;
- the exact proposer-view SHA-256 and every public member SHA-256;
- one ordinary SOL `ObservationBundle`.

The caller must also provide the envelope's full SHA-256. A mismatch,
malformed provenance, case drift, evaluator/gold field, interpreted target
name, invalid node hash, or invalid epistemic class produces explicit
`UNAVAILABLE` and no S3 run. A well-formed bundle with no relation whose every
node occurs inside a public source member produces `NO_ELIGIBLE_SOL` and no
S3 run. The loader also hashes every local frozen-authority file and refuses
projection if even one byte has drifted. The replay attestation binds the
canonical bundle hash, public case hash, and authority-manifest hash.

In particular, the historical Guo
`research/preprocessing_integration/guo/RELATION_GRAPH.json` is an aggregate
diagnostic without source-bound edge rows and Guo remains sealed; it is not an
S3 input. This implementation creates no scientific replay artifacts. Until a
fresh case-bound read-only replay is produced from the byte-exact frozen
authority, scientific S3 is explicitly unavailable rather than reconstructed
from that historical summary.

## Read-only replay builder

The builder accepts a previously loaded `PublicCase`, never a package path. It
first validates the local frozen-authority source manifest, all in-memory
member hashes, the public access-path ledger, and each member under the case's
exact namespace. It never reopens a member, proposer view, assumption file, or
catalog and rejects any contaminated public ledger or evaluator/reference/
verification path.

`RPSPublicMemberContainerV1` orders members by exact public id and embeds every
unchanged member string as the argument of a deterministic opaque unary
wrapper. The wrapper Add is observation-only: it is never a scientific
expression, verifier input, source member, or package-member hash. Its
construction, member order/hashes, wrappers, and full text hash are included
in the replay attestation.

`RPSSOLReplayPolicyV1` is not caller-tunable:

- backend preset: `relations`;
- requested backends: `sympy`, `matchpy`, `lgg`, `egglog`;
- per-backend timeout: 12 seconds;
- context key: `rps_replay_policy`.

The artifact records requested and actually run backends, complete backend
statuses, backend versions, Python/SymPy/optional-backend versions, and host
system identifiers needed to recreate the environment. Projection requires
the complete frozen status-key set and exact agreement between each replay
backend version and its corresponding environment version. It is staged in the
destination directory, fsynced, and passed through `load_sol_projection()`
before no-overwrite atomic hard-link publication. The containing directory is
fsynced after link creation and again after staging cleanup. `NO_ELIGIBLE_SOL`
is a valid replay artifact but still prevents S3 search; `UNAVAILABLE` is
never published. The returned `SOLReplayResult` reports the final artifact
SHA-256. Existing outputs are never overwritten.

The replay attestation is not a signature and does not prove that execution
occurred. It makes the inputs, authority bytes, environment, policy, bundle,
and output replayable and hash-auditable. Reproduction is the audit.

## Frozen routing policy

`RPSSOLPriorityPolicyV1` assigns fixed integer units to legal actions. It can
prefer member grouping, latent reuse, substitution, derivative, Newton,
recurrence, permutation, basis, composition, and reconstruction actions only
when a source-bound eligible relation supports the corresponding action. A
derivative edge may prioritize a repeated-node hypothesis only when the
repeated node label is among that edge's public node symbols. This is a search
heuristic, never a proof or a multiplicity fact.

Ordering is:

1. descending cumulative SOL units;
2. frozen M2 complexity;
3. depth;
4. canonical state hash.

Every used relation records the source artifact hash, relation id/type,
rule id, legal-action hash, affected child-state hash, and integer
contribution. Every legal child considered gets a public routing record,
including zero-contribution children. No private reasoning is recorded.

S3 calls the same `extract_candidate_pool()` and `expand_state()` as S0/S1,
uses the same `SearchPolicy`, grammar ablations, and fixed state budgets, and
records the unchanged legal-child hashes in each expansion. It uses zero LLM
tokens and no verifier outcomes for ordering.

## Anchoring control

Candidate/descriptive SOL relations are allowed to influence priority without
being treated as identities. A synthetic misleading recurrence relation is
therefore tested explicitly: it routes recurrence ahead of an unsupported
derivative action. This is the intended anchoring control and a reason S3 must
be compared with S2 under matched state budgets rather than presumed helpful.
