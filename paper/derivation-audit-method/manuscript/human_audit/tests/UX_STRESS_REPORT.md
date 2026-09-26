# HUMAN_AUDIT_HTML_UX_STRESS_V1

Verdict: **UX_STRESS_RECORDED**

These pages are disposable presentation tests. They are **not** the canonical Guo HTML.
Scientific authority remains frozen machine records on `v0.3.0-alpha` @ `f1d225e`.
No verifier semantics, frozen verdicts, `draft-v3`, paper claims, or experiment results were changed.

Canonical report (unchanged in this campaign):

```text
manuscript/human_audit/guo/index.html
```

Test views:

```text
manuscript/human_audit/tests/reviewer-compact.html
manuscript/human_audit/tests/edge-deep-dive.html
manuscript/human_audit/tests/status-gallery.html
manuscript/human_audit/tests/render-stress.html
```

Do not auto-promote a test variant to canonical. This file reports results only.

---

## Authority

| Item | Value |
|---|---|
| Software | `v0.3.0-alpha` @ `f1d225e` |
| Engine | `python_sympy_exact_v1 0.3.0` |
| Paper | Guo et al., PRL 136, 206303, arXiv:2511.16422v2 |
| Evidence | `examples/flagship/guo/{RESULTS.md, RELATIONS_FROZEN.yaml, expressions/}` |
| HTML role | human-readable projection |

---

## Test A — reviewer compact

File: `reviewer-compact.html`

Kept on the first screen:

- paper / arXiv identity
- 189/189 inventoried (explicitly not certification)
- 146 source-grounded relations
- 53 executable relations
- Appendix D topology for the four flagship transitions
- collapsible legend

Demoted to “Technical provenance (secondary)”:

- engine SHA / tag
- 0/155 false-promotion controls
- 15 UNKNOWN_REMAINDER + 2 UNKNOWN vs historical summary line 17

Observation: a physicist can read the compact page as a single column without opening 146 edges.
The D-66 chain still contains two different zeros (substitution residual vs later cancellation).
Cold readers noticed that; they did not collapse `ZERO_UNDER_SUBSTITUTION` into `EXACT_ZERO`.

---

## Test B — edge deep dive

File: `edge-deep-dive.html`

Edges: D-66→D-67, D-114→D-119, D-57, D-59→D-60, plus multi-parent D-61+D-67→D-68.

Compiled obligations (not a universal \(E_{\mathrm{before}}-E_{\mathrm{after}}\)):

| Edge | Compiled obligation | Direct residual |
|---|---|---|
| D-59 → D-60 | \(R=K_{1A}^{\mathrm{D-59}}-K_{1A}^{\mathrm{D-60}}\) | \(R=0\) |
| D-66 → D-67 | \(R=T_{B,\mathrm{geo}}^{\mathrm{D-66}}-T_{B,\mathrm{geo}}^{\mathrm{D-67}}\) | \(\frac{f_2'(\epsilon_{12}+\epsilon_{21})(g_{ab}v_2^c+g_{ac}v_2^b)}{4}\) |
| D-61, D-67 → D-68 | \(R=T_A^{(-2)}+T_{B,\mathrm{geo}}^{(-2)}\) | \(R=0\) |
| D-114 → D-119 | local \(R_{\mathrm{Leibniz}}=\partial_k(uv)-[(\partial_k u)v+u(\partial_k v)]\); parent integral not posed | child ZERO; parent N/A |
| D-57 | no executable residual; author-declared \(O(\Gamma)\) | UNKNOWN |

Canonical `guo/report.js` still templates every executable residual as

```tex
R_{\mathrm{direct}}=E_{\mathrm{before}}-E_{\mathrm{after}}.
```

That template is wrong for the IBP parent, the remainder claim, and the two-parent cancellation.
The deep-dive page is the intended replacement pattern if a later presentation revision is authorized.

---

## Test C — status gallery

File: `status-gallery.html`

One frozen example each, labelled PRESENTATION TEST ONLY:

| Status | Example |
|---|---|
| EXACT_ZERO | Eq. (D-59) → Eq. (D-60) |
| ZERO_UNDER_SUBSTITUTION | Eq. (D-66) → Eq. (D-67) |
| CERTIFIED_BY_RULE | Eq. (D-114) → Eq. (D-119) |
| UNKNOWN_REMAINDER | Eq. (D-57) |
| STRUCTURAL | Eq. (4) |
| UNSUPPORTED | Eq. (A-11) → Eq. (A-14) |

No new scientific evidence. Cards use “means / does not mean” rather than a ranked scale.

Chrome rendering: all six cards visible; D-66 residual in the gallery card is cramped (indices collide).
The compact and deep-dive pages render that residual more clearly.

---

## Test D — rendering stress

File: `render-stress.html` (append `?nomathjax=1` for TeX fallback)

Exercised: long residual (D-126→D-127 projection), tensor indices, Greek, derivatives, bars, multi-parent sum, min-width overflow, print CSS.

| Environment | Result |
|---|---|
| Chrome, `http://127.0.0.1` | Mathematics rendered (MathJax 3). Long residual shows a horizontal scrollbar rather than clipping. |
| Chrome, `file://` | Compact page byte-identical screenshot to HTTP (CDN MathJax loaded). |
| Chrome print-to-PDF | Compact: 3 pages, inventory sentence present. Stress: 2 pages. Test banner hidden by print CSS. |
| MathJax suppressed | Raw `\(...\)` / `\[...\]` visible. Not clipped. Readable as source. |
| Safari | Compact HTTP URL opened in Safari.app. No headless screenshot API used. |
| Firefox | Not installed on this machine. **Not tested.** |

No silent truncation observed in Chrome. Overflow is explicit (`overflow-x: auto`).

---

## Audit of canonical `guo/index.html`

These are findings. **Not applied** in this campaign.

1. **First-screen metrics.** Canonical shows eight tiles (including EXACT_ZERO 32, substitution 21, CERTIFIED_BY_RULE 11, 0/155, “0 final NONZERO”). Spec for a cold first screen: only 189/189, 146, 53. Compact test implements that.

2. **False-promotion 0/155.** On the canonical headline strip. Should be validation/provenance. Compact demotes it.

3. **“0 final NONZERO”.** On the canonical headline. Cold readers already stumble on NONZERO vs paper-error; putting a zero count in the header does not help. Compact omits it.

4. **15 + 2 vs historical 17.** Canonical header paragraph. Compact moves it to technical provenance.

5. **Verification-authority banner.** Canonical header includes tag, SHA, engine name, ZERO≠CERTIFIED_BY_RULE, UNKNOWN never promotes. Compact keeps a one-line inventory note up top; SHA/engine live in a collapsed drawer and footer.

6. **Search index.** Canonical `data-hay` is only display, move, status, cue, from, to, role. Missing: condition text, source-context paraphrase, human explanation, residual/math labels. Searching `epsilon_21` or “torus” will miss edges.

7. **Why-NONZERO vs frozen evidence.** All 21 direct-NONZERO rows are `ZERO_UNDER_SUBSTITUTION` with a recorded `subst`. The why-text is the frozen condition plus, when the projected residual actually contains \(\epsilon_{12}+\epsilon_{21}\) or \(f_n'-2f_{0,n}'\), that factor. No “paper forgot” / “equation is wrong” / “likely true.” **Supported.** The extra factor sentence is a projection of the residual, not a new verdict.

8. **Derivation-map arrows.** 27 chain steps, 27 unique relation IDs, all present in frozen `RESULTS.md` / YAML. Leftover rows are buttons, not arrows. No adjacency-only arrows found.

Additional canonical issue (from Test B): universal \(R=E_{\mathrm{before}}-E_{\mathrm{after}}\) in `report.js`.

---

## Cold-reader test

Protocol: three independent read-only reviewers. Each was instructed to open **only** `reviewer-compact.html` (no RESULTS.md, no JSON, no product docs).

These reviewers are isolated agents, not laboratory humans. Times are self-estimated. The test still checks whether the *wording* of the compact page forces the forbidden readings.

Expected answers:

| Q | Required meaning |
|---|---|
| A | Inventory, not certified |
| B | No |
| C | \(\epsilon_{21}=-\epsilon_{12}\) |
| D | Residual of D-66→D-67 after that identity (not unconditional parent ZERO) |
| E | Local Leibniz ZERO + declared BZ torus rule; parent not engine ZERO |
| F | No |
| G | No |
| H | No general remainder certificate |

Results (3 reviewers × 8 questions = 24):

| Q | R1 | R2 | R3 | Wrong semantic reading? |
|---|---|---|---|---|
| A | correct | correct | correct | no |
| B | correct | correct | correct | no |
| C | correct | correct | correct | no |
| D | correct (slight hesitation) | correct (slight) | correct (slight) | no |
| E | correct | correct | correct | no |
| F | correct | correct | correct | no |
| G | correct | correct | correct | no |
| H | correct (slight) | correct (slight) | correct (slight) | no |

**Score: 24 / 24 = 100%** on the core questions.

No reviewer treated ZERO_UNDER_SUBSTITUTION as unconditional ZERO, CERTIFIED_BY_RULE as parent ZERO, or UNKNOWN_REMAINDER as “D-57 is false.”

Hesitation / confusion (not errors):

- 189/189 still *looks* like a pass rate until the inventory sentence is read.
- NONZERO still *looks* like a failed paper identity until the substitution sentence is read.
- Two zeros on the D-66…D-68 chain (conditional residual vs later EXACT_ZERO cancellation).
- Child Leibniz ZERO vs parent CERTIFIED_BY_RULE.
- H: page names the missing object (“general remainder certificate”) but not the analytic hypotheses that certificate would need.

Self-estimated time per reviewer: about 2 minutes of reading for A–H. Fits the “under 3 minutes” compact-view goal for this protocol.

Success criterion (≥90%, no semantic misunderstanding of the four status classes): **met on the compact test page**, under this agent protocol.

The **canonical** `guo/index.html` was not given to these reviewers. It still has the eight first-screen issues above, so this score does **not** certify the canonical page.

---

## Recommendation (not applied)

If a later presentation revision is authorized, in this order:

1. Adopt the compact first screen (3 metrics + inventory sentence + four flagship rows + D topology).
2. Replace the universal residual template with compiled-obligation language from `edge-deep-dive.html`.
3. Expand search `data-hay`.
4. Keep SHA, 0/155, and 15+2 in provenance.
5. Keep the status gallery’s “means / does not mean” copy near the legend.

Do **not** replace `guo/index.html` from this report automatically.

---

## Files

| Path | Role |
|---|---|
| `tests/reviewer-compact.html` | Test A |
| `tests/edge-deep-dive.html` | Test B |
| `tests/status-gallery.html` | Test C |
| `tests/render-stress.html` | Test D |
| `tests/tests.css` | Shared test CSS |
| `tests/UX_STRESS_REPORT.md` | This report |
| `guo/index.html` | Canonical (unchanged here) |

`draft-v3` unchanged. Product semantics unchanged. `v0.3.0-alpha` not moved.
