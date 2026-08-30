# RPSCasePackageV1

This contract repairs the case-mining boundary exposed by admission audit
`da95ac3`: a scientific dossier is context, not a benchmark task. A package is
the smallest immutable, parser-facing unit that can enter a later admission
gate. Package construction is not a search result and makes no DEV/TEST choice.

## Required layout

```text
<case-id>/
├── package.json
├── symbols.json
├── assumptions.json
├── source_catalog.json
├── proposer_view.json
├── source_manifest.json
├── members/*.txt
├── reference/program.json
├── reference/obligations.json
└── verification/
```

All paths in JSON are package-relative. All JSON is UTF-8, sorted-key,
newline-terminated canonical JSON. Every file except `package.json` is bound by
path and SHA-256 from `package.json`; a manifest never attempts to hash itself.
Member identity is the raw `.txt` bytes plus SHA-256, not a transcription.

## Public/private firewall

The search method may receive only `proposer_view.json` and the exact files it
references. That view may contain:

- source-member ids, paths, hashes, and exact expressions;
- the declared assumption contract;
- source-facing structural observations;
- the legal grammar and frozen search policy supplied by the runner.

It must not contain audited depth, target representation type, gold program,
operator sequence, latent/member roles, hidden instance maps, reference
obligations, or verification receipts. The evaluator-only `reference/` tree is
never search input.

## Package status

Exactly one status is recorded:

- `PACKAGE_READY`: every required reference obligation compiled and returned
  exact `ZERO`; sources and assumptions are complete; leakage audit passes.
- `PROOF_REQUIRED`: compilation succeeded but at least one required obligation
  is `UNKNOWN` and none is `NONZERO`.
- `REFUTED`: at least one required obligation is exact `NONZERO`.
- `PACKAGING_GAP`: the frozen parser cannot express the required source object
  or obligation, or required machine files are absent.

`UNKNOWN`, time-budget expiry, numeric agreement, and a high representation
score never produce `PACKAGE_READY`. `PROOF_REQUIRED` is a proof-axis outcome,
not `HUMAN_REQUIRED`. Newly required assumptions instead fail the assumption
gate.

## Exact verification evidence

Every reference transformation is run through a recorded engine session. The
package retains the run manifest and step record, including current/candidate
hashes, residual, simplified residual, verdict, and counterexample when
present. Only the main coordinator may later promote a package into a frozen
partition.

## Fixed-instance lowering

`lowering_scope` is one of:

- `SYMBOLIC_SOURCE_OBJECT`;
- `FIXED_SCIENTIFIC_INSTANCE`;
- `FINITE_INDEX_DIAGNOSTIC`.

A fixed matrix size, finite index set, or parameter value must be explicit in
the title, assumptions, catalog, and source manifest. A finite replay is never
reported as proof for symbolic dimension or symbolic bounds.

## Scientific provenance

`source_manifest.json` identifies the source, formula/theorem location, stable
URL or DOI, retrieval date when online, and the exact lowering from the cited
statement to each member. Citation prose alone is insufficient. A package that
cannot trace every member to a source statement stays `PACKAGING_GAP`.

## Admission

`PACKAGE_READY` is necessary but not sufficient. A later coordinator gate must
also reconcile the independent assumption and duplicate/leakage audits,
non-tautology, depth, source authenticity, and frozen-baseline comparability.
