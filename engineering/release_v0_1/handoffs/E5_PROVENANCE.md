# E5 — Provenance / Run Records Handoff

## Scope

Engineering-only production support for a bounded researcher-workspace run
record. No CLI or workspace loader was integrated, and no frozen research
artifact or scientific/verifier semantic was changed.

## Production API

`symbolic_compactification.provenance` provides:

- `sha256_file(path)` — SHA-256 of exact file bytes; read-only and chunked.
- `hash_named_files({logical_label: path})` — deterministic key-sorted hashes
  without recording absolute host paths.
- `dependency_versions(...)` — installed versions from an explicit allow-list;
  it does not inventory the environment.
- `build_run_record(...)` — fixed `ResearchRunProvenanceV1` JSON schema.
- `write_run_record(runs_directory, record)` — exclusive run-directory
  creation and fsynced-temp/atomic-rename JSON persistence.
- `record_research_run(...)` — read-only hash/build/write convenience API.

The persisted path is:

```text
<caller runs_directory>/<run_id>/provenance.json
```

Existing run ids fail with `PROVENANCE_RUN_ALREADY_EXISTS`; no record is
overwritten.

## Recorded fields

The schema records exactly:

- timestamp and run id;
- package, engine, and agent-protocol versions;
- git commit (including the existing `-dirty` convention);
- Python implementation/version and explicit dependency versions;
- named input and expression SHA-256 hashes;
- hypothesis and assumptions SHA-256 hashes (or explicit `null` when absent);
- verifier route, result, runtime, and warnings.

Supported result values are `ZERO`, `NONZERO`, `UNKNOWN`, `PARSE_FAILURE`,
`COMPILE_FAILURE`, and `ASSUMPTION_REQUIRED`.

## Secret boundary

The production code does not read process environment variables, `.env`
files, API/request objects, headers, logging configuration, or a package
inventory. It accepts no arbitrary metadata. The only free-form field is a
bounded warning list; common API-key, authorization, bearer, GitHub, Slack,
AWS, and Google credential forms are redacted before persistence. Direct
records with extra fields are rejected.

The older generic sanitizer was inspected but remains under
`research/llm_abstraction`; production code does **not** import frozen research
modules. If E6 introduces an equivalent production sanitizer during
integration, E5's private redaction helper can be replaced with that helper
without changing this schema.

## Cache-key audit

- The new module has no cache and no cache key.
- File provenance keys are SHA-256 over exact bytes, never filenames, sizes,
  operation counts, or partial content.
- Hash maps are serialized with sorted labels; JSON is emitted with sorted
  keys, so fixed inputs and injected clock/version evidence produce identical
  bytes.
- Existing production caches are limited to parser/adapter-local symbol lookup
  keyed by exact symbol name. Persistent scientific caches found by repository
  search live under frozen research code and were not changed.
- Existing proposal/packet content identifiers use canonical JSON plus SHA-256;
  this work did not alter them.

## Tests

Python 3.12 targeted command:

```bash
.venv/bin/python -m pytest -q \
  tests/test_run_provenance.py \
  tests/test_provenance.py \
  tests/test_namespace_rules.py \
  tests/test_reporting.py \
  tests/test_reporting_delta.py
```

Result: `59 passed in 20.54s`.

The 14 new focused tests cover exact/deterministic hashes, required field
inventory, byte-identical serialization, caller-selected run roots,
atomic/non-overwrite behavior, read-only source handling, all public result
states, invalid-state fail-closed behavior, secret redaction, and rejection of
arbitrary fields.

## Integration notes

- Public names are exported from `symbolic_compactification.__init__`.
- E3/E4 can call `record_research_run` after adjudication, or use
  `build_run_record` + `write_run_record` when they already own the hashes.
- The workspace-facing integration should supply logical relative labels, not
  absolute paths.
- Provenance does not imply certification; `result` must come from the caller's
  actual verifier/compiler outcome.

## Blockers

None within E5 scope.
