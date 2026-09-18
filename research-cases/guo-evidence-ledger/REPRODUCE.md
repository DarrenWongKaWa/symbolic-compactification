# Reproduce the Guo flagship audit

Source: arXiv:2511.16422v2 (`input/source_anchors/main.tex`).
Engine semantics: frozen `python_sympy_exact_v1` (engine 0.3.0).

From a checkout with the package installed:

```bash
python examples/guo-evidence-ledger/scripts/inventory_equations.py
python examples/guo-evidence-ledger/scripts/relations_frozen.py
python examples/guo-evidence-ledger/scripts/verify_and_report.py
```

The first command rebuilds the numbered-equation inventory from TeX
counters. The second rewrites the frozen relation manifest. The third
reruns `verify_hypothesis` on executable residuals and regenerates
`evidence/RESULTS.md` and `output/REPORT.md`. No LLM and no API key.

Rebuild the HTML presentation (does not adjudicate mathematics):

```bash
python examples/guo-evidence-ledger/presentation/assemble_ledger.py
python examples/guo-evidence-ledger/presentation/verify_presentation.py
```

Public residuals under `evidence/expressions/` are the same
commuting-scalar transcriptions used in the selected-edge validation
(`archive/guo-selected-edge-validation-v1`).
