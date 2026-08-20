# Engineering guidelines

These rules govern changes to the engine. The operating protocol is
[AGENTS.md](../AGENTS.md); module responsibilities and invariants are in
[ARCHITECTURE.md](ARCHITECTURE.md).

## Preserve the trust boundaries

1. Humans authorize scientific meaning, assumptions, boundary conditions,
   branches, gauges, limits, and other physical choices.
2. Agents discover structure and propose candidates. They do not certify.
3. Deterministic code ingests, transforms within policy, verifies, records,
   and reports. It fails closed.

Any change that weakens one of these boundaries is a correctness change, not
an ergonomic refactor.

## Preserve representation

- Keep semantic structures such as `Sum`, `Product`, `Piecewise`, and indexed
  functions through ingestion and proposal.
- Lower only for a named, bounded verification or diagnostic operation.
- Never make an expanded CAS form the only representation available to an
  agent or human.
- Add a custom symbolic IR only after a demonstrated SymPy limitation; no such
  limitation currently justifies one.

## Bound symbolic work

All potentially expensive SymPy work must enter through `budgets.py` with a
named operation-specific budget. Public helpers do not get an unbounded
shortcut. Timeout is an UNKNOWN proof outcome, not evidence for equality or
inequality.

Process mode is the production default. Lifecycle changes must retain owned
PID/process-group tracking, readiness handshake, exact-target termination,
reaping, cleanup telemetry, nested-operation safety, and unrelated-process
protection.

## Treat text and artifacts as untrusted

- Reject before construction using character/token, nesting, literal-size,
  symbol/function, and AST-operation bounds.
- Never use Python `eval`/`exec` or an unrestricted SymPy namespace.
- Unsupported adapter syntax fails explicitly; adapters never guess or run an
  external CAS.
- Persist JSON and final artifacts atomically. Never reuse a step or packet
  index.
- Validate run IDs before joining filesystem paths.

## Keep state transitions mechanical

`pipeline.adjudicate_candidate()` is the normal stateful API. CLI code may
load files and render output but may not recreate certification policy.

Promotion must stay bound to the exact current hash, candidate raw hash and
text, ZERO verdict, PROVEN/CERTIFIED states, exact symbolic evidence, and
assumption gate. New proposal or report fields must not become an alternate
promotion path.

## Determinism and provenance

- Sort semantically unordered collections before construction, hashing, or
  serialization; do not reorder `Piecewise` branches or other meaningful
  sequences.
- Use canonical JSON for hashes.
- Record package, engine, protocol, Git (including dirty state), policies,
  expression hashes, verdict evidence, and timing.
- Store externally meaningful rationale only, never private model reasoning.

## Change discipline

Classify proposed work:

- P0: correctness, security, reproducibility, or invariant failure;
- P1: demonstrated maintainability or user-path improvement;
- P2: speculative convenience.

Implement every justified P0 and only high-value P1. Avoid P2 unless it is
trivial. Do not add services, databases, custom model runtimes, schedulers,
ontologies, or broad frameworks.

Use neutral synthetic tests. Every defect fix needs a contract regression at
the boundary where it failed. Do not couple tests to CLI-private helpers when
the behavior belongs to the library pipeline.

## Release gate

Before release:

1. run the complete suite;
2. run cross-process/hash-seed determinism coverage;
3. run process timeout, cancellation, and unrelated-process tests;
4. run the clean-room firewall;
5. verify editable and normal installs plus CLI smoke;
6. complete a temporary fresh-clone replay with an explicit final form;
7. inspect the baseline-to-head diff and ensure Git is clean;
8. confirm no scientific workload or historical answer entered the repo.
