# E4 — Stable Python API Handoff

## Scope

Engineering-only Python API for the external researcher workspace. No CLI,
proposer, scientific semantics, or frozen research evidence was changed.

## Public API

The package root now exports:

```python
from symbolic_compactification import (
    GeneratedReport,
    HypothesisVerificationResult,
    ObligationVerification,
    generate_report,
    load_workspace,
    verify_hypothesis,
)
```

Canonical use:

```python
workspace = load_workspace("my_workspace")
verification = verify_hypothesis(workspace)
report = generate_report(workspace, verification.run_id)

print(verification.result)  # ZERO | NONZERO | UNKNOWN | ...
print(report.path)
```

`verify_hypothesis(...)` returns a frozen `HypothesisVerificationResult`.
Its public `to_dict()` is JSON-native and exposes the aggregate result,
per-obligation exact verifier results, runtime, bounded warnings, stable error
code, and run artifact paths. `result` and the compatibility property
`verdict` have the same value.

`generate_report(...)` accepts a run id or the returned verification object.
It returns a frozen `GeneratedReport` with `run_id`, `result`, `path`, and
`text`. It returns the existing report or regenerates a missing report from
the bounded persisted run records without rereading scientific source files.

## Compiler boundary

The v0.1 compiler intentionally supports only:

- `hypothesis_type: "equivalence"`
- at least one proof obligation
- `relation: "equivalent"`
- left/right members already validated and grounded by `load_workspace(...)`

Unsupported hypothesis types, relations, or an empty obligation list produce
`COMPILE_FAILURE`. Workspace/YAML/JSON/expression failures produce
`PARSE_FAILURE`. Nothing is silently normalized beyond the already documented
simple equivalence form in `workspace.py`.

Every supported obligation calls the existing `verify_equivalent(...)` with
the workspace's declared symbols and functions. Aggregate precedence is:

1. any exact `NONZERO` -> `NONZERO`;
2. otherwise any non-`ZERO` -> `UNKNOWN`;
3. only all exact `ZERO` -> `ZERO`.

## Artifacts and safety

Every attempt against an existing, safe workspace directory creates:

```text
workspace/runs/<run_id>/
├── provenance.json
├── result.json
└── REPORT.md
```

The run directory is exclusive and all three files use atomic writes. The API
records source-byte hashes, versions, verifier route, runtime, warnings, and
exact obligation details. Parse/compile reports persist stable codes rather
than raw failure detail, preventing source text or credentials from being
copied into artifacts. The API never reads environment variables or `.env`
files and never writes researcher source files. Unsafe `runs/` symlinks are
rejected.

## Tests

Python 3.12 fresh virtual environment:

```text
python -m pytest -q \
  tests/test_research_api.py \
  tests/test_workspace.py \
  tests/test_run_provenance.py

35 passed in 12.97s
```

Focused E4 coverage includes:

- ZERO, NONZERO with exact counterexample, and intentional UNKNOWN;
- PARSE_FAILURE and COMPILE_FAILURE provenance/report artifacts;
- all-ZERO and mixed UNKNOWN/NONZERO multi-obligation aggregation;
- source bytes, mtimes, and modes unchanged;
- secret-like malformed input absent from generated artifacts;
- report return and regeneration;
- package-root public exports.

## Integration notes

- New implementation: `src/symbolic_compactification/research_api.py`
- New focused tests: `tests/test_research_api.py`
- Public exports: `src/symbolic_compactification/__init__.py`
- `cli.py` was not edited.
- There is intentionally no proposer API in this alpha surface.
