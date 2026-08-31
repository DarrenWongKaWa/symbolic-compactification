# External-user simulation — E11

## Verdict

`INTERNAL_ONLY`

The release-critical Mode A workflow is functional and fail-closed, but the
installed release identity, provenance inventory, human report content, and
default diagnostic UX do not yet satisfy the declared v0.1 alpha contract.
This verdict applies to integrated commit
`6227c1e5b0291fb1915ce83a007b8ba6aa247bd0`; it is an engineering assessment,
not a scientific verdict.

## Simulation posture

The operator acted as a theoretical physicist unfamiliar with repository
internals. The only preparation read was the release quickstart and workspace
format. No production code or frozen scientific evidence was changed.

- Host: macOS arm64
- Python: CPython 3.12.13
- Installation: fresh virtual environment, ordinary local wheel install
  (`pip install .`), not editable
- Installed dependencies: PyYAML 6.0.3, SymPy 1.14.0, mpmath 1.3.0
- Installed package location:
  `.venv/e11/lib/python3.12/site-packages/symbolic_compactification`
- CLI paths: `.venv/e11/bin/symbolic-compactification` and `.venv/e11/bin/ssc`

All temporary environments and user workspaces were kept under the ignored
`.venv/e11/` tree. Generated run artifacts were not committed.

## Exact replay commands

The following are the material shell commands used from
`/private/tmp/ssc-eng-user-test`:

```bash
/usr/bin/time -p python3.12 -m venv .venv/e11
/usr/bin/time -p .venv/e11/bin/python -m pip install .
.venv/e11/bin/python -m pip check
.venv/e11/bin/symbolic-compactification --version
.venv/e11/bin/ssc --version

mkdir -p .venv/e11/workspaces
/usr/bin/time -p .venv/e11/bin/symbolic-compactification \
  init .venv/e11/workspaces/physicist-alpha
/usr/bin/time -p .venv/e11/bin/symbolic-compactification \
  inspect .venv/e11/workspaces/physicist-alpha
/usr/bin/time -p .venv/e11/bin/symbolic-compactification \
  verify .venv/e11/workspaces/physicist-alpha
/usr/bin/time -p .venv/e11/bin/symbolic-compactification \
  report .venv/e11/workspaces/physicist-alpha
```

The initialized example was then edited as a normal researcher workspace:

- `current.txt`: `omega**2 + 2*m*omega + m**2`
- `candidate.txt`: `(omega + m)**2`
- `assumptions.yaml`: explicit real declarations for `omega` and `m`
- `hypothesis.json`: both assumptions listed and one explicit equivalence
  obligation
- `project.yaml`, notes, and references: a dispersion-factorization objective,
  context note, and manually curated notebook citation

The documented Python quickstart was also replayed exactly:

```bash
.venv/e11/bin/python -c 'from symbolic_compactification import generate_report, load_workspace, verify_hypothesis; workspace = load_workspace(".venv/e11/workspaces/physicist-alpha"); run = verify_hypothesis(workspace); print(run.result); report = generate_report(workspace, run); print(report.path)'
```

It printed `ZERO` and the generated report path.

### Intentional NONZERO replay

```bash
.venv/e11/bin/symbolic-compactification \
  init .venv/e11/workspaces/nonzero-case
# candidate.txt was changed to: (x + 1)**2 + 1
OPENAI_API_KEY='sk-e11-canary-please-redact' \
AUTHORIZATION='Bearer e11-auth-canary' \
SSC_E11_SECRET='e11-environment-canary' \
/usr/bin/time -p .venv/e11/bin/symbolic-compactification \
  verify .venv/e11/workspaces/nonzero-case
.venv/e11/bin/symbolic-compactification \
  report .venv/e11/workspaces/nonzero-case
rg -n 'sk-e11-canary-please-redact|e11-auth-canary|e11-environment-canary' \
  .venv/e11/workspaces/nonzero-case/runs
```

The verifier returned `NONZERO`, exit status 2, residual `-1`, and an exact
counterexample at `x = -2`. The canary scan found no match.

### Committed Demo C replay through the CLI

```bash
cp -R engineering/release_v0_1/demos/demo_c_unknown \
  .venv/e11/workspaces/demo-c-cli
/usr/bin/time -p .venv/e11/bin/symbolic-compactification \
  inspect .venv/e11/workspaces/demo-c-cli
/usr/bin/time -p .venv/e11/bin/symbolic-compactification \
  verify .venv/e11/workspaces/demo-c-cli
/usr/bin/time -p .venv/e11/bin/symbolic-compactification \
  report .venv/e11/workspaces/demo-c-cli
```

The committed polygamma demonstration returned `UNKNOWN`, exit status 3, and
retained the undecided residual. Both CLI and report state that this is neither
likely true nor likely false and cannot promote scientific state. That wording
was clear to a first-time user.

### Source-byte checks

For each main workspace, source snapshots excluded only `runs/` and used:

```bash
find WORKSPACE -path '*/runs' -prune -o -type f -print0 \
  | sort -z | xargs -0 shasum -a 256 > BEFORE_OR_AFTER.sha256
diff -u BEFORE.sha256 AFTER.sha256
```

The final diff exit status was 0 for the custom ZERO workspace, intentional
NONZERO workspace, and copied Demo C workspace. Repeating `init` against the
existing custom workspace returned `WORKSPACE_ALREADY_EXISTS`, exit status 4,
and left the source snapshot unchanged.

## Results and timings

Times are one observed `time -p` replay, not a performance benchmark.

| operation | observed wall time | outcome |
|---|---:|---|
| create Python 3.12 virtual environment | 0.90 s | PASS |
| ordinary `pip install .` | 3.61 s | PASS |
| workspace `init` | 0.15 s | PASS |
| custom workspace `inspect` | 0.15 s | PASS |
| custom workspace `verify` | 0.62 s | `ZERO` |
| custom workspace `report` | 0.16 s | PASS |
| intentional refutation `verify` | 1.26 s | `NONZERO` |
| intentional refutation `report` | 0.15 s | PASS |
| Demo C `inspect` | 0.18 s | PASS |
| Demo C `verify` | 3.36 s | `UNKNOWN` |
| Demo C `report` | 0.18 s | PASS |

The recorded verifier runtimes were 0.438662 seconds (`ZERO`), 1.067804
seconds (`NONZERO`), and 3.145978 seconds (`UNKNOWN`). Peak memory was not
measured in this user-simulation lane.

## What worked for a new researcher

- The quickstart install completed without repository-local import leakage;
  the package imported from the fresh environment's `site-packages`.
- `init` made a small, readable workspace with no database or benchmark
  vocabulary.
- Editing expressions, explicit assumptions, notes, references, and the
  equivalence obligation was understandable after reading one format page.
- `inspect` exposed exact source text, parsed text, hashes, declared symbols,
  and member paths.
- `ZERO`, `NONZERO`, and `UNKNOWN` were visibly distinct and used distinct
  exit statuses 0, 2, and 3.
- `NONZERO` included an exact residual and exact counterexample.
- `UNKNOWN` was presented as a legitimate fail-closed result, never success.
- Verification created a non-overwriting run directory with result,
  provenance, and report artifacts.
- `inspect`, `verify`, `report`, the Python API replay, and refused repeated
  initialization did not change researcher source bytes.
- Environment secret canaries were absent from all scanned run artifacts.

## Release-critical blockers

1. **Release identity is not the requested alpha identity.** The installed
   distribution and both CLI commands report package version `0.3.0`; the
   requested alpha identity is `0.1.0-alpha`. `pip show` also exposes the old
   summary, "Agent-native symbolic compactification and exact certification
   engine," instead of the approved research-preview positioning. Engine and
   protocol versions may remain historically versioned, but the external
   distribution/release identity must be deliberate and documented.

2. **Run provenance does not record all installed dependency versions.** The
   fresh environment installed PyYAML 6.0.3, SymPy 1.14.0, and mpmath 1.3.0,
   while `provenance.json` contains only
   `{"dependency_versions":{"sympy":"1.14.0"}}`. At minimum the direct
   runtime dependency PyYAML is missing, contrary to the run-provenance
   contract.

3. **The human report is materially thinner than its documented contract.**
   `REPORT.md` contains the aggregate result, member paths, residual, basic
   versions, and two top-level hashes. It does not summarize declared
   assumptions, expression/member hashes, project objective, hypothesis
   reconstruction/latent/operator fields, notes/references grounding,
   dependency versions, warnings, or a concrete artifact inventory. These are
   promised by the quickstart and are needed for a provenance-rich grounded
   report without forcing a physicist to reverse-engineer JSON.

4. **Default parse and compile diagnostics are not actionable enough.** A
   malformed expression made `inspect` print only
   `error: EXPRESSION_PARSE_FAILURE`; workspace `verify` added only the generic
   action "correct the declared workspace or hypothesis and retry." Neither
   names the offending member nor gives a safe syntax reason. An unsupported
   relation similarly reports `UNSUPPORTED_RELATION` without the obligation
   id or submitted relation. Stable codes and hidden tracebacks are good, but
   a first-time user cannot locate the correction efficiently.

5. **`ASSUMPTION_REQUIRED` is advertised but is not a workspace API result.**
   The quickstart presents it as a possible `verify` outcome, while
   `research_api.PUBLIC_RESULTS` excludes it and the external equivalence
   compiler has no route that emits it. The release must either add a genuine
   fail-closed emission path or document it as reserved/not emitted by Mode A
   v0.1. A status that users cannot actually receive should not be presented
   as active behavior.

## Non-blocking friction

- `inspect` reports `"sums": 0` and `"products": 0` for expressions that
  visibly contain ordinary addition and multiplication. Those counters refer
  to explicit bound `Sum`/`Product` nodes, but the CLI does not label that
  distinction. Renaming or explaining them would prevent a misleading first
  impression.
- The stable hypothesis JSON is necessarily more verbose than the two
  expressions. The documented simple form helps, but `init` demonstrates only
  the full form; a short-form example would lower first-use friction.
- `verify` already writes `REPORT.md`, so the subsequent `report` command is a
  display/retrieval step. The quickstart could state this explicitly.

## Readiness score from this lane

| category | E11 assessment | evidence |
|---|---|---|
| INSTALL | PARTIAL | clean install passes; release identity does not |
| CLI | PARTIAL | workflow passes; diagnostics are too generic |
| PYTHON_API | PASS | documented minimal replay succeeds |
| WORKSPACE | PASS | readable format, strict init, source-safe |
| PROVENANCE | PARTIAL | hashes/routes/runtimes pass; dependency inventory incomplete |
| FAIL_CLOSED | PASS | distinct ZERO/NONZERO/UNKNOWN and error exits |
| SECURITY | PASS | canaries absent; no default tracebacks |
| DEMOS | PASS | committed Demo C replays through all required CLI commands |
| DOCS | PARTIAL | quickstart works; report/status contracts overstate behavior |
| REPRODUCIBILITY | PARTIAL | local replay passes; this lane is not the final clean-room gate |

The critical categories contain no observed mathematical unsoundness or source
mutation. `INTERNAL_ONLY` is driven by concrete release-contract gaps that can
be corrected entirely within the authorized engineering program.
