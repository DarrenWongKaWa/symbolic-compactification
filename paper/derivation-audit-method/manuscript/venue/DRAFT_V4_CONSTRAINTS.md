# Draft-v4 constraints (PRIMARY = CPC, Computational Physics Paper)

Do **not** write draft-v4 in this campaign.
Parent: `PAPER_AUTHORITY_LOCK.md`, `CLAIM_EVIDENCE_MATRIX.md`, `VENUE_FREEZE.md`.

Venue adaptation must never change ZERO semantics, 189/189 inventory meaning,
sampled vs full-paper, Forward caveats, Related Work novelty boundary,
approximation status, or software authority.

---

## Title direction (family, not final wording)

Preferred family for CPC:

1. Typed Evidence Graphs for Verifiable Symbolic Derivations in Theoretical Physics
2. Fail-Closed Verification of Symbolic Derivations in Theoretical Physics
3. Verified Symbolic Reasoning for Theoretical Physics through Typed Evidence Graphs

Do not use: AI scientist; autonomous physicist; proof of physics papers;
verified paper correctness.

Subtitle may retain “From stepwise derivation to manuscript audit.”

---

## Abstract emphasis

Follow `ABSTRACT_POSITIONING.md`. Lead with the computational method and
Guo as the substantive physics demonstration. LLMs appear only as optional
untrusted proposers. No 189-verified; no five-paper full audits.

---

## Introduction framing (first two paragraphs)

Paragraph 1 — physics practice, not software:

Theoretical physicists manipulate long symbolic derivations. CAS and
optional agents can propose a next expression. Proposal is not evidence.

Paragraph 2 — computational method CPC can name:

A typed, fail-closed evidence graph records heterogeneous moves
(algebra, substitution, rule, limit, remainder, definition) and promotes
scientific state only on deterministic evidence. Effectiveness is shown
on a published nonlinear-transport derivation (Guo et al.).

Do not open with GitHub, packaging, or “AI for physics.”

The Introduction must satisfy CPC’s desk bar: novelty, significance, and
how the method advances an important physics application (manuscript-scale
symbolic derivation under heterogeneous evidence).

---

## Methods emphasis

1. Typed graph γ; Forward and Audit as two uses of one object.
2. τ vs c; `ZERO` ≠ `CERTIFIED_BY_RULE`; `UNKNOWN` never promotes.
3. Promotion/refusal rule (fail-closed).
4. Source-grounded printed-equation identity; adjacency is not a derivation.
5. Implementation pointer: `v0.3.0-alpha` @ `f1d225e`; no API key for core
   verify. Performance details only as needed for CPC CP (“normally include
   software implementation and performance details”) — not a software paper.

---

## Results ordering

1. **Guo flagship** (CPC “substantive problem in physics”).
2. Forward public demos + replay caveats.
3. Five-paper **sampled** stress (41 edges), explicitly not five full audits.
4. Limitations in the same breath as counts where required (L18, L19, L21).

Do not lead Results with packaging or proposer leaderboards.

---

## Figure order (FIGURES_FROZEN)

Keep the frozen four; CPC-facing narrative order:

1. Fig. 1 — two workflows, one graph
2. Fig. 2 — τ versus c; `ZERO` ≠ `CERTIFIED_BY_RULE`
3. Fig. 4 — Guo flagship (inventory ≠ verified; D-59, D-66, D-114, D-57)
4. Fig. 3 — Forward fail-closed (0/36; not a leaderboard)

Fig. 4 is the physics-demonstration figure for CPC. Do not hide it.

---

## Related Work placement

After the method is stated, before or immediately after the first results
block — not as an appendix. Use frozen `related_work/`. Conjunction
novelty only. “We are not aware of prior work that jointly …”.

---

## Software / reproducibility placement

A short subsection or end-matter box:

- tag `v0.3.0-alpha` @ `f1d225e`
- GitHub URL
- Guo `RESULTS.md` / `RELATIONS_FROZEN.yaml`
- human-facing HTML is a **projection**, not authority
- core verify: no API key

Do not submit as Computer Programs in Physics (CPiP) unless a later
companion deposits the program in the CPC Library. This manuscript is a
**Computational Physics Paper**.

---

## Limitations (must remain visible)

- Inventory is not algebra (L22).
- Guo is formative (L18).
- Five-paper work is sampled (L19).
- Coefficient `ZERO` ≠ remainder certificate (L21).
- One named global rule (L23).
- Approximation overlays: Discussion only (L25).
- Does not prove the paper or physical conclusions (L20).

---

## Required declarations (CPC)

- Elsevier generative-AI declaration before references (see
  `AI_DISCLOSURE_PLAN.md`). Research-process AI in Methods.
- Data/code availability: GitHub + tag. Prefer also a Zenodo snapshot of
  the tag at submission (not created in this campaign).
- Software citation of `symbolic-compactification` as software, not only
  as this article.

Do not list an AI system as an author.

---

## Supplementary-material strategy

CPC CP: software on GitHub is the intended location.
Optional supplement:

- frozen Guo `RESULTS.md` excerpt / human-audit HTML pointer
- Forward demo transcripts

The paper must stand without the supplement. Human-audit HTML is
presentation, not a new certificate.

---

## What draft-v4 must not do

- Rewrite the paper as an ML/AI contribution to fit MLST.
- Compress into a Letter.
- Strengthen novelty past `NOVELTY_BOUNDARY.md`.
- Cite `main` for scientific counts.
- Humanize before venue constraints are applied to a new draft.
