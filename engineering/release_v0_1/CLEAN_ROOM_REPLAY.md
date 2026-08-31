# Clean-room replay — Research Preview v0.1

## Decision

`ALPHA_READY` for the clean-room reproducibility lane.

This decision is scoped to installation, the release-critical gate, the three
committed CLI demos, provenance, source immutability, secret-canary handling,
and an isolated wheel install. It is not the coordinator's final release
decision and does not reopen or reinterpret any scientific experiment.

## Frozen input

- Commit under test:
  `eb02da4ee06f9d8d523b82a526dbdb317050588c`
- Checkout mode: detached HEAD in a new `git clone --no-local --no-checkout`
- Host: macOS 26.4 (build 25E246), arm64
- Python: CPython 3.12.13
- pip: 25.0.1
- Replay date: 2026-08-31

The validation checkout was clean before installation and remained clean after
tests, demo execution, and wheel construction. Pytest created only its ignored
`.pytest_cache`; `git status --porcelain --untracked-files=all`, the worktree
diff, and the index diff were empty.

## Ordinary non-editable install

The ordinary install was performed into a new virtual environment from outside
the source checkout:

```bash
python3.12 -m venv "$CLEAN_ROOT/env-normal"
"$CLEAN_ROOT/env-normal/bin/python" -m pip install "$CLEAN_ROOT/repo[dev]"
"$CLEAN_ROOT/env-normal/bin/python" -m pip check
"$CLEAN_ROOT/env-normal/bin/symbolic-compactification" --version
"$CLEAN_ROOT/env-normal/bin/ssc" --help
```

Results:

- non-editable package installation: PASS
- installed package: `symbolic-compactification 0.1.0a0`
- user-facing version: `0.1.0-alpha`
- installed runtime dependencies: PyYAML 6.0.3 and SymPy 1.14.0
- `pip check`: `No broken requirements found.`
- both console entry points: PASS
- import origin: the new environment's `site-packages`, not the checkout

## Release-critical gate

Exact command:

```bash
"$CLEAN_ROOT/env-normal/bin/python" -m pytest -q -m release_critical
```

Result:

```text
............                                                             [100%]
12 passed in 8.15s
```

The full suite was not rerun in this lane. That follows the program's explicit
single-full-suite policy; the integration result and historical-only triage are
recorded separately in `FULL_SUITE_RESULT.md`.

## Installed-CLI demo replay

Each committed demo workspace was copied to a new path outside the checkout.
For every copy, the installed console script ran this sequence:

```bash
symbolic-compactification inspect "$WORKSPACE"
symbolic-compactification verify "$WORKSPACE"
symbolic-compactification report "$WORKSPACE"
```

All commands used the non-editable installation. The values below are one
clean-room measurement; wall time and maximum RSS came from macOS
`/usr/bin/time -l`.

| Demo | Result | Inspect exit | Verify exit | Report exit | Inspect wall / RSS | Verify wall / RSS | Report wall / RSS |
|---|---:|---:|---:|---:|---:|---:|---:|
| A — exact factorization | `ZERO` | 0 | 0 | 0 | 0.23 s / 63.39 MiB | 0.85 s / 64.23 MiB | 0.23 s / 63.27 MiB |
| B — grounded Newton DD | `ZERO` | 0 | 0 | 0 | 0.26 s / 63.75 MiB | 3.21 s / 65.78 MiB | 0.21 s / 63.64 MiB |
| C — intentional proof gap | `UNKNOWN` | 0 | 3 | 0 | 0.23 s / 63.53 MiB | 3.84 s / 67.00 MiB | 0.22 s / 63.38 MiB |

Installed CLI startup (`--version`) measured 0.22 s wall time and 63.31 MiB
maximum RSS. The verifier-recorded runtimes were 0.617239 s, 2.977561 s, and
3.604474 s for A, B, and C respectively.

Demo B certified all four declared obligations. Demo C displayed the required
fail-closed explanation: `UNKNOWN` is not success and does not permit
scientific promotion. Its exit status was exactly 3.

## Provenance audit

Every run contained all required fields:

- timestamp and run id
- package, engine, and protocol versions
- exact source commit and Python version
- direct dependency versions
- input and expression hashes
- hypothesis and assumptions hashes
- verifier route, result, runtime, and warnings

All three records contained the bare, lowercase, exact 40-hex revision
`eb02da4ee06f9d8d523b82a526dbdb317050588c`, not `unknown`, a short SHA, or a
dirty suffix. All recorded file hashes were recomputed from the copied source
bytes and matched: 7 entries for Demo A, 13 for Demo B, and 7 for Demo C. The
dependency map was exactly `pyyaml: 6.0.3` and `sympy: 1.14.0`.

Generated artifact hashes:

| Demo | `provenance.json` SHA-256 | `REPORT.md` SHA-256 |
|---|---|---|
| A | `279381f2408747769741e0a205cd0e03aefc8b1845959f3bea3bec3e0d165a95` | `87540573e102019d99a6778ff0d38431434f31dcef5aec8f5daf8b646d40ab55` |
| B | `83c9bd80e3df49ffa846a9270533a90862638b9e121001c88db7293cc5e6da51` | `0c39fddb129016119b20223ea8e00e042c0c23ed6c7beda6c84631bd138865e2` |
| C | `98ddcaf83cf35ea8bf74a118f0d78dc18a1efd9d0187bd90b6d7d4907bc335b7` | `b5086828b327a5347ff40666c9aa6c5c78f45f61afbaa8763c0d255e09a86278` |

These artifact hashes identify this replay instance; timestamps and run ids
make them intentionally different from another valid replay.

## User-source immutability

Before `inspect`, `verify`, and `report`, every non-`runs/` file in each copied
workspace was hashed byte-for-byte. The same manifest was produced afterward.

| Demo | Source-manifest SHA-256 | Before/after |
|---|---|---|
| A | `f2ea07e15ff48fa658d0f024e177ba549f05f198062811e51b7b551dffb1a59b` | identical |
| B | `43736fd1d3c48064d88036eaa152742bbefe9ef650f670bb55f456d521e9d5d7` | identical |
| C | `51f7553450c37f6784a9d861b59b299434c3b197fc48bc7de7c84a0de710cc2d` | identical |

Only new run artifacts appeared under each workspace's `runs/<run_id>/`.

## Secret-canary audit

Three synthetic secret values were supplied only through environment variables
during the CLI replay: an API-key-shaped value, an authorization-header-shaped
value, and a generic private-token value. Their values are intentionally not
persisted in this report. Their SHA-256 digests were:

- `a65d2c57873be545f468817f23f8b840813e3d566585b7ee06f81616ca71a1a9`
- `6d8e8fb1c481cf6b078d749d4e4e392c716e6e7f45a92d4a7fec646434073922`
- `758574a8ca5e19c8a9a543cfa4a64083043aefba1ca379881c3ad3c3c47c0896`

A fixed-string scan covered copied workspaces, generated run artifacts,
reports, CLI stdout/stderr, and timing logs. It found zero matches: PASS.

## Wheel build and outside-checkout execution

The wheel was built directly from the still-clean detached checkout into an
external directory, installed into a second new Python 3.12 environment, and
executed from outside the checkout:

```bash
python3.12 -m venv "$CLEAN_ROOT/env-wheel-build"
"$CLEAN_ROOT/env-wheel-build/bin/python" -m pip wheel \
  --no-deps --wheel-dir "$CLEAN_ROOT/dist" "$CLEAN_ROOT/repo"
python3.12 -m venv "$CLEAN_ROOT/env-wheel"
"$CLEAN_ROOT/env-wheel/bin/python" -m pip install \
  "$CLEAN_ROOT/dist/symbolic_compactification-0.1.0a0-py3-none-any.whl"
"$CLEAN_ROOT/env-wheel/bin/python" -m pip check
```

Wheel evidence:

- filename: `symbolic_compactification-0.1.0a0-py3-none-any.whl`
- size: 127,770 bytes
- SHA-256:
  `c111dcc047c9667afb510fcddc2d56c3453772ff49b75ddfce24371a4aff7c84`
- installed import origin: the wheel environment's `site-packages`
- `pip check`: PASS
- both installed entry points: PASS

The wheel-installed CLI then ran `init`, `inspect`, `verify`, and `report` on a
new workspace outside the checkout. All four commands exited 0, verification
returned `ZERO`, source bytes were unchanged after initialization, and the run
record preserved the exact tested commit. A second pair of secret canaries was
absent from its workspace, report, provenance, and command logs.

Wheel smoke artifact hashes:

- provenance:
  `5216a43dadf93c4b8204929c93e924331e6289e39636ddb88863aafd80dd5a06`
- report:
  `0d711f4c8cd1b8909c8e4c184b33797ac1ba8ebf4beb3ef9b21f57495763f524`

The wheel SHA-256 is build-instance evidence, not a published release hash.

## Blockers and boundaries

No clean-room blocker was found. The replay does not establish cross-platform
support, does not supersede the separately recorded full-suite triage, and does
not make any claim about scientific representation discovery. Final alpha
status still requires the coordinator's readiness audit and the three
independent release reviews.
