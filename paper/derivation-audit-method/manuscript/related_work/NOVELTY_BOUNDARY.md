# Novelty boundary — RELATED_WORK_REAUDIT_V1

Parent: `PAPER_AUTHORITY_LOCK.md`, `CLAIM_EVIDENCE_MATRIX.md`.
Evidence table: `RELATED_WORK_EVIDENCE.md`.

Candidate conjunction under test:

> A shared typed evidence graph for both constructive derivation and
> retrospective manuscript audit, in which heterogeneous
> theoretical-physics symbolic claims are source-grounded and may enter
> scientific state only through explicit fail-closed evidence.

---

## 1. Definitely not novel

| Principle | Where it already lives |
|---|---|
| Untrusted producer + independent checker | Necula 1997 PCC; Blum & Kannan 1995 program checking |
| Certificates for a computation distinct from the producer | Kaufmann & Biere 2023 Nullstellensatz/PAC; PCC safety proofs |
| Hiding a theorem prover behind a CAS | Gottliebsen, Kelsey & Martin 2005; Adams et al. Maple+PVS 2001 (related, not in the core 21) |
| Proof kernels that reject invalid terms | Lean 4; Coq; Isabelle/HOL |
| LLM proposes, formal/symbolic engine checks | GPT-f; LeanDojo; AlphaGeometry; Lean Copilot |
| Symbolic simplification / rewrite search | SymPy; Cadabra; egg equality saturation |
| Process/data lineage graphs | First Provenance Challenge; notebook provenance |
| Physics content *can* be formalized in a proof assistant | HepLean |
| Markup of mathematical documents | OMDoc |

Do not claim novelty for any row above.

---

## 2. Inherited / adapted

- Producer/checker split (PCC, program checking, hidden verification).
- Exact symbolic engine as a *route* (SymPy), not as the scientific object.
- Fail-closed rejection of invalid certificates (kernels, checkers).
- Optional model proposers that cannot self-certify (Lean copilots, GPT-f).
- Document-level concern for ordinary mathematical text (OMDoc; Jupyter as a working document).

---

## 3. Component-wise moat test

| Component | Status | Why |
|---|---|---|
| A. Shared graph for forward + retrospective use | **NO CLOSE MATCH FOUND** | ITPs are constructive in a formal environment. Provenance graphs are retrospective lineage. OMDoc stores documents. None is one evidence graph with *both* promote/refuse on a working expression *and* equation-indexed audit of a printed path. PDG website claims a physics derivation graph but is not an archival primary source. |
| B. Heterogeneous claim semantics | **PARTIAL PRIOR ART** | CAS rewrite kinds; ITP tactics; PDG “inference rules”; OMDoc statement classes. None of the archival sources uses the physics-typed statuses `EXACT_ZERO` / `ZERO_UNDER_SUBSTITUTION` / `CERTIFIED_BY_RULE` / `UNKNOWN_REMAINDER` / `STRUCTURAL` / `UNSUPPORTED` as first-class, mutually exclusive scientific states. |
| C. Theoretical-physics manuscript-native grounding | **PARTIAL PRIOR ART** | Cadabra: TeX-like input. HepLean: HEP results *after* Lean encoding. OMDoc: textbook markup. None inventories printed equation numbers of an ordinary PRL/PRD paper and binds residuals to those numbers. |
| D. Claim type \(\tau\) vs certificate provenance \(c\) | **PARTIAL PRIOR ART** | PCC separates *code* from *safety proof*. AMulet separates *circuit* from *algebraic certificate*. Kernels separate *tactic* from *proof term*. The archival sources do not treat “algebraic equivalence” as a move type independent of “DIRECT_EXACT vs RULE_CERTIFICATE” on a manuscript edge. |
| E. Fail-closed scientific-state promotion | **PARTIAL PRIOR ART** | Checkers and kernels refuse bad certificates. Jupyter has no promotion gate. CAS `simplify` typically *is* the new state. `UNKNOWN` as a recorded, non-promotable scientific state on a working expression is not the object of the cited systems. |
| F. Reviewer-facing equation-indexed evidence | **NO CLOSE MATCH FOUND** | HepLean lists “easy review of papers” as a *potential benefit of digitalisation into Lean*. Provenance tables answer lineage queries. No archival system in this set emits a generated `RESULTS.md` keyed by printed Eq. (D-57), Eq. (D-59)→(D-60), … with fail-closed statuses. |

“NO CLOSE MATCH FOUND” is **not** “first ever”. It means: among the frozen primary set, no close match was identified.

---

## 4. Candidate specific contribution (conjunction)

Manuscript-native typed evidence graph spanning **both** Forward derivation and retrospective Audit for **heterogeneous theoretical-physics steps**, with **source-grounded printed-equation identity**, **independent fail-closed evidence**, and a **generated equation-indexed reviewer table**.

The contribution is the **conjunction**, not any conjunct.

---

## 5. What remains uncertain

- Whether an unpublished or non-indexed physics-education / MKM tool already emits equation-indexed audit tables. PDG’s website is the nearest named project; it is not used as a technical authority here.
- Whether flexiformal OMDoc/MMT deployments already encode remainder vs exact vs rule-mediated physics steps. The 2006 book documents markup of textbooks, not this status vocabulary.
- Whether later Lean-for-physics libraries beyond HepLean change component C. HepLean still requires Lean encoding.

Uncertain items stay out of novelty sentences.

---

## 6. Allowed wording

- “We are not aware of prior work that jointly …”
- “Prior work separately addresses producer/checker separation, formal proof, CAS simplification, and workflow provenance.”
- “Our contribution is the combination/application of these ideas to manuscript-native theoretical-physics derivation edges.”
- “The distinction lies in the object: a typed evidence graph over printed derivations, not a proof kernel, a CAS session, or a workflow trace.”
- “AI may propose; it may not certify itself — a split already standard in formal mathematics; here it is applied to ordinary physics manuscripts and is proposer-agnostic.”

## 7. Prohibited wording

- “No prior work has …”
- “This is the first …”
- “Unlike all previous methods …”
- “Previous methods cannot …”
- “We invent the producer/checker split.”
- “This is more rigorous than Lean/Coq.”
- “Proof assistants cannot handle physics.”
- “This is just provenance plus SymPy” as a *positive* novelty claim, or its denial without the object-level distinction.
- Any uniqueness claim about independent verification of untrusted computation.

---

## 8. Against CLAIM_EVIDENCE_MATRIX.md

Do **not** strengthen L1–L26.

| Matrix row | RW effect |
|---|---|
| L1 one typed framework | Remains *demonstrated of this system*, not uniqueness. Forbidden column already bans “first system ever”. **No amendment.** |
| L2–L3 proposal ≠ verification | Prior art in ITP/LLM-provers is now explicit. Keep caveats. **No strengthening.** Optional draft-v4 note: acknowledge the split is inherited. **Proposed amendment (wording only, not strength):** L2 allowed wording may add “a split already used in formal proof assistants; here applied to physics manuscripts.” Strength stays `implemented`. |
| L8–L9 generated tables / threat model | Do not upgrade to “unforgeable”. **No amendment.** |
| L14 inventory vs verified | RW does not support calling inventory “verification”. **No amendment.** |
| L19 sampled five-paper | RW does not support “general cross-paper applicability”. **No amendment.** |
| L25 approximation | Still candidate. **No amendment.** |
| P14 exhaustive novelty | After this freeze, combination wording is allowed; exhaustive novelty remains prohibited. **No automatic matrix edit in this pass.** |

Recorded proposed amendment (not applied): L2 allowed-wording footnote above.
