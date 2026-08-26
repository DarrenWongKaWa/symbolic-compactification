# Reproducibility — structure-discovery line

Does not replace `REPRODUCIBILITY.md` (compactification protocol v0).

## Environment

- Python ≥ 3.10 (this snapshot: CPython 3.12 via `.venv`)
- `pip install -e '.[dev]'` (SymPy + pytest)
- Engine 0.3.0; no method edits after `research/structure_discovery/final/FREEZE_MANIFEST.json`

## Commands

```bash
python -m pytest tests/test_structure_discovery.py -q
python -m research.structure_discovery.prototype.build_benchmark
python -m research.structure_discovery.prototype.run_dev      # DEV only
python -m research.structure_discovery.prototype.freeze       # then stop editing
python -m research.structure_discovery.prototype.run_final    # held-out, once
python -m research.structure_discovery.prototype.run_case_studies
python -m research.structure_discovery.prototype.generate_figures
```

Makefile: `make sd-test sd-bench sd-dev sd-final`

## What cannot be reproduced here

- LLM / multi-model / 5-seed tables (`ANTHROPIC_AUTH_TOKEN` length 35; no
  OpenAI, Gemini, xAI, WolframKernel, Lean, egglog).
- Human physicist D6 annotations (none collected; none fabricated).

## Leakage

`proposer_view` strips hidden gold. Context strings contain no gold auxiliary
names. Guo is not in TEST.
