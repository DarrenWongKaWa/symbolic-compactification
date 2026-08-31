# Verification and Error Semantics

The verifier fails closed. A hypothesis is speculative until every required
obligation receives `ZERO`. Numeric tolerance, model confidence, matching
terminology, and a plausible derivation never replace this result.

## Scientific verdicts

### `ZERO`

The tested residual was reduced to exact symbolic zero through the declared
verifier route, using the declared namespace and assumptions. This certifies
the submitted equality under those engine semantics.

`ZERO` does not establish that the hypothesis was novel, physically useful,
or discovered by AI. It does not broaden the declared domain.

### `NONZERO`

Exact evidence showed a tested residual to be nonzero. For the core
equivalence route, an exact rational probe that is provably nonzero refutes the
submitted universal identity under the declared domain.

The residual and counterexample are evidence to preserve. `NONZERO` is not a
license to change assumptions, boundary conditions, symmetry, or limit order
until the identity passes.

### `UNKNOWN`

The engine could not prove either exact zero or exact nonzero within its
supported route and resource bounds.

`UNKNOWN` is not:

- likely true;
- likely false;
- partial certification;
- numerical agreement;
- permission to promote or replace scientific state.

The correct response is to retain the original state, inspect the proof gap,
and optionally submit a smaller or more verifier-friendly hypothesis without
changing its scientific meaning.

## Ingestion and compilation statuses

### `PARSE_FAILURE`

A workspace or expression could not be parsed under the strict input policy.
No mathematical verdict was produced. The error identifies the file and a
stable failure code without exposing an internal stack trace by default.

Examples include malformed YAML/JSON, duplicate metadata keys, undeclared
symbols, disallowed expression syntax, or resource limits reached during
parsing.

### `COMPILE_FAILURE`

The hypothesis was readable, but it could not be lowered to a supported proof
obligation without guessing or changing scientific meaning. No mathematical
verdict was produced.

An unknown relation name, unsupported member structure, or unsupported
operator is a compilation failure rather than an invitation to choose a
nearby relation.

### `ASSUMPTION_REQUIRED`

Verification requires a genuinely new scientific/domain choice that was not
declared: for example positivity, nonzero conditions, boundary behavior,
symmetry, integration by parts, or an order of limits. The tool stops and asks
the researcher to decide explicitly.

In the v0.1 equivalence workflow, the operational trigger is narrower and
fully explicit: a hypothesis that omits a symbol already present in the
researcher-owned assumptions file from `assumptions_used` returns
`ASSUMPTION_REQUIRED`. The engine does not attempt to infer other missing
domain predicates from the formula.

This differs from `UNKNOWN`. `ASSUMPTION_REQUIRED` is an assumption gate;
`UNKNOWN` is a proof gap after the available assumptions have been applied.

## Multi-obligation hypotheses

Every obligation receives its own result and provenance. A composite
hypothesis is certified only when all required obligations are `ZERO`.

- Any `NONZERO` refutes the submitted composite claim.
- Any `UNKNOWN` prevents certification, even when other obligations are
  `ZERO`.
- Any parse, compile, or assumption failure prevents a scientific verdict for
  the affected obligation and prevents composite certification.

The aggregate result must preserve per-obligation evidence. It must not hide a
failure behind a majority, score, or successful sub-obligation.

## Assumptions and domains

Exactness is always conditional on the declared engine namespace and
assumptions. The tool does not silently:

- assume variables are real, positive, or nonzero;
- add physical folklore;
- integrate by parts or discard boundary terms;
- change symmetry assumptions;
- reorder limits;
- change domains or boundary conditions.

If such a choice is scientifically necessary, it belongs in researcher-owned
input and run provenance before verification.

## Reports and provenance

Every workspace verification attempt receives a new run record. The record
includes exact source hashes, hypothesis and assumptions hashes, verifier
route, result, runtime, versions, commit, and warnings. A report explains that
record; it does not strengthen the verifier outcome.

Source hashes establish which bytes were tested. Grounding establishes which
source objects a hypothesis names. Neither constitutes mathematical proof
without `ZERO`.

## CLI process behavior

User-visible named statuses are more important than process exit codes. The
workspace CLI must provide stable non-success exits for `NONZERO`, `UNKNOWN`,
and input/compile/assumption failures, while preserving the full status in the
run record. Developer tracebacks are available only through an explicit debug
mode.

The existing file-oriented CLI retains its historical mapping (`ZERO` exit 0,
`NONZERO` exit 2, `UNKNOWN` exit 3, ingestion/usage error exit 4). The
workspace-level mapping must be confirmed in the integrated CLI help before
automation depends on it.

## What the semantics do not claim

symbolic-compactification is not a general formal proof system. `ZERO` is exact
certification under the declared engine route, not a theorem about every
possible interpretation. `UNKNOWN` is expected on difficult limits,
special-function identities, unsupported scientific objects, and expressions
outside current coverage.
