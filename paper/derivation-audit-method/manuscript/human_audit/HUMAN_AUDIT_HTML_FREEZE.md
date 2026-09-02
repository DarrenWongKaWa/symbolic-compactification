# Human-facing Guo audit — presentation freeze

Verdict: **HUMAN_AUDIT_HTML_FROZEN**

Canonical entry:

```text
manuscript/human_audit/guo/index.html
```

Scientific authority remains frozen machine records on
`v0.3.0-alpha` @ `f1d225e`. This HTML does not assign verdicts.

UX stress evidence (not canonical):

```text
manuscript/human_audit/tests/UX_STRESS_REPORT.md
commit 5bc5e26
```

Canonical small convergence is this freeze commit (first-screen metrics,
compiled-obligation residual language, expanded search, footer provenance).

`draft-v3` unchanged. Product semantics unchanged. Tag not moved.
Not five-paper HTML. Not draft-v4. Not humanizer.

---

## Decision from UX_STRESS_REPORT.md

Cold-reader protocol on `reviewer-compact.html`: 24/24 on A–H.
No semantic collapse of ZERO, ZERO_UNDER_SUBSTITUTION,
CERTIFIED_BY_RULE, or UNKNOWN_REMAINDER.

Canonical HTML was therefore given **one small convergence**, not a
replacement by the compact test page. Full map and 146 collapsed edges remain.

---

## Classification of confusions

### Safe information design (applied)

| Issue | Action |
|---|---|
| First screen had eight metric tiles | Keep 189/189, 146, 53 only |
| 0/155 looked like a coverage count | Footer / validation |
| “0 final NONZERO” in the headline | Removed from header (legend still explains direct NONZERO) |
| 15+2 vs historical 17 in the header | Footer; statuses still not merged |
| Heavy SHA/engine banner | One-line header; details in footer |
| Search missed condition / paraphrase / why | `data-hay` expanded |
| D-66 chain has two different zeros | One sentence under flagship table |
| Universal \(R=E_{\mathrm{before}}-E_{\mathrm{after}}\) | Compiled obligation: lhs−rhs for equalities; not used for IBP/remainder/multi-parent sum-to-zero |
| “Before / After” read as narrative time | “Left / right encoding (frozen)” |

### Epistemic / PAPER_AUTHORITY_LOCK (not loosened)

Do not, in this or later presentation edits:

- write 189 equations verified
- merge UNKNOWN limit rows into UNKNOWN_REMAINDER on the page
- treat CERTIFIED_BY_RULE as parent ZERO
- treat ZERO_UNDER_SUBSTITUTION as unconditional ZERO
- treat UNKNOWN_REMAINDER as “the expansion is false”
- treat author-declared as machine-certified
- invent why-NONZERO causes beyond frozen subst / residual factors
- cite live `main` for counts or semantics
- retune residuals or change frozen statuses

Lock depth line “UNKNOWN_REMAINDER 17” is the RESULTS.md summary convention
(15 remainder rows + 2 UNKNOWN). The HTML still shows the split in the footer.

### Stress-fixture only (not entered into canonical)

- `render-stress.html` min-width overflow box
- `?nomathjax=1` harness
- gallery-card cramped D-66 residual (deep-dive form is enough)
- sympy expanding both Leibniz encodings to the same TeX
- Firefox not installed; Safari not headless-captured
- print-to-PDF of test pages

---

## Freeze contents

Canonical files:

- `guo/index.html`
- `guo/report.js`
- `guo/report.css`
- `guo/report-data.json` / `report-data.js` (view model; statuses still copied from RESULTS.md)
- `guo/README.md`

Test fixtures remain under `tests/` for reproducibility of the UX experiment.

---

## Next allowed step

Venue freeze, then draft-v4. Not humanizer. Not five-paper HTML.
