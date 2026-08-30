# M8 / E follow-up handoff — frozen SOL public-case replay

## Implementation

- Branch: `work/rps-sol-search`
- Implementation commit: `34ff7e319a1730edaf988d4c6519cded8c5c2b01`
- Scope: a read-only replay builder and synthetic controls only.
- No scientific DEV/TEST case, Guo case, historical benchmark case, or hidden
  reference program was replayed.
- No SOL, parser, verifier, package manifest, or benchmark manifest source was
  modified.

## Public boundary and frozen authority

`build_sol_replay_artifact()` accepts only an already loaded `PublicCase`. It
does not accept a case-package path and never reopens proposer, assumption,
catalog, member, evaluator, reference, or verification files. Before importing
the callable SOL API it hashes every local source dependency in the hard-coded
authority manifest for frozen commit `0a2905b`. Any missing or changed byte
fails before observation and before output creation.

Each in-memory member is re-hashed and parsed under the exact public symbol and
function namespace. A contaminated public access ledger, member drift, parser
failure, wrapper collision, forbidden output path, or existing output fails
closed.

## Observation-only structural container

`RPSPublicMemberContainerV1` sorts public member ids and embeds each unchanged
member string as the argument of an opaque deterministic unary wrapper. The
surrounding Add is only a carrier for the frozen observation API. It never
enters a verifier, scientific expression, source member, or package-member
hash. The full container hash, member order and hashes, wrapper map, and exact
construction name are bound into the replay attestation and recomputed during
projection.

## Frozen replay policy and provenance

`RPSSOLReplayPolicyV1` is fixed to the existing `relations` preset, requested
backends `sympy/matchpy/lgg/egglog`, a 12-second per-backend timeout, and the
single public context key `rps_replay_policy`. The builder calls only the
existing frozen `symbolic_compactification.observations.api.observe` surface.

`RPSSOLArtifactV1` records:

- the complete authority file/hash manifest and its canonical hash;
- exact proposer-view, case, and source-member bindings;
- the canonical observation-bundle hash;
- the full replay policy and structural-container description;
- requested and actually run backends, the complete backend-status map, and
  backend versions;
- Python, SymPy, optional-backend, implementation, machine, and operating
  system versions needed for reproduction.

Projection requires exact top-level and nested attestation schemas, exact
policy/container recomputation, the complete frozen backend-status key set,
backend/version/status cross-field consistency, and exact environment keys.
Extra or changed fields produce `UNAVAILABLE` even if the caller supplies the
new artifact hash.

These fields are replay/hash evidence, not a signature or proof that execution
occurred. Reproduction against the recorded authority bytes is the audit.

## Atomic publication and search gate

The artifact is serialized deterministically, staged in the destination
directory, file-fsynced, and immediately loaded through
`load_sol_projection()` using its final SHA-256. An `UNAVAILABLE` projection
is never published. A validated artifact is published by a same-directory
hard link that refuses overwrites; the directory is fsynced after link creation
and again after removal of the staging name. Failure after publication removes
only that newly linked destination and performs a best-effort directory fsync.

`NO_ELIGIBLE_SOL` may be preserved as a valid diagnostic replay, but S3 still
does not run. A scientific S3 comparison remains `UNAVAILABLE` until an
admitted fresh public case is explicitly replayed, reviewed, and frozen with
its artifact hash. The sealed aggregate Guo graph remains ineligible.

## Synthetic controls

The tests use only a fabricated three-member public case. They cover:

- two actual safe synthetic frozen-API replays with byte-identical artifacts;
- immediate projection reload and final artifact SHA binding;
- exact unchanged member-byte embedding and deterministic container hashing;
- no verifier call and no reference/verification file read;
- authority drift before SOL invocation;
- access-ledger, member-hash, parser, wrapper/output, and existing-file gates;
- cleanup when immediate projection fails;
- file and directory fsync observation plus atomic no-overwrite publication;
- immutable replay policy;
- exact policy/container/backend/environment attestation validation, including
  a tampered extra field;
- compatibility with the same M2 legal frontier and S3 matched-budget surface.

The synthetic replay is an integration/control result only. It is not a
scientific representation-search result and establishes no S3 advantage.

## Verification

- Focused replay + S3 + M2 controls: `46 passed in 7.02s`
- Full repository suite with bytecode writes disabled:
  `1797 passed in 210.80s (0:03:30)`

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 \
  /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m pytest -q
```
