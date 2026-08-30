# Handoff — fresh strict-R3 matrix-exponential candidate

## Outcome

One candidate-only package was mined and built:

- package: `packages/fresh_r3/rps-case-q7v3`
- public case id: `Q7V3`
- status: `CANDIDATE_FOR_INDEPENDENT_REVIEW`
- depth claim: evaluator reference at `R3_REPEATED_NODE_ARITY_FOUR`
- required full-program receipts: `3 ZERO / 0 NONZERO / 0 UNKNOWN`
- all grammar-control receipts: `9 ZERO / 0 NONZERO / 0 UNKNOWN`

It has not been added to DEV or any shared manifest. Independent scientific,
leakage, and duplicate review is still required.

## Source and specialization

Primary source: Schweitzer (2023), Theorem 2, equations (8)--(9), DOI
`10.1016/j.laa.2022.10.005`, arXiv `2203.03930v2`. The stored exact equation
block has SHA-256
`76cbf6191983c656681daca3b3c58bf9d62688fb5f4602ba0e42005dff0222a1`.
The source archive hash, complete TeX hash, exact locators, lowering, symbols,
and assumption locators are bound in `source_manifest.json`.

The fixed instance is the third Fréchet derivative of `exp` at
`diag(a,b,c)`. Rank-one directions isolate three scalar components. Their
evaluator-only site sequences are `[a,a,b,b]`, `[a,a,b,c]`, and `[a,b,c,c]`.
The public projection contains none of these sequences or their roles.

## Freshness

The audit found no exact member-byte overlap with current packages or
historical task expressions, and no explicit JSON arity-four node signature
with multiplicity partition `(2,2)` or `(2,1,1)`. Manual controls explicitly
cover:

- old `test-a-hermite-two`: generic arity three, partition `(2,1)`;
- C3J9 (`reference/program.json` SHA
  `e80150be846e1f9fb6b0b86fc77912389bfd1fcaae0a2932d9ce89becd349bd5`):
  second-order logarithm, arity three;
- historical phi dossier SHA
  `dabcbdf5c0b2b3c7f6af47af734711e60dec5029190f5d14db9fa0f193f1e9dc`:
  fixed-zero-node partition `(3,1)`.

This is a bounded structural audit, not a claim of mathematically exhaustive
equivalence checking over all prose artifacts.

## Grammar controls

- `G_FULL`: explicit arity-four `HERMITE_DD` nodes, 3 compiled obligations.
- `G_NO_HERMITE`: primitive recurrence construction, 3 compiled obligations.
- `G_PRIMITIVE`: the same primitive construction under the primitive grammar,
  3 compiled obligations.

All variants are non-tautological and all obligations have exact session
receipts. A named Hermite primitive is therefore unnecessary for M1
expressibility. This does not establish frozen-search reachability.

## Key hashes

- full program: `f1ab5391f81386721532d06007e8eddafa797079a2a17459b9022b8d93ce81b2`
- primitive program: `6bde27a80b13974c3b8b932cfa1e57d2e20d55cda7e0717671bf5859a8971e1a`
- lowering: `fcfea1469589f906aad882a4076d4de216c96fbc1c135fed84815aaa6e457f48`
- duplicate audit: `59f4ce0fa4f8897b6dee2c79f7bcb23a0d3cccda502af2cf29a76f6ed386b550`
- source manifest: `e844a09da0c54cb0a0b17c989ac33f5f340474d71b0f260650c7cadb4e669f11`
- package manifest: `5c3d424fb9e89a0c2ce7d3c6e0e8f03905b4bf9915b34afce0986d0fa28eef6e`

## Validation

```text
fresh_r3.validate: VALID_CANDIDATE
tests/test_rps_fresh_r3_candidate.py: 10 passed
full repository suite: 1830 passed in 343.29s
```

## Strict claim boundary

Do not treat this artifact as DEV admission, search success, AI evidence,
generalization evidence, or proof that the frozen enumerator covers arity
four. It is a source-backed, assumption-complete, M1-compilable candidate for
independent review only.
