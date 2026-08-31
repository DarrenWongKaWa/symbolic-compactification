# Final clean-room replay — Research Preview v0.1

## Decision

`ALPHA_READY`

This is the final reproducibility-lane decision for the bounded Mode A
researcher-workspace release at commit
`3de1a9054541e18dfa8154808ddba85a0635bdb5`. No clean-room, provenance,
source-immutability, report-integrity, or secret-handling blocker was found.
The coordinator still owns the final engineering decision and tag.

This replay does not reopen a scientific experiment, claim representation
discovery, or reinterpret the separately disclosed historical full-suite
failures.

## Frozen input and isolation

- Source commit: `3de1a9054541e18dfa8154808ddba85a0635bdb5`
- Checkout: detached HEAD in a separate `git clone --no-local --no-checkout`
- Replay root: a new directory under `/private/tmp`, outside the development
  worktree
- Host: macOS 26.4 (build 25E246), arm64
- Python: CPython 3.12.13
- pip: 25.0.1
- Replay date: 2026-08-31

The checkout was clean before installation. It remained clean after both
install routes, tests, wheel construction, demo execution, and report
generation. `git diff --check` also remained clean. Generated workspaces and
logs were outside the checkout; pytest's cache was ignored.

The final fix commit changes only alpha implementation, documentation, demos,
and tests. It does not edit frozen research evidence.

## Fresh ordinary installation

A new Python 3.12 virtual environment installed the package non-editably from
the detached checkout with the `dev` extra:

```bash
python3.12 -m venv ENV
ENV/bin/python -m pip install 'CHECKOUT[dev]'
ENV/bin/python -m pip check
ENV/bin/symbolic-compactification --version
ENV/bin/ssc --help
```

Results:

- installation: PASS
- import origin: the new environment's `site-packages`, not the checkout
- distribution version: `0.1.0a0`
- displayed release version: `0.1.0-alpha`
- engine/protocol: `0.3.0` / `0.3.0`
- direct runtime dependencies: PyYAML 6.0.3 and SymPy 1.14.0
- `pip check`: no broken requirements
- both console entry points: PASS

## Release-critical gate

Exact command:

```bash
ENV/bin/python -m pytest -q -m release_critical
```

Result:

```text
................                                                         [100%]
16 passed in 13.00s
```

The measured command used 13.17 seconds wall time and 85,524,480 bytes maximum
RSS. The group covers clean parsing, every public verdict/failure class,
provenance, deterministic hashes, source immutability, secret redaction,
workspace initialization, installed CLI/report behavior, the historical
remainder regression, and the final reviewer regressions.

## Installed-CLI demos

Each committed demo was copied outside the checkout. The installed console
script ran `inspect`, `verify`, and `report` against the copy with synthetic
secret canaries in its environment.

| demo | result | inspect exit | verify exit | report exit | inspect wall / RSS | verify wall / RSS | report wall / RSS |
|---|---:|---:|---:|---:|---:|---:|---:|
| A — exact factorization | `ZERO` | 0 | 0 | 0 | 0.22 s / 66,551,808 B | 0.83 s / 66,994,176 B | 0.22 s / 66,420,736 B |
| B — fixed grounded Newton DD | `ZERO` | 0 | 0 | 0 | 0.23 s / 66,879,488 B | 0.90 s / 68,698,112 B | 0.22 s / 66,568,192 B |
| C — intentional proof gap | `UNKNOWN` | 0 | 3 | 0 | 0.22 s / 66,404,352 B | 3.80 s / 70,549,504 B | 0.21 s / 66,404,352 B |

Demo B is the reviewer-fixed, denominator-safe specialization with fixed
nodes `10/9` and `25/9`. Its single declared obligation returned exact
`ZERO`; the replay does not promote that fixed verification into a generic
family or discovery claim. Demo C's report states that `UNKNOWN` is neither
likely true nor likely false and does not permit scientific promotion.

The deterministic Python demo runner independently reproduced all three
results, complete provenance, generated reports, and unchanged source files.
Its content-based source snapshot hashes were:

| demo | source snapshot SHA-256 |
|---|---|
| A | `86d49a214745ba91ae10cd5c57d67312b627bf8248dba9fa67513f431ebc948f` |
| B | `89eb0d3f9f087e56adbd8969f1f8669d98e3c6cc5c6a843d6607b34b78ea1136` |
| C | `6d6ea6b9ce449965bb1c562c4c2ed03637f5927f4212acc784268d6940a34377` |

## Provenance and hash audit

All three runs contained exactly the required public provenance fields. Each
record named:

- exact full source commit
  `3de1a9054541e18dfa8154808ddba85a0635bdb5`;
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
| A | `7dba66eac0fec28eaf4849e4dce76b5f5d905ddbca67691f39ec65dcce750707` | `e628c2e22b30891686de898d52c5980dde5847850694bbd08350f63cb9f48d82` | `0c2f6d5f54f29413714ccdd2d6fe6209f97a23a75a243d36486cb8324ead5eca` |
| B | `3ff649765f10117e1c918f4626f6478368ba9a422af6aab5ab3b3b964c666726` | `411dce68917503f23628a96bd06c34c543bc1849dbd04979fca8d64cf3d9b940` | `614683e393391371340a70bbedf1355adad20b893c055beb3bd56337cfa0ac84` |
| C | `9656e4dadc6c8d5a81bafa2b962102ed90e0eb42a19b03824340603ff2fd67ad` | `fa1771079e95f7eeda12ee9afbc03ad8e2a043d44e685f27e98b18f5c2394ff1` | `b49a1d28f715b120358583b70805c7993794878ccd4b2f1e53fd860d694dbdd2` |

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

- `162960b0808f30c584302d22dafc725c0a24c11d24a54797dfddbd38b0e6b52c`
- `6968f58ebb97c5a3a19a7fac1c33a3bdb783ab222b27ad9c32fb3cf93cc6f2b6`
- `2fefcf63b94460305a45ff2c932c3485cfa7d28cfe1cd9adf03e3823e056c164`

A fixed-string scan covered copied source workspaces, generated run artifacts,
reports, CLI stdout/stderr, and timing logs. It found zero matches. A separate
wheel-workspace canary scan also found zero matches.

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

The corresponding Python API and CLI regression also passed. No attacker
content was returned or printed, and an authentic `UNKNOWN` could not be
presented as `ZERO`.

## Metadata snapshot/hash binding replay

The focused adversarial regression deterministically changed each critical
metadata file immediately after its one allowed byte read:

- `project.yaml`;
- `assumptions/assumptions.yaml`; and
- `hypotheses/hypothesis.json`.

For all three cases, parsing, workspace summary, and recorded hash remained
bound to the same immutable original byte snapshot even though the file on
disk was subsequently changed by the test. No run paired old parsed semantics
with a new source hash.

The exact focused result, including the report-integrity attack, was:

```text
4 passed, 12 deselected in 6.10s
```

## Wheel and outside-checkout replay

A wheel was built from the still-clean detached checkout, installed in a
second fresh Python 3.12 environment, and executed outside the checkout.

- wheel: `symbolic_compactification-0.1.0a0-py3-none-any.whl`
- size: 129,811 bytes
- build-instance SHA-256:
  `132e915548ebc855fe51a32bc57e3d90a77683468f958216f276989e1278a0cd`
- import origin: the wheel environment's `site-packages`
- embedded source identity:
  `3de1a9054541e18dfa8154808ddba85a0635bdb5`
- `pip check` and both entry points: PASS

The wheel-installed CLI ran `init`, `inspect`, `verify`, and `report` with all
four exits equal to 0 and result `ZERO`. All provenance hashes recomputed, the
exact source commit and dependency versions were present, source bytes were
unchanged, and the canary scan was empty.

Wheel smoke artifact hashes:

- provenance:
  `eb1f7861c9bf33598e52b90a9ba7c24b9836d596122d0846c457607af11f54d0`
- report:
  `2c939e9e5226c80885f61c5e04f9fdb73f91a74bddb40c37c82d4a9297fdae7d`

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

No final clean-room blocker was found for the bounded Research Preview Alpha
workflow on the tested Python 3.12/macOS arm64 environment.

Recommendation: `ALPHA_READY`.

The coordinator should issue an alpha decision only if the final reviewer
recheck and requirement-by-requirement readiness audit also pass. No release
tag existed at replay time.
