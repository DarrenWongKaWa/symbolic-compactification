# Methods paper workspace

Writing and analysis only. This directory must not modify Derivation Audit
product semantics.

| Field | Value |
|---|---|
| Working title | Verified Symbolic Reasoning for Theoretical Physics through Typed Evidence Graphs |
| Subtitle | From stepwise derivation to manuscript audit |
| Paper type | Technique with cross-domain framing |
| Forbidden titles | Autonomous Theoretical Physicist; AI Discovers Physics; AI Proves Physics; Universal Symbolic Reasoner |
| Product tag | `v0.3.0-alpha` (peels `f1d225e`) |
| Evidence | archive tags in `SOFTWARE_AUTHORITY.md` |
| Current draft | `manuscript/draft-v3.md` |
| Prior drafts | `draft-v2-audit-only.md`, `draft-v1.md`, `draft-v0.md` |
| Engineering | CLOSED |

## One-sentence story

Theoretical physics has two complementary symbolic workflows: constructing a
derivation and auditing an existing one. We represent both as operations on
the same typed evidence graph, where candidate transformations may be
proposed freely but may advance a derivation, or enter a reviewer-facing
verified table, only through explicit fail-closed evidence.

Shorter: one evidence graph, two directions.

An AI may propose a derivation; it may not certify itself.

## Headline (remember this, not a pass rate)

The same evidence system supports stepwise construction and manuscript
audit. Guo flagship is a 189/189 inventory with typed statuses, not
"189 equations proved."

## Layout

```text
SOFTWARE_AUTHORITY.md              v0.3.0-alpha freeze lock
manuscript/draft-v3.md              current draft (authority realignment)
manuscript/draft-v2.md              pre-v0.3 two-mode draft (preserved)
manuscript/draft-v2-humanized.md    after humanizer
manuscript/draft-v2-prehumanizer.md before humanizer
manuscript/draft-v2-audit-only.md   previous audit-only v2 (preserved)
manuscript/draft-v1.md              five-act audit-only rewrite
manuscript/draft-v0.md              earlier complete draft
working/paper-repositioning-v2.md   tech-paper-template
working/related-work-audit-v2.md
working/venue-v2.md
working/pre-submission-checklist-v2.md
working/future-product-gaps.md      record only; do not implement
figures/                            vector specs (not drawn yet)
tables/
```
