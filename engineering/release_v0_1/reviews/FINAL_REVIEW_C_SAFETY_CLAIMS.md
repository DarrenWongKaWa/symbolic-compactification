# Final Review C — Safety and Claim Boundary

## Verdict

ALPHA_READY

## Reviewed SHA

Integration HEAD: `98bb15076d1179f3bade5987b0ecb2c7c5cd81dd`
(`engineering/research-preview-alpha-v0.1`)

Product (packaged source) commit: `bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0`
(ancestor of HEAD). `src/`, `tests/`, `pyproject.toml`, and `setup.py` are
identical between that product commit and this HEAD.

Independent install: ordinary non-editable `pip install .` from this worktree
into a new CPython 3.12.13 venv at
`/private/tmp/ssc-final-review-c-safety/venv`. Installed identity:
`symbolic-compactification 0.1.0-alpha` (PEP 440 `0.1.0a0`; engine `0.3.0`,
protocol `0.3.0`); SymPy `1.14.0`; PyYAML `6.0.3`. Import origin was
site-packages, not the checkout. Embedded build identity:
`SOURCE_GIT_COMMIT = 98bb15076d1179f3bade5987b0ecb2c7c5cd81dd`,
`SOURCE_GIT_DIRTY = True`. Run provenance recorded
`98bb15076d1179f3bade5987b0ecb2c7c5cd81dd-dirty` because this worktree had
unrelated local `STATUS.md` dirt and untracked files at build time. That
suffix is install hygiene, not a safety defect.

No production code, tests, frozen research, or demo source was edited by this
review. Attacks used copies under `/private/tmp`.

This is an engineering safety/claim-boundary decision. Scientific lines were
not reopened.

## Blocking findings

None.

Historical blockers (report symlink trust and double-read metadata hashing)
were independently re-attacked on an authentic Demo C `UNKNOWN` run and on
the release-critical snapshot tests. They did not reproduce. Extra
non-regular-artifact and path-escape hunts also fail closed.

## Attacks

### 1. Demo C copy — symlink `REPORT.md`

Copied `engineering/release_v0_1/demos/demo_c_unknown` to
`/private/tmp/ssc-final-review-c-safety/demo_c_unknown`. Installed CLI
`verify` returned `UNKNOWN` (exit 3), obligation
`polygamma-order-two-recurrence -> UNKNOWN`.

Replaced that run's `REPORT.md` with a symlink to an outside file containing
`Result: **ZERO**` and canary `GENERIC_PRIVATE_CANARY_7M2Q`.

| path | observed |
|---|---|
| Python `generate_report` | `WorkspaceError` `RUN_REPORT_INVALID`; detail `run artifact must be a regular file`; no canary in exception, stdout, stderr, or traceback |
| CLI `report --run` | exit 4; stdout empty; stderr `error: RUN_REPORT_INVALID`; no canary; no forged `ZERO` |
| persisted `result.json` | still `UNKNOWN`; symlink left in place unread |

### 2. Same run — forged regular `REPORT.md`

Same canary/`ZERO` bytes as a regular file.

| path | observed |
|---|---|
| Python `generate_report` | `RUN_REPORT_MISMATCH`; no canary |
| CLI `report --run` | exit 4; stdout empty; stderr `error: RUN_REPORT_MISMATCH`; no canary |
| persisted `result.json` | still `UNKNOWN` |

Deleting the forged file and calling `generate_report` regenerated
`Result: **UNKNOWN**` from the bounded records.

### 3. `real: false` + Piecewise vs 0

Fresh `init` workspace, `real: false` on `x`, current
`Piecewise((1, Eq(x,0)), (0, True))`, candidate `0`.

Python and CLI: `PARSE_FAILURE` /
`UNSUPPORTED_COMPLEX_SYMBOL_SEMANTICS`; no obligations; not warning-free
`ZERO`. CLI exit 4; hint tells the researcher to use `real: true`.

### 4. Environment canaries

`OPENAI_API_KEY=sk-REVIEWC-OPENAI-CANARY-9X7KZZ` and
`AUTHORIZATION=Bearer REVIEWC-AUTH-CANARY-4P2NWW` were set during Demo C
`verify`. Zero raw matches in stdout, stderr, or any file under `runs/`
(and the rest of the copied workspace). Provenance records the allow-listed
schema only (`git_commit`, hashes, versions, `result: UNKNOWN`).

### 5. Default CLI missing path

`report` / `verify` of a nonexistent directory: `error: WORKSPACE_NOT_FOUND`
only, no `Traceback`. `inspect` of the same missing path:
`error: EXPRESSION_SOURCE_UNREADABLE` only (inspect also accepts an
expression file). `--debug` may show a traceback, as documented.

Bare argparse (no command / `report` with no workspace) prints usage, not a
stack trace, and does not execute verification.

### 6. Demo source hashes outside `runs/`

SHA-256 of every non-`runs/` Demo C file was identical for the committed
tree, the copy before CLI, the copy after `verify`, and the copy after the
report attacks:

| path | sha256 |
|---|---|
| `assumptions/assumptions.yaml` | `694d4a337ce65c8dec9d13be46ff389bdc7c07083fd371c20b0001e6b6d335c7` |
| `expressions/candidate.txt` | `8d5200c480654f88f957030d73d984da4fa3ff09c5f2f3c18c2535fba78f4e39` |
| `expressions/current.txt` | `f88cf696ab9215fe744a8507ac011883742040cd4ea5e9373fe63f143d09b780` |
| `hypotheses/hypothesis.json` | `de52f6da881d5782c7701999f4988f62754f841377c14c322cc17fabe755ea7c` |
| `notes/research_notes.md` | `39b0a6e23feda38a54c5fd50e6afb47b1d7baaa10f4f326aa8b1e09b217abe6b` |
| `project.yaml` | `7f8b0d4b81ff708a427106f5c1d6d5cf57a51f45c9fff8572fb2644d71447b3a` |
| `references/README.md` | `033ea9cca5e05d19c2f66a4fb190b6945bc52829f11a1848b2605ee6147f71fb` |

### 7. Demo C `UNKNOWN` is not success

CLI semantics: "this is not success and does not permit scientific
promotion". Report: neither likely true nor likely false; no promotion.
Objective text: the recurrence "remains unpromoted". Exit 3, not 0.

### 8. Forbidden product claims

Grep of user docs for `AI discovers physics`, `Autonomous theoretical
physicist`, `Guaranteed scientific simplification`, and `Always finds hidden
structure`: no affirmative product claims. `LIMITATIONS.md` lists those
phrases only as things the tool must **not** be described as. Root and
preview READMEs deny "autonomous theoretical physicist" / guaranteed
simplifier. `E8_DOCS.md` only cites the same strings as an audit command.
Matches outside user docs are research notes, not positioning.

### 9. Laurent remainder never-certify

`tests/test_release_critical.py::test_finite_laurent_coefficients_without_remainder_never_certify`
still exists and passed on the installed interpreter (`1 passed`). Companion
release-critical safety tests (symlink/forged report, `real: false` gate,
single-snapshot hashing) also passed (`7 passed` in the focused subset).

### 10. No workspace `propose` promotion path

Public CLI subcommands: `init`, `inspect`, `verify`, `report`,
`init-session`, `summary`, `step`, `finalize`, `observe`, `backends`.
`symbolic-compactification propose` is an invalid choice. `observe` is
labelled "no promotion". README: no workspace-level `propose` command is
promised; proposer text cannot promote.

## Extra hunts (not historical blockers)

All fail closed, no canary:

- `result.json` symlink → `RUN_RESULT_INVALID`
- `provenance.json` symlink → `RUN_PROVENANCE_INVALID`
- FIFO `REPORT.md` → `RUN_REPORT_INVALID` (no hang)
- hardlink of forged `REPORT.md` → `RUN_REPORT_MISMATCH`
- expression file symlink out of workspace → `PARSE_FAILURE` /
  `PATH_OUTSIDE_WORKSPACE`; canary not copied into `runs/`
- `runs/` directory symlink → `RUNS_DIRECTORY_UNSAFE`

## Gate assessment

| Gate | Result |
|---|---|
| `SECURITY` | PASS — no symlink follow, no env-canary leak, non-regular artifacts rejected |
| `FAIL_CLOSED` | PASS — authentic `UNKNOWN` cannot be presented as forged `ZERO` report prose |
| `PROVENANCE` | PASS — snapshot-hash regressions still pass; Demo C hashes stable |
| claim boundary | PASS — public claims remain denials/limitations |
| scientific-line lock | PASS — no research experiment reopened |

ALPHA_READY
