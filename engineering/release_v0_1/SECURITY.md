# Security and secret-handling boundary

Status: **PASS for the bounded v0.1 release path**, subject to the integration
rule below.

This audit covers the installed `symbolic_compactification` package, researcher
run provenance, certified-form report rendering, default CLI failures, and
tracked release artifacts. It does not certify historical research programs or
optional third-party proposer transports.

## Release rule

The release path must never pass process environments, `.env` contents, HTTP
request objects, authentication headers, client objects, or raw exceptions to
a persisted run record or user report. Free-form warning/report metadata must
cross `symbolic_compactification.security.redact_text` or
`redact_public_data` immediately before rendering or persistence.

This sanitizer is defence in depth, not a general data-loss-prevention system.
The primary control remains a small allow-listed record schema.

## Implemented controls

- The package does not load `.env`, enumerate the environment, or read request
  headers. Researcher provenance records collect a fixed schema only.
- Input expressions, notes, assumptions, references, and hypotheses are
  represented by SHA-256 hashes in provenance; their contents are not copied
  into `provenance.json`.
- Warning text is bounded to 2,048 characters, redacted before truncation, and
  redacted again immediately before the atomic write.
- Credential-shaped run ids, verifier routes, logical file labels, and
  dependency names fail closed with `PROVENANCE_UNSAFE_VALUE` or their existing
  field-specific validation error.
- Dependency versions, warning strings, report metadata, and nested public
  metadata redact common API tokens, authorization/cookie headers, sensitive
  assignments, URL user-info passwords, JWT-shaped values, and private-key
  blocks.
- Verifier assumption evidence is sanitized before it can enter a session
  record. This changes only recorded metadata; adjudication semantics are
  unchanged.
- Unknown objects are represented by type name rather than `str`/`repr`,
  preventing request/client/exception representations from exposing embedded
  credentials.
- Certified mathematical expressions are not modified by the redactor. They
  pass through the strict expression parser and remain the exact scientific
  artifact.
- Existing run directories are never overwritten; provenance is written by an
  fsynced temporary file and atomic rename.
- `.env` and `.env.*` are ignored by Git. No `.env`, log, crash, or dump
  artifact is tracked at audit time.
- Default CLI error handling emits stable error codes, not exception messages
  or tracebacks. Any developer-only debug mode added during integration must
  remain opt-in and must not persist its traceback.

## Audit evidence

Focused Python 3.12 regression command:

```bash
PYTHONPATH=src /private/tmp/ssc-alpha-main-venv/bin/python -m pytest -q \
  tests/test_release_security.py tests/test_run_provenance.py \
  tests/test_verifier.py tests/test_reporting.py tests/test_reporting_delta.py
```

Result: `70 passed`.

The tracked-file credential-pattern scan found matches only in synthetic
redaction/transport test fixtures:

- `tests/test_llm_abstraction.py`
- `tests/test_representation_llm.py`
- `tests/test_rps_llm_guided.py`
- `tests/test_run_provenance.py`
- `tests/test_release_security.py` after this change is tracked

Each uses explicit test doubles or values labelled synthetic; none is accepted
by a live service. No matching credential literal was found in production
package code or release documentation.

The production source scan found no `os.environ`, `os.getenv`, dotenv loader,
request-header read, or auth-header collection in `src/symbolic_compactification`.
Backend exceptions in the observation layer record exception type only. The
verifier's unexpected-exception paths record stable codes and fail closed.

## Residual risks and operator guidance

- Researcher source files are intentional user content. They are hashed for
  provenance and are not copied into provenance, but a command explicitly
  designed to display an expression or note will display that selected file.
  Researchers should not store credentials in scientific inputs.
- `--debug`, if provided by the integrated CLI, is for local developer use.
  Its output may reveal local paths or source fragments and must never be
  redirected automatically into a run artifact.
- The optional proposer remains experimental. A future transport must retain
  its API key inside the client boundary, persist typed decisions only, and run
  the same release security tests before being enabled.
- Secret scanners use recognizable patterns and cannot identify every possible
  high-entropy value. Do not weaken the allow-listed provenance/report schema
  on the assumption that redaction will catch arbitrary secrets.

## Integration acceptance

E3/E4 report and exception payloads pass this audit only if all newly added
free-form metadata is sanitized with the shared production helper and default
errors remain stable-code-only. Scientific expressions must remain exact and
must not be routed through generic redaction.
