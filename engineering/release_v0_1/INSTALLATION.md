# Installation — Research Preview v0.1

## Supported release environment

The release gate uses CPython 3.12. The package metadata currently permits
Python 3.10 and newer, but only Python 3.12 is part of this alpha clean-room
contract. A local checkout is required until a release artifact is published.

## Install from a checkout

From the repository root:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/symbolic-compactification --version
```

The shorter `ssc` command is installed as an equivalent entry point:

```bash
.venv/bin/ssc --help
```

The runtime installation includes bounded dependencies for exact symbolic
work (`sympy>=1.12,<2`) and the researcher workspace format
(`PyYAML>=6,<7`). Optional observation backends are not installed by default.

## Editable developer install

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest -q tests/test_packaging_contract.py
```

Optional backends remain explicit extras:

```bash
.venv/bin/python -m pip install -e '.[dev,observations]'
.venv/bin/python -m pip install -e '.[dev,egraph]'
```

They are not required by the release-critical verification workflow.

## Build and install the wheel artifact

This checks the same install path intended for a release artifact:

```bash
python3.12 -m venv .venv-build
.venv-build/bin/python -m pip wheel --no-deps --wheel-dir dist .

python3.12 -m venv .venv-wheel
.venv-wheel/bin/python -m pip install dist/symbolic_compactification-*.whl
.venv-wheel/bin/symbolic-compactification --help
.venv-wheel/bin/ssc --help
```

Do not infer scientific readiness from successful installation. Installation
only establishes that the packaged code and CLI can be loaded. The verifier's
`ZERO`, `NONZERO`, and `UNKNOWN` semantics and the final alpha decision are
separate release gates.

## Reproduced installation check

On 2026-08-31 the installation lane was replayed on macOS arm64 using CPython
3.12.13 and pip 25.0.1 in newly created virtual environments:

- editable install with development dependencies: PASS;
- package/metadata version consistency: PASS on the earlier integration
  baseline. The release source now declares `0.1.0-alpha`, canonically
  installed as `0.1.0a0`; final confirmation belongs to clean-room replay;
- both console entry points: PASS;
- 36 focused packaging, verifier, and reporting tests: PASS;
- wheel build and isolated wheel install: PASS;
- installed runtime versions: SymPy 1.14.0 and PyYAML 6.0.3;
- exact installed-package smoke check: `ZERO`;
- wheel SHA-256 for that local build:
  `56421c53a279ce1daa743c8692612f17969d339c9f6f3d615910bd8931e98aef`.

The wheel hash is build-instance evidence, not a published release hash. The
final clean-room replay must build a fresh artifact and record its own hash.

`--version` distinguishes the alpha release identity from the unchanged
deterministic engine and agent-protocol identities (`0.3.0` each).

## Troubleshooting

- `python3.12: command not found`: install CPython 3.12, then recreate the
  virtual environment.
- CLI command missing: invoke `.venv/bin/python -m pip show
  symbolic-compactification` and confirm the command is run from the same
  virtual environment.
- dependency resolution fails: retain the declared upper bounds; do not
  bypass them with `--no-deps` for a runnable install.
- optional backend unavailable: install only the corresponding extra. Backend
  absence must not change the core verifier result into success.
