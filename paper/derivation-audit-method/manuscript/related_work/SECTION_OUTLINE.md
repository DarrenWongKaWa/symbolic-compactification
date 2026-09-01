# Related Work section outline (not polished prose)

For `draft-v4` §Related Work. Do not paste into `draft-v3`.
Novelty language: `NOVELTY_BOUNDARY.md`. Citations: `CITATION_LEDGER.md`.

Recommended six-paragraph spine. Each paragraph names the prior-art principle first, then the object-level distinction.

---

### Paragraph 1 — Checked / certified computation

**Job.** Establish producer/checker separation as **prior art**, not as the contribution.

**Sources.** Necula 1997; Blum & Kannan 1995; Gottliebsen et al. 2005; Kaufmann & Biere 2023.

**Points.**

- Untrusted code or a CAS session can be required to supply a checkable certificate (PCC; hidden PVS behind Maple; Nullstellensatz/PAC for multipliers).
- Independent checking of an untrusted computation is therefore not new.
- Those certificates attach to *programs*, *CAS analysis VCs*, or *circuits*.

**Bridge.** The present object is a derivation edge in a theoretical-physics calculation or manuscript, not a safety policy or a circuit identity.

**Insertion note (draft-v3 §8 first paragraph).** Current draft already cites PCC, hidden verification, and AMulet. Keep that acknowledgment; delete any tone that “those lines of work do not stop a notebook from conflating proposal with authority” if it reads as “previous methods cannot.” Prefer: they certify a different artifact.

---

### Paragraph 2 — Proof assistants / formal methods

**Job.** Stronger formal guarantees; different formalization target.

**Sources.** de Moura & Ullrich 2021; Bertot & Castéran 2004; Nipkow et al. 2002; Tooby-Smith 2025.

**Points.**

- Lean/Coq/Isabelle check proof terms in a kernel. Tactics do not certify themselves.
- That is a *stronger* guarantee than a local residual `ZERO`, once a claim is encoded.
- HepLean shows HEP definitions and theorems *can* be digitalised in Lean, and lists paper review as a potential benefit *after* encoding.
- Do not say proof assistants cannot do physics.
- Do not say this framework is more rigorous than a kernel.

**Bridge.** Ordinary PRL/PRD derivations mix algebra, substitution, IBP, remainders, and definitions. This work types those moves in the manuscript as written, and allows `UNKNOWN` / structural / rule-mediated statuses to remain explicit rather than requiring a complete formalization first.

---

### Paragraph 3 — CAS and symbolic rewriting

**Job.** Expression transformation vs epistemic derivation-state control.

**Sources.** Meurer et al. 2017; Peeters 2007; MacCallum 2018 (survey, orientation); Willsey et al. 2021.

**Points.**

- Theoretical physics already uses CAS (MacCallum; Cadabra’s TeX-like scratch pad; SymPy in Python).
- Equality saturation searches many equivalent forms.
- `simplify` answers whether A can be rewritten toward B.

**Bridge.** A successful rewrite is not, by itself, permission to promote a scientific derivation state, nor a record of whether the move was exact, substitution-conditioned, theorem-mediated, or an uncertified remainder.

---

### Paragraph 4 — Scientific provenance / workflows / notebooks

**Job.** Lineage vs mathematical evidence semantics.

**Sources.** Moreau et al. 2008; Wilkinson et al. 2016; Kluyver et al. 2016; Koop 2021.

**Points.**

- Provenance graphs record where a result or process came from (fMRI challenge workflow; FAIR findability).
- Notebooks store code, results, and explanation; they often omit full process provenance.

**Bridge.** Lineage does not encode \(\tau\) (what move is claimed) or \(c\) (what evidence authorizes it), and does not gate promotion of a current expression.

---

### Paragraph 5 — LLM / agent reasoning

**Job.** Proposal/checking patterns already exist; this framework is proposer-agnostic.

**Sources.** Polu & Sutskever 2020; Yang et al. 2023; Trinh et al. 2024; Song et al. 2024.

**Points.**

- GPT-f, LeanDojo, AlphaGeometry, and Lean Copilot already instantiate “a model may propose; a checker decides.”
- Lean Copilot states that Lean leaves “no room for hallucination” *inside the assistant*.
- Acknowledge this split as inherited.

**Bridge.** Those checkers judge *formal theorems or geometry proofs*. Here the same split is applied to ordinary physics manuscripts, the proposer may be a human, a CAS, or a model, and there is no shipped `propose` command. Core verification needs no API key.

---

### Final paragraph — Conjunction

**Job.** Exact combination claimed, with cautious wording.

**Allowed closing (style-editable, strength-frozen):**

> We are not aware of prior work that jointly treats constructive
> derivation and retrospective manuscript audit as operations on one
> typed evidence graph over source-grounded theoretical-physics steps,
> with fail-closed scientific-state promotion and a generated
> equation-indexed reviewer table. Prior work separately addresses
> producer/checker separation, formal proof, CAS simplification, and
> workflow provenance. The distinction lies in the object, not in the
> existence of an independent checker.

**Do not close with** “first framework” or “no previous method.”

Optional one-sentence named-project hedge (no fake citation):

> A public software project, the Physics Derivation Graph, also links
> physics expressions by inference rules; we found no archival
> publication with stable bibliographic metadata in this pass and
> therefore do not treat it as a primary source.
