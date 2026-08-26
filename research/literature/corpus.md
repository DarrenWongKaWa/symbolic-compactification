# Literature corpus: certified agentic symbolic compactification

Frozen brief date: 2026-08-26
Retrieval: web search over arXiv, venue pages, Semantic Scholar, OpenReview,
DBLP-indexable titles. Unconfirmable works are omitted.

## Brief

**Topic.** Untrusted AI proposers acting on scientific symbolic expressions,
with exact or certified checkers.

**Research questions.**

- RQ1. What architectures already exist for rewriting or simplifying
  symbolic expressions with an exactness guarantee?
- RQ2. Which systems use a learned or LLM-guided search over rewrites or
  programs, and what does their verifier actually guarantee?
- RQ3. Which of those systems handle large special-function, Piecewise,
  indexed, or theoretical-physics expressions?

**Angle.** The crowded object is "LLM + verifier". The sparse object is
*certified compactification of already-symbolic scientific expressions*
that must keep `Sum`/`Piecewise`/indexed structure, fail closed on UNKNOWN,
and bind promotions to hashed state. The survey is written to prevent
claiming the crowded object.

**Intended reader.** The authors of this repository, before any paper draft.

**Capability note.** Perspectives were searched from this session and from
parallel subagents. Citations below are independently confirmed against
arXiv or the venue landing page. Numbers quoted from search snippets are
not treated as results; only bibliographic facts and abstracts are used.

---

## Method (search perspectives)

1. Mainstream rewriting: NeuRewriter, egg, equality saturation, Ruler, Enumo,
   Herbie, LGuess, guided equality saturation.
2. Neuro-symbolic discovery: FunSearch, AlphaGeometry, AlphaProof, LeanDojo,
   DeepSeek-Prover, DSP, AI Feynman.
3. LLM + CAS / tool-using math: ToRA, PAL, Moxia/AXIOM, MATH solvers.
4. Scientific CAS / physics compactification: FullSimplify, FORM, Cadabra,
   xAct, IBP/Kira/FIRE.
5. Critics / measurement: what "certified" means; UNKNOWN vs abstain;
   numeric agreement vs identity.

---

## Taxonomy (MECE)

1. **Destructive or greedy rewriting** (CAS, Herbie, NeuRewriter).
2. **Equality saturation / e-graphs** (Tate, egg, Ruler, Enumo, guided EqSat,
   LGuess).
3. **Program/search with a scored evaluator** (FunSearch, AI Feynman).
4. **Formal proof assistants with neural proposers** (DSP, LeanDojo,
   AlphaProof, DeepSeek-Prover, AlphaGeometry).
5. **LLM tool-use for contest math answers** (PAL, ToRA, Moxia).
6. **Domain CAS for theoretical physics** (FORM, Cadabra, xAct, IBP tools).

Our method sits between 2, 4, 5, and 6, and is identical to none of them.

---

## Branch A — Rewriting and e-graphs

**NeuRewriter** (Chen & Tian, NeurIPS 2019; arXiv:1810.00337) learns a
region-picking and rule-picking policy with actor-critic RL and iteratively
rewrites local components. One of three tasks is expression simplification
in the Halide rule set, compared with Z3-simplify and Halide-rule search.
Exactness, when present, is that of the underlying rewrite rules, not a
fail-closed residual against a scientific source. Representation is
Halide/combinatorial terms, not `Sum`/`Piecewise` physics kernels.
Difference from us: learned policy over a fixed rule set; no UNKNOWN
adjudication; no hashed certified state; no scientific-domain expressions.

**Equality saturation** (Tate, Stepp, Tatlock, Lerner, POPL 2009; journal
LMCS 2011, arXiv:1012.1802) records equalities instead of destroying terms,
then extracts a profitable program. **egg** (Willsey, Nandi, Wang, Flatt,
Tatlock, Panchekha, POPL 2021, doi:10.1145/3434304) makes that practical
via rebuilding and e-class analyses. Soundness is rewrite-rule soundness
plus congruence; extraction uses a cost model (often AST size). Applications
cited by the egg authors include Herbie-style accuracy, vectorization,
Tensat compute graphs, and Szalinski CAD. Difference: no untrusted LLM
proposer; rules are trusted; no scientific Piecewise/indexed compactification
benchmark; no residual UNKNOWN channel.

**Guided equality saturation** (Koehler, Goens, Bhat, Grosser, Trinder,
Steuwer, POPL 2024, PACMPL 8(POPL):58, doi:10.1145/3632900) inserts **human**
intermediate guides when saturation does not scale, demonstrated in Lean 4
and the Rise compiler. LGuess later replaces the human with an LLM.

**LGuess** (Peng, Ji, Xiong, arXiv:2511.00403, 1 Nov 2025; EGRAPHS 2025 talk)
is the closest LLM-guided equality-saturation paper retrieved. LLMs propose
high-level rewrite **checkpoints**; e-graphs fill low-level chains; a
learned probabilistic model extracts checkpoints from a saturated e-graph.
Evaluation: multivariable **polynomial factorization** (255/320 in the
authors' abstract). Exactness: rewrite-system soundness, not a scientific
residual engine. Does not handle Piecewise, indexed Green's functions, or
physics assumptions. Difference: we adjudicate `current − candidate` in a
CAS residual engine with ZERO/NONZERO/UNKNOWN and promote hashed state;
we do not maintain an e-graph of the physics expression (and currently
cannot: no egg runtime on this host).

**Ruler** (Nandi, Willsey, et al., OOPSLA 2021, doi:10.1145/3485496) and
**Enumo** (Pal, Saiki, et al., OOPSLA 2023) synthesize rewrite rules with
e-graphs, validated by SMT or interpreters (bool, bitvector, rational,
Herbie). They produce **rules**, not an agent protocol for a given huge
expression.

**Herbie** (Panchekha, Sanchez-Stern, Wilcox, Tatlock, PLDI 2015,
doi:10.1145/2737924.2737959) searches rewrites to reduce **rounding error**,
using sampled points and regime splitting. Objective is accuracy, not
semantic compactification; sampled floats are the opposite of our "numeric
agreement is never ZERO" rule.

---

## Branch B — Discovery with an evaluator

**FunSearch** (Romera-Paredes et al., Nature 625:468–475, 2024,
doi:10.1038/s41586-023-06924-6) pairs a pretrained LLM with a systematic
evaluator and evolves functions in program space (cap set; bin packing).
The evaluator is trusted for a **numeric/combinatorial score**, not for
symbolic identity of two physics expressions. Accepted programs can be
inspected; there is no hashed expression-state machine and no UNKNOWN
residual. Difference: we do not search for new constructions in combinatorics;
we compactify a given expression under exact residual identity.

**AI Feynman** (Udrescu & Tegmark, Sci. Adv. 6:eaay2631, 2020) performs
symbolic **regression from data** using physics-inspired inductive biases.
Input is tables of numbers; output is a formula that fits. That is a
different problem from rewriting an already-known symbolic object.

---

## Branch C — Formal provers

**Draft, Sketch, and Prove** (Jiang, Welleck, Zhou, et al., ICLR 2023,
arXiv:2210.12283) maps informal proofs to Isabelle sketches; Sledgehammer
closes gaps. **LeanDojo** (Yang et al., NeurIPS 2023 Datasets & Benchmarks)
extracts mathlib proofs and trains ReProver. **DeepSeek-Prover-V2**
(arXiv:2504.21801, 2025) is an LLM for Lean 4 (MiniF2F / PutnamBench).
**AlphaProof** (Hubert et al., Nature, 2025,
doi:10.1038/s41586-025-09833-y) trains an AlphaZero-style agent in Lean;
IMO 2024 silver with AlphaGeometry 2. **AlphaGeometry** (Trinh, Wu, Le, He,
Luong, Nature 625:476–482, 2024, doi:10.1038/s41586-023-06747-5) uses a
language model to guide a symbolic geometry engine; AG2 (JMLR 2025) extends
coverage.

Exactness here is **kernel checking** of a formal proof, which is stronger
than our SymPy residual. The object is a theorem in a proof assistant, not
a compact form of a 20 kB Wolfram physics sum. Lean mathlib does not
currently host Guo \(\sigma_{abc}\) Piecewise polygamma kernels, and this
host has no Lean. Claiming "formal proof" for our ZERO verdict would be
false.

---

## Branch D — LLM + tools for math answers

**PAL** (Gao et al., 2022/2023) and **ToRA** (Gou et al., ICLR 2024,
arXiv:2309.17452) interleave language with Python/CAS tool calls to produce
**answers** on GSM8K/MATH. The tool output is not a fail-closed identity
check of two scientific expressions; wrong CAS use can still yield a
confident numeric answer.

**Moxia / AXIOM** (Bruno, arXiv:2606.00671, v3 12 Aug 2026; formerly AXIOM)
is the closest 2026 "trust-first LLM + CAS" architecture retrieved. The LLM
is a **canonicalizer** of informal MATH problems into a schema; a
deterministic CAS handler derives the answer or **abstains**. Routing is
1:1:1 regex/prompt/handler. The paper emphasizes zero confident-wrong
answers and abstain as first-class. Difference from us:

- input is a natural-language contest problem, not a huge structural
  physics expression;
- output is an answer, not a certified compact form plus provenance;
- abstain ≈ our UNKNOWN, but there is no hashed promote-only-on-ZERO
  expression state, no representation-preservation contract for
  `Sum`/`Piecewise`, and no scientific ladder metric.

A reviewer who has read Moxia will treat "LLM proposes, CAS checks, abstain
on failure" as already published. We must not lead with that sentence.

---

## Branch E — Scientific computer algebra

Mathematica `Simplify`/`FullSimplify` use a `ComplexityFunction` (often
`LeafCount`) and heuristic search; they can change form using assumptions
and can be wrong relative to a physicist's intended branch. SymPy
`simplify` is similarly heuristic. FORM is the workhorse for Dirac algebra
and trace compactification in HEP. Cadabra and xAct/xPerm canonicalize
tensor expressions. IBP/Laporta tools (FIRE, Kira, Reduze) reduce Feynman
integrals to masters.

These systems **are** the scientific baseline. They do not:

- treat the LLM as untrusted;
- record NONZERO counterexamples as first-class;
- refuse to promote UNKNOWN;
- keep a hashed certified current distinct from diagnostic lowering;
- evaluate false-promotion rate of agents.

Our B1/B2 baselines exist because this branch is the honest competitor for
**compactness**. If B1 wins certified compactness, C2 is false.

No retrieved paper was titled "symbolic compactification" as a generic AI
task. That absence is **not** novelty; it is a naming gap.

---

## Cross-branch synthesis

| Need | Who already has it | Who does not |
|---|---|---|
| Untrusted proposer | FunSearch, AG, LeanDojo, LGuess, ToRA, Moxia | egg, Ruler, CAS |
| Exact checker | egg, Lean kernel, FunSearch evaluator, LGuess, Moxia CAS | ToRA/PAL (execution ≠ identity) |
| Fail-closed UNKNOWN/abstain | Moxia abstain; our UNKNOWN | most LLM+tool papers |
| Hashed certified state + provenance | **this repo** (engine contract) | not retrieved as a packaged protocol |
| Large physics Sum/Piecewise/indexed | FORM/Cadabra/xAct/human CAS | LGuess, MATH agents, Lean IMO |
| Scientific compactness ≠ AST size | physicists' named kernels | egg cost models, FullSimplify LeafCount |
| Honest "not a formal proof" | rare | many "certified" LLM papers |

The remaining gap is therefore **narrow and empirical**: does the protocol
change false-promotion and certified progress on scientific expressions
enough to matter, once LGuess-style, FunSearch-style, CAS, and
LLM+CAS baselines are run fairly?

---

## Answers to the research questions

**RQ1.** Exact rewriting is solved in several mature ways: trusted rewrite
rules + e-graphs; kernel-checked proofs; CAS heuristics; scored program
evaluators. Fail-closed three-way residuals (ZERO/NONZERO/UNKNOWN) with
promotion gates are **not** the standard CAS or LLM-tool interface.

**RQ2.** LLM-guided search with a trusted checker exists (FunSearch,
AlphaGeometry, AlphaProof, DSP, LeanDojo, LGuess, Moxia). Verifiers
guarantee, respectively: a score, a geometry proof, a Lean proof, an
Isabelle proof, a rewrite chain, or a CAS answer. None of those guarantees
is "two physics expressions differ by a SymPy-zero residual under declared
assumptions, else do not promote".

**RQ3.** Large special-function / Piecewise / indexed scientific expressions
are handled by **domain CAS and humans**, not by the LLM+verifier papers
retrieved. LGuess is polynomials. FunSearch is combinatorics programs.
AlphaGeometry is Euclidean geometry. LeanDojo is mathlib. Moxia is MATH.
AI Feynman is data-driven. That is the application gap, and also why a
single Guo example cannot carry a generalization claim.

---

## Self-adversarial notes

- A 2026 preprint (Moxia) occupies the "trust-first LLM+CAS+abstain" slogan.
  If we cannot show N1–N3 on scientific compactification, we should not
  write a method paper.
- LGuess is the paper a PL reviewer will say we must baseline. egg is not
  installed here; a restricted Python e-graph is a mismatch that must stay
  documented.
- Existing Guo A/B already threatens C2. The corpus does not rescue C2.
- Independent researcher preprints (Moxia) have weaker venue signal than
  Nature/POPL; they still block "first" claims.

## Unconfirmed / not used

- Any paper whose title was suggested by memory but not retrieved with
  matching authors/year/venue.
- Numeric tables copied from search snippets (forbidden by
  idea-evaluator/deep-research citation protocol).
