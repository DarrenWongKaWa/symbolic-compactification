# Threat model (derivation audit)

Goal: a reviewer can trust that `TABLE_VERIFIED` contains only integrity-bound
engine `ZERO` rows, and that private local sources do not leak into public
artifacts.

## Assets

- Verified-table inclusion (`may_appear_in_verified_table`)
- Source immutability (manuscript, manifests, expressions, assumptions)
- Snapshot hashes binding a run to exact bytes
- Remainder-soundness (no coefficient `ZERO` promoted as a global remainder)
- Local private sources and denylist material
- Credentials that might appear in free-form strings

## Adversaries / misuse

- Author or model writes “ZERO” into Markdown or YAML
- Residual substitution after a claimed `ZERO`
- Encoding an asymptotic remainder as `ALGEBRAIC_EQUIVALENCE`
- Path traversal, symlinks, YAML anchors/aliases
- Packaging private local files or denylist hits
- Network or proposer use against local private sources
- Secret-shaped strings in reports

## Controls

| Threat | Control |
|---|---|
| Authored / LLM “verified” rows | Tables generated only from `table_bucket` / `may_appear_in_verified_table`. Markdown `ZERO` ignored. |
| Forged `ZERO` without hashes | `integrity_issues`: executable rows require residual, obligation, assumptions hashes and a verifier route. |
| Status `ZERO` with non-`ZERO` result | `STATUS_ZERO_REQUIRES_ENGINE_ZERO`; non-executable `ZERO` rejected. |
| Split parent labelled `ZERO` | `SPLIT_PARENT_CANNOT_BE_ENGINE_ZERO`; public label never contains `ZERO`. |
| Coefficient `ZERO` as remainder proof | `ASYMPTOTIC_CLAIM` cannot be engine `ZERO` without `remainder_certificate_hash`; type excluded from verified table. |
| Stale `ZERO` after edits | New snapshot hashes; prior rows do not transfer silently. |
| Source overwrite | `audit init` refuses existing paths; commands write only `runs/` and `reports/`. |
| Path escape | Workspace-relative `/` paths; no `..`, `\\`, or symlinks; containment checks. |
| YAML bombs / alias tricks | Anchors and aliases rejected; bounded file sizes. |
| Secret leakage | Allow-listed records; `redact_text` / `redact_public_data` on public CLI/JSON. Not a general DLP system. |
| Private source export | `.private_validation/` gitignored; denylist scan is a release blocker; private acceptance is never release evidence. |
| Network / proposer in private mode | `SSC_PRIVATE_OFFLINE=1` refuses network-shaped targets and disables the proposer. |
| Inventory treated as proof | Inspect/inventory counts are labelled non-evidence; inventory does not parse LaTeX as algebra. |

## Out of scope

- Proving a manuscript, referee report, or physical model
- Enforcing undeclared analytic assumptions
- PDF understanding or literature RAG
- Stopping a reviewer from misreading `TABLE_STRUCTURAL` as proof
- Guaranteeing that researcher-transcribed residuals match a PDF glyph-for-glyph

## Residual risk

Manual transcription can encode the wrong identity (detected as `NONZERO` or
missed if both sides are wrong the same way). `UNKNOWN` can be misread as
support. Defence in depth still requires humans not to commit private sources
or secrets.

See [PRIVACY.md](PRIVACY.md), [STATUS_SEMANTICS.md](STATUS_SEMANTICS.md), and
[engineering/release_v0_1/SECURITY.md](../engineering/release_v0_1/SECURITY.md).
