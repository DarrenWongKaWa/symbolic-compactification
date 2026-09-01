# Figure 2 — Two-axis evidence semantics

Skill: `figure-designer`. Supporting methodology figure (solution-overview
detail), not a bar chart.

Supersedes `fig2-certificate-taxonomy.md` as the load-bearing semantics figure.
Do not draw a pyramid or a truth ranking.

---

### 1. Figure type

- Type: solution-overview (detail of the centre of Figure 1)
- Reason: the method's mechanism is the two-axis record, not a pipeline stage.

### 2. Paradigm

- Paradigm: Multi-layer (two horizontal axes, not a ranking)
- Why: the paper's technical claim is \(\tau \neq c\).
- Rejected: pipeline (hides the two axes); performance chart (no metric).

### 3. Layout sketch

- Canvas: ~150 mm × 85 mm.
- TOP ROW — **What move is claimed?** (\(\tau\), edge type)
  - cards: `ALGEBRAIC_EQUIVALENCE`; `BZ_PERIODIC_INTEGRATION_BY_PARTS`;
    `ASYMPTOTIC_CLAIM`; `DEFINITION_INSERTION`
- BOTTOM ROW — **What supports it?** (\(c\), certificate provenance)
  - cards: `DIRECT_EXACT` (circle); `SUBSTITUTION_EXACT` (square);
    `RULE_CERTIFICATE` (diamond); `UNKNOWN` (triangle); `STRUCTURAL` (hexagon)
- Example matrix (thin arrows, not a heat map):

| Claim \(\tau\) | Provenance \(c\) |
|---|---|
| algebraic equivalence | `DIRECT_EXACT` |
| algebraic equivalence | `SUBSTITUTION_EXACT` |
| BZ IBP | `RULE_CERTIFICATE` |
| asymptotic remainder | `UNKNOWN` |
| definition | `STRUCTURAL` |

- Side callout: engine adjudication `{ZERO, NONZERO, UNKNOWN}` is a third
  strip, **not** a certificate class. `CERTIFIED_BY_RULE` is never engine ZERO.
- Equal visual weight on the five provenance cards. No gold/silver/bronze.

### 4. Labelling

- Axis titles exactly: "Claim semantics \(\tau\)" and "Certificate provenance \(c\)".
- Dual encoding: colour + shape (same shapes as draft-v2 figures).
- Font ≥ 9 pt. ColorBrewer Set2.

### 5. Tool

- Primary: draw.io. Alternative: PowerPoint. Export SVG/PDF.

### 6. Caption

> Figure 2. Claim semantics and certificate provenance are different axes.
> `ALGEBRAIC_EQUIVALENCE` is a type of scientific move; `DIRECT_EXACT` is a
> kind of support. `BZ_PERIODIC_INTEGRATION_BY_PARTS` is a claim type;
> `RULE_CERTIFICATE` is provenance. The five provenance cards are not a
> ranking of mathematical truth. Engine `ZERO` is never `CERTIFIED_BY_RULE`.

### 7. Integrity

- No ranking pyramid: pass (explicitly forbidden).
- Vector/fonts/colour: user-verify after drawing.
