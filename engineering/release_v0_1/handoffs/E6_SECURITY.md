# E6 — Security / Secret Audit Handoff

## Outcome

`PASS` for the bounded release path implemented on `work/eng-security`.

No release blocker was found inside E6 ownership. Integration must apply the
shared helper to any new E3/E4 free-form error or report metadata; otherwise
the security category must return to `PARTIAL`.

## Changes

- Added `src/symbolic_compactification/security.py` with:
  - `redact_text(str) -> str`
  - `redact_public_data(JSON-like) -> JSON-like`
  - `REDACTED`
- Consolidated E5 warning/dependency redaction onto the production helper.
- Re-sanitized provenance immediately before persistence.
- Rejected credential-shaped provenance map keys.
- Sanitized certified-report metadata and summary fields without touching the
  certified formula.
- Sanitized optional verifier assumption evidence before session persistence.
- Added `tests/test_release_security.py` covering dotenv non-ingestion,
  credential headers, sensitive mappings, URLs, private keys, JWTs, raw object
  representations, provenance re-sanitization, report output, and verifier
  evidence.
- Added `engineering/release_v0_1/SECURITY.md` with threat boundary, scan
  evidence, limitations, and integration rules.

## Focused verification

```text
70 passed in 41.09s
```

Covered suites:

- `tests/test_release_security.py`
- `tests/test_run_provenance.py`
- `tests/test_verifier.py`
- `tests/test_reporting.py`
- `tests/test_reporting_delta.py`

`git diff --check` passed.

## Audit findings

- No tracked `.env`, log, crash, or dump artifact.
- No process-environment/dotenv/request-header collection in the production
  package.
- Credential-pattern matches are confined to explicit synthetic test fixtures.
- Default CLI failures expose stable error codes rather than raw exception
  text.
- Historical/optional research transport code was audited for tracked literal
  secrets only; it is outside the v0.1 release surface.

## Integration note

E3/E4 should import from `symbolic_compactification.security`; do not create a
second redactor. Persist only allow-listed structured fields. Do not sanitize
the certified expression itself.
