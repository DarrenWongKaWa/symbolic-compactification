# Interface contract (PHASE 0 freeze)

Agents must import these names. Do not invent parallel enumerations.

## File ownership

| Owner | Files (only these unless noted) |
|---|---|
| Coordinator freeze | `audit/schema.py`, `audit/io.py`, `audit/privacy.py` constants, `audit/workspace.py` init/load, `audit/cli.py` dispatch, `cli.py` argparse, this directory |
| E2 | `audit/inventory.py`, `tests/test_audit_inventory.py` |
| E3 | `audit/edges.py`, `tests/test_audit_edges.py` (do not rewrite init) |
| E4 | `audit/lowering.py`, `tests/test_audit_lowering.py` |
| E5 | `audit/evidence.py`, `tests/test_audit_evidence.py` |
| E6 | `audit/tables.py`, `audit/report.py`, `tests/test_audit_tables.py` |
| E7 | CLI handler bodies in `audit/cli.py` only if a freeze stub is insufficient; prefer not to edit argparse in `cli.py` |
| E8 | `audit/package.py`, `tests/test_audit_package.py` |
| E9 | `audit/html.py` (optional, non-blocking) |
| E10 | `tests/test_derivation_audit_release_critical.py`, `tests/test_audit_adversarial.py` |
| E11 | `engineering/derivation_audit_v0_2/demos/A/` |
| E12 | `engineering/derivation_audit_v0_2/demos/B/` |
| E13 | `engineering/derivation_audit_v0_2/demos/C/` |
| E14 | privacy enforcement + `tests/test_audit_privacy.py` (do not weaken `privacy.py` constants) |
| E15 | user docs listed in the program (`DERIVATION_AUDIT.md`, …) |
| E16 | `tests/test_audit_backward_compat.py` only |

Do not edit another owner's files. Do not bump `RELEASE_VERSION`.

## Authority

```
LLM TEXT CAN NEVER CREATE VERIFIED STATUS.
VERIFIED TABLE IS GENERATED, NOT AUTHORED.
```

`schema.may_appear_in_verified_table` and `schema.table_bucket` are the only
inclusion functions. Markdown ZERO is ignored.

## Asymptotic soundness

Finite Laurent/series/coefficient ZERO ≠ remainder proof. An `ASYMPTOTIC_CLAIM`
must not receive engine ZERO without `remainder_certificate_hash`.

## Signatures

See the stub modules:

- `inventory_equations(workspace, *, write=False) -> EquationInventory`
- `load_edges(workspace) -> tuple[AuditEdge, ...]`
- `ground_edge(edge, workspace) -> GroundingResult`
- `lower_edge(edge, workspace, grounding) -> LoweringResult`
- `verify_audit(workspace) -> AuditRun`
- `load_audit_run(workspace, run_id) -> AuditRun`
- `generate_tables(workspace, run) -> TableArtifacts`
- `generate_audit_report(workspace, run) -> Path`
- `build_reviewer_package(workspace, run, dest=None) -> Path`

Generated artifacts belong under `runs/` and `reports/` only.

## CLI (frozen names)

```
symbolic-compactification audit init|inventory|inspect|verify|table|report|package <dir>
```

`ssc` remains an alias of the same entry point.

## Public demos (independent constructions)

- A: algebraic equation-to-equation identities (multiple ZERO)
- B: typed steps — index relabeling, projector, pairwise reduction
- C: coefficient ZERO + uncertified global remainder UNKNOWN

Do not reverse-engineer unpublished work. Do not use private equation numbers,
nicknames, or recognizable kernels.

## Tests during implementation

Targeted tests only. No full suite per agent. Return commit SHA, files changed,
tests run, interface assumptions, blockers.
