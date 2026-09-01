# Methods paper workspace

Writing and analysis only. This directory must not modify Derivation Audit
product semantics.

| Field | Value |
|---|---|
| Working title | Machine-Auditable Theoretical Derivations through Typed Evidence Graphs |
| Subtitle | A fail-closed audit layer for AI-assisted symbolic science |
| Forbidden titles | Autonomous Theoretical Physicist; AI Discovers Physics |
| Product tag | `derivation-audit-v0.2.1-alpha` (`783ec64`) |
| Evidence branch | `engineering/real-paper-validation-arxiv-2511-16422` (`69ad474`) |
| Current draft | `manuscript/draft-v2.md` |
| Prior drafts | `draft-v1.md`, `draft-v0.md` |
| Engineering | CLOSED |

## One-sentence story

Modern theoretical derivations mix human reasoning, AI proposals, CAS
manipulations, substitutions, symmetry arguments, global theorems, and
asymptotics. The missing object is an audit layer that records exactly
what was claimed, what was actually checked, under which assumptions,
and with what machine evidence.

Derivation Audit turns a derivation into a typed, provenance-bearing
evidence graph.

## Headline (remember this, not 19 ZEROs)

The system preserved different epistemic statuses on a real derivation.

An AI may propose a derivation; it may not certify itself.

## Layout

```text
manuscript/draft-v2.md    current journal draft (read this)
manuscript/draft-v1.md    five-act rewrite before accounting/RW fixes
manuscript/draft-v0.md    earlier complete draft
working/                  Supervisor-Skills skeleton, evidence map
figures/                  Figure 1–4 specifications
tables/                   Table 1–4 plans
```

## Evaluation as three questions

- RQ1. Can the tested narrative/record attacks populate the verified table? Under the implemented threat model, no.
- RQ2. Can heterogeneous steps retain type? Synthetic demos.
- RQ3. Formative field validation: can the architecture represent a published derivation without false certificates? Not a held-out generalisation test.

Guo is a stress test of the epistemic architecture, not the story subject.
189 numbered equations → 25 selected paper steps; 18 paper-level ZERO plus one Leibniz helper.
