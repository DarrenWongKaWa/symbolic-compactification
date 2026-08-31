# E1 Handoff — Installation and Packaging

## Scope

Packaging and clean-install behavior only. No scientific semantics, frozen
research evidence, workspace implementation, Python API, or user-facing CLI
logic was changed.

## Changes

- Added the bounded runtime dependency `PyYAML>=6,<7` because the alpha
  researcher workspace declares YAML project and assumption files.
- Added installed-distribution contract tests for version consistency, YAML
  dependency bounds, and both supported console entry points.
- Added a reproducible installation guide covering local, editable, and wheel
  installs under CPython 3.12.

## Verification

Environment: macOS arm64, CPython 3.12.13, clean `venv` environments.

```text
editable install: PASS
symbolic-compactification entry point: PASS
ssc entry point: PASS
focused tests: 36 passed in 49.97s
wheel build: PASS
isolated wheel install: PASS
installed exact-verifier smoke: ZERO
wheel SHA-256: 56421c53a279ce1daa743c8692612f17969d339c9f6f3d615910bd8931e98aef
```

Focused test command:

```bash
python -m pytest -q \
  tests/test_packaging_contract.py \
  tests/test_verifier.py \
  tests/test_reporting.py
```

## Integration notes

- The inherited package, engine, and protocol versions all remain `0.3.0`.
  Version/tag preparation for `research-preview-v0.1.0-alpha` belongs at the
  final alpha-readiness gate; changing engine/protocol semantics was outside
  this lane.
- The repository has no release publication step in this handoff. A normal
  local wheel was built and installed successfully.
- The final coordinator-owned clean-room replay must rebuild and re-hash the
  integrated artifact after all workspace/CLI/API changes land.

## Packaging readiness

`PASS` for the Python 3.12 local-checkout and wheel-install requirements.
No E1 blocker remains.
