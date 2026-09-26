# Adversarial Related Work check — RELATED_WORK_REAUDIT_V1

## Reviewer A — formal methods

**Strongest objection.** “You are claiming novelty for independent checking that already exists in PCC, program checking, and proof kernels.”

**Prior work supporting the objection.** Necula 1997; Blum & Kannan 1995; Lean/Coq/Isabelle kernels; Kaufmann & Biere 2023.

**Precise answer.** Independent checking is **not** the novelty. It is inherited. The paper’s claim is a different *object*: typed manuscript-native derivation edges with heterogeneous physics statuses and fail-closed promotion, used both Forward and Audit. Kernel checking of a Lean theorem is a stronger guarantee *once the claim is encoded*; it is not an equation-indexed audit of an ordinary PRL derivation that may remain `UNKNOWN`.

**Wording change needed.** Any sentence that sounds like “we introduce independent verification of untrusted computation” must be rewritten to “we apply that prior-art split to …”. draft-v3 §8 already leans this way; tighten, do not invent uniqueness.

**Overclaim test.** Answerable without overclaiming if novelty stays at the conjunction.

---

## Reviewer B — computational scientist

**Strongest objection.** “Is this just workflow provenance plus SymPy?”

**Prior work supporting the objection.** Moreau et al. 2008; Kluyver et al. 2016; Meurer et al. 2017; MacCallum 2018; Peeters 2007.

**Precise answer.** SymPy is the exact-adjudication *route* (`python_sympy_exact_v1`), not the scientific object. Provenance answers where a process/data product came from. This graph asks what mathematical claim an edge makes (\(\tau\)), what evidence class supports it (\(c\)), and whether that evidence may promote scientific state. A notebook cell that ran, or a CAS `simplify` that returned a form, is not a generated Eq. (D-57) `UNKNOWN_REMAINDER` row.

**Wording change needed.** Do not insult CAS users. Say: physics already computes in CAS; the missing piece we target is epistemic state control on manuscript-grounded steps. Do not say “CAS cannot check equalities.”

**Overclaim test.** Answerable if we do not claim CAS lack equivalence checking.

---

## Reviewer C — AI / scientific-agent researcher

**Strongest objection.** “Is this merely verifier-guided LLM reasoning?”

**Prior work supporting the objection.** Polu & Sutskever 2020; Yang et al. 2023; Trinh et al. 2024; Song et al. 2024.

**Precise answer.** Verifier-guided LLM proving is real prior art. This paper’s Forward path is **proposer-agnostic**: human, CAS, or experimental model. There is no shipped `propose` command. Core verification needs no API key. The checker’s object is a physics manuscript edge (or a working expression), not a Metamath/Lean/geometry theorem. LLM-assisted proposal is experimental evidence (`FORWARD_WORKFLOW_DEMONSTRATED_WITH_CAVEATS`), not the contribution headline.

**Wording change needed.** Explicitly concede “AI may propose; a checker decides” is already instantiated in formal mathematics. Then locate the difference in the artifact and in proposer-agnostic manuscript use.

**Overclaim test.** Answerable if we do not claim we invented verifier-guided AI.

---

## Joint outcome

All three objections are answered by **narrowing** novelty to the conjunction in `NOVELTY_BOUNDARY.md`, not by denying prior art.

If draft-v4 cannot keep that narrowing, the boundary is not frozen. This pass keeps it frozen.
