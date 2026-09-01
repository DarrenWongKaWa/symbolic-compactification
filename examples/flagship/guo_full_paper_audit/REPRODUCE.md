# Reproduce

Product: derivation-audit-v0.2.1-alpha (commit 783ec64).
Paper: arXiv:2511.16422v2 (`source_anchors/main.tex`).

From a checkout of this branch, with the frozen package installed:

```bash
python examples/flagship/guo_full_paper_audit/scripts/inventory_equations.py
python examples/flagship/guo_full_paper_audit/scripts/relations_frozen.py
python examples/flagship/guo_full_paper_audit/scripts/verify_and_report.py
```

The first command rebuilds `EQUATION_INVENTORY.yaml` from `source_anchors/main.tex` (Route A) and `source_anchors/html_printed_numbers.json` (Route B). Optional: download https://arxiv.org/html/2511.16422v2 to `source_anchors/arxiv_html_v2.html` and rerun inventory against live HTML tags.

The second command rewrites `RELATIONS_FROZEN.yaml` from the frozen Python manifest. It does not invent new relations.

The third command reruns `verify_hypothesis` on executable residuals and regenerates `RESULTS.md` and `COVERAGE.json`. It does not call an LLM.

Public residuals under `expressions/` were copied unchanged from the public Guo evidence at 69ad474.
