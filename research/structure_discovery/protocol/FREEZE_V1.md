# Protocol freeze v1 (structure discovery)

Date: 2026-08-27

Frozen *before* held-out evaluation:

- Claims C1–C3 as in `CLAIMS.md`
- Taxonomy D0–D6
- Hypothesis schema (`prototype/hypothesis.py`)
- Observation features listed in `observations/FEATURES.md`
- Benchmark version `ssc-structure-bench-v0.1`
- Engine 0.3.0 verifier (no new ZERO rules)
- Metrics: four axes in `prototype/evaluator.py`
- Seeds: deterministic method has one seed (variance 0)
- Models: none (LLM blocked)
- Budgets: 8s per verify attempt; max 8 hypotheses

After `research/structure_discovery/final/FREEZE_MANIFEST.json` is written:

NO method, prompt, metric, or test-set edits under this version id.
