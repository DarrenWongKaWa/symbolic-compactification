# symbolic-compactification

**Typed derivation audit with fail-closed exact verification.**

**Derivation Audit Alpha** (`0.2.0-alpha`) on
`engineering/derivation-audit-v0.2`, tag `derivation-audit-v0.2.0-alpha`.
This is an additive engineering layer on the still-supported v0.1 **Mode A:
verify my hypothesis** preview (`0.1.0-alpha`, tag
`research-preview-v0.1.0-alpha`). It is **not** a stable v1.0 release and is
**not** merged to `main`.

A derivation audit inventories manuscript equations, records typed
equation-to-equation edges, lowers only supported edges to executable
residuals, and lets the deterministic verifier judge each residual. LLM text
cannot create verified status. The verified table is generated, not authored.

Exact algebraic and local structural identities that were lowered to
executable residuals were evaluated under the declared symbolic semantics.
Only obligations returning exact ZERO are listed as machine-verified.

Definitions, integral-level arguments, asymptotic remainder claims, and
unsupported transformations are tracked separately rather than being
misreported as exact algebraic identities.

This tool does not write papers. Scientific experimentation remains closed.
See [SCIENTIFIC_EXPERIMENTS_CLOSED.md](SCIENTIFIC_EXPERIMENTS_CLOSED.md) and
[FINAL_ENGINEERING_RELEASE.md](FINAL_ENGINEERING_RELEASE.md).

## Start here

### 1. Derivation audit (v0.2 Research Preview Alpha)

This is the public product surface.

- [Overview](docs/DERIVATION_AUDIT.md)
- [Quickstart](docs/AUDIT_QUICKSTART.md)
- [Edge types](docs/EDGE_TYPES.md)
- [Status semantics](docs/STATUS_SEMANTICS.md)
- [Reviewer package](docs/REVIEWER_PACKAGE.md)
- [Public demos A/B/C](docs/PUBLIC_DEMOS.md)
- [Privacy](docs/PRIVACY.md)
- [Limitations](docs/DERIVATION_AUDIT_LIMITATIONS.md)
- [Threat model](docs/THREAT_MODEL.md)

```bash
symbolic-compactification audit init my-paper-audit
# inventory → inspect → verify → table → report → package
```

Public examples: `engineering/derivation_audit_v0_2/demos/{A,B,C}/`.
Demo C is intentional: coefficient identities can be `ZERO` while the
enclosing asymptotic remainder stays `UNKNOWN`.

### 2. Mode A: verify my hypothesis (v0.1, still supported)

A researcher provides expressions, assumptions, notes, references, and a
candidate symbolic relation. The tool grounds that relation to named source
files, compiles its explicit proof obligations, runs the deterministic
verifier, and writes an immutable, provenance-rich run report
(`init` → `inspect` → `verify` → `report`). The proposer is experimental and
never promotes scientific state. The verifier—not a model, explanation, or
confidence score—is the only judge. Only `ZERO` certifies the submitted
obligation under the declared engine semantics and assumptions.

- [Quickstart](engineering/release_v0_1/QUICKSTART.md)
- [Installation](engineering/release_v0_1/INSTALLATION.md)
- [Workspace format](engineering/release_v0_1/WORKSPACE_FORMAT.md)
- [Result semantics](engineering/release_v0_1/SEMANTICS.md)
- [Limitations](engineering/release_v0_1/LIMITATIONS.md)
- [Security](engineering/release_v0_1/SECURITY.md)
- [Release demos](engineering/release_v0_1/DEMOS.md)

v0.1 release gates that passed: clean install, CLI, Python API, workspace,
provenance, fail-closed semantics, security, three demos, documentation, and
reproducibility. Release-critical tests: **17/17**. Clean-room replay:
**PASS**. Three independent reviewers: **ALPHA_READY**.

The historical full test suite is **not** fully green:
`2049 passed, 24 failed`. Those failures are frozen historical authority
drift, one optional client, and cache enumeration. They were disclosed, not
rewritten, to make a release. GitHub Actions merge checks follow the same
contract: they require `pytest -m release_critical`,
`pytest -m derivation_audit_release_critical`, the clean-room firewall, and a
package/CLI smoke. `pytest tests/` still runs, but only as a non-blocking
informational job.

### 3. Research history

Closed campaigns, capability boundary, and frozen negatives:
[SCIENTIFIC_EXPERIMENTS_CLOSED.md](SCIENTIFIC_EXPERIMENTS_CLOSED.md),
[CAPABILITY_BOUNDARY.md](CAPABILITY_BOUNDARY.md),
[NEGATIVE_RESULTS.md](NEGATIVE_RESULTS.md).

## Install

The alpha release gate uses CPython 3.12. From the v0.2 tag:

```bash
git clone --branch derivation-audit-v0.2.0-alpha \
  https://github.com/DarrenWongKaWa/symbolic-compactification.git
cd symbolic-compactification
python3.12 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/symbolic-compactification --version
```

The shorter `ssc` entry point is equivalent. Core verification requires no
model service and no API key. This tag is **not** on `main`.

## Canonical researcher workflow (derivation audit)

```bash
symbolic-compactification audit init my-paper-audit
# add manuscript.tex / expressions / edges
symbolic-compactification audit inventory my-paper-audit
symbolic-compactification audit inspect my-paper-audit
symbolic-compactification audit verify my-paper-audit
symbolic-compactification audit table my-paper-audit
symbolic-compactification audit package my-paper-audit
cd my-paper-audit/reviewer-verification-package
./reproduce.sh
```

`verify` records a run. It does not mean the derivation is certified.
Only rows in `TABLE_VERIFIED.md` with engine `ZERO` and integrity PASS are
machine-verified. The verified table is generated from those records, not
authored.

## Mode A workflow (v0.1, still supported)

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

Audit-workspace statuses such as `NOT_LOWERED`, `DEFINITION`, `RECORDED`, and
`SPLIT` are documented in [docs/STATUS_SEMANTICS.md](docs/STATUS_SEMANTICS.md).

## Python API

The Mode A workspace façade mirrors the CLI:

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

Audit workspaces use `symbolic-compactification audit …` and
`symbolic_compactification.audit.workspace`.

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
reproducible runs. The derivation-audit layer additionally tracks typed
derivation edges and generates reviewer tables from machine records. It does
**not** establish robust mathematical representation invention, universal
scientific simplification, or general exact limit certification.

Context-conditioned representation invention remains unestablished and was
not tested at realistic scale because too few adjudicable real scientific
tasks were available. That is an evidence boundary, not a finding that the
idea works or fails. Finite Laurent coefficients alone never certify an exact
limit without supported remainder control.

The alpha cannot machine-enforce positivity, general inequalities, excluded
poles, parameter identities, boundaries, symmetries, or limit order. Claims
that depend on those predicates are outside its supported certification
boundary; contextual prose does not extend verifier semantics.

This tool is not a substitute for a scientist, a universal theorem
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

The researcher workspace above is the primary v0.1 external interface. Existing
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
- derivation-audit protocol: `0.2.0` (alpha in development; package identity
  unchanged)

Engine and protocol identities remain frozen in this engineering program. For
developer installation, tests, architecture, and the agent-native operating
contract, see [Installation](engineering/release_v0_1/INSTALLATION.md),
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and [AGENTS.md](AGENTS.md).
