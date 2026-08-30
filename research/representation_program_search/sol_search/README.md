# S3 frozen-SOL-conditioned search

This package adds a deterministic priority layer over the exact M2 legal
frontier. It does not run, modify, or retune SOL, create candidate programs,
call the verifier, or consume evaluator artifacts.

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
