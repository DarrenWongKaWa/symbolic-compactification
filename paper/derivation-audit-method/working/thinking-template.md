# Thinking template (Supervisor-Skills / tech-paper-template)

Internal planning file. Not part of the manuscript.

## 1. Paper-type positioning

- Type: New Problem/Setting Paper (with a realizing method)
- Rationale: The load-bearing contribution is a new scientific object — a machine-auditable epistemic type for theoretical-physics derivation steps — not a faster CAS or a stronger theorem prover on an existing leaderboard.

## 2. Thinking template

| Stage | Content |
|---|---|
| Research background | Theoretical derivations now mix handwriting, CAS, AI proposal, substitutions, global theorems, and asymptotics. Reviewers still receive a narrative in which neighbouring equations look like equalities. |
| Limitation 1 | Computer-algebra notebooks evaluate expressions but collapse heterogeneous scientific steps into pass/fail, erasing epistemic type. |
| Limitation 2 | Proof assistants certify fully formal theorems in a trusted kernel; that is a different object from auditing the manuscript physicists actually write. |
| Limitation 3 | LLM/AI-for-science systems generate derivations and often score themselves; proposal and authority are fused. |
| Key Idea / Our Goal | Record each scientific step as a typed, provenance-bearing evidence object, so AI/CAS may propose freely while certification remains attached to generated, source-grounded evidence. Headline: Derivation Audit turns a derivation into a typed evidence graph. |
| Challenge 1 | Heterogeneous steps (definition, algebra, symmetry, IBP, remainder) cannot be encoded as lhs−rhs without fake ZERO or empty UNKNOWN. |
| Challenge 2 | Exact, substitution, theorem-mediated, and asymptotic claims cannot share one PASS/FAIL bit. Certificate class must encode dependency, not confidence. |
| Challenge 3 | Narrative and model output can capture the verified table unless inclusion is generated from integrity-bound records. |
| Methodology topic sentence | Derivation Audit is a fail-closed audit layer that compiles a manuscript into a typed evidence graph and emits generated certificates. |
| Module A (C1) | Typed derivation graph \(\gamma=(e_{\mathrm{from}},e_{\mathrm{to}},\tau,\rho,A)\). Equation proximity \(\neq\) equality. |
| Module B (C2) | Certificate provenance: DIRECT_EXACT, SUBSTITUTION_EXACT, RULE_CERTIFICATE, STRUCTURAL, ASYMPTOTIC/UNKNOWN. ZERO \(\neq\) CERTIFIED_BY_RULE. |
| Module C (C3) | Authority separation: generated-not-authored tables; fail-closed UNKNOWN; hashes bind source/claim/assumptions/obligation. |
| Contribution 1 | Problem formulation: loss of epistemic type; derivation as typed evidence graph (Section 2). |
| Contribution 2 | Certificate provenance semantics, not a ranking of truth (Section 3). |
| Contribution 3 | Authority separation: an AI may propose, it may not notarize itself (Sections 4–5). |
| Contribution 4 | Evaluation as RQ1–RQ3, including a public PRL field validation that preserves types rather than maximising green rows (Section 6). |

## 3. Self-consistency checks

- Check 1 Limitations -> Key Idea: pass (all three limitations are forms of missing audit/epistemic type)
- Check 2 Key Idea -> Challenges: pass (challenges arise from implementing typed evidence, mixed certificates, and generated authority)
- Check 3 Challenges -> Methodology: pass (A/B/C one-to-one)
- Check 4 Methodology -> Contributions: pass

## 4. Severity summary

0 CRITICAL, 0 MAJOR, 0 MINOR.

## 5. Next skill

`intro-drafter` then `paper-writer`.
