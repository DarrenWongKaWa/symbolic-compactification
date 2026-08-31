# Derivation-audit reviewer verification package

This directory is a machine-generated export of one recorded derivation-audit run. It is evidence of exact residual checks under declared symbolic semantics. Markdown text cannot create ZERO or VERIFIED status; table inclusion is generated from integrity-bound engine records.

Exact algebraic and local structural identities that were lowered to executable residuals were evaluated under the declared symbolic semantics. Only obligations returning exact ZERO are listed as machine-verified.

Definitions, integral-level arguments, asymptotic remainder claims, and unsupported transformations are tracked separately rather than being misreported as exact algebraic identities.

- Run id: `20260831T224354Z-5082de88`
- Audit id: `arxiv-2511-16422-v2-field-validation`
- Engine version: `0.3.0`
- Schema: `DerivationAuditV1`

## Reproduce (offline)

`reproduce.sh` re-runs verification and then table generation on the bundled replay workspace in `replay/`. It does not use the network and does not install packages.

```sh
./reproduce.sh
```

Equivalent commands:

```sh
symbolic-compactification audit verify ./replay
symbolic-compactification audit table ./replay
```

`ssc` is an alias of the same entry point. If neither console script is on `PATH`, the script falls back to `python3 -m symbolic_compactification.cli`.

## Package contents

- `TABLE_VERIFIED.md`
- `TABLE_STRUCTURAL.md`
- `TABLE_NONZERO.md`
- `TABLE_UNCERTIFIED.md`
- `assumptions.yaml` — declared symbols and functions
- `obligations/` — residual texts and obligation JSON from records
- `machine_results/` — `machine_records.json` and provenance
- `replay/` — expressions and manifests sufficient to replay
- `MANIFEST.json` — SHA-256 digests of packaged files
- `reproduce.sh` — offline verify-then-table replay

A NONZERO residual is a disproof of the encoded identity under the declared semantics. UNKNOWN fails closed and is not promoted.
