# Figure 1 — Motivated example: loss of epistemic type

**Type.** Motivated example (page 1).
**Paradigm.** Existing vs Ours (figure-designer Paradigm B).
**Rejected.** Performance teaser (the paper’s value is not a single accuracy bar). Pipeline-only (that is Figure 2).

**Caption (draft).** Neighbouring displayed equations are not the same kind of claim. Left: an untyped workflow treats every printed arrow as an equality and stamps verified, mixing algebra, substitution, Brillouin-zone integration by parts, and an asymptotic remainder. Right: Derivation Audit records the same public fragment from Guo et al. as a typed evidence graph. Equation proximity is not an equality claim.

## Layout

Canvas: landscape, two columns, ~180 mm wide.

### Left column — Existing (untyped)

Title inside panel: Untyped equation list.

Vertical list:

```text
(D-57) Γ expansion
   ↓  "verified"
(D-59)→(D-60) regroup
   ↓  "verified"
(D-66)→(D-67)
   ↓  "verified"
(D-114)→(D-119) IBP
   ↓  "verified"
```

Red stamp overlay: VERIFIED on every arrow.
Annotation: epistemic type lost.

### Right column — Ours (typed graph)

Title inside panel: Typed evidence graph.

```text
(D-57)  ASYMPTOTIC / UNKNOWN
(D-59)→(D-60)  DIRECT_EXACT  (engine ZERO)
(D-66)→(D-67)  SUBSTITUTION_EXACT  (ε21=−ε12 supplied)
(D-114)→(D-119)  RULE_CERTIFICATE
                 child: Leibniz ZERO
                 rule: BZ torus periodicity
```

No green wash on UNKNOWN or RULE. RULE node is not labelled ZERO.

Dashed box at bottom of right column: LLM/CAS may propose edges; they have no write path to VERIFIED.

## Colour and labels

- DIRECT: filled circle, ColorBrewer Dark2 blue
- SUBSTITUTION: square, orange
- RULE: diamond, purple
- UNKNOWN: open triangle, grey
- False VERIFIED stamp on the left: red, not used on the right

Font after scaling: ≥8 pt. Vector export (PDF/SVG).

## Tool

Primary: PowerPoint or draw.io. Alternative: Figma. Not Matplotlib.

## Universal rule audit

- Vector: planned
- Font size: user must verify after draw
- Colour-blind safe: shape plus colour
- Self-contained caption: yes
- Honest axes: n/a
- No chartjunk: no 3D, no decorative icons
