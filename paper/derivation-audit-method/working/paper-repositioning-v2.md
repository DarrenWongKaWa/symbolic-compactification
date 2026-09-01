# Paper repositioning v2 (tech-paper-template)

Skill: `tech-paper-template` (HKUSTDial/Supervisor-Skills).
Source freeze: product tag `derivation-audit-v0.2.1-alpha` peels `783ec64`;
evidence `69ad474`; Mode A docs on the same product tree.
Engineering is CLOSED. This file is a logical skeleton, not manuscript prose.

The previous paper lock (`working/thinking-template.md`) positioned an
audit-only New Problem/Setting. That lock is superseded here.

---

## 1. Paper-type positioning

- Type: **Technique Paper with cross-domain framing**
- Rationale: The community already studies trustworthy symbolic computation
  (CAS, proof assistants, proof-carrying code, certified computer algebra,
  workflow provenance). The load-bearing contribution is now a unified
  method: one typed evidence graph with an untrusted proposal layer and an
  independent fail-closed authority layer, executed in two directions.
  Experiments characterise that method (gating, integrity, formative
  field validation) rather than beating a shared leaderboard.

Mixed-case note (skill rule: pick the contribution the paper delivers best).
A New Problem/Setting reading remains available: manuscript-native typing of
heterogeneous physics arrows is under-studied. After the two-mode reframing,
the paper delivers a working framework more strongly than it delivers a
newly named problem. Technique therefore carries Paragraph 3; the setting
appears as contribution language, not as the narrative spine.

Not a benchmark paper. `benchmark-paper-template` is not used.
`idea-evaluator` is not used: the system is implemented and frozen.

---

## 2. Thinking template

| Stage | Content |
|---|---|
| Research background | A theoretical physicist does two recurrent symbolic jobs: construct the next transformation of a long expression given papers, notes, and assumptions; and, later, decide which printed steps in a manuscript are actually supported. Those jobs already mix human algebra, CAS, notebooks, and experimental AI proposal. |
| Limitation 1 | Candidate generation and certification are often the same act: a CAS session, a notebook cell, or a model trace that writes "verified" is treated as evidence. |
| Limitation 2 | Heterogeneous scientific operations (algebra, substitution, definition, global theorem, asymptotic remainder) are collapsed into a generic equality or pass/fail bit. |
| Limitation 3 | Constructive derivation and retrospective manuscript checking lack a shared evidence representation, so a step that was gated while working cannot be the same object a reviewer later inspects. |
| Key Idea / Our Goal | Represent both workflows as operations on one typed evidence graph whose proposal layer is untrusted and whose authority layer is independent and fail-closed. |
| Challenge 1 | Record a candidate scientific transformation without granting the proposer (human, rule, or model) the power to promote scientific state. |
| Challenge 2 | Compile heterogeneous transformations into honest typed obligations: a residual where a residual is the claim, a rule certificate where a theorem is the claim, and UNKNOWN/NOT_LOWERED where the engine cannot speak. |
| Challenge 3 | Support iterative state advancement and parallel manuscript audit with the same edge semantics, the same status tokens, and the same inclusion functions. |
| Methodology topic sentence | A typed evidence graph with an untrusted proposal layer and a fail-closed verifier is the shared object of both execution modes. |
| Module A (Challenge 1) | Proposal gate: ground, compile, verify; promote or enter `TABLE_VERIFIED` only on integrity-bound engine ZERO. |
| Module B (Challenge 2) | Two-axis typing: claim semantics \(\tau\) versus certificate provenance \(c\); engine ZERO is never `CERTIFIED_BY_RULE`. |
| Module C (Challenge 3) | Dual execution: Forward Mode constructs an evidence-backed path; Retrospective Audit inspects an existing path in parallel. |
| Contribution 1 | Unified formulation: constructive derivation and retrospective audit are operations on one typed evidence graph (Sections 2–3). |
| Contribution 2 | Typed fail-closed evidence semantics: claim type, certificate provenance, engine adjudication, theorem-mediated certificate, structural record, and unsupported/unknown claim are distinct; `ZERO ≠ CERTIFIED_BY_RULE` (Section 3). |
| Contribution 3 | Verification-gated iterative derivation: candidates may come from humans, rules, or an experimental AI proposer; state advancement requires independent evidence. Public evidence is a supported verification path plus an experimental proposal surface, not autonomous discovery (Section 4, RQ1). |
| Contribution 4 | Parallel manuscript audit: existing paths are typed edge-by-edge; reviewer tables are generated; public Guo field validation is formative, not held-out (Sections 5 and 7, RQ3). |

Goal (Technique bridge, not a contribution): handle both scientific jobs under one evidence contract.

---

## 3. Self-consistency checks

- Check 1 Limitations -> Key Idea: **pass**. L1 is answered by the untrusted proposal / independent authority split. L2 is answered by two-axis typing. L3 is answered by one graph, two directions.
- Check 2 Key Idea -> Challenges: **pass**. The three challenges are what a naive "add a verifier to a CAS" implementation of the Key Idea would miss: promotion authority, honest obligation compilation, and shared semantics across workflows.
- Check 3 Challenges -> Methodology: **pass**. Module A/B/C map one-to-one onto Challenges 1/2/3.
- Check 4 Methodology -> Contributions: **pass**. C1 names the shared object; C2 names Module B; C3 names Module A in Forward Mode; C4 names Module C in Audit Mode plus the public field case. No contribution is "extensive experiments."

---

## 4. Integrity gate

1. Paper-type consistent with the actual contribution: **pass** (Technique, not shoehorned New Problem).
2. Limitations specific and citable: **pass** (CAS/notebooks; collapsed type; missing shared object; adjacent PCC/CAS/provenance cited in Related Work).
3. Key Idea is one quotable sentence: **pass**.
4. Challenges derived from implementing the Key Idea: **pass**.
5. Modules one-to-one with challenges: **pass**.
6. Contributions map to modules and sections: **pass**.
7. Four self-consistency checks pass: **pass**.

Skeleton status: ready for `intro-drafter`.

---

## 5. Methodology outline (for Sections 2–6)

Topic sentence: both workflows operate on edges
\(\gamma=(e_{\mathrm{from}},e_{\mathrm{to}},\tau,\rho,A)\).

Section 2. Problem formulation: one evidence graph, two workflows.

Section 3. Typed evidence graph.
- 3.1 Claim semantics \(\tau\) (frozen edge catalogue).
- 3.2 Certificate provenance \(c\) (`DIRECT_EXACT`, `SUBSTITUTION_EXACT`, `RULE_CERTIFICATE`, structural, unknown).
- 3.3 Fail-closed status semantics (engine triad; inclusion functions in `schema.py`).

Section 4. Forward symbolic derivation (Module A + C-forward).
- 4.1 Context and candidate generation (human / rule / experimental AI).
- 4.2 Candidate grounding and obligation compilation.
- 4.3 Verification-gated state advancement (`ZERO` promote; `NONZERO`/`UNKNOWN` retain).
- 4.4 Capability boundary of the proposer (experimental; representation invention unestablished).

Section 5. Retrospective manuscript audit (Module C-audit).
- 5.1 Equation inventory (labels, not algebra).
- 5.2 Parallel edge verification.
- 5.3 Rule certificates and structural steps.
- 5.4 Generated reviewer evidence.

Section 6. Authority, integrity, implementation (cross-cutting Module A/B).

Section 7. Evaluation: RQ1 gating, RQ2 threat-model integrity, RQ3 formative Guo audit.

---

## 6. Title lock

Primary: Verified Symbolic Reasoning for Theoretical Physics through Typed Evidence Graphs

Subtitle: From stepwise derivation to manuscript audit

Forbidden: Autonomous Theoretical Physicist; AI Discovers Physics; AI Proves Physics; Universal Symbolic Reasoner.

Working story: Theoretical physics has two complementary symbolic workflows,
constructing a derivation and auditing an existing one. We represent both as
operations on the same typed evidence graph, where candidate transformations
may be proposed freely but may advance a derivation, or enter a reviewer-facing
verified table, only through explicit fail-closed evidence.

Authority statement (not a substitute for technical explanation):
An AI may propose a derivation; it may not certify itself.

---

## 7. Severity summary

- 0 CRITICAL, 0 MAJOR, 0 MINOR.
- Next skill: `intro-drafter`.

---

## 8. Evidence posture for RQ1 (frozen; do not upgrade)

Forward Mode is an **implemented workflow / supported verification path plus
experimental proposal surface**, not demonstrated autonomous discovery.

Public Mode A demos are one-shot researcher-supplied hypotheses
(`demo_a_zero` ZERO; `demo_b_grounded_newton_dd` ZERO, not discovery;
`demo_c_unknown` UNKNOWN, no promotion). External replay records a mutated
candidate `(x+1)^2+1` as NONZERO with residual `-1`. Multi-candidate promotion
is shown by session tests with a **scripted** proposer
(`tests/test_proposer_protocol.py` CASE B), not a live model and not a
committed multi-step demo workspace. No `propose` CLI is shipped.
Representation-invention campaigns remain closed.

---

## 9. Guo accounting lock (RQ3) — superseded by SOFTWARE_AUTHORITY.md

Canonical counts are the v0.3.0-alpha flagship table (189/189 inventory,
146 relations). The 25/26 selected-edge arithmetic below is lineage only.

Do not mix 189 inventoried equations with 32 `EXACT_ZERO` rows.
Headline is type preservation on a complete inventory, not "189 passed."
