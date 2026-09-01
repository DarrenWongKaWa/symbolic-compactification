# Citation ledger — RELATED_WORK_REAUDIT_V1

Primary unless marked. Maximum wording is the strongest sentence the source
justifies. Ambiguity is recorded. Famous-but-unused papers are listed under
Rejected.

---

## Retained (21)

### A1. Necula, G. C. “Proof-carrying code.” POPL 1997, pp. 106–119.

- DOI: 10.1145/263699.263712
- Primary conference paper.
- **Supports:** an untrusted code producer must supply a safety proof; the host validates it without trusting the producer.
- **Max wording:** untrusted computation can be admitted only with an independently checked certificate of *safety wrt a policy*.
- **Ambiguity:** none for the producer/checker split; does not mention physics manuscripts.

### A2. Blum, M., and Kannan, S. “Designing programs that check their work.” J. ACM 42(1):269–291, 1995.

- DOI: 10.1145/200836.200880
- Primary journal (archival of STOC 1989).
- **Supports:** a checker certifies whether a program’s output on an instance is correct (sorting, GCD, …).
- **Max wording:** instance-correctness of an algorithm can be checked independently of trusting the program.
- **Ambiguity:** checkers may be probabilistic; not a manuscript object.

### A3. Gottliebsen, H., Kelsey, T., and Martin, U. “Hidden verification for computational mathematics.” J. Symbolic Comput. 39(5):539–567, 2005.

- DOI: 10.1016/j.jsc.2004.12.005
- Primary journal. Abstract verified via University of St Andrews record.
- **Supports:** PVS called from Maple to discharge continuity/convergence/differentiability VCs while shielding the user from the prover.
- **Max wording:** a CAS session can be backed by a hidden theorem prover for analysis VCs (DE solvers, look-up tables).
- **Ambiguity:** “hidden” means UX, not that verification is optional.

### A4. Kaufmann, D., and Biere, A. “Improving AMULET2 for verifying multiplier circuits using SAT solving and computer algebra.” Int. J. Softw. Tools Technol. Transfer 25:133–144, 2023.

- DOI: 10.1007/s10009-022-00688-6
- Primary journal (TACAS 2021 special issue). Tool paper TACAS 2021 DOI 10.1007/978-3-030-72013-1_19 is the predecessor.
- **Supports:** SAT+CAS verification of multipliers; certificates in Nullstellensatz or PAC.
- **Max wording:** algebraic circuit identities can be independently certified.
- **Ambiguity:** object is circuits, not papers.

### B1. de Moura, L., and Ullrich, S. “The Lean 4 theorem prover and programming language.” CADE 28, LNAI 12699, pp. 625–635, 2021.

- DOI: 10.1007/978-3-030-79876-5_37
- Primary conference system paper.
- **Supports:** Lean 4 is an ITP; users extend tactics/automation; proofs live in Lean.
- **Max wording:** interactive theorem proving in Lean with user-extensible automation.
- **Ambiguity:** paper is a system description, not a physics case study.

### B2. Bertot, Y., and Castéran, P. *Interactive Theorem Proving and Program Development. Coq’Art: The Calculus of Inductive Constructions.* Springer, 2004.

- DOI: 10.1007/978-3-662-07964-5
- Primary book (system + CIC).
- **Supports:** Coq develops proofs and certified programs in CIC; tactics build terms a kernel checks (standard ITP architecture).
- **Max wording:** Coq provides a kernel-checked proof environment for CIC.
- **Ambiguity:** textbook, not a single theorem; sufficient as the canonical Coq citation.

### B3. Nipkow, T., Paulson, L. C., and Wenzel, M. *Isabelle/HOL: A Proof Assistant for Higher-Order Logic.* LNCS 2283, Springer, 2002.

- DOI: 10.1007/3-540-45949-9
- Primary book.
- **Supports:** interactive proof in HOL using Isabelle.
- **Max wording:** Isabelle/HOL is a proof assistant for higher-order logic.
- **Ambiguity:** tutorial volume; still the standard system citation.

### B4. Tooby-Smith, J. “HepLean: Digitalising high energy physics.” Comput. Phys. Commun. 308:109457, 2025.

- DOI: 10.1016/j.cpc.2024.109457 ; arXiv:2405.08863
- Primary journal.
- **Supports:** HEP definitions/theorems/proofs/calculations digitalised in Lean 4; potential benefits include finding results, AI/automation, “easy review of papers for mathematical correctness,” and teaching. Demonstrations: CKM matrices, anomaly cancellation, Higgs physics.
- **Max wording:** some HEP results can be encoded and kernel-checked in Lean; paper review is a stated *potential* benefit of that encoding.
- **Ambiguity:** “review of papers” is prospective, not an evaluation of ordinary LaTeX manuscripts. Do not read as equation-indexed `RESULTS.md`.

### C1. Moreau, L., Ludäscher, B., Altintas, I., et al. “The First Provenance Challenge.” Concurr. Comput. Pract. Exp. 20(5):409–418, 2008.

- DOI: 10.1002/cpe.1233
- Primary community-challenge paper (16 teams; fMRI workflow + queries).
- **Supports:** provenance systems record and query representations of what a scientific workflow produced.
- **Max wording:** provenance representations capture workflow/data lineage sufficient to answer challenge queries.
- **Ambiguity:** medical imaging workflow, not symbolic physics.

### C2. Wilkinson, M. D., Dumontier, M., Aalbersberg, I. J., et al. “The FAIR Guiding Principles for scientific data management and stewardship.” Sci. Data 3:160018, 2016.

- DOI: 10.1038/sdata.2016.18
- Primary publication of the FAIR principles (Comment).
- **Supports:** findable, accessible, interoperable, reusable data, including machine-actionability.
- **Max wording:** scholarly data should be machine-findable; this is not a derivation-typing standard.
- **Ambiguity:** principles, not a system evaluation.

### C3. Kluyver, T., Ragan-Kelley, B., Pérez, F., et al. “Jupyter Notebooks — a publishing format for reproducible computational workflows.” In *Positioning and Power in Academic Publishing*, IOS Press, 2016, pp. 87–90.

- DOI: 10.3233/978-1-61499-649-1-87
- Primary short system paper.
- **Supports:** notebooks publish code, results, and explanations in one readable/executable document.
- **Max wording:** a computational narrative can mix prose and executed code.
- **Ambiguity:** does not claim typed math certificates.

### C4. Koop, D. “Notebook archaeology: inferring provenance from computational notebooks.” IPAW 2020+2021, LNCS 12839, pp. 109–126, 2021.

- DOI: 10.1007/978-3-030-80960-7_7
- Primary workshop paper.
- **Supports:** notebooks often do not record full provenance because steps are repeated, reordered, or removed; provenance can be inferred statistically.
- **Max wording:** notebook process history is often incomplete.
- **Ambiguity:** reconstructive, not a promotion policy.

### D1. Polu, S., and Sutskever, I. “Generative language modeling for automated theorem proving.” arXiv:2009.03393, 2020.

- URL: https://arxiv.org/abs/2009.03393
- Primary preprint (no archival version found).
- **Supports:** GPT-f proposes Metamath proofs; accepted short proofs entered the Metamath library.
- **Max wording:** an LLM can propose formal proof steps that a Metamath checker accepts or rejects.
- **Ambiguity:** “first time a deep-learning based system has contributed proofs …” is *their* claim; we do not need it.

### D2. Yang, K., Swope, A., Gu, A., et al. “LeanDojo: Theorem proving with retrieval-augmented language models.” NeurIPS 2023 (Datasets and Benchmarks, oral).

- DOI: 10.52202/075280-0944 ; arXiv:2306.15626
- Primary conference paper.
- **Supports:** LLM prover interacts with Lean; kernel remains the environment; open data/tools.
- **Max wording:** retrieval-augmented LLMs can propose Lean proof steps that Lean checks.
- **Ambiguity:** benchmark/tooling paper; not a physics manuscript auditor.

### D3. Trinh, T. H., Wu, Y., Le, Q. V., He, H., and Luong, T. “Solving olympiad geometry without human demonstrations.” Nature 625:476–482, 2024.

- DOI: 10.1038/s41586-023-06747-5
- Primary journal.
- **Supports:** neural language model guides a symbolic deduction engine; 25/30 IMO-AG geometry problems.
- **Max wording:** a neuro-symbolic geometry prover: the model proposes, a symbolic engine checks.
- **Ambiguity:** Euclidean olympiad geometry, not condensed-matter manuscripts.

### D4. Song, P., Yang, K., and Anandkumar, A. “Lean Copilot: Large language models as copilots for theorem proving in Lean.” arXiv:2404.12534, 2024.

- URL: https://arxiv.org/abs/2404.12534
- Primary preprint; GitHub notes acceptance to NeuS 2025 (not used as a venue claim beyond “preprint / accepted workshop-conference”).
- **Supports:** LLMs as Lean copilots; “correctness of formal proofs can be rigorously verified, leaving no room for hallucination” *in Lean*.
- **Max wording:** inside Lean, an LLM suggestion is not a certificate; the assistant is.
- **Ambiguity:** do not extend “no hallucination” outside Lean.

### E1. Meurer, A., Smith, C. P., Paprocki, M., et al. “SymPy: symbolic computing in Python.” PeerJ Comput. Sci. 3:e103, 2017.

- DOI: 10.7717/peerj-cs.103
- Primary journal system paper.
- **Supports:** open-source Python CAS; extensible architecture.
- **Max wording:** SymPy performs symbolic manipulation in Python.
- **Ambiguity:** not a scientific-state machine.

### E2. Peeters, K. “Cadabra: a field-theory motivated symbolic computer algebra system.” Comput. Phys. Commun. 176(8):550–558, 2007.

- DOI: 10.1016/j.cpc.2007.01.003 ; arXiv:cs/0608005
- Primary journal.
- **Supports:** TeX-like input; tensor/Young symmetries; paper-to-computer translation is error-prone on general CAS.
- **Max wording:** a physics-facing CAS can take TeX-like tensor input; that is still a CAS scratch pad.
- **Ambiguity:** “first system” Young-projector claim is *theirs*; unused.

### E3. MacCallum, M. A. H. “Computer algebra in gravity research.” Living Rev. Relativ. 21:6, 2018.

- DOI: 10.1007/s41114-018-0015-6
- **Survey** (orientation only).
- **Supports:** CA is widely used in GR; many packages exist.
- **Max wording:** theoretical-physics calculations already use computer algebra.
- **Ambiguity:** survey; no promotion-policy claims.

### E4. Willsey, M., Nandi, C., Wang, Y. R., Flatt, O., Tatlock, Z., and Panchekha, P. “egg: Fast and extensible equality saturation.” Proc. ACM Program. Lang. 5(POPL):23, 2021.

- DOI: 10.1145/3434304
- Primary journal (PACMPL).
- **Supports:** e-graphs represent many equivalent expressions; equality saturation searches rewrites.
- **Max wording:** rewrite search can saturate equivalences without committing to one syntactic form early.
- **Ambiguity:** compiler/synthesis workloads, not physics audit tables.

### M1. Kohlhase, M. *OMDoc — An Open Markup Format for Mathematical Documents [version 1.2].* LNAI 4180, Springer, 2006.

- DOI: 10.1007/11826095
- Primary book/specification.
- **Supports:** markup of mathematical textbooks/articles (definitions, theorems, proofs) for knowledge management; stepwise formalization of existing text (Bourbaki fragment).
- **Max wording:** ordinary mathematical documents can be annotated with structure and (flexi)formal meaning.
- **Ambiguity:** knowledge-management format, not fail-closed `ZERO`/`UNKNOWN` promotion.

---

## Rejected (not used as technical authority)

| Item | Why rejected |
|---|---|
| Physics Derivation Graph website (allofphysics.com) | No archival paper with stable metadata found. Named in outline as a hedge only. |
| DeepMind AlphaGeometry blog | Secondary; Nature paper is primary. |
| Coq HTML reference manual | Official docs; Coq’Art used as citable primary. |
| W3C PROV-O spec | Standard; Moreau 2008 already covers provenance graphs. |
| Toolformer / ReAct / ToRA | Tool-using LLMs; would inflate Block D without changing the proposer/checker finding. |
| Theorema / Analytica | Overlap with Maple+PVS/hidden verification; Gottliebsen is enough. |
| Adams et al., TPHOLs 2001 Maple+PVS | Strong related primary; omitted to keep Block A to four. May be added if hidden-verification paragraph needs a second system paper. |
| Mehlhorn “certifying algorithms” survey 2011 | Survey of certification; Blum & Kannan + Kaufmann suffice. |

---

## Count

Retained: 21 (A4 + B4 + C4 + D4 + E4 + OMDoc).
Survey among retained: MacCallum only.
Preprints among retained: GPT-f; Lean Copilot (LeanDojo and HepLean and AlphaGeometry have archival venues).
