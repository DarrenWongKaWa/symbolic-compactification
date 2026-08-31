# symbolic-compactification

**Context-grounded symbolic hypotheses with fail-closed verification.**

Status: v0.1 research-preview engineering candidate.
Scientific experimentation is closed during this consolidation phase; this
repository is not opening a new discovery campaign. The alpha name is earned
only if the installation, safety, reproducibility, demo, and release-review
gates pass.
See [SCIENTIFIC_EXPERIMENTS_CLOSED.md](SCIENTIFIC_EXPERIMENTS_CLOSED.md) for
the research-line lock.

The release-critical workflow is **Mode A: verify my hypothesis**. A researcher
provides expressions, assumptions, notes, references, and a candidate symbolic
relation. The tool grounds that relation to named source files, compiles its
explicit proof obligations, runs the deterministic verifier, and writes an
immutable, provenance-rich run report.

The verifier—not a model, explanation, or confidence score—is the only judge.
Only `ZERO` certifies the submitted obligation under the declared engine
semantics and assumptions.

## Start here

- [Quickstart](engineering/release_v0_1/QUICKSTART.md) — the canonical CLI and
  Python workflows
- [Installation](engineering/release_v0_1/INSTALLATION.md) — Python 3.12,
  editable, ordinary, and wheel installation
- [Workspace format](engineering/release_v0_1/WORKSPACE_FORMAT.md) — source
  files and stable hypothesis schema
- [Result semantics](engineering/release_v0_1/SEMANTICS.md) — exact meanings,
  composite obligations, and exit codes
- [Limitations](engineering/release_v0_1/LIMITATIONS.md) — coverage and claim
  boundaries that must be read before scientific use
- [Security](engineering/release_v0_1/SECURITY.md) — secret handling and
  bounded run metadata
- [Release demos](engineering/release_v0_1/DEMOS.md) — `ZERO`, grounded
  `ZERO`, and intentional `UNKNOWN`

## Install

The alpha release gate uses CPython 3.12. From a checkout:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/symbolic-compactification --version
```

The shorter `ssc` entry point is equivalent. Core verification requires no
model service and no API key.

## Canonical researcher workflow

Create a workspace at a path that does not already exist:

```bash
symbolic-compactification init my-symbolic-project
```

The generated workspace is deliberately small:

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

Replace the example expressions and declare every symbol and allowed undefined
function. The alpha operationally supports only `real: true` symbols, an
optional `nonzero` flag, and declared functions. It rejects `real: false`
because the complex-domain namespace contract is not safe for certification.
It cannot enforce positivity, general inequalities,
excluded poles, parameter identities, boundary conditions, symmetries, or
limit order. Do not submit a claim that depends on one of those predicates as
being within alpha certification. Then inspect, verify, and render the report:

```bash
symbolic-compactification inspect my-symbolic-project
symbolic-compactification verify my-symbolic-project
symbolic-compactification report my-symbolic-project
```

`inspect` reads and summarizes the workspace without changing source files.
`verify` creates a new run under `runs/<run_id>/`. `report` renders from that
recorded run. Original expressions, notes, assumptions, references, and
hypotheses are never overwritten by these commands.

## Result contract

| Result | Meaning |
|---|---|
| `ZERO` | Exact certification that the declared obligation vanishes under the recorded engine semantics and assumptions. |
| `NONZERO` | Exact evidence refutes the submitted universal identity under the recorded verification route. |
| `UNKNOWN` | The verifier cannot decide. Nothing is certified or promoted. |
| `PARSE_FAILURE` | A source cannot be parsed safely in the supported expression language. |
| `COMPILE_FAILURE` | The hypothesis cannot be lowered to a supported obligation without changing its meaning. |
| `ASSUMPTION_REQUIRED` | `assumptions_used` is missing or omits a symbol already declared in the assumptions file; this is not needed-assumption discovery. |

`UNKNOWN` is not likely true, likely false, partial success, or permission to
advance scientific state. Approximate numerical agreement never becomes
`ZERO` or `NONZERO`.

## Python API

The workspace façade mirrors the CLI:

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

`load_workspace(...)` validates a read-only snapshot,
`verify_hypothesis(...)` compiles and adjudicates its declared obligations,
and `generate_report(...)` renders persisted evidence. Fail-closed statuses are
returned as structured results; they are not success-like exceptions.

## Provenance and source safety

Each run records the tool and semantic versions, Python and direct dependency
versions, verifier route, runtime, warnings, source hashes, hypothesis and
assumption hashes, and the exact source revision of an installed build when it
was built from a Git checkout. Credential-shaped values are excluded or
redacted; `.env` files and unrelated process environment variables are not
inventoried.

Generated build provenance is written into the build artifact, never into the
source package at runtime. The dirty-state policy and `unknown` fallback are
documented in [Installation](engineering/release_v0_1/INSTALLATION.md).

## Capability boundary

The preview supports exact hypothesis adjudication in covered domains,
explicit source grounding, structured observations, provenance, and
reproducible runs. It does **not** establish robust mathematical
representation invention, universal scientific simplification, or general
exact limit certification.

Context-conditioned representation invention remains unestablished and was
not tested at realistic scale because too few adjudicable real scientific
tasks were available. That is an evidence boundary, not a finding that the
idea works or fails. Finite Laurent coefficients alone never certify an exact
limit without supported remainder control.

The alpha cannot machine-enforce positivity, general inequalities, excluded
poles, parameter identities, boundaries, symmetries, or limit order. Claims
that depend on those predicates are outside its supported certification
boundary; contextual prose does not extend verifier semantics.

This tool is not an autonomous theoretical physicist, a universal theorem
prover, or a guaranteed simplifier. Verification coverage is incomplete;
`UNKNOWN` is expected on hard expressions. Exactness is always relative to the
recorded, machine-supported engine semantics. Reference ingestion is
lightweight: file paths, notes, curated excerpts, and optional metadata—not
full paper understanding or RAG.

## Mode B: propose then verify

Model-assisted proposal is optional and experimental. It is not required for
the v0.1 release and no workspace-level `propose` command is promised by this
preview. Any proposed candidate must be typed, grounded to source members,
compiled into obligations, and sent through the same verifier. Proposer text
can never promote state.

## Legacy and advanced compatibility

The researcher workspace above is the primary external interface. Existing
file-oriented and session commands remain available for established users:

```bash
symbolic-compactification inspect expression.txt --symbols symbols.json
symbolic-compactification verify \
  --current current.txt --candidate candidate.txt --symbols symbols.json
symbolic-compactification init-session --help
symbolic-compactification step --help
symbolic-compactification summary --help
symbolic-compactification finalize --help
```

The lower-level Python APIs `load_expression(...)`,
`verify_equivalent(...)`, and the stateful session functions remain
compatibility surfaces. Their files and namespace schemas are different from
the researcher-workspace YAML format; do not translate scientific assumptions
silently.

Structural observation (`symbolic-compactification observe`) is also retained
as an analysis surface. Observations and named patterns are hypotheses, not
proof, until the required obligations receive `ZERO`.

## Development identities

- research-preview release: `0.1.0-alpha` (PEP 440: `0.1.0a0`)
- deterministic engine: `0.3.0`
- agent protocol: `0.3.0`

Engine and protocol identities remain frozen in this engineering program. For
developer installation, tests, architecture, and the agent-native operating
contract, see [Installation](engineering/release_v0_1/INSTALLATION.md),
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and [AGENTS.md](AGENTS.md).
