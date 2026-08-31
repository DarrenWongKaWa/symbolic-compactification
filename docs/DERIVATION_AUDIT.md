# Derivation audit

v0.2 derivation-audit alpha in development on
`engineering/derivation-audit-v0.2`. Additive to the still-supported v0.1
Mode A workspace (`init` → `inspect` → `verify` → `report`). Package identity
remains `0.1.0-alpha`. This layer does not write papers and does not replace
a human derivation.

Exact algebraic and local structural identities that were lowered to
executable residuals were evaluated under the declared symbolic semantics.
Only obligations returning exact ZERO are listed as machine-verified.

Definitions, integral-level arguments, asymptotic remainder claims, and
unsupported transformations are tracked separately rather than being
misreported as exact algebraic identities.

```
LLM TEXT CAN NEVER CREATE VERIFIED STATUS.
VERIFIED TABLE IS GENERATED, NOT AUTHORED.
```

`schema.may_appear_in_verified_table` and `schema.table_bucket` are the only
inclusion functions. Markdown `ZERO` is ignored.

## What it does

A derivation audit is a typed graph over inventoried equations:

1. Place a manuscript source and explicit native-text members in an audit
   workspace.
2. Inventory extracts **labels, environments, order, and source ranges**. It
   does not interpret LaTeX as algebra.
3. You declare typed **edges** (equation → equation, or a residual you
   supply).
4. Supported edges **lower** to executable residuals. Others stay typed
   non-executable statuses (`DEFINITION`, `RECORDED`, `SPLIT`, `NOT_LOWERED`,
   `UNKNOWN`, …).
5. The deterministic verifier judges each executable residual.
6. Reviewer tables, `REPORT.md`, and a reviewer package are generated from
   the integrity-bound evidence store.

The verifier—not a model, explanation, or confidence score—is the only judge.

## Command surface

```bash
symbolic-compactification audit init|inventory|inspect|verify|table|report|package <dir>
```

`ssc` is the same entry point. `--json` emits one machine-readable object.

| Command | Role |
|---|---|
| `audit init <dir>` | Create a new audit workspace. Never overwrites. |
| `audit inventory <dir>` | Extract equation labels into a tool-owned sidecar under `reports/`. |
| `audit inspect <dir>` | Summarize hashes and config. Counts are not scientific evidence. |
| `audit verify <dir>` | Snapshot, ground, lower, verify executable edges, persist `runs/<run_id>/`. |
| `audit table <dir>` | Generate the four reviewer tables from a recorded run. |
| `audit report <dir>` | Write `reports/REPORT.md` from machine evidence. |
| `audit package <dir>` | Export a clean reviewer package with `reproduce.sh`. |

`table`, `report`, and `package` accept `--run <id>` (latest recorded run by
default). `package` accepts `--dest`.

## Workspace

```text
my-paper-audit/
├── audit.yaml
├── manuscript/source.tex
├── equations/equations.yaml
├── edges/edges.yaml
├── expressions/          # native-text members and residuals
├── assumptions/assumptions.yaml
├── runs/                 # immutable evidence (tool-owned)
└── reports/              # tables, REPORT.md, inventory sidecars (tool-owned)
```

`audit.yaml` keys (all required): `schema_version`, `audit_name`,
`manuscript_source`, `equation_manifest`, `edge_manifest`, `assumptions`,
`output_dir`, `verifier_profile`. Alpha accepts only verifier profile
`python_sympy_exact_v1` and schema `DerivationAuditV1`.

Researcher-owned sources are never rewritten. Generated artifacts belong
under `runs/` and `reports/` only.

## Authority and soundness

- A row may enter `TABLE_VERIFIED.md` only when `status == result == ZERO`,
  the record is executable and integrity-ok, and the edge is not
  `SPLIT_PARENT` or `ASYMPTOTIC_CLAIM`.
- Finite Laurent/series/coefficient `ZERO` is not a remainder proof. An
  `ASYMPTOTIC_CLAIM` must not receive engine `ZERO` without
  `remainder_certificate_hash`.
- A `SPLIT_PARENT` is never itself `ZERO`. If every required child is
  integrity-ok `ZERO`, the parent may be `CERTIFIED_BY_CHILDREN`, displayed
  as `SPLIT — all children certified`.
- Changing source, residual, or assumptions invalidates prior `ZERO` rows
  for the new snapshot.

## Assumptions

The machine-enforced surface matches Mode A: declared `real: true` symbols,
optional `nonzero`, and named undefined functions. Notes, manuscript prose,
and citations are not assumptions. Positivity, inequalities, excluded poles,
parameter identities, boundary conditions, symmetries, and limit order are
outside alpha certification.

## Related pages

- [Quickstart](AUDIT_QUICKSTART.md)
- [Edge types](EDGE_TYPES.md)
- [Status semantics](STATUS_SEMANTICS.md)
- [Reviewer package](REVIEWER_PACKAGE.md)
- [Public demos](PUBLIC_DEMOS.md)
- [Privacy](PRIVACY.md)
- [Limitations](DERIVATION_AUDIT_LIMITATIONS.md)
- [Threat model](THREAT_MODEL.md)
- Mode A (still supported): [engineering/release_v0_1/QUICKSTART.md](../engineering/release_v0_1/QUICKSTART.md)
