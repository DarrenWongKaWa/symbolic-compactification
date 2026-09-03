PYTHON ?= python3

.PHONY: venv test release-gate forward-demo audit-demo flagship-html flagship-replay anan-v3

venv:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install -e '.[dev]'

test:
	$(PYTHON) -m pytest -q -m 'release_critical or derivation_audit_release_critical'

release-gate: test
	$(PYTHON) scripts/check_clean_room.py
	$(PYTHON) examples/guo-evidence-ledger/presentation/verify_presentation.py

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
	symbolic-compactification audit report examples/audit/minimal

flagship-html:
	$(PYTHON) examples/guo-evidence-ledger/presentation/assemble_ledger.py
	$(PYTHON) examples/guo-evidence-ledger/presentation/verify_presentation.py

flagship-replay:
	$(PYTHON) examples/guo-evidence-ledger/scripts/inventory_equations.py
	$(PYTHON) examples/guo-evidence-ledger/scripts/relations_frozen.py
	$(PYTHON) examples/guo-evidence-ledger/scripts/verify_and_report.py

anan-v3:
	$(PYTHON) examples/2604.04520/tools/render.py --check
