# Methods paper workspace

Writing and analysis only. This directory must not modify Derivation Audit
product semantics.

| Field | Value |
|---|---|
| Working title | Verified Symbolic Reasoning for Theoretical Physics through Typed Evidence Graphs |
| Subtitle | From stepwise derivation to manuscript audit |
| Paper type | Technique with cross-domain framing |
| Forbidden titles | Autonomous Theoretical Physicist; AI Discovers Physics; AI Proves Physics; Universal Symbolic Reasoner |
| Product tag | `derivation-audit-v0.2.1-alpha` (peels `783ec64`) |
| Evidence branch | `engineering/real-paper-validation-arxiv-2511-16422` (`69ad474`) |
| Current draft | `manuscript/draft-v2.md` |
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

## Headline (remember this, not 19 ZEROs)

The same evidence system supports stepwise construction and manuscript
audit, and it preserves distinct epistemic statuses on a real derivation.

## Layout

```text
manuscript/draft-v2.md              current two-mode journal draft
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
