# Reproducibility

Python ≥ 3.10 (repo `.venv` is 3.12). Engine: SymPy only.

```bash
uv venv .venv --python python3.12
uv pip install -e '.[dev]' --python .venv/bin/python
.venv/bin/pytest tests/ -q
.venv/bin/python benchmark/generation/generate_ssc_bench.py   # v0.1; do not edit test after freeze
.venv/bin/python research/baselines/runners/run_deterministic.py
.venv/bin/python research/method_v2/run_dev.py
.venv/bin/python benchmark_v0.2/generation/build_v02.py
.venv/bin/python research/final_eval/run_v02.py
```

Frozen hashes: `benchmark/validation/freeze_manifest.json`,
`benchmark_v0.2/validation/freeze_manifest.json`.

v0.1 **test** must not be edited. Method v2 does not change ZERO meanings.

No API keys required for the deterministic v2 eval. LLM bottleneck
subagent transcripts are under `research/search_bottleneck/runs/`.

Do not commit secrets or PRB closed-form gold.
