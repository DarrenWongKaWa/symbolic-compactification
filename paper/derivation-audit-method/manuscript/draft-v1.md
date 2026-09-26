# Machine-Auditable Theoretical Derivations through Typed Evidence Graphs

A fail-closed audit layer for AI-assisted symbolic science

---

## Abstract

Modern theoretical derivations increasingly mix human reasoning, computer-algebra manipulations, AI proposals, substitutions, symmetry arguments, global theorems, and asymptotics. What is missing is not another reasoning agent, but an audit layer that records exactly what was claimed, what was actually checked, under which assumptions, and with what machine evidence. This paper formulates that missing object. We treat a derivation as a typed evidence graph rather than as a list of neighbouring equations. Each edge carries an epistemic type, an optional executable residual, and a declared assumption set. Exact local identities may receive an engine certificate. Substitutions are labelled as such. Global theorems such as Brillouin-zone integration by parts receive a rule certificate, not a fake engine zero. Asymptotic remainders are allowed to stay unknown. The verified table is generated from integrity-bound records; model or author text cannot create certified status. We ask three questions: can narrative output forge certification; can heterogeneous scientific steps keep their type; and does the architecture survive a published theoretical-physics manuscript. Adversarial tests answer the first in the negative. Public demonstrations and a field validation on Guo et al., Phys. Rev. Lett. 136, 206303 (2026), show that algebra, substitution, theorem-mediated integration by parts, and an asymptotic remainder retain distinct statuses. The system is an equation-level audit. It does not prove a paper or confirm physical conclusions. An AI may propose a derivation; it may not certify itself.

---

## 1. Introduction

Theoretical calculations no longer live only on paper. A contemporary derivation in mathematical physics typically interleaves handwritten algebra, a computer-algebra rewrite, an AI-proposed rearrangement, a substitution taken as known, a global theorem about a domain, and a prose claim that a remainder is small. Computational notebooks already mix code, results, and explanation in one document [1]. Computer-algebra systems such as SymPy evaluate symbolic expressions as part of ordinary scientific Python work [2]. Language models now emit intermediate reasoning traces [3] and attempt quantitative problems in mathematics and the sciences [4]. The practical difficulty for a later reader is not that these tools exist. It is that neighbouring printed equations are still read as if they were the same kind of claim.

Consider two consecutive displayed formulae \(E_{17}\to E_{18}\) in a theoretical-physics supplement. That arrow may be an algebraic identity, a dummy-index relabeling, a definition, a use of symmetry, an integration by parts, an asymptotic reduction, or the statement that a term is negligible. Existing AI and computer-algebra workflows readily collapse all of those into a single word: verified. The collapse is epistemic information loss. Two failure modes follow. False certification occurs when an author or model writes verified into a table, when agreement of Laurent coefficients is taken as a remainder proof, or when an integral identity is marked green although the engine never integrated. False refutation occurs when a tool's inability to encode a step is heard as a mathematical error, or when a not-lowered encoding gap is reported as a scientific failure. Fluent generation can be unfaithful to its source [5]. Pairing a language model with an external evaluator is already useful for mathematical search [6], and neuro-symbolic provers can check geometry proofs in a symbolic engine [7]. Those systems still do not give a reviewer of a physics manuscript a typed record of which neighbouring equations were which kind of step.

Interactive theorem provers such as Lean and Isabelle/HOL certify fully specified proofs in a trusted kernel [8, 11]. Language models can propose tactics to such a proof assistant [12]. That is a different scientific object from the manuscript a condensed-matter theorist actually writes. The encoding cost of moving a long physics supplement into a kernel is not the same as asking, for each printed arrow, what was claimed and what was checked. Data-management principles such as FAIR make scholarly data findable and reusable by machines [9]; they do not type derivation steps. Our goal is therefore not a stronger solver. It is a machine-auditable evidence layer for the derivations that already occur.

Three obstacles follow from that goal. First, equation proximity is not an equality claim: forcing every scientific step into a residual \(lhs-rhs\) produces either a fake zero or an uninformative unknown. Second, local exactness, substitution, a declared global theorem, and an asymptotic remainder cannot share one pass/fail bit; a certificate must record dependency, not confidence. Third, if verified status can be authored in Markdown or emitted by a model, the audit layer is not an audit. Naive reuse of a notebook, a computer-algebra session, or a chain-of-thought trace fails all three.

We present Derivation Audit, a fail-closed audit layer that compiles a manuscript into a typed evidence graph (Section 2). Each edge is a claim \(\gamma=(e_{\mathrm{from}},e_{\mathrm{to}},\tau,\rho,A)\) with an epistemic type \(\tau\), an optional residual \(\rho\), and declared assumptions \(A\). Certificate classes distinguish direct engine zeros, substitution-conditioned zeros, rule certificates, structural records, and remainders that stay unknown (Section 3). Proposal is separated from authority: a language model may suggest edges and residuals, but only generated, integrity-bound records may enter the verified table (Section 4). Implementation binds source, obligation, and result by hashes and regenerates reviewer tables from a recorded run (Section 5).

We summarise our contributions as follows. (1) We formulate theoretical derivation audit as preservation of epistemic type, and define a derivation as a typed evidence graph rather than as a list of neighbouring equalities (Section 2). (2) We give certificate provenance semantics in which classes encode dependency, not a ranking of mathematical truth, including the invariant that engine zero is not a rule certificate (Section 3). (3) We separate proposal from authority so that verified tables are generated, not authored (Sections 4 and 5). (4) We evaluate the architecture with three research questions: whether narrative can forge certification; whether heterogeneous steps retain type; and whether the design survives a published theoretical-physics derivation (Section 6), using Guo et al. [10] as a public field validation rather than as a score to maximise.

---

## 2. Derivation as a typed evidence graph

The basic mistake is to treat a derivation as a sequence of displayed equations \(e_1,e_2,\ldots,e_n\) together with the implicit claim that each consecutive pair is an equality. In theoretical physics the actual graph is typed:

\[
E_1 \xrightarrow{\mathrm{definition}} E_2 \xrightarrow{\mathrm{algebra}} E_3 \xrightarrow{\mathrm{symmetry}} E_4 \xrightarrow{\mathrm{IBP}} E_5 \xrightarrow{\mathrm{asymptotic}} E_6.
\]

It is not

\[
E_1-E_2=0,\qquad E_2-E_3=0,\qquad \ldots
\]

Equation proximity is not an equality claim. If a method cannot say which arrow is which, it has already discarded the information a reviewer needs.

A derivation claim is therefore an edge

\[
\gamma = (e_{\mathrm{from}}, e_{\mathrm{to}}, \tau, \rho, A),
\]

where \(\tau\) is the scientific type of the step, \(\rho\) is an optional executable residual, and \(A\) is a declared assumption set. Inventory extracts labels, environments, order, and source ranges; it does not interpret LaTeX as algebra. Native-text members are researcher-authored transcriptions of the printed identities that will be checked. That transcription is a stated limitation, not a hidden intelligence.

The type catalogue is frozen and narrow. Algebraic equivalence, index relabeling, pairwise reduction, and projector identities may lower to a local residual. Definition insertion is a name introduction, not a proof. A split parent delegates to children and is never itself an engine zero. An asymptotic claim is a remainder, not a truncated series set equal to the original object. A generic integral argument is not a local residual. Brillouin-zone periodic integration by parts is a typed global step with a local Leibniz child. Selection uses the most specific type that matches the scientific claim. If no residual exists, the honest status is not-lowered or unknown, not a nearby algebraic encoding.

Figure 1 (left) shows the failure of the untyped list on a public running example drawn from Guo et al. [10]. In that supplement, a \(\Gamma\) expansion, a local regrouping, a substitution of \(\varepsilon_{21}=-\varepsilon_{12}\), and a Brillouin-zone integration by parts can appear as consecutive displayed formulae. Treating each pair as \(lhs-rhs\) would either invent an integral zero or bury the remainder in the same bucket as a successful regroup. Figure 1 (right) is the same fragment as a typed graph. The scientific object of this paper is that graph, together with the evidence attached to each edge.

---

## 3. Certificate provenance

The output of an audit is not pass or fail. It is certificate provenance: a record of what the conclusion depends on. Four claim kinds cover the cases that arise in manuscript audit.

An engine certificate is an executable residual \(r\) that a deterministic exact verifier simplifies to zero under the recorded route, namespace, and assumptions, or that an exact probe proves nonzero, or that it cannot decide. Direct exactness means the residual was not rewritten by an upstream identity that the assumption language cannot enforce:

\[
R = 0.
\]

Substitution exactness means the residual is zero after a declared identity is written in:

\[
R\big|_{\varepsilon_{21}=-\varepsilon_{12}} = 0.
\]

The tool then tells the reviewer that the downstream algebra is exact and that the upstream identity was supplied. It does not independently prove \(\varepsilon_{21}=-\varepsilon_{12}\).

A rule certificate combines a local engine certificate with a declared theorem and domain. Brillouin-zone integration by parts is the motivating case. The local Leibniz product rule is a residual and may be engine zero,

\[
\partial_k(uv)-u'v-uv'=0,
\]

while the vanishing of the integral of a total \(k\)-derivative is a theorem about a torus,

\[
\int_{\mathrm{BZ}}\partial_k(uv)\,d^dk = 0
\]

under declared periodicity of the integrand combination. The parent status is certified by rule, not engine zero. The computer-algebra engine did not evaluate the integral. Missing periodicity is assumption-required. Missing local child is not-lowered. A gauge-dependent Berry connection is not automatically allowed because the Brillouin zone is a torus; the declared rule must apply to the integrand combination actually used.

A structural record tracks definitions, bookkeeping, and splits. It is not a proof. An uncertified claim covers remainders, unsupported integrals, and parse or compile gaps. An asymptotic statement of the form

\[
F(\Gamma)=\frac{A}{\Gamma}+O(\Gamma)
\]

may have coefficient children that are engine zero; the remainder stays unknown unless a remainder certificate exists. Finite Laurent agreement is not a remainder proof.

Certificate classes encode dependency, not confidence. Direct exact, substitution exact, rule certificate, and unknown are not a ladder

\[
\mathrm{DIRECT} > \mathrm{SUBSTITUTION} > \mathrm{RULE} > \mathrm{UNKNOWN}.
\]

A substitution-exact row can be the scientifically central identity. A rule certificate can be the only honest encoding of a standard theorem. An unknown remainder can be the most important caveat in the paper. Figure 2 is this taxonomy.

The invariant that must not be weakened is

\[
\mathrm{ZERO} \neq \mathrm{CERTIFIED\_BY\_RULE}.
\]

Rule growth is field-driven. A named rule is added only when a real public derivation uses the step, the existing taxonomy cannot express it without a fake residual zero, and the conditions are explicit and fail-closed. Completeness, Stokes, Hermiticity, and trace cyclicity stay untyped until field use exposes them. This paper does not propose a theorem-prover library.

---

## 4. Separating proposal from authority

Language models may participate in science. They must not notarize themselves.

An AI can suggest candidate edges, propose substitutions, draft residuals, explain formulae, and even search for a new representation. FunSearch already pairs a language model with a systematic evaluator so that generation is not trusted on its own [6]. AlphaGeometry uses a language model to guide a symbolic deduction engine whose output is computer-checkable [7]. Those designs are consistent with the principle, but they solve different objects: combinatorial constructions and olympiad geometry, not a physics manuscript's typed arrows. In a derivation audit, none of the generative acts above may create verified status.

The authority chain is

\[
\mathrm{source}
\rightarrow
\mathrm{grounded\ edge}
\rightarrow
\mathrm{obligation}
\rightarrow
\mathrm{verifier}
\rightarrow
\mathrm{evidence\ record}
\rightarrow
\mathrm{generated\ table}.
\]

A reviewer need not believe a model's confidence. The reviewer inspects the tuple

\[
(\mathrm{source},\ \mathrm{claim\ type},\ \mathrm{assumptions},\ \mathrm{obligation},\ \mathrm{certificate}).
\]

The corresponding slogan is that the verified table is generated, not authored. Inclusion is a function of a machine record: integrity must hold; status and engine result must both be zero; the edge must be executable; split parents and asymptotic claims are excluded from the verified table. Markdown that contains the word zero is ignored. A forged record without residual, obligation, and assumption hashes fails integrity. Relabelling unknown as zero without an engine zero is rejected. Deleting a nonzero row from Markdown does not hide it; regeneration from the bound run restores it. A split parent with an uncertified child cannot certify, and never becomes engine zero.

This is a scientific design principle, not merely a software hardening trick. The more autonomous the proposer becomes, the more important the separation. AI autonomy does not require epistemic self-certification.

---

## 5. Implementation

The public implementation is Derivation Audit 0.2.1-alpha in the symbolic-compactification repository, engine 0.3.0, protocol 0.2.1, immutable tag `derivation-audit-v0.2.1-alpha`. A researcher workspace holds a manuscript stub, an equation inventory, a typed edge manifest, native-text expressions, and an assumption file. Commands snapshot, ground, lower, verify, generate tables, write a report, and export a reviewer package with `reproduce.sh`.

Provenance is mechanical. Manuscript bytes, manifests, expression files, and assumptions are hashed. Changing source, residual, or assumption bytes produces a new snapshot; prior zero rows do not transfer. Paths are workspace-relative. The assumption language is deliberately small: real symbols, optional nonzero, named functions. Parameter identities that the language cannot encode must be substituted into the residual and labelled substitution-exact.

Reviewer tables are regenerated from the recorded run. Four buckets are used: verified (integrity-ok executable engine zero), nonzero, structural (including certified-by-rule), and uncertified (unknown, not-lowered, failures). Optional AI proposal is experimental, disabled in private-offline mode, and has no write path into the verified table.

The v0.2.1 patch adds one field-driven adapter, Brillouin-zone periodic integration by parts, after a public real-paper validation exposed an encoding gap. The exact-engine meanings of zero, nonzero, and unknown are unchanged. Historical tag 0.2.0-alpha is not moved. Public case evidence lives on a separate branch from the product tag.

---

## 6. Evaluation

The evaluation is not a benchmark accuracy. It answers three questions about the epistemic architecture. No new scientific campaign is introduced; results are existing public artifacts.

### 6.1 RQ1. Can narrative or model output forge certification?

No. Public adversarial tests include: a Markdown zero without a machine record; a forged JSON zero missing hashes; mutation of source, assumption, or residual bytes; relabelling unknown as zero; hiding nonzero by editing Markdown; a split parent with an uncertified child; rewriting an asymptotic truncation as an exact equality; and treating a Brillouin-zone integration-by-parts parent as engine zero. In each case the inclusion functions refuse the upgrade. These tests do not prove the absence of every encoding cheat: a human can still transcribe the wrong identity on both sides. They show that table machinery does not accept narrative, forgery, or remainder promotion as certification.

### 6.2 RQ2. Can heterogeneous theoretical steps retain type?

Public synthetic demonstrations ship with the product. Demo A lowers algebraic equation-to-equation identities to engine zero. Demo B records typed linear-algebra steps together with definition and bookkeeping. Demo C certifies Laurent coefficient identities as zero while the enclosing asymptotic remainder stays unknown. The last demonstration is soundness evidence: the tool will not rewrite a remainder as an exact residual to manufacture a green row.

### 6.3 RQ3. Does the architecture survive a real theoretical-physics manuscript?

The Derivation Audit pipeline has been exercised end-to-end on a published theoretical-physics derivation [10]. Public authority is arXiv:2511.16422v2. The PDF and source tarball are not committed; they are reconstructed from bibliographic provenance. The workspace is evidence, not product source.

The question is not whether 19 equations passed. The question is whether the taxonomy remains honest when exposed to algebra, substitutions, geometry, Brillouin-zone integration by parts, and an asymptotic remainder. Of 25 selected paper steps the machine report is

\[
\begin{align*}
\mathrm{machine\ ZERO} &= 19 = 13\ \mathrm{DIRECT\_EXACT} + 6\ \mathrm{SUBSTITUTION\_EXACT},\\
\mathrm{RULE\_CERTIFICATE} &= 2,\\
\mathrm{ASYMPTOTIC\ UNKNOWN} &= 1,\\
\mathrm{NONZERO} &= 0.
\end{align*}
\]

A shared local Leibniz child is a machine helper for both integration-by-parts parents and is counted among the 13 direct-exact rows; it is not an additional paper step.

Illustrative public rows, using printed equation numbers (appendix counters in this paper do not reset; local D-1 is printed D-57):

- Direct residual equality: (D-59)\(\to\)(D-60) regroup of \(K_{1A}\) is unsubstituted local algebra and returns engine zero.
- Explicit substitution: (D-66)\(\to\)(D-67) is zero given \(\varepsilon_{21}=-\varepsilon_{12}\) written into the residual. Other substitutions include a metric-velocity pair, the definition of \(\Omega_{ab}^{1}\), \(\Omega^{2}=-\Omega^{1}\), and \(f_n'=2f_{0,n}'\).
- Rule certificate: (D-114)\(\to\)(D-119) and (D-123)\(\to\)(D-124) are certified by rule with local Leibniz zero and declared Brillouin-zone torus periodicity. Without the declaration the parents would be assumption-required.
- Asymptotic unknown: (D-57) is typed as an asymptotic claim. It is not rewritten as truncated series equals the object. The remainder stays unknown.

The two non-green outputs are the most valuable soundness results. Integration by parts is not pretended to be a SymPy integral zero. The \(\Gamma\) remainder is not turned green for narrative convenience. The field validation began on frozen v0.2.0-alpha; the integration-by-parts parents were originally an encoding gap, not a mathematical dead end. The generic adapter is the v0.2.1-alpha product patch. The verifier core was not redesigned.

This is an equation-level audit and does not prove the paper or confirm its physical conclusions.

---

## 7. Related work

Computer-algebra systems evaluate symbolic expressions [2]. Computational notebooks publish code, results, and prose together [1]. Both are necessary infrastructure. Neither records, for each printed arrow in a physics supplement, whether the step was a definition, a substitution, a domain theorem, or a remainder. A notebook that prints True has the same epistemic shape as a model that prints verified.

Interactive theorem provers certify theorems in a trusted kernel [8, 11]. Retrieval-augmented language models can propose tactics to such a proof assistant [12]. That line of work is the right authority model for fully formal mathematics. It is the wrong default encoding for an existing theoretical-physics manuscript: the object to be audited is already written in LaTeX, not in a calculus of constructions. Derivation Audit is weaker than a kernel and stricter than a notebook. It does not replace Lean; it types the claims a referee actually sees.

Language models emit chains of thought [3] and solve some quantitative science problems without tools [4]. Generated text can be unfaithful [5]. Systems that matter scientifically pair generation with an external check: FunSearch searches programs under an evaluator [6]; AlphaGeometry guides a symbolic engine [7]. Our contribution is not another solver in that family. It is an audit layer for heterogeneous manuscript steps, including the steps a solver should refuse to paint green.

Scientific data stewardship emphasises machine-actionable reuse [9]. Provenance for datasets is not provenance for derivation claims. A FAIR conductivity tensor still does not tell a reviewer whether equation (D-114) to (D-119) was local algebra or a declared torus theorem.

---

## 8. Discussion

For authors, the useful artefact before submission is a derivation ledger, not the sentence that a computer-algebra system checked it. The ledger says which arrows were exact, which used a supplied identity, which invoked a declared theorem, and which remainders were left open.

For reviewers, verification ambiguity drops. A referee can read that (D-59) to (D-60) is exact algebra, that (D-114) to (D-119) is theorem-mediated, and that the (D-57) remainder is not machine-certified. Disagreement can then target the actual dependency rather than a global verified stamp.

For AI for science, the design principle is larger than symbolic algebra. Scientific AI should be allowed to propose freely, but scientific authority should remain attached to explicit, typed, reproducible evidence. Autonomy does not require self-certification. The more a model participates in a derivation, the more important it is that proposal and authority stay apart.

Limitations are in-scope boundaries. Inventory does not understand PDFs. Transcription is manual and can encode the wrong identity. Many scientifically real steps have no supported residual. Generic integrals, exact limits, and remainder proofs are out of scope. The machine-enforced assumption namespace cannot represent positivity, excluded poles, or parameter identities as assumptions. Unknown can still be misread as support by a human; the software can only refuse to emit a verified row. These limits are not an invitation to grow a twenty-rule theorem prover in order to make a methods paper look broader.

A second public manuscript, audited without changing engine semantics, would be the natural next case if it either fits the taxonomy or exposes one new generic adapter with explicit fail-closed conditions and human authorization. Unpublished local work is not that case.

---

## 9. Conclusion

The missing object in AI-assisted theoretical derivation is not another agent. It is an audit layer. Derivation Audit turns a derivation into a typed, provenance-bearing evidence graph. Neighbouring equations are not silently equalities. Certificates record dependency rather than confidence. Verified tables are generated, not authored. On a published theoretical-physics derivation the system keeps algebra, substitution, Brillouin-zone integration by parts, and an asymptotic remainder in different epistemic statuses.

An AI may propose a derivation; it may not certify itself.

---

## Acknowledgements

Public product and evidence artefacts are those tagged `derivation-audit-v0.2.1-alpha` and branched `engineering/real-paper-validation-arxiv-2511-16422` in the symbolic-compactification repository. Engineering for v0.2 is closed; this manuscript is a writing object, not a product patch.

---

## References

[1] T. Kluyver, B. Ragan-Kelley, F. Perez, B. Granger, M. Bussonnier, J. Frederic, et al., "Jupyter Notebooks – a publishing format for reproducible computational workflows," in Positioning and Power in Academic Publishing: Players, Agents and Agendas (ELPUB), IOS Press, 2016, pp. 87-90.

[2] A. Meurer, C. P. Smith, M. Paprocki, O. Certik, S. B. Kirpichev, M. Rocklin, et al., "SymPy: symbolic computing in Python," PeerJ Computer Science, vol. 3, p. e103, 2017.

[3] J. Wei, X. Wang, D. Schuurmans, M. Bosma, B. Ichter, F. Xia, E. Chi, Q. V. Le, and D. Zhou, "Chain-of-thought prompting elicits reasoning in large language models," in Proc. NeurIPS, 2022, pp. 24824-24837.

[4] A. Lewkowycz, A. Andreassen, D. Dohan, E. Dyer, H. Michalewski, V. Ramasesh, et al., "Solving quantitative reasoning problems with language models," in Proc. NeurIPS, 2022, pp. 3843-3857; arXiv:2206.14858.

[5] Z. Ji, N. Lee, R. Frieske, T. Yu, D. Su, Y. Xu, E. Ishii, Y. Bang, A. Madotto, and P. Fung, "Survey of hallucination in natural language generation," ACM Computing Surveys, vol. 55, no. 12, Art. 248, 2023.

[6] B. Romera-Paredes, M. Barekatain, A. Novikov, M. Balog, M. P. Kumar, E. Dupont, et al., "Mathematical discoveries from program search with large language models," Nature, vol. 625, pp. 468-475, 2024.

[7] T. H. Trinh, Y. Wu, Q. V. Le, H. He, and T. Luong, "Solving olympiad geometry without human demonstrations," Nature, vol. 625, pp. 476-482, 2024.

[8] L. de Moura, S. Kong, J. Avigad, F. van Doorn, and J. von Raumer, "The Lean theorem prover (system description)," in Proc. CADE-25, LNCS 9195, Springer, 2015, pp. 378-388.

[9] M. D. Wilkinson, M. Dumontier, I. J. Aalbersberg, et al., "The FAIR Guiding Principles for scientific data management and stewardship," Scientific Data, vol. 3, p. 160018, 2016.

[10] Z. Guo, X.-Y. Liu, H. Wang, L.-k. Shi, and K. Chang, "Dissipation-shaped quantum geometry in nonlinear transport," Phys. Rev. Lett., vol. 136, p. 206303, 2026; arXiv:2511.16422v2.

[11] T. Nipkow, L. C. Paulson, and M. Wenzel, Isabelle/HOL: A Proof Assistant for Higher-Order Logic, LNCS 2283. Springer, 2002.

[12] K. Yang, A. M. Swope, A. Gu, R. Chalamala, P. Song, S. Yu, S. Godil, R. J. Prenger, and A. Anandkumar, "LeanDojo: theorem proving with retrieval-augmented language models," in Proc. NeurIPS, 2023, pp. 21573-21612.
