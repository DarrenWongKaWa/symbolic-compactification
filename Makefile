PYTHON ?= python3

.PHONY: venv test release-gate forward-demo audit-demo flagship-replay

venv:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install -e '.[dev]'

test:
	$(PYTHON) -m pytest -q -m 'release_critical or derivation_audit_release_critical'

release-gate: test
	$(PYTHON) scripts/check_clean_room.py

forward-demo:
	$(PYTHON) -c "from pathlib import Path; import tempfile, shutil; from symbolic_compactification import ZERO, NONZERO, verify_hypothesis; \
root=Path('examples/forward'); \
d=Path(tempfile.mkdtemp()); \
shutil.copytree(root/'exact-step', d/'exact'); \
shutil.copytree(root/'refused-step', d/'refused'); \
assert verify_hypothesis(d/'exact').result==ZERO; \
assert verify_hypothesis(d/'refused').result==NONZERO; \
print('forward demos PASS')"

audit-demo:
	symbolic-compactification audit verify examples/audit/minimal
	symbolic-compactification audit table examples/audit/minimal

flagship-replay:
	$(PYTHON) examples/flagship/guo/scripts/inventory_equations.py
	$(PYTHON) examples/flagship/guo/scripts/relations_frozen.py
	$(PYTHON) examples/flagship/guo/scripts/verify_and_report.py
