# Guo evidence ledger (flagship)

Guo, Pan, Peotta, Du, and Nagaosa, *Dissipation-Shaped Quantum Geometry
in Nonlinear Transport*, Phys. Rev. Lett. **136**, 206303 (2026)
([arXiv:2511.16422v2](https://arxiv.org/abs/2511.16422v2)).

This folder is the reference implementation of the product: take a
paper, build evidence layers, show a reviewer HTML and the same science
as Markdown.

**Presentation is not a certificate.** Open `output/index.html`.

## What a new reader should do

1. Open [`output/index.html`](output/index.html) in a browser.
2. Read the three cells: inventoried / extracted / executable.
   Inventory coverage is not a paper pass.
3. Green = local residual 0. Blue = definition or cited rule.
   Orange = you must look. Dark red = residual ≠ 0.
4. Sign the four claimed cancels if you accept them. Signing does not
   rewrite `evidence/RESULTS.md`.
5. Click Appendix map A–G (first screen) to jump into the ledger.
6. Compare any row to [`output/REPORT.md`](output/REPORT.md) — same
   frozen statuses.

## Layers (provenance)

```text
input/          paper TeX + numbered-equation inventory
evidence/       frozen relations, encodings, RESULTS.md
expected/       presentation hashes and integrity fixtures
output/         reviewer HTML + Markdown
presentation/   HTML sources (assemble_ledger.py)
scripts/        inventory / freeze / replay (does not change src/)
```

| Layer | What it is | Who may change it |
|---|---|---|
| `input/source_anchors/main.tex` | Paper source | Nobody in this replay |
| `input/EQUATION_INVENTORY.yaml` | Every numbered equation | Inventory script only |
| `evidence/RELATIONS_FROZEN.yaml` | Source-grounded edges | Frozen before verify |
| `evidence/expressions/` | Compiled residuals | Frozen encodings |
| `evidence/RESULTS.md` | Scientific table | Verify replay copies engine verdicts; do not hand-edit statuses to look better |
| `output/index.html` | Reviewer HTML | `presentation/assemble_ledger.py` |
| `output/REPORT.md` | Reviewer Markdown | Same table as RESULTS |

Every HTML row traces to a RESULTS row, which traces to a frozen
relation, which traces to printed equation numbers in the TeX.

## How symbolic compactification helps

The engine checks whether a compiled left−right residual is exactly 0
under declared symbols. It does **not** certify integrals, \(O(\cdot)\)
remainders, special-function identities, or claimed cancellations.

On this paper: 53 executable obligations, 32 `EXACT_ZERO`, 21
`ZERO_UNDER_SUBSTITUTION`, 11 `CERTIFIED_BY_RULE`. The rest stay
orange or blue.

## Reproduce

```bash
# presentation only (no engine):
python examples/guo-evidence-ledger/presentation/assemble_ledger.py
python examples/guo-evidence-ledger/presentation/verify_presentation.py

# engine replay of frozen executable residuals:
python examples/guo-evidence-ledger/scripts/inventory_equations.py
python examples/guo-evidence-ledger/scripts/relations_frozen.py
python examples/guo-evidence-ledger/scripts/verify_and_report.py
```

Software authority: symbolic-compactification `v0.3.0-alpha` @ `f1d225e`,
engine `python_sympy_exact_v1` 0.3.0. This packaging release does not
change those verdicts.

## Out of scope

- `0*` workspace overlay is invalid history
  (`docs/history/invalid-0star-lineage/`). It is not in `output/`.
- Other papers in `examples/audit/` are formative, not this flagship.
