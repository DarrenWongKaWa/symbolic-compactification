# External-user post-fix retest — E11

## Verdict

`INTERNAL_ONLY`

All five blockers reported by the first E11 simulation are fixed at integrated
commit `590bc1c5da7bc36ed36c23510f6b2ca9422e62f9`. The documented Mode A
workflow now installs cleanly, returns precise fail-closed results, preserves
researcher source bytes, and produces a substantially complete human report.

Two release-contract blockers remain: an ordinary installed run records its
originating Git commit as `unknown`, and the root README used as the packaged
long description still presents an obsolete scientific-era status and old
workflow. This is an engineering assessment, not a scientific verdict.

## Retest posture

The operator acted as a theoretical physicist unfamiliar with the internals.
Only public release documentation and installed CLI/API surfaces were used for
the workflow. No production code or frozen scientific evidence was changed.

- Host: macOS 26.4 arm64
- Python: CPython 3.12.13
- Source commit: `590bc1c5da7bc36ed36c23510f6b2ca9422e62f9`
- Installation: fresh virtual environment and ordinary `pip install .`, not
  editable
- Installed location:
  `/private/tmp/ssc-e11-retest.vrPl8O/venv/lib/python3.12/site-packages/symbolic_compactification`
- Installed runtime dependencies: PyYAML 6.0.3, SymPy 1.14.0, mpmath 1.3.0
- Built wheel SHA-256 reported by pip:
  `5ffacac6e0e038cfcbf3c8c6cb883fd0c8ccc325a961192471e35b9244d4261a`
- Temporary replay root: `/private/tmp/ssc-e11-retest.vrPl8O`

Generated workspaces and run records remained outside the repository and were
not committed.

## Clean non-editable installation

Material commands:

```bash
python3.12 -m venv /private/tmp/ssc-e11-retest.vrPl8O/venv
/private/tmp/ssc-e11-retest.vrPl8O/venv/bin/python -m pip install .
/private/tmp/ssc-e11-retest.vrPl8O/venv/bin/python -m pip check
/private/tmp/ssc-e11-retest.vrPl8O/venv/bin/symbolic-compactification --version
/private/tmp/ssc-e11-retest.vrPl8O/venv/bin/ssc --version
```

Observed:

- virtual-environment creation: 0.91 seconds;
- non-editable installation: 3.84 seconds;
- `pip check`: no broken requirements;
- distribution version: PEP 440 `0.1.0a0`;
- both CLIs: `0.1.0-alpha (PEP 440 0.1.0a0; engine 0.3.0,
  protocol 0.3.0)`;
- distribution summary: `Context-grounded symbolic hypotheses with
  fail-closed verification.`;
- import resolved inside the fresh environment's `site-packages`, not the
  checkout.

## First-time physicist workflow

The installed CLI created a fresh workspace. The researcher then supplied:

- current expression: `omega**2 + 2*m*omega + m**2`;
- candidate: `(omega + m)**2`;
- explicit real declarations for `omega` and nonzero `m`;
- a typed equivalence hypothesis with latent-object, operator, reconstruction,
  and obligation fields;
- a short research note and manually curated notebook reference.

The public sequence succeeded:

```bash
symbolic-compactification init WORKSPACE
symbolic-compactification inspect WORKSPACE
symbolic-compactification verify WORKSPACE
symbolic-compactification report WORKSPACE
```

`inspect` showed both exact source texts, hashes, parsed forms, symbols,
assumptions, member roles, notes/references paths, and structural summaries.
`verify` returned `ZERO` and exit 0. `report` rendered the persisted report.
The installed Python API quickstart also returned `ZERO`:

```python
from symbolic_compactification import (
    generate_report,
    load_workspace,
    verify_hypothesis,
)

workspace = load_workspace("WORKSPACE")
run = verify_hypothesis(workspace)
print(run.result)
report = generate_report(workspace, run)
print(report.path)
```

The two recorded successful runs were
`20260831T135129Z-b27911c2` (CLI) and
`20260831T135301Z-32701f68` (Python API).

## Re-audit of the five prior blockers

| prior blocker | post-fix result | direct evidence |
|---|---|---|
| alpha release identity | PASS | package installs as `0.1.0a0`; both CLIs explicitly display `0.1.0-alpha` while preserving engine/protocol `0.3.0` |
| PyYAML and SymPy provenance | PASS | every inspected `provenance.json` and `REPORT.md` records `pyyaml: 6.0.3` and `sympy: 1.14.0` |
| complete human `REPORT.md` | PASS | report includes project/objective, declared symbols/functions, full typed hypothesis, grounding metadata, all input/member hashes, per-obligation evidence, versions, dependency versions, warnings, and fixed artifact inventory |
| safe actionable parse/compile diagnostics | PASS | parse failure names `expressions/candidate.txt`; compile failure points to `hypotheses/hypothesis.json#/proof_obligations/0/relation`; both provide stable codes, bounded correction hints, exit 4, persisted reports, and no default traceback |
| operational `ASSUMPTION_REQUIRED` | PASS | omitting declared `x` from `assumptions_used` returns `ASSUMPTION_REQUIRED`, code `DECLARED_ASSUMPTIONS_OMITTED`, a precise source/hint, exit 4, and no obligation execution |

The complete success report was inspected directly, not inferred from a unit
test. Notes and references are grounded by path/hash/size while their contents
are not copied. The report's artifact inventory names `provenance.json`,
`result.json`, and `REPORT.md`.

## Verdict and ingestion-path checks

| case | CLI result | exit | evidence |
|---|---|---:|---|
| researcher factorization | `ZERO` | 0 | exact residual `0` |
| intentional mutation `(x + 1)**2 + 1` | `NONZERO` | 2 | residual `-1`; exact counterexample `x = -2`, value `-1` |
| committed Demo C | `UNKNOWN` | 3 | undecided polygamma residual retained; report explicitly forbids promotion |
| malformed `sin(` candidate | `PARSE_FAILURE` | 4 | stable parse code, exact workspace-relative member, correction hint |
| unsupported `proportional` relation | `COMPILE_FAILURE` | 4 | stable compile code, JSON-pointer-like source, instruction to use the supported relation |
| omitted declared assumption | `ASSUMPTION_REQUIRED` | 4 | stable assumption code; no inferred repair |

The outputs never presented `UNKNOWN`, parsing failure, compilation failure,
or assumption gating as success.

## Demo CLI replay

The committed `demo_c_unknown` workspace was copied outside the checkout and
run through the installed CLI:

```bash
symbolic-compactification inspect DEMO_C_COPY
symbolic-compactification verify DEMO_C_COPY
symbolic-compactification report DEMO_C_COPY
```

Observed times were 0.18 seconds, 3.18 seconds, and 0.17 seconds. The result
was `UNKNOWN`, exit 3, with the exact undecided residual preserved. The report
states that `UNKNOWN` is neither likely true nor likely false and cannot
promote scientific state. This agrees with `DEMOS.md` and `SEMANTICS.md`.

## Source immutability

Before/after SHA-256 manifests excluded only each tool-owned `runs/`
directory. Every comparison returned diff exit 0 for:

- the custom `ZERO` CLI workflow;
- the documented Python API workflow;
- intentional `NONZERO`;
- parse failure;
- compile failure;
- `ASSUMPTION_REQUIRED`;
- copied Demo C `UNKNOWN`;
- the secret-like malformed input case.

Repeating `init` against the populated workspace returned
`WORKSPACE_ALREADY_EXISTS`, exit 4, and also left all source hashes unchanged.

## Secret audit

Verification was run with these synthetic environment canaries:

- `OPENAI_API_KEY=sk-e11-retest-canary`;
- `AUTHORIZATION=Bearer e11-retest-auth-canary`;
- `SSC_E11_SECRET=e11-retest-env-canary`.

A separate malformed researcher expression contained a synthetic
`sk-proj-...` canary. It produced only a stable parse code, member path, and
bounded hint. Scans of all generated run artifacts found none of the four
canary values and none of the environment-variable/header names. Source files
were not altered to achieve redaction.

## Documentation accuracy

The release-local `QUICKSTART.md`, `WORKSPACE_FORMAT.md`, `SEMANTICS.md`,
`LIMITATIONS.md`, `INSTALLATION.md`, and `DEMOS.md` accurately describe the
tested workspace/API/CLI behavior. The installed help surface exposes exactly
the documented `init`, workspace `inspect`, workspace `verify`, and `report`
commands, plus the stated compatibility commands. Lightweight reference
handling, optional proposer status, and fail-closed limitations are presented
without a scientific-discovery claim.

Two documentation/provenance discrepancies remain release-blocking below.
Minor non-blocking friction remains: `inspect` emits the lower-level code
`EXPRESSION_PARSE_FAILURE` rather than the quickstart's generic phrase
`PARSE_FAILURE`, though workspace `verify` correctly emits the public result;
and structural `sums`/`products` counters mean explicit bound `Sum`/`Product`
nodes, which is not apparent from the human CLI output.

## Remaining release blockers

1. **Installed provenance does not identify the originating commit.** Every
   non-editable installed run recorded `"git_commit": "unknown"`. The
   implementation asks Git from beside the installed module, where ordinary
   wheel/site-packages installs have no `.git` directory. The release contract
   requires a Git commit for every run; a field containing `unknown` is not an
   originating commit. Build-time provenance or another bounded immutable
   package identity is needed, then must be replayed from a non-editable
   install.

2. **The packaged root README is obsolete.** `pyproject.toml` uses the root
   `README.md` as the distribution long description, but that file still
   describes an old Publication E state, says no paper snapshot is frozen,
   foregrounds historical research lines, and teaches the legacy session
   workflow instead of the v0.1 researcher workspace. A first-time installed
   user therefore receives documentation inconsistent with the closed
   scientific boundary and the working preview interface. It should be
   consolidated to the approved release positioning and link the current
   workspace documentation.

## Readiness score from this lane

| category | E11 retest assessment | basis |
|---|---|---|
| INSTALL | PASS | fresh Python 3.12 non-editable install, metadata, both CLIs, and `pip check` pass |
| CLI | PASS | Mode A and all public failure statuses are actionable and fail closed |
| PYTHON_API | PASS | documented three-call replay succeeds from site-packages |
| WORKSPACE | PASS | readable schema, strict initialization, grounded context, source-safe behavior |
| PROVENANCE | FAIL | complete hashes/dependencies/report, but installed origin commit is `unknown` |
| FAIL_CLOSED | PASS | ZERO/NONZERO/UNKNOWN and all ingestion gates remain distinct |
| SECURITY | PASS | environment and source canaries absent from generated artifacts |
| DEMOS | PASS | required one-demo CLI retest reproduces committed Demo C |
| DOCS | FAIL | release-local docs work; packaged root README is stale and externally misleading |
| REPRODUCIBILITY | PARTIAL | this independent replay passes; the separate final clean-room gate owns full release reproducibility |

No full suite or release decision was run in this lane. Those remain
coordinator gates. The `INTERNAL_ONLY` result follows from the two concrete
release-contract failures above, not from verifier mathematics or scientific
performance.
