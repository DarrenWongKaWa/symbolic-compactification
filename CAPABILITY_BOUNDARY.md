# Capability Boundary — Research Preview v0.1

This is the concise external boundary for `symbolic-compactification`. The
scientific representation-discovery campaign remains closed.

## Supported

- Strict, local ingestion of covered symbolic expressions with explicit
  symbol/function declarations.
- Researcher-supplied equivalence hypotheses grounded to workspace expression
  files.
- Exact `ZERO`, exact `NONZERO`, and fail-closed `UNKNOWN` adjudication under
  the documented engine route.
- Explicit parse, compile, and declared-assumption gates.
- Read-only researcher sources; generated files live only under `runs/`.
- Input, expression, hypothesis, assumption, version, dependency, verifier,
  runtime, warning, and source-revision provenance.
- Structural observation as non-proof context.
- Reproducible CLI and Python workflows for the supported workspace schema.

The alpha's machine-enforced assumption namespace is deliberately small: each
declared symbol has only `real` and `nonzero` flags, and undefined functions
must be named explicitly. Positivity, general inequalities, excluded poles,
parameter identities, boundary conditions, symmetries, and limit order cannot
be represented or enforced. A scientific claim that depends on any such
predicate is outside supported alpha certification; putting the predicate in
notes or references does not make it operational.

`ASSUMPTION_REQUIRED` is also narrow: it detects that
`hypothesis.assumptions_used` is missing or omits a symbol already declared in
the assumptions file. It does not discover which mathematical or physical
assumptions a hypothesis needs.

## Experimental

- AI-assisted proposal generation.
- Context-conditioned hypothesis generation.
- Structural observations as proposal heuristics.

Experimental outputs remain speculative until grounded, compiled, and given a
verifier result. Proposer text can never promote scientific state.

## Unsupported or unestablished

- Robust mathematical representation invention.
- Autonomous physics discovery.
- Universal scientific simplification.
- A general theorem-proving or formal-proof system.
- General matrix/operator, integral-module, continued-fraction, or Lehmann-map
  evaluation.
- General exact limit or special-function certification.
- Exact limits inferred from finitely many Laurent coefficients without
  remainder control.
- Automatic authorization of physical assumptions, domains, boundaries,
  symmetries, or limit order.

`UNKNOWN` is a valid result: it means the tool cannot decide. It is not likely
true, likely false, partial success, or permission to advance scientific
state.
