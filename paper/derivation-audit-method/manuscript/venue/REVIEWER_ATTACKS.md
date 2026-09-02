# Expected reviewer attacks (PRIMARY = CPC, Computational Physics Paper)

Parent: `PAPER_AUTHORITY_LOCK.md`, `CLAIM_EVIDENCE_MATRIX.md`, `related_work/NOVELTY_BOUNDARY.md`.
No new experiments are proposed as the default reply.

---

## R1 — computational physicist

**Strongest objection.** “Is this just SymPy wrapped in bookkeeping?”

**Frozen answer.** The engine is an exact residual adjudicator (`python_sympy_exact_v1` 0.3.0), not a simplification policy that *is* the new scientific state. Promotion is fail-closed: `ZERO` is exact residual zero; `ZERO` ≠ `CERTIFIED_BY_RULE`; `UNKNOWN` never promotes; substitution-conditioned zero is not unconditional equality (L4, L5, L7). The object is a typed evidence graph with printed-equation identity, not `simplify()`.

**Current weakness.** If the Introduction leads with repository layout or packaging, R1’s reading is invited. Implementation details belong after the method and Guo.

**Section that must address it.** Introduction (computational method, not wrapper); Methods (τ vs c; promotion rule); a short implementation paragraph pointing at `v0.3.0-alpha` @ `f1d225e`.

---

## R2 — theoretical physicist

**Strongest objection.** “Does this help with real derivations or only selected toy identities?”

**Frozen answer.** Guo et al., PRL 136, 206303, arXiv:2511.16422v2: 189/189 numbered equations inventoried; 146 source-grounded relations; 53 executable; typed statuses including exact, substitution, rule-mediated IBP, and `UNKNOWN_REMAINDER` (L14–L17). Flagship printed examples: (D-59)→(D-60), (D-66)→(D-67), (D-114)→(D-119), (D-57). Human-facing HTML is a projection of that table, not a second verdict.

**Current weakness.** Guo is formative, not held-out generalisation (L18). Five-paper work is a **sampled** 41-edge stress test, not five full audits (L19). Those caveats must travel in the same paragraphs as the counts.

**Section that must address it.** Results: Guo first, as the substantive physics demonstration CPC requires; then Forward demos; then sampled breadth. Limitations: formative adapter (BZ IBP), inventory ≠ algebra, no paper-proof.

---

## R3 — formal-methods / related-work reviewer

**Strongest objection.** “Independent checking is old. What exactly is new?”

**Frozen answer.** Independent checking is prior art (PCC, kernels, CAS+ITP). Novelty is the **conjunction**: manuscript-native typed graph for **both** Forward and Audit, heterogeneous physics statuses, printed-equation grounding, fail-closed promotion, generated equation-indexed reviewer table (`NOVELTY_BOUNDARY.md`). Allowed wording: “we are not aware of prior work that jointly …”.

**Current weakness.** If any sentence says “first system ever” or “no prior work has”, the paper violates the Related Work freeze.

**Section that must address it.** Related Work after the method is stated, using the frozen 21-primary set. Do not expand novelty.

---

## R4 — scientific-software / reproducibility reviewer

**Strongest objection.** “Is the implementation general and reproducible enough?”

**Frozen answer.** Public tag `v0.3.0-alpha` @ `f1d225e`; core verification needs no API key (L10); Forward and Audit demos in-tree; Guo `RESULTS.md` regenerable from frozen YAML; false promotion 0/155 on injected controls (Guo) and 0/36 (Forward replay, with caveats). CPC CP papers “normally include software implementation and performance details”; GitHub is an approved location.

**Current weakness.** One named global rule in the product catalogue (`BZ_TORUS_PERIODICITY`). Approximation overlays are **candidate / Discussion only**. No shipped `propose` command. Do not claim a theorem-prover library.

**Section that must address it.** A compact Reproducibility / software subsection (not the lead). Limitations: rule catalogue, transcription, remainder non-certificate.

---

## Shared instruction for draft-v4

Do not answer R1–R4 with new experiments. Answer with frozen evidence, explicit caveats, and section placement.
