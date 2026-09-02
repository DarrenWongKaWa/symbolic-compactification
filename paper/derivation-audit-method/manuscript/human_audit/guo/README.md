# Human-facing audit report (Guo flagship)

`index.html` is a **presentation** of the frozen Guo et al. paper-audit.

It is not verification authority.

```text
paper → derivation map → expand one edge → why accepted / refused / unresolved
```

Machine records remain the scientific source:

- `examples/flagship/guo/RESULTS.md`
- `examples/flagship/guo/RELATIONS_FROZEN.yaml`
- `examples/flagship/guo/expressions/`

on software authority

```text
symbolic-compactification v0.3.0-alpha @ f1d225e
engine python_sympy_exact_v1 0.3.0
```

`report-data.json` / `report-data.js` are a view model projected from those records.
JavaScript never infers `ZERO`, `NONZERO`, `UNKNOWN`, `CERTIFIED_BY_RULE`, or
`ZERO_UNDER_SUBSTITUTION`. It only renders statuses copied from `RESULTS.md`.

189/189 means **numbered equations inventoried**. It does not mean 189 equations
were certified. The first screen shows only inventory, relation, and executable
counts. SHA, 0/155 controls, and the 15+2 vs 17 remainder-summary note live in
the footer. Presentation freeze: `../HUMAN_AUDIT_HTML_FREEZE.md`.

## Open locally

No build step is required.

```text
paper/derivation-audit-method/manuscript/human_audit/guo/index.html
```

Open that file in a browser (double-click, or `open index.html` on macOS).
Keep `report.css`, `report.js`, and `report-data.js` in the same folder.

A local HTTP server is optional:

```bash
python3 -m http.server 8765 --directory .
# then visit http://127.0.0.1:8765/
```

## Math renderer

Mathematics is rendered with **MathJax 3** from jsDelivr:

```text
https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js
```

That CDN request needs network access. No custom font files are committed.
If you are offline, TeX delimiters `\(...\)` and `\[...\]` remain visible as
source; statuses and derivation topology still work.

## Frozen vs generated

| File | Role |
|---|---|
| `examples/flagship/guo/RESULTS.md` on `v0.3.0-alpha` | Frozen scientific table (authority) |
| `examples/flagship/guo/RELATIONS_FROZEN.yaml` | Frozen source-grounded relations (authority) |
| `examples/flagship/guo/expressions/` | Frozen encodings / selected residuals (authority) |
| `report-data.json`, `report-data.js` | Generated presentation view model |
| `index.html`, `report.css`, `report.js` | Presentation shell |
| `build_report_data.py` | Regenerates the view model |

Do not treat HTML copy as a new experiment, a new certificate, or a reason to
retune residuals.

## Regenerate presentation data

From this directory, with the frozen flagship tree readable (the consolidation
worktree used for this freeze, or a checkout of `v0.3.0-alpha`):

```bash
python3 build_report_data.py \
  --flagship /path/to/examples/flagship/guo \
  --out .
```

The script copies per-row statuses from `RESULTS.md`. It may project frozen
`left`/`right` encodings into TeX so a scientist can see a residual. That
projection does not change the verdict. If a projection is unavailable, the
frozen status is still shown and the encoding is left in Technical provenance.

Requires: Python 3, `PyYAML`, `sympy` (display projection only).

## What this report is for

A theoretical physicist should be able to answer, from the HTML alone:

1. Which printed equations are related.
2. What move the author claims.
3. What the machine actually checked.
4. If the direct residual is NONZERO, what that residual is and why.
5. Which source-grounded condition was then applied.
6. Why the final status is `EXACT_ZERO`, `ZERO_UNDER_SUBSTITUTION`,
   `CERTIFIED_BY_RULE`, `UNKNOWN_REMAINDER`, etc.

Internal IDs (`R048`, `D.TBgeo-eps21`) live only in the Technical provenance
drawer.

## Out of scope

- Other papers (Hagiwara, Cohen, Souza, Flathmann) are not built here.
- Product code under `src/` is not modified.
- `manuscript/draft-v3.md` is not modified.
- `v0.3.0-alpha` is not moved.
