# E7 — Error Semantics / Fail-Closed UX Handoff

## Outcome

PASS within E7 scope. The workspace API and CLI now expose all six documented
public results without treating a proof gap, unsupported hypothesis, parse
error, or assumption gate as success.

## Integrated changes

- Added public `ASSUMPTION_REQUIRED` support across the Python API, package
  exports, persisted result validation, report semantics, CLI explanation, and
  non-success exit mapping.
- Classified omission of a researcher-declared symbol from
  `hypothesis.assumptions_used` as `ASSUMPTION_REQUIRED` with stable code
  `DECLARED_ASSUMPTIONS_OMITTED`; the tool does not repair the omission.
- Kept undeclared expression syntax as `PARSE_FAILURE` and unsupported
  hypothesis language as `COMPILE_FAILURE`.
- Registered the fast `release_critical` pytest marker and added its explicit
  11-test release gate.
- Preserved the historical finite-Laurent-without-remainder regression as an
  explicit release-critical invariant.
- Added the detailed audit at
  `engineering/release_v0_1/SEMANTIC_AUDIT.md`.

No verifier route, simplification rule, assumption inference, or frozen
scientific evidence was changed.

## Verification

Python environment: CPython 3.12.13, editable install with the core dev extra.

```bash
.venv/bin/python -m pytest -q -m release_critical
# 11 passed in 5.88s

.venv/bin/python -m pytest -q \
  tests/test_release_security.py \
  tests/test_run_provenance.py \
  tests/test_research_api.py \
  tests/test_research_cli.py \
  tests/test_workspace.py \
  tests/test_release_demos.py \
  tests/test_cl_remainder.py \
  tests/test_cl_engine.py \
  tests/test_rc_schema.py \
  tests/test_session.py
# 103 passed in 27.90s
```

The release gate and researcher API/CLI/workspace suites contain 47 passing
tests in total at this commit.

## Coordinator checks

- Cherry-pick the E7 commit after review.
- Rerun `pytest -q -m release_critical` at the final integrated head.
- Retain the exact result/exit mapping documented in the semantic audit.

## Blockers

None.
