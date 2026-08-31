# Final external-user retest — E11

## Verdict

`ALPHA_READY`

At integrated commit `eb02da4ee06f9d8d523b82a526dbdb317050588c`, a
first-time researcher can install the ordinary package in a fresh Python 3.12
environment, follow the root README and release quickstart for Mode A, obtain
all documented fail-closed outcomes, and retain provenance-rich reports
without source mutation or credential leakage.

Every blocker from the earlier E11 simulation and post-fix retest is resolved.
No release blocker was observed in this final E11 lane. This is an engineering
UX/reproducibility assessment; the coordinator and final release reviewers own
the project-wide release decision.

## Retest posture

The operator acted as a theoretical physicist unfamiliar with repository
internals. Production code and frozen scientific evidence were read-only. The
workflow used only the public root README, release quickstart, installed CLI,
installed Python API, and one committed demo.

- Integration commit: `eb02da4ee06f9d8d523b82a526dbdb317050588c`
- Branch under review: `work/eng-user-final`
- Host: macOS 26.4 arm64
- Python: CPython 3.12.13
- Installation: ordinary `pip install .` into a new virtual environment, not
  editable
- Import location:
  `/private/tmp/ssc-e11-final.IYAb9T/venv/lib/python3.12/site-packages/symbolic_compactification/__init__.py`
- Replay root: `/private/tmp/ssc-e11-final.IYAb9T`
- User workspaces: `/private/tmp/ssc-e11-final.IYAb9T/outside`, outside every
  Git checkout
- Locally built wheel SHA-256:
  `63a89f8394776e209a9364795d40021305029cdfeb42c8fb3143e15443b163f8`

Generated workspaces and run records remained outside the repository. Only
this report and the E11 handoff are committed by this lane.

## Fresh ordinary installation

Material commands:

```bash
python3.12 -m venv /private/tmp/ssc-e11-final.IYAb9T/venv
/private/tmp/ssc-e11-final.IYAb9T/venv/bin/python -m pip install .
/private/tmp/ssc-e11-final.IYAb9T/venv/bin/python -m pip check
/private/tmp/ssc-e11-final.IYAb9T/venv/bin/symbolic-compactification --version
/private/tmp/ssc-e11-final.IYAb9T/venv/bin/ssc --version
```

Observed:

- virtual-environment creation: 1.30 seconds;
- ordinary installation: 5.11 seconds;
- `pip check`: no broken requirements;
- distribution identity: PEP 440 `0.1.0a0`;
- both CLIs: `0.1.0-alpha (PEP 440 0.1.0a0; engine 0.3.0,
  protocol 0.3.0)`;
- distribution summary: `Context-grounded symbolic hypotheses with
  fail-closed verification.`;
- direct dependencies: PyYAML 6.0.3 and SymPy 1.14.0;
- transitive SymPy dependency: mpmath 1.3.0;
- import resolution: the fresh environment's `site-packages`, not the source
  checkout.

## Current public documentation

The packaged long description is the current root `README.md`. Metadata read
from the installed distribution begins with:

```text
# symbolic-compactification
**Context-grounded symbolic hypotheses with fail-closed verification.**
```

It contains the Mode A researcher workflow and no obsolete scientific-era
status or forbidden discovery claim. The root README and
`engineering/release_v0_1/QUICKSTART.md` agree on the release identity,
workspace commands, Python API, result semantics, source-safety policy, and
capability boundary.

## Mode A replay

The exact root README/quickstart sequence was run from outside the checkout:

```bash
symbolic-compactification init physicist-alpha
symbolic-compactification inspect physicist-alpha
symbolic-compactification verify physicist-alpha
symbolic-compactification report physicist-alpha
```

The initialized exact factorization produced `ZERO`, exit 0, residual `0`, and
run `20260831T141432Z-8be9cf7a`. Observed CLI times were 0.20 seconds for
`init`, 0.21 seconds for `inspect`, 0.85 seconds for `verify`, and 0.22 seconds
for `report`.

The documented installed Python API was then replayed:

```python
from symbolic_compactification import (
    generate_report,
    load_workspace,
    verify_hypothesis,
)

workspace = load_workspace("physicist-alpha")
run = verify_hypothesis(workspace)
print(run.result)
report = generate_report(workspace, run)
print(report.path)
```

It returned `ZERO`, created run `20260831T141502Z-8a19b76c`, and generated a
report in 0.26 seconds total.

## Scientific and ingestion outcomes

| case | installed CLI result | exit | evidence |
|---|---|---:|---|
| initialized Mode A factorization | `ZERO` | 0 | exact residual `0` |
| intentional candidate mutation `(x + 1)**2 + 1` | `NONZERO` | 2 | residual `-1`; exact counterexample `x = -2`, value `-1` |
| committed Demo C polygamma recurrence | `UNKNOWN` | 3 | undecided residual retained; report forbids promotion |
| malformed candidate carrying a synthetic source canary | `PARSE_FAILURE` | 4 | code `EXPRESSION_PARSE_FAILURE`; exact member path and safe hint |
| unsupported `proportional` relation | `COMPILE_FAILURE` | 4 | code `UNSUPPORTED_RELATION`; JSON-pointer-like source and correction hint |
| omitted declared `x` from `assumptions_used` | `ASSUMPTION_REQUIRED` | 4 | code `DECLARED_ASSUMPTIONS_OMITTED`; no obligation executed |

`ZERO`, `NONZERO`, and `UNKNOWN` were never conflated. The `UNKNOWN` CLI and
report explicitly state that the result is neither likely true nor likely
false and cannot promote scientific state. All ingestion failures are named
non-success results, and none displayed a traceback by default.

## Committed demo replay

`engineering/release_v0_1/demos/demo_c_unknown` was copied outside the
checkout and replayed with the installed CLI:

```bash
symbolic-compactification inspect demo-c-unknown
symbolic-compactification verify demo-c-unknown
symbolic-compactification report demo-c-unknown
```

The copied sources match the committed demo byte-for-byte when `runs/` is
excluded. The workflow returned `UNKNOWN`, exit 3, in run
`20260831T141549Z-8185e1e3`. Observed times were 0.23 seconds for `inspect`,
4.05 seconds for `verify`, and 0.24 seconds for `report`.

## Blocker-closure audit

| previously reported blocker | final result | authoritative observation |
|---|---|---|
| ordinary installed provenance recorded `unknown` | PASS | every one of seven installed runs outside the checkout records exact commit `eb02da4ee06f9d8d523b82a526dbdb317050588c` |
| packaged root README was obsolete | PASS | installed long description is the current research-preview README and Mode A workflow |
| release identity was old/ambiguous | PASS | distribution is `0.1.0a0`; both CLIs present `0.1.0-alpha` while separately naming engine/protocol `0.3.0` |
| dependency inventory omitted PyYAML | PASS | every provenance file and human report records direct dependencies `pyyaml: 6.0.3` and `sympy: 1.14.0` |
| human report was incomplete | PASS | inspected report contains project/objective, declared symbols/functions, full typed hypothesis, context grounding metadata, every input/member hash, per-obligation evidence, versions, dependencies, warnings, and fixed artifact inventory |
| diagnostics were not actionable | PASS | parse and compile failures identify the exact source, stable code, bounded correction hint, non-success exit, persisted report, and no default traceback |
| `ASSUMPTION_REQUIRED` was advertised but not operational | PASS | omitted declared symbol returns the named status, stable code, precise source/hint, exit 4, persisted report, and executes no obligation |

## Installed-build provenance

All seven generated `provenance.json` records were inspected directly:

| run | result | recorded commit |
|---|---|---|
| `20260831T141432Z-8be9cf7a` | `ZERO` | `eb02da4ee06f9d8d523b82a526dbdb317050588c` |
| `20260831T141502Z-8a19b76c` | `ZERO` via Python API | `eb02da4ee06f9d8d523b82a526dbdb317050588c` |
| `20260831T141526Z-b76e92a4` | `NONZERO` | `eb02da4ee06f9d8d523b82a526dbdb317050588c` |
| `20260831T141549Z-8185e1e3` | `UNKNOWN` | `eb02da4ee06f9d8d523b82a526dbdb317050588c` |
| `20260831T141636Z-22c71b08` | `PARSE_FAILURE` | `eb02da4ee06f9d8d523b82a526dbdb317050588c` |
| `20260831T141641Z-e156ac48` | `COMPILE_FAILURE` | `eb02da4ee06f9d8d523b82a526dbdb317050588c` |
| `20260831T141647Z-14f597ce` | `ASSUMPTION_REQUIRED` | `eb02da4ee06f9d8d523b82a526dbdb317050588c` |

Every record also contains timestamp, package/engine/protocol versions,
CPython version, direct dependency versions, input and expression hashes,
hypothesis and assumption hashes, verifier route, result, runtime, and
warnings. The exact Git identity was obtained from build-time package
provenance; the runs were launched where no repository `.git` directory was
available.

## Complete report inspection

The `ZERO` report was inspected directly rather than inferred from tests. It
contains:

- aggregate result and exact semantics;
- project name, objective, and expression entrypoint;
- complete declared symbol and function inventories;
- the full typed hypothesis, including assumptions, members, operators,
  instance maps, reconstruction rule, and proof obligations;
- note/reference paths, hashes, and sizes without copying their contents;
- per-obligation member paths, verdict, residual, and simplified residual;
- timestamp, package/engine/protocol versions, Git commit, Python version,
  verifier route, and runtime;
- PyYAML and SymPy versions;
- warnings;
- every input and expression-member hash;
- the generated artifact inventory for `provenance.json`, `result.json`, and
  `REPORT.md`.

The same bounded report structure remains present for `NONZERO`, `UNKNOWN`,
and the three fail-closed ingestion results.

## Actionable fail-closed diagnostics

The malformed expression produced:

```text
result:      PARSE_FAILURE
error_code:  EXPRESSION_PARSE_FAILURE
source:      expressions/candidate.txt
hint:        Correct the named expression and declare every symbol/function in the assumptions file.
```

The unsupported relation produced:

```text
result:      COMPILE_FAILURE
error_code:  UNSUPPORTED_RELATION
source:      hypotheses/hypothesis.json#/proof_obligations/0/relation
hint:        Set the named proof-obligation relation to 'equivalent'.
```

The omitted assumption produced:

```text
result:      ASSUMPTION_REQUIRED
error_code:  DECLARED_ASSUMPTIONS_OMITTED
source:      hypotheses/hypothesis.json
hint:        List every declared symbol explicitly in hypothesis.assumptions_used.
```

All three generated provenance and reports, executed no unrequested repair,
and told the user to change researcher-owned input explicitly.

## Source immutability and overwrite refusal

For the Mode A CLI and Python runs, intentional `NONZERO`, committed
`UNKNOWN` demo, `PARSE_FAILURE`, `COMPILE_FAILURE`, and
`ASSUMPTION_REQUIRED`, SHA-256 manifests were captured before and after tool
execution while excluding only `runs/`. Every source hash was identical.

The protected files included `project.yaml`, expressions, assumptions, notes,
references, and hypothesis JSON. Repeating `init` against the populated Mode A
workspace returned `WORKSPACE_ALREADY_EXISTS`, exit 4, and preserved every
source hash. No production file or frozen evidence was modified by this lane.

## Secret and traceback audit

Verification was exercised with synthetic values in:

- `OPENAI_API_KEY`;
- `AUTHORIZATION`;
- `SSC_E11_SECRET`.

A malformed researcher expression also contained a synthetic
`sk-proj-...` source canary. A recursive scan across every generated `runs/`
tree found none of the canary values, environment/header names, or Python
traceback marker. The malformed source itself remained unchanged outside
`runs/`; redaction did not mutate researcher data.

## Readiness score from E11

| category | assessment | basis |
|---|---|---|
| INSTALL | PASS | fresh Python 3.12 ordinary install, metadata, both CLIs, and `pip check` |
| CLI | PASS | Mode A and all documented statuses are precise and actionable |
| PYTHON_API | PASS | documented three-call installed API replay returns `ZERO` and a report |
| WORKSPACE | PASS | small readable schema, strict initialization, grounded context, source-safe behavior |
| PROVENANCE | PASS | exact installed commit, complete hashes, versions, routes, runtimes, and warnings |
| FAIL_CLOSED | PASS | `ZERO`, `NONZERO`, `UNKNOWN`, parse, compile, and assumption gates remain distinct |
| SECURITY | PASS | all environment/source canaries and traceback markers absent from generated artifacts |
| DEMOS | PASS | committed Demo C replays through the installed CLI and yields intentional `UNKNOWN` |
| DOCS | PASS | root/package README and release quickstart match observed behavior and claim boundaries |
| REPRODUCIBILITY | PASS for E11 replay | clean ordinary install and all user flows reproduced outside checkout; coordinator owns the separate final clean-room gate |

## Remaining friction

No release blocker was observed. Two minor terminology points remain
non-blocking:

- `inspect` uses the lower-level code `EXPRESSION_PARSE_FAILURE` while
  workspace `verify` uses the public result `PARSE_FAILURE`; the displayed
  source and hint make the distinction actionable.
- structural `sums` and `products` count explicit bound `Sum`/`Product` nodes,
  not ordinary arithmetic addition/multiplication; this is not explained in
  the compact human `inspect` output.

Neither point changes a verdict, provenance, source bytes, or the ability to
complete Mode A safely.

## E11 conclusion

`ALPHA_READY`

The final external-user lane found no blocker at
`eb02da4ee06f9d8d523b82a526dbdb317050588c`. The installed workflow is usable,
fail-closed, provenance-rich, source-immutable, and aligned with the approved
research-preview claim boundary.
