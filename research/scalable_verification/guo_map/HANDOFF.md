# HANDOFF — V8 Guo obligation map

Parent: `329c49c22c7d68d0192a59f04bf3ba8ad12c9b48`

Branch: `work/v-guo-obligations`

## Tests

```bash
.venv/bin/python -m pytest tests/test_sv_guo_map.py -q
```

## What landed

- `build.py` reads frozen `research/representation_invention/llm/runs/guo-sigma-abc__P2__s*.json` and the Guo catalog / source index.
- `GUO_OBLIGATION_MAP.json` is evaluation-only: each hypothesis lists `G####` members, copies claimed type / operators / reconstruction (240-cap), attaches full `node.text` (not the catalog 220-cap), and maps `member_id → parent_sum_gid`.
- Does not adjudicate claims. No LLM. Historical runs are not rewritten.

## Remaining risks

- Parent-sum walk follows `build_index` numbering; a traversal change retargets gids.
- Copied `representation_type` strings are claims, not instructions.

## Owned paths

`research/scalable_verification/guo_map/**`, `tests/test_sv_guo_map.py`
