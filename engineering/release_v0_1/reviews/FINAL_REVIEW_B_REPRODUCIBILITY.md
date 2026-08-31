# Final Reviewer B — Software and Reproducibility

## Verdict

`ALPHA_READY`

No software/reproducibility blocker was found for the bounded Mode A
Research Preview v0.1 workflow at the current integration head. This verdict
does not relabel the disclosed historical full suite as green, does not
endorse closed scientific research paths, and does not claim byte-identical
wheels.

## Independent review posture

- Review lane: Final Reviewer B (software and reproducibility only)
- Reviewed integration HEAD:
  `416867289f372f469be5ee8b72c948e48bf31821`
- Product commit (last packaged-source change):
  `bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0`
- Independent root: `/private/tmp/ssc-final-review-b.yVEaEh`
- Checkout: detached, `git clone --no-local --no-checkout` of the reviewed
  HEAD
- Runtime: CPython 3.12.13, pip 26.2.1
- Host: macOS 26.4 (Darwin 25.4.0), arm64
- Production and frozen research files: not edited
- Review output: this report only

`src/`, `tests/`, `pyproject.toml`, and `setup.py` are identical between
product commit `bd6f0a1` and this HEAD. The intervening commits add
engineering evidence only (`CLEAN_ROOM_HEAD_REPLAY.md`, status/merge-log
ledger, and `SCIENTIFIC_EXPERIMENTS_CLOSED.md` lock text). The clean-room
report was treated as a claim to challenge, not as proof. I rebuilt and
exercised this HEAD independently.

The development worktree that produced this HEAD was dirty (unstaged
`STATUS.md` plus unrelated untracked research/workspace files). Installing
from that tree would be `-dirty` by design. The independent clone was clean
before and after install, tests, wheel construction, and demo execution.

## Installation and package identity

A fresh ordinary, non-editable installation from the detached current-head
checkout passed:

```bash
python3.12 -m venv env-normal
env-normal/bin/python -m pip install -U pip
env-normal/bin/python -m pip install "$CLEAN_CHECKOUT"
env-normal/bin/python -m pip check
env-normal/bin/symbolic-compactification --version
env-normal/bin/ssc --help
```

Results:

- installed distribution: `symbolic-compactification 0.1.0a0`
- user-facing identity: `0.1.0-alpha`
- engine / protocol: `0.3.0` / `0.3.0`
- CLI `--version`:
  `symbolic-compactification 0.1.0-alpha (PEP 440 0.1.0a0; engine 0.3.0, protocol 0.3.0)`
- import origin:
  `$REVIEW_ROOT/env-normal/lib/python3.12/site-packages/symbolic_compactification/__init__.py`
  (not the checkout)
- embedded source identity:
  `416867289f372f469be5ee8b72c948e48bf31821` (`SOURCE_GIT_DIRTY = False`)
- direct runtime dependencies: PyYAML 6.0.3 and SymPy 1.14.0
- `pip check`: `No broken requirements found.`
- console entry points `symbolic-compactification` and `ssc`: PASS

Build provenance is written only into setuptools' build directory. The clone
had no `src/symbolic_compactification/_build_info.py` before or after
installation.

A dirty-tree attack clone of the same HEAD, with one non-ignored untracked
file, installed as
`416867289f372f469be5ee8b72c948e48bf31821-dirty`
(`SOURCE_GIT_DIRTY = True`). Clean and dirty identities are therefore
distinct, and a clean release artifact records the bare 40-hex commit.

## Release-critical and focused tests

Pytest was added after the identity check (`pip install pytest`). Exact
command from the clean checkout, using the non-editable environment:

```text
python -m pytest -q -m release_critical
.................                                                        [100%]
17 passed in 9.69s
```

That matches the advertised 17-test gate at product SHA `bd6f0a1` and
reproduces it at this HEAD. The group covers clean parse, workspace
initialization, CLI smoke, distinct `ZERO` / `NONZERO` / `UNKNOWN`,
parse/compile/assumption gates, provenance and deterministic hashes, metadata
snapshot/hash binding, source immutability, secret redaction, report
integrity, the retracted finite-Laurent/remainder regression, and the
`real: false` namespace rejection.

Focused engineering surface at the same HEAD:

```text
python -m pytest -q \
  tests/test_workspace.py tests/test_research_api.py \
  tests/test_run_provenance.py tests/test_release_security.py \
  tests/test_release_demos.py tests/test_release_critical.py \
  tests/test_packaging_contract.py
96 passed in 34.28s
```

The full suite was not rerun.

## Demos, hashes, and source immutability

The three committed demo workspaces were copied outside the checkout. The
non-editable installed CLI ran `inspect`, `verify`, and `report` against each
copy.

| demo | result | inspect | verify | report | source snapshot |
|---|---|---:|---:|---:|---|
| A — exact factorization | `ZERO` | 0 | 0 | 0 | unchanged |
| B — fixed grounded Newton DD | `ZERO` | 0 | 0 | 0 | unchanged |
| C — intentional polygamma proof gap | `UNKNOWN` | 0 | 3 | 0 | unchanged |

Source-snapshot SHA-256 values (content hashes of every non-`runs/` file)
were identical before and after the three commands, and they match the
clean-room record:

- A: `86d49a214745ba91ae10cd5c57d67312b627bf8248dba9fa67513f431ebc948f`
- B: `89eb0d3f9f087e56adbd8969f1f8669d98e3c6cc5c6a843d6607b34b78ea1136`
- C: `6d6ea6b9ce449965bb1c562c4c2ed03637f5927f4212acc784268d6940a34377`

Generated files appeared only under each copy's `runs/<run_id>/`. Demo C's
CLI semantics line is "not success and does not permit scientific promotion";
its report states that `UNKNOWN` is neither likely true nor likely false.
Demo B's compact CLI still prints an unsimplified residual beside a `ZERO`
verdict; `result.json` retains `simplified_residual: "0"` and
`exact_symbolic_zero`. Verbose, not a correctness or reproducibility blocker.

Every public provenance field was present. Each record named the exact
installed commit `416867289f372f469be5ee8b72c948e48bf31821`, package
`0.1.0a0`, engine/protocol `0.3.0`, CPython 3.12.13, PyYAML 6.0.3, SymPy
1.14.0, and verifier route `python_sympy_exact_v1`.

Independent `shasum -a 256` recomputation of Demo A matched
`provenance.json` byte-for-byte:

| artifact | SHA-256 |
|---|---|
| `expressions/current.txt` | `31db8a3228376dd5b1cff3aece3109a286157eef4a49f2658e24d1403a35dd54` |
| `expressions/candidate.txt` | `eb51ce0f796ab5f31ea1bb91d637e13af1c623c17487edefb80d9735420a4f2e` |
| `hypotheses/hypothesis.json` | `e8ac6d5e0431e55a19abbff8b6345b3ee4292741fb9c30017b8ba8e0d6a799a2` |
| `assumptions/assumptions.yaml` | `d77ee604715ec602f59490f5f3fd664e0ed1129553b1c65cd141c8fffa0ec296` |

The same match held for Demo B and Demo C: every `input_hashes` and
`expression_hashes` entry recomputed from source bytes, and the top-level
hypothesis/assumptions digests equaled the corresponding named input hashes.
`result.json`, `provenance.json`, and `REPORT.md` agreed on run id, verifier
route, and result.

Replay-instance artifact hashes (intentionally not stable across runs):

| demo | provenance | result | report |
|---|---|---|---|
| A | `43cf9b7768e57d314ac3c950a15ba562ed8da679f7eedc175b064096dc09dda6` | `0c8eea5d0d9a3ae0fe51cf7785d2b36c3f03081a96ca80942e77466fe0ab2cf1` | `064bc5040f70ad1f122a04464a40d288bf237d86f3f3caaa412ad63749bb59ea` |
| B | `d75991baae0b2026eb789a013b09524e3099dc1f48e15b7ddf0fbe20b8d5bef8` | `ba2ffb0bc51a7202ba2233b035e6226a9e71d1b7ed5f54a21c544911453ea8b4` | `886172447228b4735c24725c985280b96cfbd59a11c2a3f4216f08d94d697104` |
| C | `bb2d3d37e90924cf8786d4847d57bd7f6730ad6fb526e0a32c54259a36ea92c6` | `2f28cbd1f347fd61b765ffc2476460dc7abaa6cd400a1f9f833eb061ab7ee2fb` | `db8d20f4ac6925ad923cb739e5dd49036489ed7754459b91314820ac710acbbc` |

The detached source checkout remained free of tracked or non-ignored
untracked changes. Ignored debris was limited to pytest cache, bytecode,
`build/`, and `*.egg-info`.

## Wheel install outside the checkout

A wheel was built from the still-clean detached checkout, installed in a
second fresh Python 3.12 environment, and executed from
`/private/tmp/ssc-final-review-b-wheel-ws` (outside the checkout).

- wheel: `symbolic_compactification-0.1.0a0-py3-none-any.whl`
- size: 130,104 bytes
- build-instance SHA-256:
  `820180923c2fa29d7207835e72597d926c5502367618f138ed9c3a24af8d40b1`
- import origin: the wheel environment's `site-packages`
- embedded source identity:
  `416867289f372f469be5ee8b72c948e48bf31821` (`SOURCE_GIT_DIRTY = False`)
- `pip check` and both entry points: PASS

Wheel-installed `init` / `inspect` / `verify` / `report` returned exits
0 / 0 / 0 / 0 and result `ZERO`. Provenance recorded the exact reviewed
commit, package/engine/protocol versions, and both direct dependency
versions. All input and expression hashes recomputed. The public Python
workflow also passed outside the checkout:

```python
workspace = load_workspace("api-workspace")
run = verify_hypothesis(workspace)
report = generate_report(workspace, run)
```

It returned `ZERO` and left user-source files outside `runs/` unchanged.
The wheel hash is build-instance evidence, not a published byte-reproducible
artifact.

Root README, `INSTALLATION.md`, `QUICKSTART.md`, and `DEMOS.md` give the
exact install, init/inspect/verify/report, wheel, and demo-replay commands
used above. Dirty-tree identity is documented: a clean release artifact must
record the bare 40-character commit.

## Full-suite boundary

The full repository suite was not rerun. The authorized integration result
remains honestly non-green:

```text
2049 passed, 24 failed in 455.57s
```

`FULL_SUITE_RESULT.md` and the HEAD clean-room report disclose that result
and do not describe it as green. The 24 failures remain the frozen-research
authority/hash inventory, one research-only optional client, and historical
package enumeration. This review does not edit frozen evidence to make the
suite green.

## Non-blocking boundaries

- The alpha support contract independently validated here is CPython 3.12 on
  the tested macOS arm64 host. Metadata `requires-python >= 3.10` is not a
  tested platform matrix.
- Wheels built at different times are not asserted to be byte-identical.
- The historical full suite remains red and must continue to be reported as
  such.
- Checked-in `STATUS.md` at this HEAD still describes clean-room replay as
  in progress even though `CLEAN_ROOM_HEAD_REPLAY.md` is already merged.
  That is coordinator ledger lag, not a defect in the tested package.
- No `research-preview-v0.1.0-alpha` tag exists, which is the correct
  pre-decision posture.
- Cross-platform installation, optional extras, experimental LLM proposal,
  and scientific representation discovery are outside this verdict.

## Blockers

None for the bounded Research Preview Alpha software/reproducibility gate.

## Recommendation

`ALPHA_READY`

Proceed only if the other two independent reviewers concur and the
coordinator's final gate preserves the disclosed full-suite failures, the
tested-platform boundary, exact release-commit identity, and fail-closed
claim language.
