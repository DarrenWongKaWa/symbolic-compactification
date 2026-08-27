# Closest work — representation invention

Audit date: 2026-08-27.
Retrieval: classic NA/interpolation sources; arXiv and venue pages for
PL/AI systems already used in frozen compactification and abstraction
audits. Unconfirmable titles are omitted. Numeric tables from search
snippets are not used as results.

**Object.** A complete, grounded, checkable change of representation

\[
H=(R,\{A_i\},\{\mathcal O_i\},F),\qquad A_i=\mathcal O_i[F],
\]

with fail-closed `ZERO`/`NONZERO`/`UNKNOWN`, catalog members `G####`,
and no gold names. Local confluence (P1, G1/R0) is the baseline, not
the claim. Ladder: `LADDER.md` (R0–R8). Gates: DD-OK, Master-OK in
`PROTOCOL.md`.

**Not the object.** Contest-math answers, Lean theorems, data-fit
symbolic regression, IBP linear reduction to a known master basis,
or first-order substitution LGG.

**Frozen literature this pack does not rewrite.**

- Compactification proposer–verifier survey:
  `research/literature/corpus.md`,
  `research/literature/novelty_boundary.md`,
  `research/literature/closest_work_matrix.csv`
  (freeze `13814ba`).
- Abstraction / LGG:
  `research/abstraction_invention/literature/NOTE.md`,
  `research/abstraction_invention/literature_v2/`,
  `research/abstraction_invention/BEYOND_LGG_TAXONOMY.md`,
  `research/abstraction_invention/LGG_CLOSED.md`
  (LGG freeze `efc0924`; beyond-LGG `3214a5a`).

Intended reader: authors of this repository, before any paper draft.

---

## 1. Frozen prior *in this repository*

| SHA | What it is | What it is not |
|---|---|---|
| `4237f6b` | Layer-1 exact-pattern structure discovery (B9) | invention of a new head / \(F\) |
| `efc0924` | First-order LGG anti-unification + instance obligations | scientific confluence, DD, masters, L4–L7 |
| `3214a5a` | Beyond-LGG taxonomy F1–F8, quality score, v0.2 bench | a solver for F5–F8 |
| `3fea222` | Grounded-Proposer-v1: 11/11 Guo local-confluence `ZERO` | Newton/Hermite DD, \(\Phi_\Gamma\), DD-OK |
| `45b2b4d` | RepresentationHypothesisV2 contracts, R0–R8 | evidence that R1+ is reachable |

Cite `efc0924` as **prior in this repo**. Re-shipping Plotkin/Reynolds
LGG is not novelty (`LGG_CLOSED.md`). P1 did not emit
`divided_difference`; it emitted `confluent_representation` with
catalog node pairs (`research/grounded_proposer/RESULTS_P1.md`).
Human labels L4–L7 and the name \(\Phi_\Gamma\) are evaluation
targets in frozen experiment notes, **not** outputs of this engine.

---

## 2. Divided differences and Newton interpolation

**Newton form.** Given nodes \(x_0,\ldots,x_n\) (pairwise distinct in
the non-confluent case), the interpolant admits the Newton expansion
whose coefficients are divided differences
\(F[x_0]\), \(F[x_0,x_1]\), …, with the first-order identity

\[
F[x,y]=\frac{F(x)-F(y)}{x-y}.
\]

Historical source: Isaac Newton, interpolation with unequal intervals
(treated by 1687; *Methodus Differentialis*, 1711). de Boor (2005)
quotes Newton (1676) on the beauty of the construction.

**Modern textbook algorithm.** Conte and de Boor, *Elementary
Numerical Analysis: An Algorithmic Approach*, 3rd ed. (1980), Chapter
2: polynomial forms, the divided-difference table, interpolation of
an increasing number of points, and §2.7 osculatory interpolation.
(The mission brief’s “Conti/de Boor” is this pair: **S. D. Conte and
Carl de Boor**, not Costanza Conti’s later spline papers.)

**Survey.** de Boor, “Divided Differences,” *Surveys in Approximation
Theory* 1 (2005) 46–69, arXiv:math/0502036. Divided differences are
defined as Newton-form coefficients; the partial sums *are* Hermite
interpolants at the listed nodes with stated multiplicities.
Continuity in the nodes is the reason a difference quotient and a
derivative are the same object.

**CAS status.** Any computer-algebra system that implements
interpolation (Newton form, `InterpolatingPolynomial`, divided
difference tables) already *constructs* \(F[x,y]\) when \(F\) and
the nodes are given. That constructor is a **symbolic baseline**,
not an AI method.

**Distance from this line.** Known mathematics. A proposer that
prints “divided difference” without catalog members, nodes,
multiplicities, explicit \(F\), operators, and reconstruction fails
the contract (`PROTOCOL.md` rule 3). A compiler that, given those
fields, checks \(A=(F(x)-F(y))/(x-y)\) is a checker, not a discovery.

---

## 3. Hermite / confluent interpolation

**Hermite (1878).** C. Hermite, “Sur la formule d'interpolation de
Lagrange,” *J. Reine Angew. Math.* 84:70–79. Interpolation that
matches derivatives as well as values.

**Repeated nodes.** When a node is listed with multiplicity \(m\),
the Newton table uses
\(F[\underbrace{x,\ldots,x}_{k}]=F^{(k-1)}(x)/(k-1)!\)
for \(k\le m\). This is osculatory / confluent interpolation
(Conte–de Boor 1980, §2.7; de Boor 1978, *A Practical Guide to
Splines*; Traub, “On Lagrange—Hermite interpolation,” *J. SIAM*
12(4):886–891, 1964). As all nodes collapse to one point, the Newton
form degenerates to a Taylor polynomial.

**Genocchi–Hermite integral.** de Boor (2005, §9) records the simplex
integral representation of \(F[x_0,\ldots,x_n]\), which makes
continuity in coalescing nodes analytic rather than formal.

**Distance.** Hermite DD is the intended representation for
Piecewise “generic vs coincident” strata (ladder R2–R4). Shipping
the formula is not novelty. The open question is whether an
untrusted proposer can *identify* \(F\), nodes, and multiplicities
from grounded scientific members without gold.

---

## 4. Symbolic confluence and piecewise degeneracy

Two different technical words collide.

| Sense | Field | Object | Closest systems |
|---|---|---|---|
| Interpolation confluence | NA / complex interpolation | nodes coalesce; DD → derivatives | Newton/Hermite/de Boor |
| Rewriting confluence | term rewriting / EqSat | joinability of rewrite paths | Knuth–Bendix, egg, egglog |

This line means the **first** sense. CAS `Piecewise` is a common
*encoding* of the second syntax for the first mathematics: one
branch for \(x\neq y\), another for \(x=y\). Folding identical
Piecewise values is frozen B9 (`4237f6b`), not LGG and not DD.
Beyond-LGG class **F5** (“confluent families”) and **F6**
(“representation change”) are exactly this gap
(`BEYOND_LGG_TAXONOMY.md`): LGG cannot invent a new head, and
identical-value folding does not name \(F[x,y]\).

No retrieved CAS paper was titled “symbolic confluence of piecewise
special-function kernels” as an AI task. That absence is a **naming
gap**, not novelty (same warning as frozen `corpus.md` on
“symbolic compactification”).

---

## 5. Representation change

**Polynomial bases.** Gander, “Change of basis in polynomial
interpolation,” *Numer. Linear Algebra Appl.* 12:769–778 (2005):
Lagrange ↔ Newton ↔ monomial is a change of language for the *same*
interpolant.

**E-graphs** extract a profitable representative from an equivalence
class generated by trusted rewrite rules (Tate et al., POPL 2009;
egg, POPL 2021). The language of terms is fixed; the representative
changes. That is representation *selection*, not invention of
Newton/Hermite as a new type.

**Program library learning** changes the DSL by adding \(\lambda\)-abstractions
(DreamCoder, Stitch, babble). The new symbols are reusable
*programs*, scored by compression on a corpus, not fail-closed
residuals on one physics expression.

**IBP** changes a spanning set of Feynman integrals to a master
basis by linear algebra. New symbols are basis integrals, not a
nonlinear operator family \(A_i=\mathcal O_i[F]\).

**This line’s F6 example.** Piecewise strata \(\to\) one DD family;
indexed components \(\to\) invariant generators. Search over
representation *class* \(R\) (`research/representation_search/PROTOCOL.md`).
No standard algorithm returns a unique LGG for that search
(taxonomy table in `BEYOND_LGG_TAXONOMY.md`).

---

## 6. Program synthesis of mathematical representations

| System | What is synthesized | Spec | Checker |
|---|---|---|---|
| FlashFill (Gulwani, POPL 2011) | string programs in a DSL | input–output examples | execution on examples |
| SyGuS (Alur et al., FMCAD 2013) | expressions in a grammar | logical spec + grammar | SMT |
| DreamCoder (Ellis et al., PLDI 2021) | programs + library | I/O examples | execution / Bayesian score |
| FunSearch (Romera-Paredes et al., *Nature* 2024) | Python functions | scored evaluator | numeric/combinatorial score |
| LLM-SR / LaSR / AI Feynman | formulae from **data** | tables | fit / Pareto |
| Mathematica / SymPy interpolation | Newton/Hermite polynomial | nodes + values | algebra of polynomials |

Closest *slogan*: “synthesize a representation that compresses
examples.” Closest *miss*: the spec here is **identity of given
symbolic members** to \(\mathcal O_i[F]\), not I/O examples and not
a data fit. SyGuS with a grammar of `{newton_dd, hermite_dd, ∂}`
and a residual checker would be a serious **symbolic baseline**
this line must beat or match; it is not a published physics-CAS
system.

---

## 7. Abstraction invention, anti-unification, LGG

**Classical.** Plotkin, “A Note on Inductive Generalization,”
*Machine Intelligence* 5 (1970) 153–163; Reynolds,
“Transformational Systems and the Algebraic Structure of Atomic
Formulas,” same volume (1970). First-order LGG unique modulo
renaming.

**Survey.** Cerna and Kutsia, “Anti-unification and Generalization:
A Survey,” IJCAI 2023, doi:10.24963/ijcai.2023/736,
arXiv:2302.00277. Covers HO, equational, nominal, constrained AU.
AC-AU is finitary, not unique. Unrestricted HO-AU is hard.

**This repo.** `prototype/antiunify.py` @ `efc0924` is first-order
syntactic LGG with per-instance residual obligations. TEST: 5/5 pos,
3/3 neg vs frozen B9 0/5 pos. Guo: parameterized polygamma template
**and** shallow junk; **no confluence; no L4–L7** (`LGG_CLOSED.md`).

**Distance.** LGG is F1/F2 machinery. F5–F8 (confluence,
representation change, bases, libraries) are declared unsolved by
LGG in the frozen taxonomy. Re-running `efc0924` is the control,
not the method.

---

## 8. Master-function induction vs IBP reduction

**Physics masters (linear).** Chetyrkin and Tkachov, *Nucl. Phys. B*
192 (1981) 159–204: IBP identities. Laporta, *Int. J. Mod. Phys. A*
15 (2000) 5087–5159: systematic reduction. Implementations: FIRE6
(Smirnov and Chukharev, *Comput. Phys. Commun.* 247 (2020) 106877,
arXiv:1901.07808); Kira (Maierhöfer, Usovitsch, Uwer,
*Comput. Phys. Commun.* 230 (2018) 99–112, arXiv:1705.05610);
Reduze 2 (von Manteuffel and Studerus). These **reduce to** a
finite linear basis. They do not invent a meromorphic \(F\) such
that Piecewise kernels are Newton/Hermite operators of \(F\).

**Special-function seeds.** Naming \(\psi\), a Meijer-\(G\), or a
thermal factor is ordinary. A human closed form may introduce a
named master; **the name is not a method**.

**This line’s master gate.** ≥2 distinct grounded members, one
explicit \(F\), nontrivial \(\mathcal O_i\), `ZERO`, not
\(F:=A_1\). Related slogan to IBP (“few masters generate the
family”), different object (operator family vs linear span).

---

## 9. Library learning

| System | Venue | Mechanism | Score |
|---|---|---|---|
| DreamCoder (Ellis, Wong, Nye, Sablé-Meyer, Morales, Hewitt, Cary, Solar-Lezama, Tenenbaum) | PLDI 2021, doi:10.1145/3453483.3454080 | wake–sleep; e-graph refactoring | compression + neural search |
| Stitch (Bowers, Olausson, Wong, Grand, Tenenbaum, Ellis, Solar-Lezama) | POPL 2023, doi:10.1145/3571234, arXiv:2211.16605 | corpus-guided top-down synthesis | compression, much faster than DreamCoder |
| babble (Cao, Kunkel, Nandi, Willsey, Tatlock, Polikarpova) | POPL 2023, doi:10.1145/3571207, arXiv:2212.04596 | e-graph anti-unification modulo a theory | library learning modulo theory |
| LAPS (Wong, Ellis, Tenenbaum, Andreas) | NeurIPS 2021, arXiv:2106.11053 | language annotations guide DreamCoder | library + search heuristics |
| LILO (Grand, Wong, Bowers, Olausson, Liu, Tenenbaum, Andreas) | ICLR 2024, arXiv:2310.19791 | LLM synthesis + Stitch + AutoDoc | task solve rate + readable library |

**Distance.** F8 in the frozen taxonomy: reusable abstractions
*across a corpus of programs*. This line is one (or few) already
exact scientific expressions, fail-closed identity, representation
*type* in {DD, Hermite, master, …}. Compression of \(\lambda\)-bodies
is the wrong metric (scientific compactness ≠ AST size; frozen
`novelty_boundary.md`). Do not claim “abstraction invention”
generically as new.

---

## 10. E-graphs and equality-aware representation search

| System | What it searches | Trusted object |
|---|---|---|
| Tate et al., POPL 2009 / LMCS 2011 | PEG equivalences | rewrite axioms + congruence |
| egg (Willsey et al., POPL 2021) | e-classes + analyses | rewrite soundness; cost extraction |
| egglog (Zhang et al., PLDI 2023, doi:10.1145/3591239) | Datalog + EqSat | same + relations |
| Ruler (OOPSLA 2021), Enumo (OOPSLA 2023) | *rules* | SMT / interpreters |
| Guided EqSat (Koehler et al., POPL 2024) | human checkpoints then EqSat | e-graph / Lean |
| LGuess (Peng, Ji, Xiong, arXiv:2511.00403) | LLM checkpoints; polynomials | rewrite chains |
| Herbie (PLDI 2015) | FP accuracy | sampled error (not identity) |
| NeuRewriter (NeurIPS 2019) | Halide local rewrites | rule soundness |

**Distance.** Serious neighbor for *search over equivalent forms*
once a rewrite theory exists. Not a neighbor for *inventing* the
theory “Piecewise strata are Hermite DDs of one \(F\).” LGuess is
the paper a PL reviewer will demand as a baseline for LLM-guided
rewriting; it factorizes polynomials, not polygamma Piecewise
kernels. This host’s egg limitation is documented in frozen
literature and is not novelty. A restricted Python e-graph that
cannot encode the scientific IR is not a fair baseline and must
stay labeled as such.

babble is the overlap of e-graphs **and** anti-unification: library
learning modulo an equational theory. If this line only AC-normalizes
then LGG-s, that is babble/F2, already closed as “not invention.”

---

## 11. Symbolic scientific reasoning, neuro-symbolic math, LLM discovery

Reuse frozen `research/literature/corpus.md` for the crowded
proposer–verifier slogan. Distance to *this* frontier:

| Cluster | Examples | Accepts | vs representation invention |
|---|---|---|---|
| Evolutionary program search | FunSearch, AlphaEvolve | better **score** | not \(A_i=\mathcal O_i[F]\) identity |
| Geometry / ITP | AlphaGeometry, LeanDojo, AlphaProof, DeepSeek-Prover, DSP | kernel / DDAR proof | theorem, not CAS compact form |
| Tool-using contest math | PAL, ToRA, Moxia/AXIOM | answer or abstain | no hashed scientific representation |
| LLM+CAS research math | O-Forge | inequality via `Resolve` | not two-expression residual |
| Symbolic regression | AI Feynman, PySR, LLM-SR, LaSR | data fit | input is tables, not a given kernel |
| HEP ML simplification | Shih 2026; Cheung–Dersy–Schwartz 2025 | simpler amplitude vs oracle | supervised policy, not fail-closed H |
| Domain CAS | FullSimplify, FORM, Cadabra, xAct | heuristic / index algebra | no untrusted \(H\) contract |

**LLM representation discovery**, narrowly: DreamCoder’s equation
domain, LLM-SR’s equation *programs*, LGuess checkpoints, LILO
libraries. None of these (i) bind catalog members of one physics
expression, (ii) require explicit \(F\) and \(\mathcal O_i\),
(iii) adjudicate `ZERO`/`NONZERO`/`UNKNOWN` without promoting
`UNKNOWN`, and (iv) forbid gold names of the target representation.

Verbal LLM slogans that say “divided difference” or “master
function” without (i)–(iii) are observation, not discovery
(frozen SOL/obligation-IR line; do not re-squeeze those JSON files).

---

## 12. Capability synthesis (what is jointly missing)

No retrieved system jointly has:

1. **Grounded members** — proposer must point at catalog `G####`
   (aliases are `PARSE_FAILURE`);
2. **Explicit \(F\)** — not a hole, not “the kernel”;
3. **Explicit operators** \(\mathcal O_i\) with reconstruction
   \(A_i=\mathcal O_i[F]\);
4. **Exact three-way residual** `ZERO`/`NONZERO`/`UNKNOWN`,
   `UNKNOWN` not success, compile failure not `UNKNOWN`;
5. **No gold leakage** — evaluation names such as \(\Phi_\Gamma\)
   / L4–L7 absent from proposer-visible files;
6. **DD as a representation type** — Newton/Hermite with nodes and
   multiplicities, not only local limits;
7. **Nontrivial master** — one \(F\), two+ members, not \(F:=A_1\);
8. **Scientific expressions** — `Sum`/`Piecewise`/indexed/special
   functions, not polynomials-only or I/O strings.

Closest *method fragments*: LGuess (LLM+trusted rewriting, wrong
domain); babble/DreamCoder/Stitch (representation invention, wrong
spec and score); IBP (masters, wrong object); Conte–de Boor / de Boor
2005 (right DD mathematics, no untrusted proposer); Moxia (abstain,
wrong task); Grounded-Proposer-v1 (grounding + local confluence,
stops before DD-OK); LGG @ `efc0924` (grounded obligations, wrong
abstraction class).

The remaining question is empirical and **narrow**. It is not
answered by this literature pack.

---

## 13. Self-adversarial notes

- A compiler that checks Newton’s formula on members that already
  *are* \((F(x)-F(y))/(x-y)\) produces compiler gain, not discovery.
- Hardcoded polygamma identities (`polygamma(1,z)=d/dz polygamma(0,z)`)
  are F4 tables, not F5 invention.
- If generic DD tasks are only polynomials, CAS interpolation wins
  and C2-style compactness claims die.
- Guo n=1 cannot carry generalization; human L4–L7 remain unproduced.
- Reviewers who know Hermite 1878 will desk-reject any paper that
  leads with “we introduce divided differences.”
- Reviewers who know DreamCoder will desk-reject “abstraction
  invention” without the capability matrix in this directory.

## Unconfirmed / not used

- Papers whose titles were recalled but not retrieved with matching
  authors/year/venue.
- Numeric solve-rate tables copied from search snippets.
- Any claim that worktrees A–G have already reached DD-OK / Master-OK
  (those directories are owned elsewhere; this pack is documentation).
