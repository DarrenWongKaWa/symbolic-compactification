# Limitations and Claim Boundary

Read this page before using a report in scientific work. The preview offers
context-grounded symbolic hypothesis generation with fail-closed
verification; it does not automate scientific judgment.

## Verification coverage is incomplete

The exact verifier supports a bounded expression language, resource policy,
and collection of symbolic routes. `UNKNOWN`, `PARSE_FAILURE`, and
`COMPILE_FAILURE` are normal outcomes for hard or unsupported inputs. A
packaging gap is not evidence that a statement is true, false, or impossible.

Large expressions, arbitrary matrix/tensor/block objects, difficult
special-function identities, and general exact limits may remain undecidable
or unsupported. The preview does not promise performance on every expression
a computer algebra system can display.

## Exactness is conditional

`ZERO` means exact certification under the declared engine semantics,
namespace, assumptions, and verifier route. It does not validate undeclared
physical assumptions, provenance outside the hashed workspace, or a broader
domain than the one tested.

Machine-supported assumptions must be explicit. The tool does not authorize
positivity, boundary terms, symmetry, integration by parts, analytic
continuation, or changes in limit order.

The alpha can machine-enforce only `real: true` symbols, an optional
`nonzero` flag, and declared undefined functions. It cannot represent
positivity, general inequalities,
excluded poles, parameter identities, boundary conditions, symmetries, or
limit order. A hypothesis that depends on one of those predicates is outside
supported alpha certification. Notes and references may document the issue,
but do not make it operational. `ASSUMPTION_REQUIRED` only catches a missing
`hypothesis.assumptions_used` field or a symbol already declared in the
assumptions file but omitted from that field; it does not discover missing
mathematical or physical assumptions.

The documented historical `real: false` namespace convention has a known
contract defect: the symbolic construction can encode "provably non-real"
instead of an unconstrained complex symbol. The v0.1 workspace rejects this
setting fail-closed.

## Exact limits require remainder control

Cancellation of finitely many negative Laurent coefficients and agreement of
a finite term do not certify an exact limit. A nonzero or unresolved remainder
can change the result. Finite series expansion is diagnostic only unless the
remainder is controlled by an exact, supported argument; otherwise the result
remains `UNKNOWN`.

## Hypothesis generation is experimental

Context-conditioned representation invention remains unestablished at
realistic scale. Earlier scientific work did not admit enough adjudicable real
tasks for that question to be tested. It is therefore incorrect to say either
that context-conditioned invention works or that it failed.

Any AI proposer is optional and experimental. Its output is speculative until
it is grounded to source members, compiled into explicit obligations, and
verified. Model names, prompts, rankings, confidence, or fluent explanations
are not proof.

The tool must not be described as:

- an AI that discovers physics;
- an autonomous theoretical physicist;
- a reliable or universal representation inventor;
- a guaranteed scientific simplifier;
- a general formal proof system;
- a system that always finds hidden structure.

## Grounding is not proof

Notes, citations, and references can explain where a member or hypothesis came
from. Grounding does not certify an identity. Structured observations,
operator names, latent-object labels, and reconstruction prose are hypotheses
until their required equalities receive `ZERO`.

## Reference ingestion is lightweight

The preview supports file paths, notes, manually curated excerpts, and
optional metadata. It is not a literature-RAG system and does not promise PDF
understanding, citation verification, or automatic extraction of assumptions
from papers.

## Source handling is read-only, not a backup

The tool writes generated output under `workspace/runs/<run_id>/` and refuses
to overwrite an existing initialization target. It does not intentionally
modify user expressions, notes, assumptions, references, or hypotheses.

Researchers remain responsible for ordinary version control, backups, access
permissions, and checking that external editors or scripts did not change a
source during a run. Provenance hashes identify the exact bytes observed by
the tool.

## Security boundary

Core verification requires no API key. Run provenance does not inspect `.env`
files, request headers, or unrelated process environment variables. Warning
fields are bounded and credential-like values are redacted.

No redaction system is a substitute for good secret hygiene. Do not put API
keys, auth headers, passwords, unpublished credentials, or unrelated private
data in expressions, notes, hypotheses, or references. If an experimental
proposer is configured, review its separate data-handling policy before use.

## Release status

The repository remains `INTERNAL_ONLY` until installation, CLI, Python API,
workspace, provenance, fail-closed behavior, security, three demos,
documentation, full release-critical tests, full-suite integration, and a
clean-room replay satisfy the final engineering gate. These documents do not
themselves grant alpha status.
