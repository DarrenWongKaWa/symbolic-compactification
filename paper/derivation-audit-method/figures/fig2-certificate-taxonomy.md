# Figure 2 — Solution overview: from typed claim to evidence object

**Type.** Solution overview (opens Section 3–4).
**Paradigm.** Pipeline (figure-designer Paradigm A) with the certificate vocabulary as the output, not a second paper.

**Caption (draft).** Two axes, not one taxonomy. Edge type \(\tau\) is claim semantics (what mathematical move is asserted). Certificate class \(c\) is provenance (what evidence supports it). `ALGEBRAIC_EQUIVALENCE` is not `DIRECT_EXACT`. The reviewer inspects (source, claim type, assumptions, obligation, certificate). Classes encode dependency, not confidence. The language-model proposal path has no certification authority.

## Layout

Canvas: wide, two rows.

### Top row — authority chain (left to right)

Boxes:

1. Manuscript / derivation
2. Typed claim \(\gamma=(e_{\mathrm{from}},e_{\mathrm{to}},\tau,\rho,A)\)
3. Source-grounded obligation
4. Deterministic verifier
5. Evidence record
6. Generated reviewer table

Solid arrows between 1–6.

A dashed box above 2 labelled LLM / researcher proposal, with a dashed arrow into 2 and a red prohibition mark into 6: no write path to TABLE_VERIFIED.

Annotation under 6: VERIFIED TABLE IS GENERATED, NOT AUTHORED.

### Bottom row — output vocabulary (not a ranking)

Five equal cards, not a pyramid:

| DIRECT_EXACT | SUBSTITUTION_EXACT | RULE_CERTIFICATE | STRUCTURAL | ASYMPTOTIC / UNKNOWN |
|---|---|---|---|---|
| \(R=0\) | \(R\) after a supplied identity | local ZERO + declared theorem | definition / split | remainder not rewritten |

Do not order them as more-to-less true.

## Tool

draw.io or PowerPoint. Names in the figure must match subsection titles in Sections 2–4.

## Universal rule audit

- Self-contained caption: first sentence states the finding (proposal cannot certify)
- Colour-blind: same shape language as Figure 1
- No pyramid / funnel metaphor for certificate classes
