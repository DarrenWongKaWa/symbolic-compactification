# Quickstart

This guide exercises **Mode A: verify my hypothesis**, the release-critical
workflow. It does not require a model or API key.

The workspace-level commands and Python façade below are the v0.1 interface.
They must pass the integrated clean-room replay before the release may be
called `RESEARCH_PREVIEW_ALPHA`.

## 1. Install from a checkout

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/symbolic-compactification --version
```

`ssc` is an equivalent short command. See [INSTALLATION.md](INSTALLATION.md)
for editable and wheel-install workflows.

## 2. Create a workspace

Choose a path that does not exist. Initialization never overwrites a file or
an existing directory.

```bash
symbolic-compactification init my-symbolic-project
```

The new workspace contains a small exact-equivalence example:

```text
my-symbolic-project/
├── project.yaml
├── expressions/
│   ├── current.txt
│   └── candidate.txt
├── notes/research_notes.md
├── assumptions/assumptions.yaml
├── references/README.md
├── hypotheses/hypothesis.json
└── runs/
```

## 3. Supply your scientific inputs

Replace the example text in `expressions/current.txt` and
`expressions/candidate.txt`. Edit `assumptions/assumptions.yaml` so every
symbol and allowed undefined function is declared. The alpha machine-enforces
only `real: true` symbols, an optional `nonzero` flag, and the declared
function namespace. It rejects `real: false` fail-closed. It cannot represent
positivity, general inequalities, excluded poles, parameter
identities, boundary conditions, symmetries, or limit order. A hypothesis that
depends on any such predicate is outside the supported alpha certification
boundary; adding prose to notes or references does not change that. Update
`hypotheses/hypothesis.json` so its members and obligations point to the exact
source files being compared.

Notes and references provide human context and provenance. They do not create
mathematical assumptions, proof obligations, or verifier facts.

## 4. Inspect without changing source files

```bash
symbolic-compactification inspect my-symbolic-project
```

Inspection should show the source members and hashes, declared assumptions,
parsed objects, and a structural summary. A parsing problem is reported as
`PARSE_FAILURE`; it is never converted into a speculative result.

## 5. Verify the declared hypothesis

```bash
symbolic-compactification verify my-symbolic-project
```

The command compiles the declared obligations, evaluates them through the
exact verifier, prints a result, and writes a new immutable run directory
under `my-symbolic-project/runs/`. It does not rewrite any source file.

Interpret the result literally:

- `ZERO`: the submitted equality is exactly certified under the declared
  engine semantics and assumptions.
- `NONZERO`: exact evidence refutes the submitted universal identity under the
  verification route.
- `UNKNOWN`: the verifier cannot decide; nothing is certified or promoted.
- `PARSE_FAILURE`: at least one source cannot be parsed safely.
- `COMPILE_FAILURE`: the hypothesis cannot be lowered to a supported proof
  obligation without changing its meaning.
- `ASSUMPTION_REQUIRED`: `assumptions_used` is missing or omits a symbol
  already declared in the assumptions file. It does not discover assumptions
  that the formula needs.

Exit status and generated JSON are automation aids; the named scientific
result remains authoritative. See [SEMANTICS.md](SEMANTICS.md).

## 6. Render the report

```bash
symbolic-compactification report my-symbolic-project
```

The report summarizes the hypothesis, grounded members, assumptions, proof
obligations, result, warnings, hashes, verifier route, tool/dependency
versions, runtime, and generated artifact paths. It remains inside the run
directory. Always retain the report and `provenance.json` with any scientific
claim that depends on the run.

## Python API

The same workflow is available without invoking the CLI:

```python
from symbolic_compactification import (
    generate_report,
    load_workspace,
    verify_hypothesis,
)

workspace = load_workspace("my-symbolic-project")
run = verify_hypothesis(workspace)
print(run.result)

report = generate_report(workspace, run)
print(report.path)
```

The v0.1 API contract is:

- `load_workspace(path)` validates and loads a read-only snapshot, including
  exact source hashes;
- `verify_hypothesis(workspace)` compiles and adjudicates the declared
  obligations, records the run, and returns a typed result;
- `generate_report(workspace, run)` renders a human-readable report from the
  recorded result without changing source inputs.

Catch `WorkspaceError` for malformed workspace inputs. Verification and
compilation outcomes are returned as structured statuses, not raised as
success-like exceptions. The integrated API reference is authoritative for
the final return-type field names; this example must be replayed before alpha
release.

## Existing CLI compatibility

Existing file-oriented and session workflows remain available. In particular:

```bash
symbolic-compactification inspect expression.txt --symbols symbols.json
symbolic-compactification verify \
  --current current.txt \
  --candidate candidate.txt \
  --symbols symbols.json
symbolic-compactification init-session --help
symbolic-compactification step --help
symbolic-compactification summary --help
symbolic-compactification finalize --help
```

The legacy namespace file is JSON; the researcher-workspace assumptions file
is YAML. Do not silently translate one into the other by hand for a scientific
run. The workspace commands own that validated normalization step.

## Optional proposal mode

Any future `propose` command is experimental. Its output is only a hypothesis:
it must be grounded to source members and sent through the same verification
path. Proposer text, rankings, or model confidence can never certify a result.
