# Handoff — Subagent G (Guo DEV catalog)

Branch: `work/representation-guo`

Tip SHA: `29594619fae799a9a2b4e526d8d9344810812397`

Catalog commit: `9a8af1ef7b5677f5294b49f4eacb58bd7f5d7975`
(`Add Guo DEV catalog and gold-free evaluation queries.`)

A follow-up dropped LLM harness files that had been staged in the same
index. `1fde151..HEAD` is Guo-owned paths only.

## Tests

```
.venv/bin/python -m pytest tests/test_representation_guo.py -q
```

6 passed. Load/parse failure on the real Guo source raises (no skip).

## What landed

- `catalog.py` wraps `build_index` + `catalog_entries` on
  `examples/long/Guo_Sigma_abc_dc_exact.txt`. Expected structural counts:
  4 Sums, 14 Piecewise branches. Member ids are G####. No gold extra fields.
- `proposer_view.py` renders the catalog plus the historical Guo scientific
  context. It does not import `eval.queries`.
- `eval/queries.py` (hidden): local confluence, Newton-DD candidate,
  repeated-node DD, possible master families. Candidate G#### pairs are
  derived from catalog fingerprints, not copied construction notes.
- `COUNTS.md` (hidden): evaluation notes for the 4/14 counts.

## Remaining risks

- Instantiated query pairs follow `build_index` numbering. A change in
  source-index traversal would retarget candidates; templates themselves
  do not hardcode ids.
- Evaluation queries must stay out of proposer packets after merge
  (Subagent D/E). They are checks, not a representation decision.
- This package does not claim divided differences or a master object.

## Owned paths

`research/representation_invention/guo/**`, `tests/test_representation_guo.py`
