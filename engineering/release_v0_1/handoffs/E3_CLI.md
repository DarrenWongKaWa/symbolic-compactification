# E3 — Researcher CLI handoff

## Scope

Implemented the minimal researcher-facing CLI over the frozen workspace and
Python verification APIs. No proposer, scientific evaluator, parser
extension, verification semantic, or frozen research artifact was changed.

## Command surface

The external workflow is now:

```bash
symbolic-compactification init <workspace>
symbolic-compactification inspect <workspace>
symbolic-compactification verify <workspace>
symbolic-compactification report <workspace> [--run RUN_ID]
```

- `init` calls `initialize_workspace(...)` and inherits its strict
  no-overwrite policy.
- `inspect` auto-detects a directory, loads the workspace read-only, and shows
  project metadata, declared assumptions, normalized hypothesis data,
  expression SHA-256 values/text summaries, parsed expressions, and structural
  summaries.
- `verify` calls `verify_hypothesis(...)`, prints the aggregate and
  per-obligation result, and points to the persisted provenance/report.
- `report` calls `generate_report(...)`. With no `--run`, it selects the
  latest valid research-API run by recorded UTC timestamp, using the immutable
  provenance-file mtime only as a same-second tie breaker. Symlinks, malformed
  metadata, legacy session runs, unsafe names, and unsupported schemas are
  ignored during automatic selection.

Every new command supports `--json`. `--debug` works globally or after any
subcommand. Default failures print a stable code only and never expose a
traceback or exception text; debug mode may re-raise for developers.

## Exit contract

Workspace verification maps results as follows:

| Result | Exit |
|---|---:|
| `ZERO` | 0 |
| `NONZERO` | 2 |
| `UNKNOWN` | 3 |
| `PARSE_FAILURE` | 4 |
| `COMPILE_FAILURE` | 4 |

`UNKNOWN` output explicitly says that it is not success and cannot promote
scientific state. Parse and compile results include their stable underlying
`error_code` while retaining the generated provenance record.

## Backward compatibility

All historical commands remain registered. In particular, these forms are
unchanged and covered by regression tests:

```bash
symbolic-compactification inspect EXPR.txt --symbols symbols.json
symbolic-compactification verify \
  --current A.txt --candidate B.txt --symbols symbols.json
symbolic-compactification init-session ...
symbolic-compactification step ...
symbolic-compactification summary ...
symbolic-compactification finalize ...
symbolic-compactification observe ...
symbolic-compactification backends ...
```

Mixing workspace verification with legacy file flags fails closed as
`VERIFY_MODES_MIXED`. Omitting both a workspace and the complete legacy flag
set fails as `VERIFY_INPUTS_REQUIRED`.

## Safety

- Workspace inspection is read-only.
- Verification writes only beneath `workspace/runs/<run_id>/`.
- Focused tests compare researcher source bytes, mtimes, and modes before and
  after inspect/verify.
- CLI JSON and human-readable free-form values pass through the shared
  `security.redact_public_data(...)` / `security.redact_text(...)` boundary.
- Default unexpected exceptions collapse to `INTERNAL_ERROR`; raw exception
  text, credentials, and stack traces are not rendered.
- Latest-run selection does not follow run or artifact symlinks and validates
  bounded `result.json` / `provenance.json` metadata before selection.

## Tests

Focused E3 coverage:

```text
PYTHONPATH=src /private/tmp/ssc-e4-venv/bin/python -m pytest -q \
  tests/test_research_cli.py \
  tests/test_release_security.py \
  tests/test_requested_proposer_mode.py \
  tests/test_consolidation_contracts.py::test_cli_json_mode_is_single_machine_readable_object

41 passed in 8.52s
```

Affected researcher/API/security/legacy CLI group:

```text
72 passed in 41.59s
```

Historical reporting/session compatibility group:

```text
48 passed in 29.80s
```

A manual Python 3.12 replay of `init -> inspect -> verify -> report` completed
with `ZERO`, a provenance record, and a human-readable report. The coordinator
still owns the single release-wide full-suite run and clean-room replay.

## Blockers

None in the E3 slice.

