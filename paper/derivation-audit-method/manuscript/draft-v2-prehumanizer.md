# Verified Symbolic Reasoning for Theoretical Physics through Typed Evidence Graphs

From stepwise derivation to manuscript audit

---

## Abstract

Theoretical physics uses two complementary symbolic workflows. While a calculation is in progress, a researcher must decide which candidate transformation of a long expression is safe to accept. After the calculation is written down, a reader must decide which printed steps are actually supported. Computer algebra, notebooks, and experimental language-model proposers participate in both jobs, but they often treat proposal, execution, and certification as the same act, and they collapse algebra, substitution, definition, global theorems, and asymptotics into a generic equality. This paper describes one verified symbolic-reasoning framework whose shared object is a typed evidence graph. Each edge is a claim \(\gamma=(e_{\mathrm{from}},e_{\mathrm{to}},\tau,\rho,A)\) with a scientific step type \(\tau\), an optional executable residual \(\rho\), and declared assumptions \(A\). Claim semantics and certificate provenance are different axes: algebraic equivalence is a type of move, while `DIRECT_EXACT` is a kind of support. Candidates may be supplied by a human, a rule, or an experimental AI proposer. They advance a derivation, or enter a reviewer-facing verified table, only after independent fail-closed evidence. Forward Mode is a supported verification-gated workflow plus an experimental proposal surface; it is not a demonstration of autonomous representation invention. Retrospective Audit is the mature application: parallel typing of an existing path, including theorem-mediated Brillouin-zone integration by parts as `CERTIFIED_BY_RULE` rather than engine `ZERO`. Under the implemented threat model, tested narrative and record manipulations cannot populate the machine-verified table. A formative field validation on Guo et al., Phys. Rev. Lett. 136, 206303 (2026), shows that heterogeneous steps retain distinct epistemic states. The system does not prove a paper or confirm physical conclusions. An AI may propose a derivation; it may not certify itself.

---

## 1. Introduction

A working theoretical physicist repeatedly faces two concrete tasks. During a derivation the current object is a long expression together with papers, notes, assumptions, and a scientific objective, and the question is which transformation to try next: a regrouping, a substitution, a symmetry reduction, a change of representation, or the introduction of an auxiliary object. After the derivation is written, the object is a published path of displayed formulae, and the question is which of those arrows are locally exact, which depend on a declared identity or a global theorem, and which are remainders that the engine cannot certify. Both tasks already mix handwritten algebra with computer-algebra systems that theoretical physics has used for decades [1, 2, 3] and with computational notebooks that store code, results, and explanation in one document [4]. Language models are beginning to propose intermediate steps. The difficulty is not that these tools exist. It is that the two tasks still lack a shared, machine-auditable evidence contract.

Current workflows are inadequate in three related ways. First, candidate generation and certification are often the same act. A notebook cell that returns true, a CAS session that simplifies an expression, or a fluent model trace that writes "verified" is treated as evidence that a scientific state may advance. The producer/checker split is old in computer science: proof-carrying code already required an untrusted producer to supply a checkable certificate [5], hidden verification placed a trusted checker behind computer-algebra output [6], and SAT-plus-computer-algebra tools have been used to verify multiplier circuits [7]. Scientific workflow provenance records what ran [8]. Those lines of work do not, by themselves, stop a physics notebook or a model trace from conflating proposal with authority. Second, heterogeneous scientific operations are collapsed into a generic equality. Neighbouring displayed formulae may be a definition, a local identity, a substitution, a Brillouin-zone integration by parts, or an asymptotic remainder. Interactive proof assistants certify fully specified formal proofs in a trusted kernel [9, 10], and language-model provers can propose tactics or terms that a kernel or a symbolic engine then checks [11, 12, 13]. That is a different object from the manuscript a condensed-matter theorist actually writes. Third, constructive derivation and retrospective checking do not share an evidence representation. A step that was gated while working is not automatically the same object a reviewer later inspects. FAIR principles make data findable [14]; they do not type derivation arrows.

The two tasks are the same graph problem in opposite directions. Forward Mode constructs an evidence-backed path: from a current expression \(E_t\) and context, candidates \(\{H_i\}\) are proposed, grounded, compiled, and judged, and only an admissible candidate may become \(E_{t+1}\). Retrospective Audit inspects an existing path \(E_1\to\cdots\to E_N\): equations are inventoried, edges are typed, independent obligations are verified in parallel, and reviewer tables are generated. Our goal is not a stronger solver and not a general theorem prover. It is a verified symbolic-reasoning method in which both workflows operate on one typed evidence graph, proposal remains untrusted, and fail-closed evidence is the only authority that may promote scientific state or fill a verified table.

Three obstacles follow from implementing that idea. A naive extension of a CAS or a notebook does not meet them. The first is representational: a candidate must be recorded as a scientific claim without granting the proposer (human, rule, or model) the power to install it as accepted state. The second is compilation: heterogeneous transformations cannot all be rewritten as \(lhs-rhs=0\) without producing either a fake zero or an uninformative unknown. Coefficient agreement is not a remainder proof; inability of a CAS to encode a step is not a mathematical falsehood; a global theorem is not a local symbolic `ZERO`. The third is dual execution: iterative state advancement and parallel manuscript audit must use the same edge semantics, the same status tokens, and the same inclusion functions, or the "shared graph" is only a slogan.

We use a typed evidence graph whose edges are claims \(\gamma=(e_{\mathrm{from}},e_{\mathrm{to}},\tau,\rho,A)\), with scientific type \(\tau\), optional residual \(\rho\), and declared assumptions \(A\) (Sections 2 and 3). Certificate provenance is a second axis: `DIRECT_EXACT`, `SUBSTITUTION_EXACT`, `RULE_CERTIFICATE`, structural records, and `UNKNOWN` describe what a conclusion depends on, not a ranking of truth. Engine adjudication `{ZERO, NONZERO, UNKNOWN}` is not itself a certificate class, and engine `ZERO` is never `CERTIFIED_BY_RULE`. Forward Mode grounds and verifies untrusted candidates before promotion (Section 4). Retrospective Audit inventories a manuscript, verifies independent edges in parallel, and generates reviewer tables from integrity-bound records (Section 5). Implementation binds source, obligation, and result by hashes; Markdown cannot create certified status (Section 6). Figure 1 is the conceptual overview.

We summarise our contributions as follows. (1) We formulate constructive symbolic derivation and retrospective manuscript audit as operations on one typed evidence graph (Sections 2–3). (2) We give fail-closed evidence semantics that separate claim type from certificate provenance and preserve the invariant that engine `ZERO` is not a rule certificate (Section 3). (3) We describe verification-gated iterative derivation: candidates may come from humans, rules, or an experimental AI proposer, but state advancement requires independent evidence. Public Forward Mode evidence is a supported verification path plus an experimental proposal surface, not autonomous discovery (Section 4). (4) We show that existing paths can be typed and audited edge-by-edge, with generated reviewer tables, and we report a formative field validation on a published theoretical-physics derivation [15] rather than a held-out generalisation benchmark (Sections 5 and 7). Three evaluation questions follow: whether untrusted candidates are gated before they become accepted state; whether tested narrative and record manipulations can populate the verified table; and whether the same framework can represent a heterogeneous published derivation without collapsing unsupported steps into false certificates.

---

## 2. Problem formulation: one evidence graph, two workflows

The basic mistake is to treat a derivation as a sequence of displayed equations \(e_1,e_2,\ldots,e_n\) together with the implicit claim that each consecutive pair is the same kind of equality, and to treat a working session as a sequence of CAS rewrites whose last simplified form is the new scientific state. In theoretical physics the actual object is a typed graph. While working, the graph is being grown. After publication, the graph already exists and must be inspected.

Forward Mode starts from a current expression \(E_t\) and a context of references, notes, and declared assumptions. A proposer, which may be a human, a named rule, or an experimental model, emits candidate next transformations \(H_1,H_2,\ldots\). Each candidate is untrusted. It must be grounded to named sources, compiled to an explicit obligation where that compilation is honest, and judged by a fail-closed verifier. Only then may it become \(E_{t+1}\). Conceptually:

\[
E_t+\text{context}\ \to\ \{H_i\}\ \to\ \text{typed grounding}\ \to\ \text{verification}\ \to\ \text{typed outcome}\ \to\ E_{t+1}.
\]

The scientific principle is that proposal authority is not verification authority, and that the absence of a certificate is the absence of promotion.

Retrospective Audit starts from an already written path \(E_1\to\cdots\to E_N\). The system inventories equations, records typed edges, grounds those edges, compiles executable obligations where the type permits, verifies independent obligations in parallel, preserves theorem-mediated, structural, and unknown statuses, and generates reviewer-facing tables. The output is not a single pass/fail bit for the manuscript. It is a typed record of which transitions are locally exact, substitution-conditioned, rule-certified, structural, unknown, or refuted.

Both modes operate on the same scientific object: a derivation edge

\[
\gamma=(e_{\mathrm{from}},e_{\mathrm{to}},\tau,\rho,A),
\]

where \(\tau\) is the scientific step type, \(\rho\) is an optional executable residual, and \(A\) is a declared assumption set. In the implementation this tuple is realised as an audit edge with `source_from`, `source_to`, `edge_type`, `residual`, and `assumptions_used`, plus rule and domain fields for theorem-mediated steps. The paper uses \(\gamma\) as the shared mathematical object; the code is a realisation, not a second semantics.

Two distinct axes sit on every edge. Claim semantics \(\tau\) answers "what move is being claimed?" Certificate provenance \(c\) answers "what supports it?" Engine adjudication answers a third question: did the deterministic verifier return `ZERO`, `NONZERO`, or `UNKNOWN` on an executable residual? Mixing the three axes is how false certification and false refutation arise. Figure 1 draws the two workflows against the shared graph. Figure 2 draws the two axes.

---

## 3. Typed evidence graph

### 3.1 Claim semantics

Inventory extracts labels, environments, order, and source ranges. It does not interpret LaTeX as algebra. Native-text members are researcher-authored transcriptions of the identities that will be checked. That transcription is a stated limitation.

The type catalogue is frozen and narrow. Algebraic equivalence, index relabeling, pairwise reduction, projector identities, and divided differences may lower to a local residual. Definition insertion is a name introduction, not a proof. A split parent delegates to children and is never itself an engine `ZERO`. An asymptotic claim is a remainder, not a truncated series set equal to the original object. A generic integral argument is not a local residual. Brillouin-zone periodic integration by parts is a typed global step with a local Leibniz child. Selection uses the most specific type that matches the scientific claim. If no residual exists, the honest status is `NOT_LOWERED` or `UNKNOWN`, not a nearby algebraic encoding.

Examples that matter for the two axes:

- `ALGEBRAIC_EQUIVALENCE` is a claim type. It may later receive `DIRECT_EXACT` or `SUBSTITUTION_EXACT` provenance if the engine returns `ZERO`.
- `BZ_PERIODIC_INTEGRATION_BY_PARTS` is a claim type. It may receive `RULE_CERTIFICATE` provenance. It must not receive engine `ZERO`.
- `ASYMPTOTIC_CLAIM` is a claim type. Finite coefficient children may be `ZERO`; the parent remains `UNKNOWN` without a remainder certificate.
- `DEFINITION_INSERTION` is a claim type. Its honest provenance is structural, not an exact identity.

### 3.2 Certificate provenance

The output of either mode is not pass or fail. It is certificate provenance: a record of what the conclusion depends on.

An engine certificate is an executable residual \(r\) that a deterministic exact verifier simplifies to zero under the recorded route, namespace, and assumptions, or that an exact probe proves nonzero, or that it cannot decide. Direct exactness means the residual was not rewritten by an upstream identity that the assumption language cannot enforce:

\[
R=0.
\]

Substitution exactness means the residual is zero after a declared identity is written in, for example

\[
R\big|_{\varepsilon_{21}=-\varepsilon_{12}}=0.
\]

The tool then tells the reviewer that the downstream algebra is exact and that the upstream identity was supplied. It does not independently prove \(\varepsilon_{21}=-\varepsilon_{12}\).

A rule certificate combines a local engine certificate with a declared theorem and domain. Brillouin-zone integration by parts is the motivating case. The local Leibniz product rule is a residual and may be engine `ZERO`,

\[
\partial_k(uv)-u'v-uv'=0,
\]

while the parent claims that the integral of a total \(k\)-derivative over the Brillouin-zone torus vanishes. That parent is `CERTIFIED_BY_RULE` when the local child is integrity-ok `ZERO` and `BZ_TORUS_PERIODICITY` is declared on domain `BRILLOUIN_ZONE_TORUS`. The computer-algebra engine did not evaluate the integral. Without the declared rule the parent is `ASSUMPTION_REQUIRED`. The certificate is conditional on the declared theorem. It is not a ranking that "rule certificates are weaker than engine zeros" or the reverse.

Structural records (`DEFINITION`, `RECORDED`, `SPLIT`, `CERTIFIED_BY_CHILDREN`) track non-executable or delegated claims. `UNKNOWN` is a valid engine result: no proof either way, and not permission to advance.

Certificate class describes provenance, not a hierarchy of mathematical truth. `DIRECT_EXACT`, `SUBSTITUTION_EXACT`, and `RULE_CERTIFICATE` tell a reader what the conclusion depends on.

### 3.3 Fail-closed status semantics

The verifier fails closed. Numeric tolerance, model confidence, and fluent prose never replace an engine result. Two fields sit on each evidence record: `result` (engine/adjudication outcome) and `status` (typed derivation-audit status).

Engine results include `ZERO`, `NONZERO`, `UNKNOWN`, `ASSUMPTION_REQUIRED`, `PARSE_FAILURE`, `COMPILE_FAILURE`, `GROUNDING_FAILURE`, and `INVALID_RECORD`. `ZERO` certifies only the submitted residual under the recorded route. It does not certify novelty, physical usefulness, or the rest of a manuscript. `UNKNOWN` is not likely true, likely false, partial success, or permission to promote.

A row may enter the machine-verified table only when `status` and `result` are both `ZERO`, the record is executable and integrity-ok, and the edge is not a split parent, an asymptotic claim, or a Brillouin-zone IBP parent. `CERTIFIED_BY_RULE` is excluded from that table by construction. Markdown `ZERO` is ignored. The inclusion functions in `schema.py` are normative; user-facing Markdown is descriptive. Appendix B records the inclusion contract.

Rule growth is field-driven. The present catalogue contains one named global rule, `BZ_TORUS_PERIODICITY`. TRACE_CYCLICITY, STOKES, HERMITICITY, and COMPLETENESS are not pre-loaded. A new named rule is added only when a real public derivation exposes a missing adapter with explicit fail-closed conditions.

---

## 4. Forward symbolic derivation

Forward Mode is the constructive workflow: grow an evidence-backed path from a current expression. The public product still supports the v0.1 Mode A surface (`init` / `inspect` / `verify` / `report`) as researcher-supplied hypothesis verification, and a compatibility session surface (`init-session` / `step` / `summary` / `finalize`) in which `step` promotes only on `ZERO`. Model-assisted proposal is experimental and never bypasses the same verifier.

### 4.1 Context and candidate generation

The researcher supplies the current expression, declared symbols and functions, an assumptions file, optional notes, and optional reference excerpts. The alpha assumption language is deliberately small: symbols are `real: true`, may be `nonzero`, and undefined functions must be named. Positivity, general inequalities, excluded poles, parameter identities, boundary conditions, symmetries, and limit order cannot be represented or enforced. Putting such a predicate in notes does not make it operational.

Candidates may include algebraic regrouping, substitution, pairwise cancellation, divided differences, coefficient extraction, a change of representation, or a structural observation. Structural observations are retained as non-proof context. They never certify equivalence without a separate `ZERO`.

The proposer may be a human editing `hypotheses/hypothesis.json` or a candidate file, a scripted proposer in tests, or an experimental model interface. In all cases the candidate is recorded as a hypothesis. The implementation forces proposal status to `HYPOTHESIS` and rejects a self-declared `CERTIFIED` claim on a candidate.

### 4.2 Candidate grounding

A candidate must bind to named source files. Grounding failure is not a mathematical `NONZERO`. Compilation failure means the claim cannot be lowered to a supported obligation without changing its meaning; the tool stops rather than guessing a nearby relation. `ASSUMPTION_REQUIRED` in this workflow detects a declaration mismatch (`assumptions_used` missing or omitting a declared symbol). It does not discover which physical assumptions a formula needs.

This compilation step is where honest typing happens in Forward Mode. A remainder must not be rewritten as \(F-A/\Gamma=0\). A global integral must not be rewritten as a local residual. A definition must not be submitted as an exact identity.

### 4.3 Verification-gated state advancement

The deterministic verifier, route `python_sympy_exact_v1`, engine version `0.3.0`, is the only judge. On the workspace façade, sources are never rewritten; runs live under `runs/`. On the session façade, promotion into `session.current` requires a last-step `ZERO` together with matching hashes and texts. `NONZERO` and `UNKNOWN` leave the current expression unchanged. A proposal record cannot promote. A later `ZERO` on a different candidate cannot be used to install an unmatched expression (`CANDIDATE_STATE_MISMATCH`).

The schematic that RQ1 tests is therefore:

- candidate A \(\to\) `ZERO` \(\to\) admissible
- candidate B \(\to\) `NONZERO` \(\to\) rejected, \(E_t\) unchanged
- candidate C \(\to\) `UNKNOWN` \(\to\) recorded, not promoted

No certificate means no scientific-state promotion.

### 4.4 Explicit capability boundary of the proposer

The public project records that AI-assisted proposal generation and context-conditioned hypothesis generation are experimental. Proposer text can never promote scientific state. Robust mathematical representation invention is unestablished. The representation-discovery campaign closed with insufficient adjudicable real tasks; that closure is not a measured zero success rate for language models, and it is not a Forward Mode gating failure.

Consequently this paper describes Forward Mode at the strongest level the public evidence supports: a verified iterative symbolic-reasoning workflow in which candidates may be supplied by a human, rules, or an AI proposer, but advancement requires independent evidence. It does not claim that a language model reliably discovers the correct next mathematical representation. It does not claim a shipped workspace-level `propose` command. References are ingested as paths, notes, curated excerpts, or metadata, not as full-paper retrieval-augmented generation.

---

## 5. Retrospective manuscript audit

Retrospective Audit is the mature real-paper application. The path already exists. The system types and checks it.

### 5.1 Equation inventory

`audit inventory` extracts labelled environments, order, and source ranges from a manuscript source. Counts produced by inventory are not scientific evidence. Native-text residuals are researcher-transcribed. Two independent read-only reviewers checked the public Guo transcription against the public source and were forbidden from assigning `ZERO`.

### 5.2 Parallel edge verification

Edges are declared with types from the frozen catalogue. Supported edges lower to executable residuals and are judged independently. Parallelism is a property of independent obligations, not a claim that the manuscript is a proof DAG in a kernel. Changing source, residual, or assumptions produces a new snapshot; prior `ZERO` rows do not transfer silently.

### 5.3 Rule certificates and structural steps

When a published step is a Brillouin-zone integration by parts, the parent is typed `BZ_PERIODIC_INTEGRATION_BY_PARTS`. A local Leibniz child may be engine `ZERO`. The parent becomes `CERTIFIED_BY_RULE` only with the declared torus-periodicity rule. Definitions, bookkeeping, and split parents remain structural. An asymptotic remainder remains `UNKNOWN`. These non-green statuses are part of the method, not a failure to maximise a pass count.

### 5.4 Generated reviewer evidence

Commands `audit table`, `audit report`, and `audit package` generate four buckets from a recorded run: verified, nonzero, structural, and uncertified. The verified table is generated, not authored. A reviewer package includes `reproduce.sh`. Inclusion uses `schema.may_appear_in_verified_table` and `schema.table_bucket` only.

---

## 6. Authority, integrity, and implementation

### 6.1 Proposal is not authority

The authority chain is source \(\to\) edge \(\to\) obligation \(\to\) verifier \(\to\) integrity-bound record \(\to\) generated table or promoted state. A language model, a human sentence, and a Markdown table are all proposers relative to that chain. Language-model provers that propose tactics a kernel or symbolic engine then checks [11, 12, 13] already separate proposal from checking inside other objects. The present framework applies the same split to a physicist's current expression and to printed manuscript arrows, with `UNKNOWN` retained as a non-promotable outcome.

### 6.2 Provenance-bound records

Records bind source bytes, residual bytes, assumptions, obligation identity, verifier route, and result. Mutation of source, residual, or assumptions changes certificate identity. Forged `ZERO` JSON without residual, obligation, and assumptions hashes fails integrity.

### 6.3 Generated-not-authored tables

LLM text cannot create verified status. The verified table is generated, not authored. Relabeling `UNKNOWN` as `ZERO` is rejected (`STATUS_ZERO_REQUIRES_ENGINE_ZERO`). Hiding `NONZERO` by editing Markdown does not survive regeneration. An uncertified split child blocks parent certification. An asymptotic truncation cannot become exact equality. A BZ IBP parent cannot become engine `ZERO`.

### 6.4 Reproducibility

The public product is Derivation Audit Alpha `0.2.1-alpha` (PEP 440 `0.2.1a0`) on annotated tag `derivation-audit-v0.2.1-alpha`, which peels commit `783ec64c0bb4ffd0b4b6ad33f33ead96dba49087`. Engine version `0.3.0` is unchanged from v0.2.0. Audit protocol version is `0.2.1`. The historical v0.2.0 tag peels `aaf1199eb6d8c471589948e1dcdaeeffe2945025` and is not moved. Public Guo evidence lives on a separate branch at `69ad474a43ebea55cb2e524934d982e518db026b` and is not a product tag. Core verification requires no model service. Mode A release-critical tests are documented as 17/17; derivation-audit release-critical tests as 14/14; BZ IBP adapter tests as 5/5. The historical full suite is disclosed as not fully green and is not rewritten to make a release.

---

## 7. Evaluation

This section does not report a benchmark accuracy. It answers three questions with existing public evidence.

### RQ1. Can untrusted candidate transformations be safely gated before advancing a symbolic derivation?

The question is not whether an AI discovers the right representation. It is whether, given candidates, the workflow prevents uncertified candidates from silently becoming accepted scientific state.

Public Mode A demos are researcher-supplied, one-shot hypotheses with no proposer in the loop [release demos]. Demo A is an algebraic factorization \(x^2+2x+1\) versus \((x+1)^2\) and returns `ZERO`. Demo B is one fixed, denominator-safe Newton divided-difference instance and returns `ZERO`; the notes forbid reading it as search success or AI discovery. Demo C is a frozen polygamma recurrence gap and returns `UNKNOWN`; the workspace states that no scientific state may be promoted. An external installed replay mutates the Demo A candidate to \((x+1)^2+1\) and records `NONZERO` with residual \(-1\) and counterexample \(x=-2\). Parse, compile, and omitted-assumption gates execute no obligations.

Multi-candidate promotion is shown by the session protocol tests with a scripted proposer, not a live model. In CASE B the current expression is \(x^2+2x+1\). A wrong candidate \(x^2+2x-1\) returns `NONZERO` and does not promote. A subsequent correct candidate \((x+1)^2\) returns `ZERO` and may promote. Proposal records themselves remain hypotheses and cannot promote. Hash mismatch between a `ZERO` step and a different candidate blocks promotion.

Figure 3 draws that gate. The honest conclusion is that the implemented workflow records uncertified candidates and does not install them as accepted state. It is not a conclusion that the proposer finds the next scientific representation. There is no committed multi-step constructive-derivation demo workspace on a published physics calculation.

### RQ2. Does the evidence layer remain fail-closed under attempted narrative or record manipulation?

The implemented threat model includes authored Markdown `ZERO`, incomplete or forged records, source mutation, assumption mutation, residual mutation, relabeling `UNKNOWN` as `ZERO`, hiding `NONZERO` by editing Markdown, uncertified split children, encoding an asymptotic truncation as exact equality, and labeling a BZ IBP parent as engine `ZERO`. Public tests in `test_audit_adversarial.py` and `test_audit_bz_ibp.py` address those cases.

Under that threat model, the tested narrative and record manipulations cannot populate the machine-verified table. This paper does not claim that all conceivable forgery is impossible. Manual transcription can still encode the wrong identity, detected as `NONZERO` or missed if both sides are wrong in the same way.

### RQ3. Can the same evidence framework audit a heterogeneous published theoretical-physics derivation?

Guo et al., "Dissipation-Shaped Quantum Geometry in Nonlinear Transport," Phys. Rev. Lett. 136, 206303 (2026), arXiv:2511.16422v2 [15], is a formative real-paper field validation, not an independent held-out generalisation benchmark. The historical lineage is explicit: tagged v0.2.0-alpha could only mark Brillouin-zone integration by parts as `NOT_LOWERED`; the public validation exposed that encoding gap; v0.2.1-alpha added a generic BZ IBP adapter. The verifier core was not redesigned.

The audit selected 25 paper steps from 189 numbered public equations. Of those 25 steps, 18 paper-level identities received engine `ZERO`: 12 `DIRECT_EXACT` and 6 `SUBSTITUTION_EXACT`. Two steps received `RULE_CERTIFICATE` (printed (D-114)\(\to\)(D-119) and (D-123)\(\to\)(D-124)). One asymptotic claim remained `UNKNOWN` (printed (D-57), the \(\Gamma\) remainder). Four steps were structural records. A shared local Leibniz helper used by the two IBP parents adds one additional `DIRECT_EXACT` machine `ZERO` that is not a selected paper step. The complete machine run therefore contains 19 `ZERO` records (13 `DIRECT_EXACT` including the helper, and 6 `SUBSTITUTION_EXACT`). No selected step returned `NONZERO`. Appendix A repeats this arithmetic. Do not mix 25 selected paper steps with 19 complete-run `ZERO` records as if the helper were another paper step.

The edge set was frozen before adjudication. Predictions in the frozen edge file are not verification authority. Residuals were not retuned after engine execution to manufacture `ZERO`. The headline result is not "19 equations passed." The headline is that the same evidence system preserved distinct epistemic states on a real heterogeneous theoretical derivation. The two most informative non-green results, BZ IBP as `CERTIFIED_BY_RULE` and the \(\Gamma\) remainder as `UNKNOWN`, are soundness evidence. Figure 4 draws a short path containing those classes.

This is an equation-level audit. It does not prove Guo et al. and does not confirm its physical conclusions.

---

## 8. Related work

We organise prior work by what it certifies, not by chronology. The novelty claim is not that an untrusted producer needs a checker.

Computer algebra is the working substrate of much theoretical calculation. General-purpose systems and physics-facing packages simplify tensor expressions, gamma-matrix algebra, and component calculations [1, 2, 3]. They evaluate expressions. They do not type manuscript arrows, they do not generate reviewer tables from integrity-bound records, and they do not gate promotion of a current scientific expression.

Proof assistants certify fully specified proofs in a trusted kernel [9, 10]. Language models can propose tactics, premises, or whole proof steps that the kernel checks [11, 13]. Encoding a long condensed-matter supplement into a kernel is a different scientific object from asking, for each printed arrow, what was claimed and what was checked.

Proof-carrying code [5], hidden verification of computer-algebra output [6], and computer-algebra verification of multipliers that combines SAT solving with Gröbner techniques [7] are the closest producer/checker lineage. We use that lineage rather than claiming to invent it. Those certificates validate a program, a CAS result, or a circuit identity. They are not manuscript-native, and they do not distinguish claim type from certificate provenance on a physics derivation edge.

Scientific workflow provenance [8] and notebook publishing formats [4, 16] record execution history. A cell that ran is not a typed derivation certificate. Notebook provenance is often incomplete because cells are reordered or deleted [16]. FAIR principles [14] concern findable data, not epistemic type of derivation steps.

Language-model mathematical search, including GPT-f [11], AlphaGeometry [12], and Lean copilots [17], already uses an external checker. HepLean digitalises definitions and theorems of high-energy physics in Lean [18]. The present work uses the same split on a different object: a physicist's current expression and a printed manuscript path, with fail-closed `UNKNOWN` and theorem-mediated statuses that a kernel proof does not need because the kernel does not accept an untyped remainder.

The Physics Derivation Graph is the closest adjacent software project: a graph of physics expressions linked by inference rules, some of which are checked by a CAS. No peer-reviewed article with stable bibliographic metadata was found in this literature pass, so we treat it as a named project rather than as a journal citation. Its aim is a global graph of mathematical physics with atomic inference rules. Our aim is manuscript-native typing of heterogeneous steps as they are written, two-axis provenance, generated reviewer tables, and verification-gated forward promotion. We do not attempt to document all of physics.

Table 5 summarises the comparison. The difference axes we defend are: a shared evidence graph for constructive derivation and retrospective audit; explicit separation of claim semantics from certificate provenance; fail-closed state promotion in symbolic scientific reasoning; and reviewer-facing generated evidence attached to printed derivation steps.

---

## 9. Discussion and limitations

For authors, the framework is a ledger. A candidate may be tried freely. Only integrity-bound `ZERO` changes accepted state or fills the verified table. Substitution-conditioned zeros should be labelled as such, so a later reader can see the upstream identity.

For reviewers, the useful output is typed disagreement. `CERTIFIED_BY_RULE` is easy to over-read as "the integral was checked." It means: local Leibniz `ZERO` plus a declared torus theorem. `UNKNOWN` is easy to over-read as support or as refutation. It is neither.

For AI-for-science, the operational rule is simple. A model may propose the next transformation or a candidate residual. It may not write the verified table and it may not promote `session.current`. Pairing a language model with an external evaluator is already standard in formal mathematics [11, 12, 13]. The missing piece in theoretical-physics manuscripts has been a typed evidence object that can serve both the working session and the later audit.

Limitations are specific. Forward Mode's public demos are one-shot researcher hypotheses; multi-candidate evidence uses a scripted proposer. Representation invention is unestablished. Inventory does not parse LaTeX as algebra. Transcription can be wrong. Generic integrals remain `NOT_LOWERED`. Remainder certification is unsupported. Parameter identities cannot be machine assumptions. Complex-domain certification is rejected. The system does not prove physical conclusions and does not understand PDFs. Guo is formative: the BZ IBP adapter was added because that paper needed it, so the case cannot be sold as independent generalisation to unseen manuscripts. Unpublished local scientific manuscripts are excluded from this public paper.

The verifier is the authority layer that makes both workflows trustworthy. It is not the scientific goal. The scientific goal is a derivation whose steps carry explicit evidence, whether those steps are being constructed or being reread.

---

## 10. Conclusion

Theoretical physics has two complementary symbolic workflows: constructing a derivation and auditing an existing one. We represented both as operations on one typed evidence graph, with an untrusted proposal layer and an independent fail-closed authority layer. Claim semantics and certificate provenance are different axes. Engine `ZERO` is never `CERTIFIED_BY_RULE`. Candidates may be proposed freely; they advance a derivation, or enter a reviewer-facing verified table, only through explicit evidence. Forward Mode is a supported gated workflow plus an experimental proposer, not autonomous discovery. Retrospective Audit preserves heterogeneous statuses on a published derivation, including the informative non-green cases. An AI may propose a derivation; it may not certify itself.

---

## Acknowledgements

Product tag `derivation-audit-v0.2.1-alpha` and public evidence commit `69ad474` are the frozen authorities for this manuscript. Engineering remains closed.

---

## References

[1] M. A. H. MacCallum, "Computer algebra in gravity research," Living Rev. Relativ., vol. 21, no. 1, p. 6, 2018.

[2] A. Meurer et al., "SymPy: symbolic computing in Python," PeerJ Comput. Sci., vol. 3, p. e103, 2017.

[3] K. Peeters, "Cadabra: a field-theory motivated symbolic computer algebra system," Comput. Phys. Commun., vol. 176, no. 8, pp. 550–558, 2007.

[4] T. Kluyver et al., "Jupyter Notebooks — a publishing format for reproducible computational workflows," in Positioning and Power in Academic Publishing: Players, Agents and Agendas, 2016, pp. 87–90.

[5] G. C. Necula, "Proof-carrying code," in Proc. POPL, 1997, pp. 106–119.

[6] H. Gottliebsen, T. Kelsey, and U. Martin, "Hidden verification for computational mathematics," J. Symbolic Comput., vol. 39, no. 5, pp. 539–567, 2005.

[7] D. Kaufmann and A. Biere, "Improving AMulet2 for verifying multiplier circuits using SAT solving and computer algebra," Int. J. Softw. Tools Technol. Transfer, vol. 25, no. 2, pp. 133–144, 2023.

[8] L. Moreau, B. Ludäscher, et al., "The First Provenance Challenge," Concurr. Comput. Pract. Exp., vol. 20, no. 5, pp. 409–418, 2008.

[9] L. de Moura and S. Ullrich, "The Lean 4 theorem prover and programming language," in Proc. CADE-28, 2021.

[10] T. Nipkow, L. C. Paulson, and M. Wenzel, Isabelle/HOL: A Proof Assistant for Higher-Order Logic. Berlin: Springer, 2002.

[11] S. Polu and I. Sutskever, "Generative language modeling for automated theorem proving," arXiv:2009.03393, 2020.

[12] T. H. Trinh, Y. Wu, Q. V. Le, H. He, and T. Luong, "Solving olympiad geometry without human demonstrations," Nature, vol. 625, pp. 476–482, 2024.

[13] K. Yang et al., "LeanDojo: theorem proving with retrieval-augmented language models," in Proc. NeurIPS, 2023.

[14] M. D. Wilkinson et al., "The FAIR Guiding Principles for scientific data management and stewardship," Sci. Data, vol. 3, p. 160018, 2016.

[15] Z. Guo, X.-Y. Liu, H. Wang, L.-k. Shi, and K. Chang, "Dissipation-shaped quantum geometry in nonlinear transport," Phys. Rev. Lett., vol. 136, p. 206303, 2026, arXiv:2511.16422v2.

[16] D. Koop, "Notebook archaeology: inferring provenance from computational notebooks," in Provenance and Annotation of Data and Processes (IPAW), LNCS 12839, 2021, pp. 109–126.

[17] P. Song, K. Yang, and A. Anandkumar, "Lean Copilot: large language models as copilots for theorem proving in Lean," arXiv:2404.12534, 2024.

[18] J. Tooby-Smith, "HepLean: digitalising high energy physics," arXiv:2405.08863, 2024.

---

## Appendix A. Guo accounting

Selected paper steps: 25, drawn from 189 numbered public equations.

Paper-level engine-`ZERO` identities: 18.

- `DIRECT_EXACT`: 12
- `SUBSTITUTION_EXACT`: 6

`RULE_CERTIFICATE`: 2 (BZ periodic IBP parents).

Asymptotic `UNKNOWN`: 1 (printed (D-57)).

Structural records: 4.

Shared Leibniz helper, used by both IBP parents, not a selected paper step: +1 `DIRECT_EXACT` machine `ZERO`.

Complete-run `ZERO` records: 19 = 13 `DIRECT_EXACT` + 6 `SUBSTITUTION_EXACT`.

`NONZERO`: 0.

Illustrative printed steps: (D-59)\(\to\)(D-60) regroup, `DIRECT_EXACT`; (D-66)\(\to\)(D-67) with \(\varepsilon_{21}=-\varepsilon_{12}\), `SUBSTITUTION_EXACT`; (D-114)\(\to\)(D-119) BZ IBP, `RULE_CERTIFICATE`; (D-57) \(\Gamma\) remainder, `UNKNOWN`.

Lineage: v0.2.0-alpha \(\to\) Guo field validation exposes BZ-IBP encoding gap \(\to\) generic v0.2.1 adapter. Formative, not held-out.

---

## Appendix B. Normative inclusion (`schema.py`)

The file `src/symbolic_compactification/audit/schema.py` is the inclusion authority. User-facing Markdown in `docs/STATUS_SEMANTICS.md` is descriptive. If they disagree, the schema wins.

`may_appear_in_verified_table` requires all of: integrity-ok; `result == status == ZERO`; executable; edge type not `SPLIT_PARENT`, `ASYMPTOTIC_CLAIM`, or `BZ_PERIODIC_INTEGRATION_BY_PARTS`; status not `CERTIFIED_BY_RULE`.

`table_bucket` assigns exactly one of `TABLE_VERIFIED`, `TABLE_NONZERO`, `TABLE_STRUCTURAL`, `TABLE_UNCERTIFIED`. Integrity failure always buckets as uncertified, even if labels say `ZERO`.

`CERTIFIED_BY_RULE` is a structural status. It is never shown as engine `ZERO`.
