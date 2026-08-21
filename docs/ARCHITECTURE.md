# Architecture

This repository implements one small pipeline:

```text
scientific source
  -> adapter / strict parser
  -> semantic ExpressionRecord
  -> structural inspection and candidate proposal
  -> targeted, budgeted verification representation
  -> ZERO | NONZERO | UNKNOWN
  -> recorded state transition
  -> explicit FINAL CERTIFIED FORM
```

The human owns scientific meaning and assumptions. A coding agent owns
structure discovery and candidate proposals. Only the deterministic engine
owns adjudication and certification.

## Responsibility map

| Stage | Module | Responsibility and boundary |
|---|---|---|
| Source adapter | `adapters/wolfram_text.py` | Translate supported Wolfram text to structural SymPy; never execute Mathematica or certify |
| Native ingestion | `parser.py` | Enforce characters, tokens, depth, size, symbols, functions, and assumptions before safe construction |
| Semantic record | `models.py` | Versioned expression, verdict, state, hashes, and orthogonal status axes |
| Structural view | `structure.py` | Deterministic inventories and explicitly diagnostic finite lowering |
| Proposer protocol | `conjecture.py`, `roles/STRUCTURAL_PROPOSER.md` | Construct attention-isolated packets and record hypotheses; never invoke a model or promote |
| Agent skill | `.grok/skills/symbolic-compactification/SKILL.md` | Configurable proposer (default `main`, optional `subagent` / `auto`); does not certify |
| Candidate transforms | `transforms.py`, `rules.py` | Small named operations, op caps, assumption gates, and local checkability |
| Resource control | `budgets.py` | Central operation budgets and engine-owned process lifecycle |
| Adjudication | `verifier.py` | Structural residual, bounded targeted lowering, exact proof/counterexample, fail-closed UNKNOWN |
| State transition | `pipeline.py` | One verify-record-promote path with namespace and hash binding |
| Persistence | `session.py` | Atomic JSON records, monotonic steps/packets, immutable run identity, promotion gate |
| Human result | `reporting.py` | Exact expansion check and complete machine/human artifacts |
| Shell interface | `cli.py` | Argument/file adapter and human/JSON output; no certification policy. `inspect` emits `structure_summary`; `init-session --proposer-mode` records skill intent; `summary` prints `run_summary` |

Dependencies point inward toward `models.py`. The pipeline composes parser,
verifier, and session behavior; the CLI depends on the pipeline. Local imports
between reporting/conjecture and session avoid import cycles without creating
a framework.

## Representation boundary

`ExpressionRecord.text` and its raw-file SHA-256 own the ingested source.
`parsed_expr` is the highest-level useful SymPy representation. `Sum`,
`Product`, ordered `Piecewise` branches, undefined functions, and common
factors remain visible.

Verification constructs `current - candidate` under a process budget. A small
residual may be expanded and simplified under named budgets; a large residual
receives only targeted primitives. Those execution forms are evidence for one
adjudication. They never overwrite the semantic source record.

No custom symbolic IR exists. Internal transform results that cross a process
boundary are reconstructed from trusted SymPy text because SymPy pickling can
evaluate deliberately factored nodes.

## State machine

```text
candidate proposal
  -> HYPOTHESIS / proof=HYPOTHESIS
  -> deterministic adjudication
       ZERO     -> CERTIFIED / proof=PROVEN -> promote exact candidate
       NONZERO  -> UNVERIFIED / proof=REFUTED -> retain current
       UNKNOWN  -> UNVERIFIED / proof=PROOF_REQUIRED -> retain current
```

The assumption axis is independent:

- `NONE`: no assumption claim accompanies the step;
- `DECLARED`: the persisted namespace contains the relevant assumptions;
- `HUMAN_REQUIRED`: a new scientific choice is required and promotion is
  blocked even if a symbolic ZERO was separately obtained.

Promotion checks all of the following mechanically: last verdict ZERO,
`CERTIFIED`, `PROVEN`, an exact-zero evidence kind, current-state hash,
candidate raw hash and text, and no active human-assumption gate. The low-level
API cannot accidentally promote a different candidate after an unrelated ZERO.

## Determinism and provenance

Symbol declarations, function declarations, structural atoms, aliases, and
serialized hash inputs are explicitly sorted. Canonical JSON uses sorted keys.
Run JSON is atomically replaced and step/packet indices cannot overwrite an
existing record. The manifest captures the initial package, engine, protocol,
Git identity (including `-dirty`), and policy snapshot; each step captures its
own engine/Git identity and policy snapshot.

Externally meaningful rationale and structured proposals may be stored. Private
model reasoning and chain-of-thought are never stored.

## Resource lifecycle

Production symbolic work defaults to one owned process per expensive
operation. A readiness handshake establishes its process group before user or
SymPy code runs. Every supported exit path—success, timeout, worker exception,
and interceptable cancellation—terminates and reaps only registry-owned
workers. Termination is SIGTERM, bounded grace, then SIGKILL if required.

Nested process budgets execute their inner deadline in a thread inside the
outer owned worker. If the inner code does not stop, termination of the outer
worker removes that thread with the process; no detached nested process group
is created. Interactive/stdin execution uses POSIX `fork` when no importable
main file exists; CLI, pytest, and guarded scripts use `spawn`.

The guarantee does not include uncatchable host termination such as SIGKILL,
power loss, or kernel failure. Windows support is not claimed. Explicit
`thread` mode is a debugging compatibility mode and cannot forcibly stop every
C-level loop; it is not the production guarantee.

## Budget policy

The centralized budget policy names residual construction, expansion,
simplification, complex expansion, probe simplification, equality checks,
factor/factor-terms/together/cancel, and finite diagnostic expansion. Unknown
operations or invalid values fail explicitly. Series, limits, and
special-function normalization have no engine API yet; callers cannot request
them through the bounded engine by pretending they are supported.

A timeout becomes `UNKNOWN` with `TIME_BUDGET_EXCEEDED` evidence. It can never
be converted to ZERO or NONZERO.

## Error taxonomy

Errors use `AdapterError(code)` rather than a large class hierarchy. Important
families are:

- ingestion: `PARSE_ERROR`-equivalent concrete codes such as
  `SYMBOLIC_PARSE_FAILED`, `UNSUPPORTED_SYNTAX`-equivalent adapter codes, and
  `EXPRESSION_TOO_LARGE`;
- policy/resources: `*_POLICY_VALUE_INVALID`, `TIME_BUDGET_EXCEEDED`;
- verdict/state: `VERDICT_NOT_ZERO`, `CURRENT_STATE_MISMATCH`,
  `CANDIDATE_STATE_MISMATCH`, `HUMAN_AUTHORIZATION_REQUIRED`;
- proof/reporting: verifier `NONZERO`/`UNKNOWN`, `PROOF_REQUIRED`, and
  `REPORT_INCOMPLETE`;
- lifecycle/persistence: process telemetry `cleanup_status=FAILED`,
  `STEP_SEQUENCE_INVALID`, `STEP_ALREADY_EXISTS`, and
  `PACKET_ALREADY_EXISTS`.

CLI verdicts use exits 0/2/3. All input, policy, state, and persistence errors
use exit 4 and print the stable code.

## Version identities

- package/repository version changes for the installable release/API;
- engine version changes for parser, verifier, deterministic transform, or
  resource-policy behavior;
- agent protocol version changes for role, state, provenance, or reporting
  contracts.

v0.3 advances all three because it changes each boundary. It preserves the
v0.2 meanings of ZERO, NONZERO, and UNKNOWN.
