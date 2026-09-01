# Reproduce the Guo flagship audit

Source: arXiv:2511.16422v2 (`source_anchors/main.tex`).
Engine semantics: frozen `python_sympy_exact_v1` (engine 0.3.0).

From a checkout with the package installed:

```bash
python examples/flagship/guo/scripts/inventory_equations.py
python examples/flagship/guo/scripts/relations_frozen.py
python examples/flagship/guo/scripts/verify_and_report.py
```

The first command rebuilds the numbered-equation inventory from TeX counters
and `source_anchors/html_printed_numbers.json`. The second rewrites the
frozen relation manifest. The third reruns `verify_hypothesis` on executable
residuals and regenerates `RESULTS.md`. No LLM and no API key.

Public residuals under `expressions/` are the same commuting-scalar
transcriptions used in the selected-edge validation
(`archive/guo-selected-edge-validation-v1`).
