# FIGURE_FREEZE_V1

Verdict: **FIGURES_FROZEN**

Software authority: `v0.3.0-alpha` @ `f1d225e`.
Editable source: TikZ (`figure.tex`). Publication PDF is the text-selectable
authority. SVG is a vector companion (pdftocairo; fonts outlined).
Canvas: two-column width \(6.95\) in. Do not insert at single-column
width without enlarging type.

Visual grammar: white ground; one blue family (`#2E5A88`) plus grayscale;
status also encoded by fill / dashed / double / dotted borders.

---

## Figure 1 — two workflows, one object

| | |
|---|---|
| Purpose | Conceptual flagship: same typed graph, Forward + Audit |
| Source | `fig1_two_workflows/figure.tex` |
| SVG / PDF | `fig1_two_workflows/figure.svg`, `figure.pdf` |
| Claims | L1, L2, L3, L6 |
| Numbers | none |
| Allowed caption | same typed evidence graph; untrusted candidates; fail-closed outputs |
| Prohibited | “AI verification”; novelty of independent checking |

## Figure 2 — \(\tau\) versus \(c\)

| | |
|---|---|
| Purpose | Independent axes, not a truth ranking |
| Source | `fig2_claim_evidence_axes/figure.tex` |
| SVG / PDF | `fig2_claim_evidence_axes/figure.svg`, `figure.pdf` |
| Claims | L4, L6, L7, L21 |
| Numbers | none |
| Allowed caption | \(\tau\) and \(c\) are independent; `ZERO` \(\neq\) `CERTIFIED_BY_RULE` |
| Prohibited | ranking certificate classes; remainder proof |

## Figure 3 — Forward fail-closed trajectory

| | |
|---|---|
| Purpose | Gating, not proposer ranking |
| Source | `fig3_forward_fail_closed/figure.tex` |
| SVG / PDF | `fig3_forward_fail_closed/figure.svg`, `figure.pdf` |
| Claims | L3, L5, L11, L13 |
| Numbers | false promotion \(0/36\) |
| Allowed caption | promote only on admissible evidence; refusals leave \(E_t\) |
| Prohibited | TargetRecovery leaderboard; autonomous discovery |

## Figure 4 — Guo flagship

| | |
|---|---|
| Purpose | Depth: inventory \(\neq\) certification |
| Source | `fig4_guo_flagship/figure.tex` |
| SVG / PDF | `fig4_guo_flagship/figure.svg`, `figure.pdf` |
| Claims | L14–L18, L20 |
| Numbers | 189/189; 146; 53; 32; 21; 11; 17; 47; 18; 0; 0/155 |
| Allowed caption | 189/189 inventoried, not 189 certified |
| Prohibited | “full paper verified”; “189 equations proved” |

---

## Three-reader check

| Reader | Question | Result |
|---|---|---|
| Theoretical physicist | What does the system do? | Pass. Fig 1 is the method; Fig 4 uses printed equation numbers. |
| Formal-methods | Independent checking drawn as novel? | Pass. Fig 1 caption locates prior art; the drawing is the shared object. |
| AI/agent | LLM as verifier? | Pass. Model is one optional proposer; adjudication is fail-closed engine output. |

## Print-scale

Designed at \(6.95\) in (two-column). Type is \(\small\)/\(\footnotesize\).
Single-column insertion would drop below 8 pt: do not.

## Gate

- [x] four figures as TikZ + SVG + PDF
- [x] one visual language
- [x] no unsupported numbers
- [x] no `main` / post-tag drift
- [x] no claim beyond the matrix
- [x] Related Work novelty boundary respected
- [x] Fig 1 two workflows / one object
- [x] Fig 2 \(\tau\) vs \(c\)
- [x] Fig 3 gating, not ranking
- [x] Fig 4 189/189 inventory, never 189 verified
- [x] Guo printed numbers (D-57), (D-59)→(D-60), (D-66)→(D-67), (D-114)→(D-119)
- [x] captions preserve epistemic boundaries
- [x] draft-v3 unchanged
- [x] no venue, no humanizer

Rebuild: `make -C manuscript/figures`.
