# HEAD clean-room replay — Research Preview v0.1

## Decision

`ALPHA_READY`

This is the reproducibility-lane decision for the bounded Mode A
researcher-workspace release at product HEAD
`bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0`. No clean-room, provenance,
source-immutability, report-integrity, or secret-handling blocker was found.
The coordinator still owns the final engineering decision and tag.

This replay does not reopen a scientific experiment, claim representation
discovery, or reinterpret the separately disclosed historical full-suite
failures. A previous clean-room replay at `3de1a90` is stale relative to this
HEAD and was not reused as current evidence.

## Frozen input and isolation

- Source commit: `bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0`
- Checkout: detached HEAD in a separate `git clone --no-local --no-checkout`
- Replay root: `/private/tmp/ssc-cleanroom-bd6f0a1.NIigUj` (new directory
  under `/private/tmp`, outside the development worktree)
- Host: macOS 26.4 (build 25E246), arm64
- Python: CPython 3.12.13
- pip: 26.2.1
- Replay date: 2026-09-01

```bash
CLEAN_ROOT=$(mktemp -d /private/tmp/ssc-cleanroom-bd6f0a1.XXXXXX)
git clone --no-local --no-checkout PARENT "$CLEAN_ROOT/repo"
git -C "$CLEAN_ROOT/repo" checkout --detach bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0
```

The checkout was clean before installation. `git status --porcelain
--untracked-files=all` and `git diff --check` remained empty after both
install routes, tests, wheel construction, demo execution, and report
generation. Generated workspaces, venvs, wheels, logs, and demo copies lived
outside the checkout. Ignored debris was limited to pytest cache, bytecode,
and setuptools `build/` plus `*.egg-info` copies; none of those paths is
tracked.

This HEAD includes the fail-closed `real: false` workspace rejection
(`f9692c1` + `bd6f0a1`). It does not edit frozen research evidence.

## Fresh ordinary installation

A new Python 3.12 virtual environment installed the package non-editably from
the detached checkout with the `dev` extra:

```bash
python3.12 -m venv "$CLEAN_ROOT/env-normal"
"$CLEAN_ROOT/env-normal/bin/python" -m pip install -U pip
"$CLEAN_ROOT/env-normal/bin/python" -m pip install "$CLEAN_CHECKOUT[dev]"
"$CLEAN_ROOT/env-normal/bin/python" -m pip check
"$CLEAN_ROOT/env-normal/bin/symbolic-compactification" --version
"$CLEAN_ROOT/env-normal/bin/ssc" --help
```

Results:

- installation: PASS
- import origin: `$CLEAN_ROOT/env-normal/lib/python3.12/site-packages/symbolic_compactification/__init__.py`, not the checkout
- distribution version: `0.1.0a0`
- displayed release version: `0.1.0-alpha`
- engine/protocol: `0.3.0` / `0.3.0`
- embedded source identity: `bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0` (`SOURCE_GIT_DIRTY = False`)
- CLI `--version`:
  `symbolic-compactification 0.1.0-alpha (PEP 440 0.1.0a0; engine 0.3.0, protocol 0.3.0)`
- direct runtime dependencies: PyYAML 6.0.3 and SymPy 1.14.0
- `pip check`: `No broken requirements found.`
- both console entry points: PASS

Installed CLI startup (`--version`) measured 0.88 s wall time and 66,191,360
bytes maximum RSS on the first post-install invocation.

## Release-critical gate

Exact command, run from the clean checkout:

```bash
"$CLEAN_ROOT/env-normal/bin/python" -m pytest -q -m release_critical
```

Result:

```text
.................                                                        [100%]
17 passed in 9.36s
```

The measured command used 9.46 seconds wall time and 85,393,408 bytes maximum
RSS. Collection used the `tests/conftest.py` policy and did not need the
`tests` fallback path. The group covers clean parsing, every public
verdict/failure class, provenance, deterministic hashes, source immutability,
secret redaction, workspace initialization, installed CLI/report behavior, the
historical remainder regression, the `real: false` namespace rejection, and
the report-integrity plus mutation-after-read snapshot-binding regressions.

The full suite was not rerun. The authorized integration result remains
`2049 passed, 24 failed` in `FULL_SUITE_RESULT.md` and is not green.

## Installed-CLI demos

Each committed demo was copied outside the checkout. The installed console
script ran `inspect`, `verify`, and `report` against the copy with synthetic
secret canaries in its environment.

| demo | result | inspect exit | verify exit | report exit | inspect wall / RSS | verify wall / RSS | report wall / RSS |
|---|---:|---:|---:|---:|---:|---:|---:|
| A — exact factorization | `ZERO` | 0 | 0 | 0 | 0.14 s / 66,387,968 B | 0.56 s / 66,977,792 B | 0.14 s / 66,338,816 B |
| B — fixed grounded Newton DD | `ZERO` | 0 | 0 | 0 | 0.14 s / 66,519,040 B | 0.62 s / 68,468,736 B | 0.14 s / 66,240,512 B |
| C — intentional proof gap | `UNKNOWN` | 0 | 3 | 0 | 0.14 s / 66,256,896 B | 2.65 s / 70,090,752 B | 0.14 s / 66,387,968 B |

Verifier-recorded runtimes were 0.415997 s, 0.458445 s, and 2.498218 s for
A, B, and C respectively.

Demo B is the reviewer-fixed, denominator-safe specialization with fixed
nodes `10/9` and `25/9`. Its single declared obligation returned exact
`ZERO`; the replay does not promote that fixed verification into a generic
family or discovery claim. Demo C's report states that `UNKNOWN` is neither
likely true nor likely false and does not permit scientific promotion. Its
CLI semantics line is "not success and does not permit scientific promotion".
Its verify exit status was exactly 3.

The deterministic Python demo runner independently reproduced all three
results, complete provenance, generated reports, and unchanged source files:

```bash
"$CLEAN_ROOT/env-normal/bin/python" \
  "$CLEAN_CHECKOUT/engineering/release_v0_1/demos/run_demos.py" \
  --output-root "$CLEAN_ROOT/demo-runner"
```

Its content-based source snapshot hashes were:

| demo | source snapshot SHA-256 |
|---|---|
| A | `86d49a214745ba91ae10cd5c57d67312b627bf8248dba9fa67513f431ebc948f` |
| B | `89eb0d3f9f087e56adbd8969f1f8669d98e3c6cc5c6a843d6607b34b78ea1136` |
| C | `6d6ea6b9ce449965bb1c562c4c2ed03637f5927f4212acc784268d6940a34377` |

CLI copies of the same committed workspaces produced the same source-snapshot
digests.

## Provenance and hash audit

All three CLI runs contained exactly the required public provenance fields.
Each record named:

- exact full source commit
  `bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0`;
- package, engine, protocol, Python, and direct-dependency versions;
- verifier route `python_sympy_exact_v1`;
- result and runtime;
- five grounded input hashes and two expression hashes;
- hypothesis and assumptions hashes; and
- warnings.

Every input and expression digest was recomputed from the copied source bytes
and matched. The hypothesis and assumptions top-level digests matched their
corresponding entries in `input_hashes`. `result.json`, `provenance.json`, and
the rendered report agreed on run id, verifier route, and result.

Replay-instance artifact hashes were:

| demo | provenance SHA-256 | result SHA-256 | report SHA-256 |
|---|---|---|---|
| A | `f1606aff104289f6fbe77cb8ba7de9250e7251abacdbf9d4435a70e0395bc527` | `8f92fadff5d5b4ee2050714c75e50cb8fa1c0cb823552c7ed1b60f382872cbef` | `a9b2cd3030a76c2c45c75a436183ac5124a171cac5f21bdfe82fa8e5c8efe433` |
| B | `33ebedd579c2e4e5c40bc684bb9c2263aa38f6d342937800a1b708d5f59239e2` | `7d839f3a7312acaf221c0e2e9dadd42e681a5c5277a09dd7edec3f4edd146824` | `29c89a03ba787cd6dab8a69247dfc9c0da35c21adb9fa8a0e07f8975991c10fc` |
| C | `a220f2b32ac8fc48090ea56d3f59f145814d5ec926d20263c5c0066bc5c58358` | `22987cb125d693e7031b9daefc31a5ec8df1adb496fe4a4f5e06c4cc64902fe0` | `3fac33d0e1766d1820933c901c08802b91f90f8823418bf7890e0ab53bf93b45` |

These hashes identify this replay instance; timestamps, run ids, and runtimes
are intentionally instance-specific.

## User-source immutability

Every non-`runs/` file in each copied CLI workspace was hashed byte-for-byte
before `inspect`, `verify`, and `report`, then hashed again afterward. All
three manifests were identical. Only tool-owned files under
`runs/<run_id>/` appeared.

The wheel-installed CLI and wheel-installed Python API were checked with the
same before/after procedure; both comparisons were also identical.

## Secret canaries

Three synthetic values were supplied only through environment variables. Their
values are not retained here. Their SHA-256 digests were:

- `5cbcc8af4c3782c827d5740ccd3fcf1c1cbbf6ebea2cee686b884f7a6960cedc`
- `c76dd779cdbbacd34a9804ea956edb8b33524202603494e5a8f44fe1c91f2cc5`
- `b46c378228a3d49d31d2fd7a324dfdf0fde8889b01781f0337135e7ec566d40b`

A fixed-string scan covered copied source workspaces, generated run artifacts,
reports, CLI stdout/stderr, logs, the demo runner, wheel workspaces, and the
adversarial replay tree (201 files). It found zero matches. No API keys, auth
headers, `.env` content, or real secrets were present in this lane.

## Adversarial report-integrity replay

A genuine Demo C run first persisted `UNKNOWN`. Its generated `REPORT.md` was
then replaced in turn by:

1. a symlink to an out-of-workspace file containing false `ZERO` prose and a
   generic private canary; and
2. a forged regular `REPORT.md` with the same contradictory content.

The installed public CLI behaved as follows:

| attack | report exit | stdout | stderr | canary emitted | persisted result |
|---|---:|---:|---|---:|---|
| out-of-workspace symlink | 4 | 0 bytes | `error: RUN_REPORT_INVALID` | no | `UNKNOWN` |
| forged regular report | 4 | 0 bytes | `error: RUN_REPORT_MISMATCH` | no | `UNKNOWN` |

No attacker content was returned or printed, and an authentic `UNKNOWN` could
not be presented as `ZERO`.

## Metadata snapshot/hash binding replay

The release-critical group includes the focused adversarial regression that
deterministically changes each critical metadata file immediately after its
one allowed byte read:

- `project.yaml`;
- `assumptions/assumptions.yaml`; and
- `hypotheses/hypothesis.json`.

Those three cases, plus the report-integrity attack above, passed inside the
17-test gate. Parsing, workspace summary, and recorded hash remained bound to
the same immutable original byte snapshot even though the file on disk was
subsequently changed by the test. No run paired old parsed semantics with a
new source hash.

## Wheel and outside-checkout replay

A wheel was built from the still-clean detached checkout, installed in a
second fresh Python 3.12 environment, and executed from a working directory
outside the checkout.

- wheel: `symbolic_compactification-0.1.0a0-py3-none-any.whl`
- size: 130,103 bytes
- build-instance SHA-256:
  `0d4842d0ab4b4342e65aeddf0aa73c7e4eb8708f8c2e7b97448559ccc21d578c`
- import origin: the wheel environment's `site-packages`
- embedded source identity:
  `bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0` (`SOURCE_GIT_DIRTY = False`)
- `pip check` and both entry points: PASS

The wheel-installed CLI ran `init`, `inspect`, `verify`, and `report` with all
four exits equal to 0 and result `ZERO`. All provenance hashes recomputed, the
exact source commit and dependency versions were present, source bytes were
unchanged, and the canary scan was empty.

Wheel smoke artifact hashes:

- provenance:
  `4978c051e9f2d3b11639ebc4e2239cc7a685159be15685248e2ba069a843ec39`
- result:
  `99aa091e843062e4736ba89f2cda520cc832ebb232b06bd4c6cede4a1c1c218e`
- report:
  `59af4885bf312ba1d32cf48c4052ee121807d648d018d45b835d89ef92bac6e6`

The public wheel-installed Python workflow also passed:

```python
workspace = load_workspace("WORKSPACE")
run = verify_hypothesis(workspace)
report = generate_report(workspace, run)
```

It returned `ZERO`, retained the exact build commit and dependencies, and
left every user-source byte unchanged.

## Full-suite boundary

The full repository suite was not rerun. This follows the program's explicit
single-full-suite policy. The authorized integration result remains
`2049 passed, 24 failed in 455.57s`, with all 24 failures disclosed and
triaged in `FULL_SUITE_RESULT.md` as frozen-research authority/hash behavior,
one research-only optional client, and historical package enumeration. This
replay does not describe the historical full suite as green and does not edit
frozen evidence to make it green.

## Blockers and recommendation

No HEAD clean-room blocker was found for the bounded Research Preview Alpha
workflow on the tested Python 3.12/macOS arm64 environment.

Recommendation: `ALPHA_READY`.

The coordinator should issue an alpha decision only if the final reviewer
recheck and requirement-by-requirement readiness audit also pass. No release
tag existed at replay time.
