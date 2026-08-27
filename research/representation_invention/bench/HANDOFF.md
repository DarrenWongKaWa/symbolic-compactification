# HANDOFF — Subagent D (benchmark)

Parent: `45b2b4dc7c823901f4b79713d279c6be7bae2859`

Branch: `work/representation-bench`

Commit message: `Add ssc-representation-bench-v0.1 DEV and frozen TEST.`

SHA: use `git rev-parse work/representation-bench` (this worktree may be on another agent branch).

## Owned

- `research/representation_invention/bench/**`
- `tests/test_representation_bench.py`

Did not mutate frozen trees under `research/llm_abstraction/`,
`research/structure_discovery/`, or `research/abstraction_invention/`.

## Delivered

`ssc-representation-bench-v0.1`

- Schema: `schema.json` + `loader.validate_task`
- `loader.proposer_view()` whitelist; hidden target labels stripped
- DEV: 18 tasks (`tasks/dev/`)
- TEST: 14 frozen tasks (`tasks/test/`) + `validation/freeze_manifest.json`
- Tiers A/B/C, positives and adversarial negatives
- `dev-guo-pointer` is DEV-only with `catalog_external`; no full Guo expression

## Tests

```
.venv/bin/python -m pytest tests/test_representation_bench.py -q
```

13 passed.

## Remaining risks

- Repeated-node / Hermite members use a declared `df`/`ds` head because the
  engine parser does not admit `Derivative`.
- `proposer_view` still exposes `split` and `tier` (not target labels).
- TEST hashes are freeze-gated; regenerating TEST without a version bump is
  a protocol break.
- Guo catalog content is owned by Subagent G; the pointer task is empty.
- Shared worktree may contain other subagent files; they are not in this commit.
