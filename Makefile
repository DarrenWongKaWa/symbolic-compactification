PYTHON ?= .venv/bin/python
RUNS := research/runs/protocol_v0

.PHONY: venv test benchmark baselines experiments ablations figures paper-data hashes method-v2 bench-v02 final-eval sd-test sd-bench sd-dev sd-final sd-cases

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

method-v2:
	$(PYTHON) -m pytest tests/test_method_v2_expand.py -q
	$(PYTHON) research/method_v2/run_dev.py

bench-v02:
	$(PYTHON) benchmark_v0.2/generation/build_v02.py

final-eval:
	$(PYTHON) research/final_eval/run_v02.py

hashes:
	@test -f benchmark/validation/freeze_manifest.json && $(PYTHON) -c \
	"import json; print('v0.1', json.load(open('benchmark/validation/freeze_manifest.json'))['n_items'])"
	@test -f benchmark_v0.2/validation/freeze_manifest.json && $(PYTHON) -c \
	"import json; print('v0.2', json.load(open('benchmark_v0.2/validation/freeze_manifest.json'))['n'])"
	@test -f research/structure_discovery/final/FREEZE_MANIFEST.json && $(PYTHON) -c \
	"import json; print('sd', json.load(open('research/structure_discovery/final/FREEZE_MANIFEST.json'))['n_test'])"

sd-test:
	$(PYTHON) -m pytest tests/test_structure_discovery.py -q

sd-bench:
	$(PYTHON) -m research.structure_discovery.prototype.build_benchmark

sd-dev:
	$(PYTHON) -m research.structure_discovery.prototype.run_dev

sd-final:
	$(PYTHON) -m research.structure_discovery.prototype.run_final

sd-cases:
	$(PYTHON) -m research.structure_discovery.prototype.run_case_studies
