# Related-work audit v2

Independent retrieval this session (web search against publisher pages, arXiv,
Crossref/DOI records, dblp/STTT bib). No model-memory entries.
`Butt and Fitch, Data & Knowledge Engineering 2021` from draft-v2 was **not
re-found** under that metadata; it is **dropped**. Notebook provenance is
represented by Kluyver (2016) and Koop (2021).

Quote-strength policy: metadata and abstracts support citation-level
statements only, except Guo (full public validation report is L1) and product
docs (L1).

Novelty is **not** "an untrusted producer needs a checker." That principle is
old. Closest prior families and the precise difference axis follow.

---

## Families searched

1. Computer algebra and symbolic computation (physics-facing)
2. Certified computer algebra / proof certificates
3. Proof assistants and theorem proving
4. Proof-carrying / independently checked computation
5. Scientific workflow provenance
6. Computational notebooks / reproducibility
7. AI-assisted theorem or mathematical search
8. AI for scientific reasoning / symbolic agents
9. Closest adjacent: physics derivation graphs / digitalisation of HEP

---

## Retrieved pool (existence + metadata)

### 1. Computer algebra

| Work | Venue | Status | Use |
|---|---|---|---|
| Meurer et al., "SymPy: symbolic computing in Python" | PeerJ Comput. Sci. 3:e103, 2017, doi:10.7717/peerj-cs.103 | VERIFIED | engine substrate |
| MacCallum, "Computer algebra in gravity research" | Living Rev. Relativ. 21:6, 2018, doi:10.1007/s41114-018-0015-6 | VERIFIED | physics CAS practice |
| Peeters, "Cadabra: a field-theory motivated symbolic computer algebra system" | Comput. Phys. Commun. 176:550–558, 2007, doi:10.1016/j.cpc.2007.01.003 | VERIFIED | tensor/field-theory CAS |
| Peeters, "Introducing Cadabra…" | arXiv:hep-th/0701238 | VERIFIED (preprint of related intro) | citation-level only if needed |
| Martin-García, xPerm / xAct | CPC (xPerm 2008); project docs | VERIFIED at project/citation level | tensor canonicalisation |
| Vermaseren, FORM lineage (Schoonschip → FORM) | CPC / hep-ph literature | VERIFIED as a CAS family, cite FORM features paper if used | HEP symbolic scale |

Difference axis vs this paper: CAS evaluates expressions. They do not type
manuscript arrows, do not generate reviewer tables from integrity-bound
records, and do not gate scientific-state promotion.

### 2. Certified CAS / hidden verification / algebraic certificates

| Work | Venue | Status | Use |
|---|---|---|---|
| Gottliebsen, Kelsey, Martin, "Hidden verification for computational mathematics" | J. Symbolic Comput. 39(5):539–567, 2005, doi:10.1016/j.jsc.2004.12.005 | VERIFIED | hidden checker behind CAS |
| Kaufmann and Biere, "Improving AMulet2 for verifying multiplier circuits using SAT solving and computer algebra" | STTT 25(2):133–144, 2023, doi:10.1007/s10009-022-00688-6 | VERIFIED | SAT + Gröbner certificates. **Citation-level only.** Do not cite unstated Nullstellensatz sizes. |
| Kaufmann and Biere, Nullstellensatz-proofs for multiplier verification | CASC 2020 | VERIFIED existence; **not used** in prose (STTT is enough) | — |

Difference axis: certificates validate a computer-algebra or circuit
computation. They are not manuscript-native, do not distinguish
`DIRECT_EXACT` from `RULE_CERTIFICATE` on printed physics steps, and do not
attach generated reviewer tables to a derivation graph.

### 3. Proof assistants

| Work | Venue | Status | Use |
|---|---|---|---|
| de Moura and Ullrich, "The Lean 4 Theorem Prover and Programming Language" | CADE-28, 2021, doi:10.1007/978-3-030-79876-5_37 | VERIFIED | Lean kernel |
| Nipkow, Paulson, Wenzel, Isabelle/HOL | Cambridge Univ. Press, 2002 | VERIFIED (book) | Isabelle |
| Yang et al., "LeanDojo: Theorem Proving with Retrieval-Augmented Language Models" | NeurIPS 2023 | VERIFIED | LLM + Lean |
| Song, Yang, Anandkumar, "Lean Copilot…" | arXiv:2404.12534 | VERIFIED preprint | copilots; tactics checked by Lean |
| Tooby-Smith, "HepLean: Digitalising high energy physics" | arXiv:2405.08863 | VERIFIED preprint | HEP in Lean; different object (formalisation, not manuscript audit) |

Difference axis: a kernel certifies a fully specified formal proof. Encoding
a condensed-matter supplement into Lean is a different scientific object from
typing the printed arrows a theorist already wrote.

### 4. Proof-carrying / producer–checker

| Work | Venue | Status | Use |
|---|---|---|---|
| Necula, "Proof-Carrying Code" | POPL 1997, pp. 106–119, doi:10.1145/263699.263712 | VERIFIED | untrusted producer, independent checker |

Difference axis: PCC is the ancestral producer/checker principle. This paper
does not claim to invent that principle. It lifts an analogous split onto
manuscript-native derivation edges with two-axis (claim vs certificate)
semantics.

### 5. Scientific workflow provenance

| Work | Venue | Status | Use |
|---|---|---|---|
| Moreau, Ludäscher, et al., "The First Provenance Challenge" | Concurr. Comput. Pract. Exp. 20(5):409–418, 2008, doi:10.1002/cpe.1233 | VERIFIED | workflow provenance |
| W3C PROV / ProvONE | standards | citation-level if used | data/process provenance |

Difference axis: provenance records *what ran*. It does not type a scientific
claim (algebra vs IBP vs remainder) or decide `ZERO`/`UNKNOWN`.

### 6. Notebooks / reproducibility

| Work | Venue | Status | Use |
|---|---|---|---|
| Kluyver et al., "Jupyter Notebooks — a publishing format for reproducible computational workflows" | ELPUB 2016, pp. 87–90, doi:10.3233/978-1-61499-649-1-87 | VERIFIED | notebooks mix code, results, prose |
| Koop, "Notebook Archaeology: Inferring Provenance from Computational Notebooks" | IPAW 2021, LNCS 12839, pp. 109–126, doi:10.1007/978-3-030-80960-7_7 | VERIFIED | notebook provenance is incomplete |
| Wilkinson et al., "The FAIR Guiding Principles…" | Sci. Data 3:160018, 2016, doi:10.1038/sdata.2016.18 | VERIFIED | findable data, not typed derivations |

Difference axis: a notebook cell that returns True is not a typed derivation
certificate. Execution order ≠ epistemic type.

### 7. AI-assisted theorem / mathematical search

| Work | Venue | Status | Use |
|---|---|---|---|
| Polu and Sutskever, "Generative Language Modeling for Automated Theorem Proving" | arXiv:2009.03393, 2020 | VERIFIED preprint | GPT-f; LM proposes, kernel checks |
| Trinh et al., "Solving olympiad geometry without human demonstrations" | Nature 625:476–482, 2024, doi:10.1038/s41586-023-06747-5 | VERIFIED | neuro-symbolic geometry; LM proposes, symbolic engine checks |
| Romera-Paredes et al., FunSearch | Nature 625, 2024 | VERIFIED at citation level from prior bib + Nature family | search + evaluator |
| Wei et al., chain-of-thought | NeurIPS 2022 | VERIFIED at citation level from prior bib | traces are not certificates |
| Lewkowycz et al., Minerva | 2022 | VERIFIED at citation level from prior bib | quantitative QA, not derivation typing |

Difference axis: these systems already separate proposal from checking
*inside a formal or contest object*. They do not audit a published physics
manuscript, and they do not implement verification-gated *state advancement*
of a physicist’s current expression under fail-closed UNKNOWN.

### 8. Closest adjacent software project

**Physics Derivation Graph** (https://allofphysics.com/, GitHub
`allofphysicsgraph/proofofconcept`). Public claims (project pages, retrieved
this session): a graph of expressions linked by inference rules; some rules
are CAS-checkable (SymPy); Lean checking is planned/secondary. **No
peer-reviewed article with stable bibliographic metadata was found this
session.** Treat as a named software project in Related Work, not as a
fabricated journal citation.

Difference axis: PDG aims at a global graph of physics with atomic inference
rules and CAS true/false checks. This work types *heterogeneous manuscript
steps as they are written*, keeps UNKNOWN and theorem-mediated statuses
first-class, generates reviewer tables from integrity functions, and uses the
same graph for forward gated derivation. It does not attempt to document all
of physics.

---

## Novelty moat (tested, not "first")

Tested statements the manuscript may use:

1. **Shared evidence graph for two workflows.** Constructive derivation and
   retrospective audit as opposite operations on one typed edge. Closest:
   PDG (graph of physics identities) and workflow provenance (graph of runs).
   Difference: promotion gate + manuscript-native typing + generated tables.
2. **Claim semantics \(\tau\) ≠ certificate provenance \(c\).** Closest:
   PCC / hidden verification / algebraic certificates. Difference: those
   systems certify a computation or a binary; they do not attach a
   two-axis record to a printed physics arrow.
3. **Fail-closed state promotion.** Closest: Lean copilots / GPT-f / AlphaGeometry
   (proposal checked before acceptance in a kernel or symbolic engine).
   Difference: the scientific state here is a physicist’s current expression
   and a reviewer table, not a Lean theorem. UNKNOWN is not a failed proof
   attempt to be retried as success.
4. **Reviewer-facing generated evidence on printed steps.** Closest: workflow
   provenance exports and notebook archaeology. Difference: inclusion is
   `schema.may_appear_in_verified_table`, not "the cell ran."

Do **not** write "first," "the first system," or "we invent producer/checker."

If a reviewer cites PDG or Lean-for-physics (HepLean) as overlap: agree that
graphs and kernels exist; the difference is manuscript-native heterogeneous
typing plus two-mode execution under fail-closed inclusion.

---

## Dropped / unresolved

| Candidate | Reason |
|---|---|
| Butt/Fitch DKE 2021 (draft-v2 [11]) | Not re-found. **Delete.** Replace with Koop 2021 + Moreau 2008. |
| Kaufmann Nullstellensatz sizes | Existence of CASC 2020 paper verified; numbers not in abstract. Do not quote sizes. |
| Physics Derivation Graph journal article | Not found. Name the project; no fake reference. |

---

## Comparison table (manuscript)

| Family | Shared graph for construct and audit | Types heterogeneous manuscript steps | Fail-closed local residual | Theorem-mediated status ≠ engine ZERO | Generated reviewer table |
|---|---|---|---|---|---|
| CAS / notebook | no | no | partial | no | no |
| Proof assistant / Lean copilots | no (formal object) | formalized differently | yes | yes, in the kernel | partial |
| Workflow provenance | process graph | no | no | no | provenance trace |
| Certified CAS / PCC | no | no | yes | system-specific certificate | certificate |
| Physics Derivation Graph | derivation graph (project) | atomic inference rules | CAS true/false | not the two-axis design | not generated inclusion tables |
| This work | yes | yes | yes | yes (`CERTIFIED_BY_RULE`) | yes |

---

## Citation verification disclosure

Rung: same-context grounding plus web retrieval (Rung 2 of
`paper-writer` verification-ladder). Independent fresh-context sub-agent
verification of the *final* reference list is scheduled after
`draft-v2-prehumanizer.md` exists.
