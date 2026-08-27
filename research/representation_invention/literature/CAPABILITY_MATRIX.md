# Capability matrix — representation invention

Audit date: 2026-08-27.
Rows: closest systems (mathematics, CAS, PL, AI, frozen repo lines).
Columns: the eight capabilities a method claim on this line would need.
This table is a **neighbor map**, not a result that any row including
`repr_invention_v1_contracts` has achieved DD-OK or Master-OK.

Legend: **Y** = first-class, used as specified; **P** = partial /
related object / not the same mathematics; **N** = absent; **—** =
not applicable.

Column meanings:

| column | yes means |
|---|---|
| grounded members | claims bind to explicit source members (catalog IDs or concrete terms), not verbal “the kernel” |
| explicit F | a named generating object \(F\) with \(A_i=\mathcal O_i[F]\) |
| operators | explicit \(\mathcal O_i\) (Newton DD, Hermite DD, ∂, shift, …) plus reconstruction |
| exact ZERO/NONZERO/UNKNOWN | fail-closed three-way residual; `UNKNOWN` does not promote; compile ≠ `UNKNOWN` |
| no gold leakage | evaluation protocol that can hide target names/answers from the proposer |
| DD | Newton/Hermite divided differences as a representation, with nodes/multiplicities |
| master | one nontrivial \(F\) generating ≥2 structurally distinct members (not \(F:=A_1\); not only a linear IBP basis) |
| scientific expressions | `Sum` / `Piecewise` / indexed / special-function physics kernels, not just polynomials or string I/O |

Frozen compactification systems (FunSearch, LeanDojo, Moxia, …) are
summarized; full proposer–verifier rows live in
`research/literature/closest_work_matrix.csv`.

---

## Matrix

| system | grounded members | explicit F | operators | exact Z/NZ/U | no gold leakage | DD | master | scientific expressions |
|---|---|---|---|---|---|---|---|---|
| Newton interpolation (classical) | P | Y | Y | — | — | Y | N | N |
| Hermite / confluent DD (Hermite 1878; Conte–de Boor 1980; de Boor 2005; Traub 1964) | P | Y | Y | — | — | Y | N | N |
| CAS FullSimplify / SymPy `simplify` / interpolation | P | P | P | N | N | P | N | Y |
| FORM / Cadabra / xAct | P | N | P | N | N | N | N | Y |
| IBP / Laporta / FIRE / Kira / Reduze | Y | P | P | P | N | N | P | Y |
| egg / equality saturation | P | N | P | N | N | N | N | N |
| egglog | P | N | P | N | N | N | N | N |
| Ruler / Enumo | N | N | P | P | N | N | N | N |
| Guided EqSat (POPL 2024) | P | N | P | P | N | N | N | N |
| LGuess (2025) | P | N | P | P | P | N | N | N |
| Herbie | P | N | P | N | N | N | N | P |
| NeuRewriter | P | N | P | N | N | N | N | N |
| DreamCoder | P | P | P | N | P | N | P | N |
| Stitch | P | P | P | N | P | N | P | N |
| babble | P | P | P | N | P | N | P | N |
| LAPS | P | P | P | N | P | N | P | N |
| LILO | P | P | P | N | P | N | P | N |
| FlashFill / SyGuS | P | P | P | P | P | N | N | N |
| FunSearch / AlphaEvolve | N | N | N | N | P | N | N | N |
| AI Feynman / LLM-SR / LaSR | N | P | N | N | P | N | N | P |
| AlphaGeometry / AlphaProof / LeanDojo | P | N | P | P | P | N | N | N |
| ToRA / PAL / Moxia | N | N | N | P | P | N | N | N |
| O-Forge | N | N | P | P | P | N | N | N |
| Shih 2026 / CDS 2025 amplitudes | P | N | P | N | N | N | N | P |
| Frozen B9 exact-pattern `4237f6b` | P | N | N | Y | Y | N | N | Y |
| Frozen LGG `efc0924` | Y | P | N | Y | Y | N | N | P |
| Grounded-Proposer-v1 `3fea222` | Y | N | P | Y | Y | N | N | Y |
| Repr. invention v1 contracts `45b2b4d` | Y | Y | Y | Y | Y | Y | Y | Y |

The last row is the **contract**: schema and gates *require* Y in
every column. It is **not** a claim that an implementation or an LLM
run has satisfied DD-OK or Master-OK. Evidence cell for this line is
empty (`STATUS.md` at contract freeze).

Machine-readable copy: `capability_matrix.json`.

---

## Row notes

**Newton interpolation.** \(F\) and nodes are inputs. “Members” are
the interpolating values, not a scientific catalog. No three-way
residual protocol. DD is the object. Not a master in the R6 sense.

**Hermite / confluent DD.** Same as Newton plus multiplicities and
\(F[x,x]=F'(x)\). This *is* the mathematics of ladder R2–R4. Known.

**CAS simplify / interpolation.** Handles scientific expressions
heuristically. Can build a Newton polynomial when asked. Does not
fail closed on `UNKNOWN`; does not bind `G####`; gold (the simplified
form) is often the human’s target. `Piecewise` is kept or dropped by
heuristics, not by a named DD family.

**FORM / Cadabra / xAct.** Domain CAS. Tensor/Dirac compactification
is representation change of a different kind (index canonicalization),
near F2/F7, not Hermite DD.

**IBP family.** Grounded members = integrals in a family. “Master”
= linear basis, marked **P** not Y: it is not \(A_i=\mathcal O_i[F]\)
with Newton/Hermite operators. Exactness is linear-algebra identity
over the IBP module (system semantics), not this engine’s three-way
residual. Gold (choice of masters) is part of the method.

**egg / egglog / Ruler / Enumo / Guided EqSat / LGuess.** Equality
search or rule synthesis. Operators = rewrite rules, not DD
operators. LGuess is the closest LLM+EqSat method; polynomials only
(`research/literature/corpus.md`). No scientific Piecewise.

**Herbie / NeuRewriter.** Rewrite search. Herbie’s checker is
sampled FP error — opposite of “numeric agreement is never ZERO.”

**DreamCoder / Stitch / babble / LAPS / LILO.** Invent \(F\) as a
\(\lambda\)-abstraction (explicit F **P**). Operators = application
in a DSL. Score ≠ residual identity. “Master” **P** = library
primitive reused across tasks (F8), not R6 on one expression.
Held-out tasks give a form of no-gold; not Guo-name firewall.

**FlashFill / SyGuS.** Synthesize expressions. Checker is examples
or SMT, not scientific residual. Grammar could *in principle*
include `newton_dd` (that would be a baseline to run, not a paper).

**FunSearch / AlphaEvolve.** No \(F\), no members of a given
expression, scored programs.

**AI Feynman / LLM-SR / LaSR.** \(F\) is a formula fitted to data
(**P**). Scientific *domain* sometimes; scientific *expressions*
as CAS objects no.

**AlphaGeometry / AlphaProof / LeanDojo.** Stronger exactness
(kernel). Not compactification; not DD. “Operators” = tactics /
constructions.

**ToRA / PAL / Moxia.** Answers. Moxia abstain ≈ `UNKNOWN` (**P**
on exact Z/NZ/U). No representation hypothesis.

**O-Forge.** LLM domain split + Mathematica `Resolve` on
inequalities. Not identity of two compact forms.

**Shih 2026 / CDS 2025.** Closest ML compactifiers of HEP
expressions. Oracle / known simple form; no fail-closed H; no DD
type; spinor-helicity not Piecewise polygamma.

**Frozen B9 `4237f6b`.** Exact residual on identical patterns. Does
not invent. Gold-hidden bench exists. No DD.

**Frozen LGG `efc0924`.** Grounded pair members; holey \(F\) as LGG
(**P**: substitution template, not a Newton seed). Obligations
ZERO/NONZERO/UNKNOWN. No operators beyond identity/substitution.
No DD. Scientific support partial (toy families + Guo DEV junk).
**Prior in this repo.**

**Grounded-Proposer-v1 `3fea222`.** Catalog `G####`, local
confluence `ZERO` 11/11 on Guo DEV. Operators **P**: limit/generic
vs degenerate roles, not `newton_dd`. Explicit \(F\) **N** as
required by V2. DD **N** (P1 type `confluent_representation` is
rejected in V2). Gold names barred. Not \(\Phi_\Gamma\), not L4–L7.

**Repr. invention v1 contracts.** Schema *asks* for every column.
Implementations and runs are out of scope for this pack.

---

## How to read a future result against this table

A method sentence is licensed only if a run fills
`repr_invention_v1_contracts` with **evidence**, not schema, and
beats the symbolic rows that already have Y/P on DD or master
(Newton/Hermite constructors; IBP if the object is linear; LGG
`efc0924`; CAS interpolation). Until then, keep Decision E
(`research/PUBLICATION_DECISION.md`; abstraction
`PUBLICATION_DECISION.md`).
