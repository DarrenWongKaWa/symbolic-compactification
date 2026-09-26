# Venue reassessment v2

Previous `working/venue.md` treated an audit-only methods paper. After the
two-mode repositioning the object is a **verified symbolic-reasoning
framework for theoretical physics** (computational-physics methods), not a
security paper and not a Nature results letter.

Do not distort the paper to fit a venue. Do not submit.

---

## Primary recommendation

**Computer Physics Communications**

Why it fits the two-mode paper:
- Audience already uses CAS (FORM, Cadabra, Maple, Mathematica, SymPy) on
  long theoretical calculations.
- CPC publishes methods, software, and verification infrastructure, not only
  new physics results.
- Forward Mode (gating a candidate transformation) and Retrospective Audit
  (typed manuscript evidence) are both computational-physics workflows.
- Traditional IMRAD is compatible with Sections 3–7.
- Program summary / software description can point at the public GitHub
  tag `derivation-audit-v0.2.1-alpha` without claiming v1.0.

What CPC would require (framing, not new science):
- A short program-summary block (title, authors, licence, URL, engine).
- Vector figures.
- Reproducibility of Mode A demos and of the Guo reviewer package.
- Restrained software-paper tone: this is not "we verified Guo."

---

## Second choice

**SciPost Physics Codebases**

Why: codebases for physics software with explicit capability boundaries.
The frozen alpha, Mode A + derivation-audit dual surface, and fail-closed
semantics are a good match.

Cost: more software-artefact and less methods-story; the two-mode scientific
argument would need to stay in the narrative, not collapse into a README.

**Alternative second: Machine Learning: Science and Technology**

Why: AI-for-science readers care about proposal ≠ authority.
Cost: they will ask for a model experiment. The public evidence does **not**
support a proposer-quality benchmark. Do not move the paper here unless the
author accepts that RQ1 stays a gating result.

---

## Weaker / higher-friction

| Venue | Issue |
|---|---|
| Physical Review Research | Would pull Guo into the foreground as physics; the paper is not a PRL comment and must not claim the physics is confirmed. |
| Nature Computational Science / Nature Machine Intelligence | Letter length; would demand a punchier AI result than the frozen evidence allows. |
| SciPost Physics (not Codebases) | Physics-result venue; Guo-as-illustration is easy to misread. |

---

## Framing that must not change with venue

- Technique paper, two execution modes, one graph.
- Guo is formative field validation of Audit Mode.
- Forward Mode is a supported verification path plus experimental proposal
  surface, not autonomous discovery.
- `ZERO ≠ CERTIFIED_BY_RULE`.
- No "we verified 19 equations."
- No "SymPy wrapper that checks AI."

Author decides. Nothing is submitted in this pass.
