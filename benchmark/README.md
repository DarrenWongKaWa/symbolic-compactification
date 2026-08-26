# ssc-bench-v0.1

Scientific Symbolic Compactification Benchmark. Frozen with protocol v0
(`research/protocol/EXPERIMENT_FREEZE.md`).

Do not edit `test/` items after freeze without minting `ssc-bench-v0.2`.

## Tiers

| Tier | Purpose | Task |
|---|---|---|
| A | verifier stress: identities + controlled corruptions | `adjudicate` |
| B | generic compactification with hidden equivalent gold | `compactify` |
| C | scientific expressions | `compactify` |

`C-guo-sigma-abc` is in **dev**, tagged contaminated (used in 2026-08-21
engine experiments). It is a case study, not an unseen test item. The PRB
closed form is **not** stored here.

Other Tier C items are author-constructed skeletons (Kubo-like sums,
Green's functions, thermal kernels, indexed vertices). They are not
copied from copyrighted papers.

## Splits

Deterministic: `sha256("ssc-bench-v0.1:split:" + id)` → test if
`int(hex[:8], 16) % 10 < 3`, else dev. Guo is forced to dev.

## Hidden fields (never to proposers)

`human_reference`, `target_compact`, `expected_verdict`, `mutation_type`,
`ladder_id`, `notes`. Use `research.metrics.evaluator.proposer_view`.

## Regenerate (dev only; do not overwrite frozen test without a new version)

```bash
.venv/bin/python benchmark/generation/generate_ssc_bench.py
```

Generation **confirms** identities with the engine. Mutations that remain
ZERO are dropped, not relabelled.

## Files

- `schema.json` — item schema
- `metadata.csv` — ids, splits, sha256 of each item file
- `validation/freeze_manifest.json` — counts and hashes
- `provenance/` — origin notes
- `dev/tier_{a,b,c}/` and `test/tier_{a,b,c}/` — one JSON per item
