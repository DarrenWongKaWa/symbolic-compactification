# Derivation-audit status semantics

The verifier fails closed. Numeric tolerance, model confidence, and fluent
prose never replace an engine result.

Two axes on each evidence record:

- `result` — engine/adjudication outcome
- `status` — typed derivation-audit status

Only `status == result == ZERO` with passing integrity and `executable=true`
may appear in the verified table. LLM text cannot populate that record with
authority.

## Engine results

| Result | Meaning |
|---|---|
| `ZERO` | Exact symbolic simplification of the encoded residual to zero under the recorded route, namespace, and assumptions. |
| `NONZERO` | An exact probe proved the residual nonzero. Preserve the residual and counterexample. |
| `UNKNOWN` | No proof either way. Not likely true, likely false, partial success, or permission to advance. |
| `ASSUMPTION_REQUIRED` | Declaration mismatch against the assumptions file; not needed-assumption discovery. |
| `PARSE_FAILURE` | Source or residual could not be parsed under the whitelist. |
| `COMPILE_FAILURE` | Could not lower to a supported obligation without changing meaning. |
| `GROUNDING_FAILURE` | Edge did not bind to declared equation/expression sources. |
| `INVALID_RECORD` | Machine record failed integrity. |

`ZERO` certifies only the submitted residual. It does not certify novelty,
physical usefulness, the rest of a manuscript, or a broader domain.

## Structural and tracking statuses

| Status | Meaning | Table |
|---|---|---|
| `DEFINITION` | Name/definition introduction. | STRUCTURAL |
| `RECORDED` | Bookkeeping or non-executable reconstruction tracking. | STRUCTURAL |
| `SPLIT` | Parent delegated; children incomplete or not all `ZERO`. | STRUCTURAL |
| `CERTIFIED_BY_CHILDREN` | Every required child is integrity-ok `ZERO`. Displayed as `SPLIT — all children certified`. Never shown as `ZERO`. | STRUCTURAL |
| `CERTIFIED_BY_RULE` | Local child `ZERO` plus a declared global theorem (BZ-torus IBP). Displayed as `CERTIFIED_BY_RULE — local ZERO + declared BZ-torus IBP`. Never shown as `ZERO`. SymPy did not evaluate the integral. | STRUCTURAL |
| `NOT_LOWERED` | No executable residual, or a typed global rule is missing required children/domain. Distinct from `UNKNOWN`. | UNCERTIFIED |

`SPLIT_PARENT` cannot have `status=ZERO`. Missing, `UNKNOWN`, or `NONZERO`
children block `CERTIFIED_BY_CHILDREN`.

## Inclusion (authoritative)

`schema.may_appear_in_verified_table(record)` is true only if all hold:

1. `integrity_ok(record)`
2. `record.result == ZERO` and `record.status == ZERO`
3. `record.executable`
4. `edge_type` is not `SPLIT_PARENT`
5. `edge_type` is not `ASYMPTOTIC_CLAIM`

Markdown `ZERO` is ignored. Forged records without residual, obligation,
assumptions hashes and a verifier route fail integrity and cannot enter
`TABLE_VERIFIED`.

`schema.table_bucket(record)` assigns exactly one bucket:

| Bucket | File | Rule |
|---|---|---|
| `TABLE_VERIFIED` | `TABLE_VERIFIED.md` | `may_appear_in_verified_table` |
| `TABLE_NONZERO` | `TABLE_NONZERO.md` | `result` or `status` is `NONZERO` |
| `TABLE_STRUCTURAL` | `TABLE_STRUCTURAL.md` | `DEFINITION`, `RECORDED`, `SPLIT`, `CERTIFIED_BY_CHILDREN` |
| `TABLE_UNCERTIFIED` | `TABLE_UNCERTIFIED.md` | Integrity failure, `UNKNOWN`, `NOT_LOWERED`, parse/compile/grounding failures, `ASYMPTOTIC_CLAIM` without remainder certificate, everything else |

Integrity failure always buckets as `TABLE_UNCERTIFIED`, even if labels say
`ZERO`.

## Asymptotic remainder

Finite Laurent/series/coefficient `ZERO` ≠ remainder proof. An
`ASYMPTOTIC_CLAIM` must not receive engine `ZERO` without
`remainder_certificate_hash` matching `[0-9a-f]{64}`. Coefficient children
may still occupy `TABLE_VERIFIED` on their own; the parent stays
`TABLE_UNCERTIFIED` until a remainder certificate exists. In this alpha,
remainder certification is a stated limitation, so Demo C keeps the parent
`UNKNOWN`.

## Composite claims

Every edge is judged on its own record. A split is certified only through
children, never by averaging, scoring, or narrative.

Changing source, residual, or assumptions produces a new snapshot. Prior
`ZERO` rows do not transfer silently.

See [edge-types.md](edge-types.md) and [rule-certificates.md](rule-certificates.md).
