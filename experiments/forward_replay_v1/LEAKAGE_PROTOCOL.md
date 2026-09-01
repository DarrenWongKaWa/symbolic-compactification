# Leakage protocol

A masked replay is invalid if the proposer can read E_{t+1} from its context.

## Mechanical rule

For each recovery task, the exact hidden target string (stripped) must not
occur in any file under `contexts/<task_id>/`.

`scan_leakage.py` enforces that and writes `metrics/leakage_scan.json`.

## Process rule

LLM generation receives only `contexts/<task_id>/`.
It must not receive `hidden/targets/`, `VALIDATION_REPORT.md`,
`TABLE_EVIDENCE.md`, `FROZEN_EDGES.yaml`, or residual files.

CAS and gplearn proposers read only `current.txt` (and declared identities
in notes).

Gold control is inserted **after** generation.

## Semantic leakage (cannot be proven absent)

FR-06 notes declare `e21 = -e12`. That identity is required to *state* the
scientific step; it is not the target formula `TBgeo_e21`.

FR-08 notes declare `f1p = 2*f01p`. Same: convention, not the compact
target expression.

A proposer that already memorized Guo et al. from pretraining is an
unmeasured contamination risk (benchmark skill Element 6). Recorded, not
denied.

## Hashes

Context package SHA-256 values live in `TASKS_FROZEN.yaml` and each
`contexts/<id>/context_meta.json`.
