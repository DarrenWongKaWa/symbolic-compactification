# Pre-Treatment Admission — Context-Conditioned Verified Scientific Representation Discovery

Status: **PRE_TREATMENT_NOT_ADMITTED**

Date: 2026-08-31

Campaign input SHA-256: `51e1ee0574a5056a5cffd64fd3a236a035c149b394b83104541c0bf8a3f3f6d8`

## Decision

The campaign required exactly five primary task families, all admissible before
treatment.  Independent corpus construction rejected Task A and Task B.  Even
if every remaining family had passed, the maximum achievable count would be
three of five.  The admission threshold is therefore impossible to satisfy.

This is a pre-treatment feasibility outcome only.  It is not a scientific
failure, a method falsification, a publication decision, or evidence for or
against context conditioning.

No leakage-review phase, benchmark freeze, DeepSeek call, symbolic baseline
run, verifier treatment, publication-review cluster, or full repository suite
was run.  Tasks D and E were stopped once the fixed-corpus invariant made
admission impossible; they are not classified as task failures.

## Admission checklist

| prerequisite | status | evidence |
|---|---|---|
| At least five admissible real physics-derived tasks | FAIL | A and B failed; only C was provisionally viable. The exact-five corpus cannot reach five. |
| At least four distinct representation families | NOT EVALUABLE | The five-task corpus was not admissible. |
| Context documents for every task | NOT EVALUABLE | No corpus was frozen. |
| Hidden target/evaluation for every task | NOT EVALUABLE | No corpus was frozen. |
| Negative or misleading-context control | NOT EVALUABLE | No corpus was frozen. |
| Operational verifier/evaluator for every task | FAIL | Task B requires matrix/differential-system semantics absent from the current executable verifier. |
| No direct target leakage in proposer-visible context | NOT EVALUABLE | No independent leakage-review phase is authorized after gate failure. |

## Independent corpus-builder findings

### Task A — matrix-function / divided-difference transfer

**FAIL** (`PROBLEM_UNDERSPECIFIED` and `PACKAGING_GAP`).  The candidate
Kubo conductivity quotient in Aydin, Keski-Rahkonen, and Heller is real
physics and contains a difference quotient, but the source display does not
complete the Fermi function, diagonal/degenerate-node treatment, or the domain
required for a confluent representation.  Verifying only its quotient would
not verify the source Kubo expression, whose operator, sum, limit, and
matrix-element semantics are outside the current scalar verifier.

The best fully specified square-root alternative duplicates the frozen
matrix-function R2/R3 historical family and was excluded for freshness.

Sources: [Aydin et al., arXiv:2303.06077](https://arxiv.org/abs/2303.06077);
[Rubensson, arXiv:2306.15814](https://arxiv.org/abs/2306.15814).

### Task B — canonical basis / representation change

**FAIL** (`NO_CURRENT_OPERATIONAL_EVALUATOR`).  A small independent
one-mass bubble system is source-grounded, has a hideable rational canonical
basis transformation, and its scalar coefficient receipts can be checked.
However, the present system cannot accept and adjudicate an arbitrary proposed
basis matrix, differentiate it, and evaluate the gauge transformation
operationally.  Precomputing the hidden matrix entries would test only
reproduction of an evaluator-supplied answer rather than the proposal.

Sources: [Abreu, Britto, and Duhr, arXiv:2203.13014](https://arxiv.org/abs/2203.13014);
[Henn, arXiv:1304.1806](https://arxiv.org/abs/1304.1806).

### Task C — master-integral / generator basis

**PROVISIONALLY VIABLE, NOT FROZEN.**  An independent source provides a
two-loop Euclidean vacuum-family recurrence whose finite source-derived
relations admit a one-generator rational reconstruction.  The scalar
coefficient obligations are exactly evaluable under explicit non-pole domain
conditions.  It could support R1 transfer from generic IBP context, subject to
an independent leakage audit and a full package-admission review.  It is not a
benchmark task, treatment input, or evidence of discovery.

Source: [Davydychev and Schröder, arXiv:2210.10593](https://arxiv.org/abs/2210.10593).

### Tasks D and E

**STOPPED / UNCLASSIFIED.**  Their miners were halted after A and B made the
pre-registered exact-five gate impossible.  No negative inference may be made
about continued fractions, polygamma, literature context, or the proposed
models from their incomplete pre-treatment work.

## Current evaluator boundary relevant to this decision

The verifier and RepresentationGrammarV1 compile scalar SymPy expressions.
`MATRIX_FUNCTION` is a typed label, not executable matrix algebra.  There is
no current evaluator for matrix products, matrix derivatives, basis changes,
trace/determinant, integrals, noncommutative operators, or a general
continued-fraction object.  This is a packaging/evaluator boundary; it is not
a claim that the underlying scientific representations are invalid or that
context would not help discover them.

The current campaign explicitly forbids extending the parser or IR before
admission, so these missing semantics cannot be repaired within this run.

## Closure

`PRE_TREATMENT_NOT_ADMITTED`

The one-pass campaign terminates here.  A new campaign would require explicit
human authorization, a new pre-registered protocol, and a fresh task corpus;
this artifact does not authorize any follow-up line.
