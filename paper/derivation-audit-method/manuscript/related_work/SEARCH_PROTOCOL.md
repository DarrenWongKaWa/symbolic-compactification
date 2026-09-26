# Related Work search protocol — RELATED_WORK_REAUDIT_V1

Frozen **before** source selection. Do not add papers because they were
already in `draft-v3`. Do not search until this file exists.

Campaign: `RELATED_WORK_REAUDIT_V1`
Paper object: typed evidence graph; Forward + Audit; fail-closed
scientific state. Software authority: `v0.3.0-alpha` @ `f1d225e`.

Target: 15–25 **primary** references, roughly 3–6 per block A–E.
Surveys are orientation only.

Novelty language cap: combination/application claims. No “no prior work
has…”, “first…”, “unlike all previous…”.

---

## Shared inclusion / exclusion

**Include** if the source is a primary conference/journal paper, archival
proceedings paper, official system/project paper, or a primary arXiv
preprint used only when no archival version is found; and it speaks to at
least one comparison axis in the campaign brief (object, producer,
verification authority, claim typing, source grounding, failure
semantics, scientific-state promotion, reader-facing artifact,
manuscript-native operation, two-way use).

**Exclude** blogs, marketing pages, generated summaries, citation-of-a-
citation without the primary, leaderboard posts, and any source used only
because it is famous.

**Prefer venues / source types:** POPL, PLDI, CAV, TACAS, ITP, CPP, CADE,
IJCAR, LICS, ICFP, OOPSLA, SIGMOD, VLDB, IPAW/IPAW-Provenance, WORKS,
SC, ICCS, ISSAC, CASC, JSC, TOMS, CPC, PeerJ CS, NeurIPS, ICLR, ICML,
ACL, Nature/Science methods papers when they are the primary report of a
system (e.g. AlphaGeometry), Living Reviews, and publisher PDFs / DOI
landing pages / arXiv abs pages.

---

## Block A — Certified / checked symbolic computation

**Research question.** What prior work separates an untrusted
computation or proposal from an independently checked certificate or
verifier, and what artifact is certified?

**Inclusion.** Proof-carrying code; proof/certificates for computation;
hidden verification of CAS output; certificate-based symbolic or
numerical computation; independently checkable computation; producing a
checkable certificate distinct from the producer.

**Exclusion.** Ordinary testing; undocumented “trust the CAS”; papers
that only describe a CAS rewrite engine with no checker.

**Search strings.**

- `proof-carrying code Necula`
- `hidden verification computational mathematics Gottliebsen Martin`
- `proof certificates computer algebra`
- `independently checkable computation certificate`
- `AMulet multiplier computer algebra SAT certificate`
- `certifying algorithms Blum Kannan`
- `proof-producing computer algebra`

**Preferred sources.** POPL; J. Symbolic Comput.; STTT; CAV/TACAS;
foundational certifying-algorithms papers.

---

## Block B — Formal proof / theorem proving

**Research question.** How do proof assistants and formalized mathematics
differ from manuscript-native audit of heterogeneous theoretical-physics
derivations? What do they actually require of a claim?

**Inclusion.** System papers for Lean, Coq, Isabelle/HOL (and close
relatives); papers on kernels, proof terms, and physics/mathlib
formalisation; SMT-backed or tactic-automation papers only when they
state what is formalized.

**Exclusion.** Tutorial blog posts; “AI will replace theorem provers”
commentary; claims that proof assistants cannot do physics unless a
primary source says so.

**Search strings.**

- `Lean 4 theorem prover de Moura Ullrich CADE`
- `Coq proof assistant kernel`
- `Isabelle/HOL tutorial Nipkow Paulson Wenzel`
- `HepLean high energy physics Lean`
- `formalized mathematics physics Lean mathlib`
- `proof kernel trusted computing base theorem prover`

**Preferred sources.** CADE, ITP, CPP, JAR, CPC (HepLean), LNCS system
volumes.

---

## Block C — Scientific workflow provenance

**Research question.** What do scientific-workflow and notebook
provenance graphs capture, and do they encode mathematical claim
semantics or scientific-state promotion?

**Inclusion.** Provenance challenge / PROV; scientific workflow
provenance systems; notebook provenance; FAIR as a data principle (one
canonical paper, not a stack of policy notes); executable-paper systems
only if primary.

**Exclusion.** Generic reproducibility editorials without a provenance
model; Git-as-provenance slogans.

**Search strings.**

- `First Provenance Challenge Moreau`
- `W3C PROV provenance`
- `scientific workflow provenance graph`
- `notebook archaeology provenance Koop`
- `Jupyter notebooks publishing Kluyver`
- `FAIR guiding principles Wilkinson Sci Data`

**Preferred sources.** Concurr. Comput. Pract. Exp.; IPAW; Sci. Data;
WORKS; journal system papers.

---

## Block D — LLM / agent scientific reasoning

**Research question.** Where does verification authority sit in
LLM/agent mathematical or scientific reasoning systems? Is “AI may
propose; it may not certify itself” already instantiated?

**Inclusion.** Primary papers on LLM theorem proving, geometry proving
with a checker, Lean copilots, tool-using / CAS-augmented LLM reasoning,
and scientific agents **when** the paper states proposer vs checker.

**Exclusion.** Model leaderboards; unpublished demo threads; papers that
only report GSM8K/MATH accuracy with no checker architecture.

**Search strings.**

- `GPT-f generative language modeling theorem proving Polu`
- `LeanDojo theorem proving retrieval Yang NeurIPS`
- `AlphaGeometry olympiad Trinh Nature`
- `Lean Copilot Song`
- `tool augmented language model mathematical reasoning`
- `self-verification large language models mathematics`

**Preferred sources.** NeurIPS, ICLR, Nature, arXiv primary technical
reports when no archival version exists.

---

## Block E — CAS / symbolic simplification

**Research question.** What do computer-algebra and rewriting systems
provide as equivalence/search, and do they control scientific derivation
state?

**Inclusion.** Foundational or system papers for general CAS used in
physics/Python; term rewriting / equality saturation if they state
equivalence semantics; physics-facing CAS (Cadabra) as a primary system
paper.

**Exclusion.** User-manual HTML as the sole authority; Mathematica
marketing; undocumented folklore about “simplify”.

**Search strings.**

- `SymPy symbolic computing Python Meurer PeerJ`
- `computer algebra gravity research MacCallum Living Reviews`
- `Cadabra field-theory computer algebra Peeters`
- `equality saturation e-graphs Tate Willsey`
- `term rewriting equivalence canonical forms Baader Nipkow`
- `ISSAC symbolic simplification`

**Preferred sources.** PeerJ CS; Living Rev. Relativ.; Comput. Phys.
Commun.; POPL/PLDI (egg); ISSAC; JSC.

---

## Comparison axes (must be filled per selected work)

1. Primary object
2. Producer
3. Verification authority
4. Claim typing
5. Source grounding
6. Failure semantics
7. Scientific-state promotion
8. Reader-facing artifact
9. Manuscript-native operation
10. Two-way use (constructive / audit / both / neither)

## Selection rule after search

Keep the smallest set that covers each block’s question. Prefer the
canonical paper that introduced the principle over later surveys. If two
papers say the same thing, keep one.

Protocol frozen. Source selection may begin.
