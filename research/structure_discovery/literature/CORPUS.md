# Structure-discovery literature corpus

Audit date: 2026-08-27.
Scope: what already counts as *inventing reusable mathematical structure*,
not the older compactification LLM+verifier survey.

This corpus is independent of `research/literature/corpus.md` (v0 line).
Citations were checked against publisher/arXiv pages in this session.

Legend for the central overlap test:

> abstraction invention + exact scientific expressions + exact verification

A paper covers the triple only if all three columns are Yes.

---

## A. Symbolic regression / equation discovery (from data)

| Work | Input | Output | Invents abstractions? | Exact verification of two expressions? | Scientific expressions already given? |
|---|---|---|---|---|---|
| Schmidt & Lipson, *Science* 2009 (Eureqa) | trajectories | differential invariants | reusable terms in a GP library, weakly | numeric fit | no (data) |
| Udrescu & Tegmark, AI Feynman, *Sci. Adv.* 2020 | numeric tables | closed formula | physics heuristics (units, symmetry) as search bias, not named objects inside an expression | numeric | no |
| Udrescu et al., AI Feynman 2.0 | tables | formula + Pareto | same | numeric | no |
| Brunton, Proctor, Kutz, SINDy, *PNAS* 2016 | snapshots | sparse ODE | library of candidate terms, not invented mid-expression | residual of dynamics, not identity of two CAS forms | no |
| Cranmer et al., PySR / *symbolic regression for science* | data | formula | optional nested functions | numeric | no |
| Shojaee et al., LLM-SR (2024) | data | program-shaped formula | LLM proposes functional form | numeric score | no |
| Xia et al., SR-Scientist, arXiv:2510.11661 | data | equation + code | agent writes analysis code | numeric | no |

**Limitation vs us:** these *discover laws from measurements*. We start from an
already-exact expression and ask what latent structure it hides.

---

## B. Invariant / symmetry / conservation discovery (from data or ODEs)

| Work | What is discovered | Exact? | On given algebra? |
|---|---|---|---|
| Liu & Tegmark, AI Poincaré, *PRL* 126:180604 (2021) | conserved quantities from trajectories | numeric independence | no |
| Liu, Madhavan, Tegmark, AI Poincaré 2.0, *PRE* 106:045307 (2022) | conservation laws from ODEs, optionally symbolic | symbolic formulas of conserved quantities, not residual identity of two physics expressions | no |
| Yang et al., LieGAN, *ICML* 2023, arXiv:2302.00236 | Lie algebra basis from a dataset | no (GAN) | no |
| Yang et al., LaLiGAN, arXiv:2310.00105 | latent-space symmetries | no | no |
| Moskovitz / LieGG, NeurIPS 2022 | extract learned Lie generators from a net | no | no |

**Limitation:** symmetry *of data or of a learned map*, not permutation orbits
and invariant generators *inside a CAS expression*.

---

## C. Library learning / concept invention (programs)

| Work | Input | Abstraction invented? | Reusable? | Interpretable? | Exact? |
|---|---|---|---|---|---|
| Ellis et al., DreamCoder, *PLDI* 2021 | I/O tasks | yes — DSL library via e-graph refactoring | corpus-level | lambda terms | program eq. / examples |
| Bowers et al., Stitch, *POPL* 2023 | corpus of programs | yes — top-down library functions | corpus-level | DSL | compression / rewrite |
| Cao et al., babble, *POPL* 2023 | programs + equational theory | yes — LLMT / anti-unification on e-graphs | corpus-level | lambda + theory | eq. modulo theory |
| Ellis / Szalinski, *PLDI* 2020 | CAD CSG programs | yes — compact parametric CAD | yes | geometric | rewrite |
| LILO / related LLM+library-learning | programs + language | yes | yes | mixed | mixed |

**Limitation:** the object is a *program corpus*, objective is *compression of
programs*, not physicist-named kernels/masters/generators in one scientific
expression. Closest *method* family to “invent a reusable intermediate.”

---

## D. Equality saturation / rewriting

| Work | Object | Invents named scientific abstractions? | Exact? |
|---|---|---|---|
| Tate et al., equality saturation, POPL 2009 | programs | no (e-classes, not named physics objects) | rewrite soundness |
| Willsey et al., egg, POPL 2021 | general terms | no | rewrite |
| Nandi et al., Ruler, OOPSLA 2021 | rewrite rules | infers *rules*, not task-level masters | SMT-validated rules |
| Pal et al., Enumo, OOPSLA 2023 | programmable rule synth | same | validated rules |
| Koehler et al., Guided EqSat, POPL 2024 | e-graph + human guides | no | rewrite / Lean |
| Peng, Ji, Xiong, LGuess, arXiv:2511.00403, EGRAPHS 2025 | multivariable polynomials | LLM checkpoints ≈ intermediate forms, not physics kernels | e-graph chains |
| Chen & Tian, NeuRewriter, NeurIPS 2019 | Halide AST | no | rule soundness |
| Panchekha et al., Herbie, PLDI 2015 | FP expressions | no | numeric error |

**Limitation:** trusted equalities + extraction. LGuess is the closest
LLM+structure+exact rewriting system; domain is polynomial factorization.

---

## E. Neuro-symbolic theorem / contest math

AlphaGeometry (Nature 2024), AlphaGeometry2 (JMLR 2025), AlphaProof (Nature 2025),
LeanDojo (NeurIPS 2023), DeepSeek-Prover-V2 (2025), Draft-Sketch-Prove (ICLR 2023).

Invent lemmas sometimes; the object is a *proof goal*, the checker is a *kernel*,
not residual identity of two scientific CAS forms.

---

## F. LLM + CAS / scientific agents

| Work | Object | Intermediate representations? | Exact identity gate? |
|---|---|---|---|
| FunSearch, *Nature* 2024 | scored programs | evolved functions | score, not residual |
| AlphaEvolve (DeepMind 2025) | programs | yes | score |
| ToRA, ICLR 2024 | contest answers | tool traces | execution |
| Moxia/AXIOM, arXiv:2606.00671 | contest answers | CAS schemas | abstain + CAS handler |
| O-Forge, arXiv:2510.12350 | asymptotic inequalities | domain split | Mathematica `Resolve` |
| Shih 2026, Learning to Unscramble | HEP / dilog ASTs | rewrite policy | oracle simplicity, not UNKNOWN |
| Cheung–Dersy–Schwartz, SciPost 2025 | spinor-helicity | learned grouping | known simple form |
| PhyNex, arXiv:2606.14266 | scorable physics tasks | method search | domain tools |
| “Little Scientist”, arXiv:2608.16951 | algorithms | Kuhn-agent conjectures | task metrics |
| multi-agent physical-law discovery, arXiv:2411.16416 | materials data | hypotheses + SR | numeric |

**Limitation:** either *answers*, *programs*, or *data-fit laws*. None maintain
a fail-closed residual state machine over `Sum`/`Piecewise`/indexed physics
kernels with typed structural hypotheses.

---

## G. Physics CAS structure (no LLM)

FORM compactification (Kuipers–Ueda–Vermaseren), Cadabra, xAct/xPerm,
IBP/Laporta (FIRE, Kira, Reduze), Butler–Portugal tensor canonicalization.

These *do* operate on real scientific expressions with exact algebra. They do
not emit a typed hypothesis (`permutation_orbit`, `divided_difference`, …)
separate from construction, and they do not wrap an untrusted proposer.

---

## H. Automated theory / conjecture generation (historical)

Lenat AM, Colton HR, Graffiti, INT (Wu et al.). Invent statements, not
representations of a given physics expression.

---

## Coverage of the triple

No reviewed system jointly does:

1. invents *named, human-interpretable scientific abstractions* (kernels,
   masters, orbits, divided differences, generators);
2. on *already-exact theoretical-physics expressions* (not data, not
   polynomials-only, not CAD programs);
3. with *fail-closed residual verification* (ZERO/NONZERO/UNKNOWN) that
   blocks incorrect structure from becoming state.

Closest fragments:

- **DreamCoder / Stitch / babble** — (1) yes, (3) program-eq, (2) no.
- **FORM / CSE / xAct** — (2)+(3) in spirit, (1) no typed scientific H.
- **LGuess** — (1) weak (factor checkpoints), (3) yes, (2) no.
- **AI Poincaré / LieGAN** — (1) invariants/symmetries, (2) no (data/ODE), (3) no residual gate.
- **This repo Method v2** — (2)+(3) yes, (1) only tautological packaging.

The *problem formulation* is therefore not title-mismatch novelty. The *method*
is a recombination and must be justified by D3–D5 evidence, not by the slogan.
