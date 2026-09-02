# VENUE_FREEZE_V1

Verdict: **VENUE_FROZEN**

Date (UTC): 2026-09-02  
Branch: `paper/derivation-audit-method`  
Software authority: `v0.3.0-alpha` @ `f1d225e`  
Parent: `PAPER_AUTHORITY_LOCK.md`, `CLAIM_EVIDENCE_MATRIX.md`  
Related Work: `RELATED_WORK_BOUNDARY_FROZEN`  
Figures: `FIGURES_FROZEN`  
Human-facing audit: `HUMAN_AUDIT_HTML_FROZEN`

`draft-v3` was not edited. No experiments, product changes, or humanizer.

---

## Frozen choice

| | Venue | Article type |
|---|---|---|
| **PRIMARY** | Computer Physics Communications (Elsevier, ISSN 0010-4655) | **Computational Physics Paper (CP)** |
| **BACKUP** | Physical Review Research (APS) | **Regular Article** |

Not Letter. Not CPiP (Computer Programs in Physics). Not MLST.

---

## Why PRIMARY wins

Official CPC focus (access 2026-09-02): contemporary computational methods
and their implementation, **evidenced on a substantive problem in physics**.
CP themes explicitly include **algebraic computation**.

This manuscript is a computational method (typed, fail-closed evidence for
heterogeneous symbolic derivation steps) demonstrated on Guo et al.,
PRL 136, 206303 — a real published theoretical-physics derivation, not a
toy CAS identity. Software lives on GitHub, which CPC names as an
acceptable implementation location for CP papers.

CPiP is the wrong class: that track deposits a program in the CPC Library.
The contribution here is the **method plus physics demonstration**, not a
library deposit. A later CPiP/JOSS/SciPost Codebases companion remains
possible; it is not this paper.

CPC lets the full argument (semantics, Guo, sampled breadth, limitations)
breathe. Reviewers are computational physicists who already read algebraic
and symbolic-method papers.

---

## CPC editorial-desk test (Principal Editor)

Simulated against title family, abstract skeleton, Fig. 1/2/4, Guo counts.

| Q | Answer from frozen evidence |
|---|---|
| A. What computational method is new? | Typed fail-closed evidence graph for Forward and Audit; heterogeneous physics statuses; printed-equation grounding. Conjunction, not “independent checking.” |
| B. Why does a computational physicist need it? | Long symbolic derivations; CAS/agents propose; proposal ≠ evidence; remainders and rules must not be collapsed into `simplify()`. |
| C. What substantive physics problem demonstrates it? | Guo et al. dissipation-shaped quantum geometry / nonlinear transport; 189/189 inventoried; 146 source-grounded relations. |
| D. Is implementation real and available? | Yes: `v0.3.0-alpha` @ `f1d225e`; no API key for core verify. |
| E. More than a SymPy wrapper? | Yes: promotion policy, τ vs c, `ZERO` ≠ `CERTIFIED_BY_RULE`, generated table, manuscript-native IDs. |
| F. Related to algebraic/computational physics? | Yes: CPC CP lists algebraic computation. |

**CPC_PRIMARY_JUSTIFIED.** Desk risk remains if the Introduction fails CPC’s
written bar (novelty + physics application in the opening). Draft-v4
constraints exist to prevent that.

---

## Why BACKUP loses narrowly

PRR Regular Article is in scope: methodological advances of interest to
physicists; no length limit; gold OA.

It loses narrowly because:

- Acceptance still requires a “significant contribution” generating
  interest for a general physics reader.
- Primary editorial risk: transfer with “better suited to a computational
  / software journal.”
- Five-paper evidence is **sampled** (41 edges), which a PRR referee may
  read as thin physics breadth.
- Software must remain supporting, not the story — harder at PRR than at
  CPC, where implementation is expected.

PRR is the correct backup if CPC desk-rejects as “not computational
enough” or if gold-OA mandate requires APS.

---

## Why MLST is not appropriate

Official MLST scope (IOP, access 2026-09-02): the article **must** either
advance ML-driven scientific applications or advance ML methods motivated
by science. Research papers are normally ≤ 8500 words.

This paper’s contribution is proposer-agnostic typed evidence.
Optional LLM proposers and research-time AI use are **not** an ML
advance. Fitting MLST would require rewriting the paper into an AI paper,
which the lock and novelty boundary forbid.

**WEAK_SCOPE_FIT.** Rejected as PRIMARY and as BACKUP.

---

## JOSS / SciPost Codebases

Companion **after** the methodology paper, not instead of it.

- **JOSS:** short software citation paper. Requires demonstrated research
  impact, feature-complete software, ≥6 months public open development
  (2026 scope). Suitable later for `symbolic-compactification` itself.
- **SciPost Physics Codebases:** physics codebase article + versioned
  release (ALF, ITensor, …). Suitable later as a code paper, not as the
  methods+Guo argument.

No companion is written in this campaign.

---

## Frozen manuscript positioning (CPC)

> A computational methodology for typed, fail-closed verification of
> symbolic derivations in theoretical physics.

Foreground: heterogeneous derivation moves; typed evidence; fail-closed
promotion; Guo as the physics demonstration; sampled cross-paper
portability.

Do not foreground: LLM performance; software engineering as the
contribution; formal-method novelty of independent checking; “AI for
physics.”

Title family: see `DRAFT_V4_CONSTRAINTS.md`.

---

## Prohibited reframings

If a venue required any of the following, the venue would be rejected
rather than the claims changed:

- 189 equations verified
- five full-paper audits
- approximation overlays as product
- AI as verification authority
- exhaustive “no prior work has”
- engine bump / `main` as scientific authority
- proving Guo’s physical conclusions

---

## Required submission declarations (CPC)

See `AI_DISCLOSURE_PLAN.md`. Elsevier generative-AI declaration before
references; research-process AI in Methods; software citation; code
availability via GitHub tag. AI is not an author.

---

## Exact scope sources

`VENUE_SOURCE_LEDGER.md` (access 2026-09-02).

---

## Completion gate

- [x] current official venue policies checked
- [x] CPC evaluated (CP paper, not CPiP)
- [x] PRR evaluated (Regular Article, not Letter)
- [x] MLST evaluated (WEAK_SCOPE_FIT)
- [x] JOSS/SciPost treated as companions
- [x] PRIMARY and BACKUP frozen
- [x] article types frozen
- [x] novelty boundary unchanged
- [x] no impact-factor-driven decision
- [x] positioning frozen
- [x] reviewer attacks anticipated
- [x] draft-v4 constraints written
- [x] draft-v3 unchanged
- [x] no new experiments
- [x] no product changes
- [x] no humanizer

---

## Next allowed task

Draft-v4 **under** `DRAFT_V4_CONSTRAINTS.md`, still obeying the authority
lock. Not humanizer until draft-v4 exists. Not five-paper HTML.
Not automatic writing of draft-v4 in this campaign.
