# Reviewer verification package

`symbolic-compactification audit package <dir>` exports a clean, replayable
bundle from a **recorded** audit run. Narrative cannot add a verified row.

```
LLM TEXT CAN NEVER CREATE VERIFIED STATUS.
VERIFIED TABLE IS GENERATED, NOT AUTHORED.
```

## Export

```bash
symbolic-compactification audit package my-paper-audit
symbolic-compactification audit package my-paper-audit --run <run_id>
symbolic-compactification audit package my-paper-audit --dest /tmp/reviewer-pack
```

Default source is the latest recorded run. `--dest` must be a new path;
exports do not overwrite existing destinations. Generated files live under
the workspace `reports/` tree unless `--dest` is given.

## What a reviewer should find

A package is a snapshot of machine evidence, not an authored proof:

- `reproduce.sh` — deterministic replay of table/report generation from the
  recorded run (no proposer, no network required)
- `TABLE_VERIFIED.md` / `TABLE_STRUCTURAL.md` / `TABLE_NONZERO.md` /
  `TABLE_UNCERTIFIED.md`
- machine table dumps (`verification_table.json` / `.csv`)
- `REPORT.md` copied from evidence (explanations are non-authoritative)
- integrity-bound records: hashes for sources, residuals, assumptions,
  obligations; verifier route; engine version; results

Record fields include: `audit_id`, `edge_id`, `source_refs`, `edge_type`,
`lhs_hash`, `rhs_hash`, `residual_hash`, `assumptions_hash`,
`source_snapshot_hash`, `obligation_hash`, `verifier_route`,
`engine_version`, `result`, `runtime_seconds`, `warnings`.

## How to review

1. Run `reproduce.sh` (or `audit table` / `audit report` on a copy).
2. Trust `TABLE_VERIFIED.md` only as generated from
   `may_appear_in_verified_table`.
3. Treat `NONZERO` as a transcription, assumption, convention, or step
   defect: *The encoded residual is NONZERO under the declared symbolic
   semantics. Check transcription, assumptions, conventions, and the
   derivation step.*
4. Treat `UNKNOWN` / `NOT_LOWERED` / `ASYMPTOTIC_CLAIM` as uncertified.
   Finite coefficient `ZERO` does not close a remainder claim.
5. Confirm `SPLIT` parents are never labelled `ZERO`.
   `CERTIFIED_BY_CHILDREN` displays as `SPLIT — all children certified`.

## What is excluded

- Local private validation (`.private_validation/`)
- Proposer traces, prompts, or model text as authority
- Network fetches
- Researcher notes presented as assumptions
- Secrets and credential-shaped strings (redacted; do not put them in
  sources)

A package is not a claim that a manuscript is correct. It is a claim about
which **lowered residuals** received exact `ZERO` under the recorded
semantics. See [PRIVACY.md](PRIVACY.md) and
[STATUS_SEMANTICS.md](STATUS_SEMANTICS.md).
