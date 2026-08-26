PYTHON ?= .venv/bin/python
RUNS := research/runs/protocol_v0

.PHONY: venv test benchmark baselines experiments ablations figures paper-data hashes

venv:
	uv venv .venv --python python3.12
	uv pip install -e '.[dev]' --python $(PYTHON)

test:
	$(PYTHON) -m pytest tests/ -q

benchmark:
	$(PYTHON) benchmark/generation/generate_ssc_bench.py

baselines:
	$(PYTHON) research/baselines/runners/run_deterministic.py

experiments: baselines

ablations:
	@echo "LLM ablations require a callable model; deterministic A7 is B7-det in baselines."

figures:
	@echo "figures deferred until experiment tables exist"

paper-data:
	@echo "paper package is gated on research/STATUS.md decision"

hashes:
	@test -f benchmark/validation/freeze_manifest.json && $(PYTHON) -c \
	"import json; print(json.load(open('benchmark/validation/freeze_manifest.json'))['n_items'])"
