# Novelty boundary — representation invention

Audit date: 2026-08-27.
Object: Verified Representation Invention v1
(`research/representation_invention/`, contracts frozen at `45b2b4d`).
This file is a positioning contract, not a result.

Newton/Hermite DD is known mathematics; not claimed as novelty.
Naming a master is not novelty.
Method claim would require grounded+certified representation invention
beyond symbolic baselines.

---

## 1. Known mathematics (not a contribution)

### Newton and Hermite divided differences

The Newton form of an interpolant, the recursive definition

\[
F[x,y]=\frac{F(x)-F(y)}{x-y},\qquad
F[x,x]=F'(x),
\]

higher-order recurrences, and the extension to repeated nodes
(osculatory / Hermite interpolation) are classical. Standard sources:
Newton, *Methodus Differentialis* (1711; interpolation with unequal
intervals already in the 17th century); Hermite (1878); Conte and
de Boor, *Elementary Numerical Analysis* (1980), Ch. 2 including
osculatory interpolation; de Boor, *A Practical Guide to Splines*
(1978) and the survey *Divided Differences* (2005,
arXiv:math/0502036). Confluent (repeated-node) divided differences
are the same object as Hermite interpolation coefficients (Traub 1964;
de Boor 2005, continuity in the nodes). Implementing
`newton_dd` / `hermite_dd` constructors, or quoting \(F[x,y]\), is
**reimplementation of a textbook**.

### Confluence of interpolation nodes ≠ rewriting confluence

In approximation theory, *confluence* means nodes coalesce and
divided differences pass continuously to derivatives. In term
rewriting, *confluence* means joinability of reduction paths
(Knuth–Bendix / e-graphs). Equality saturation searches the latter.
This line's scientific target is the former, encoded in CAS as
`Piecewise` strata that become one analytic object after a
representation change. Distinguishing the two words is mandatory.
Neither meaning is new.

### Piecewise degeneracy as a representation of one object

Writing a generic difference quotient off the diagonal and a
derivative (or higher Hermite form) on the diagonal, then packaging
the pair as `Piecewise`, is a *syntax*. Continuity of divided
differences in their arguments (de Boor 2005, §2) is the theorem
that the syntax is unnecessary once \(F\) and the node
multiplicities are named. Dropping `Piecewise` without that object
is not the theorem.

### Change of polynomial basis

Lagrange, Newton, and Hermite bases of the same interpolant are a
textbook change of representation (Gander 2005). CAS systems already
convert among them. That is not scientific representation invention.

### Master objects in physics CAS

IBP/Laporta reduction (Chetyrkin–Tkachov 1981; Laporta 2000; FIRE;
Kira; Reduze) *reduces* a linear family to a finite master-integral
basis. Naming a seed special function, a generating function, or a
thermal kernel is ordinary scientific practice. A string such as
\(\Phi_\Gamma\) is notation. **Naming a master is not novelty.**

---

## 2. Known AI / PL methods (not this contribution)

Do not write, imply, or let a figure say:

1. First anti-unification or first LGG.
   Plotkin 1970; Reynolds 1970. This repo already shipped a first-order
   LGG inventor at `efc0924`. Cite that SHA as **prior in this
   repository**, not as a result of the present line.
2. First AC / equational / higher-order anti-unification.
   Survey: Cerna and Kutsia, IJCAI 2023.
3. First library learning or abstraction invention.
   DreamCoder (PLDI 2021), Stitch (POPL 2023), babble (POPL 2023),
   LAPS (NeurIPS 2021), LILO (ICLR 2024).
4. First e-graph / equality saturation / LLM-guided EqSat.
   Tate et al. 2009; egg (POPL 2021); egglog (PLDI 2023); Ruler;
   Enumo; Guided EqSat (POPL 2024); LGuess (2025).
5. First untrusted proposer + trusted checker.
   Occupied; see frozen `research/literature/novelty_boundary.md`.
6. First LLM+CAS, first neuro-symbolic mathematics, first
   representation search, first program synthesis of mathematical
   expressions, first symbolic regression, first IBP master
   reduction, first HEP amplitude simplification.
7. A formal proof, a Lean competitor, or exactness beyond declared
   engine semantics (`ZERO`/`NONZERO`/`UNKNOWN` under SymPy residual
   budgets).
8. That this repository discovered \(\Phi_\Gamma\), Hermite kernels
   \(\mathfrak M_\Gamma,\mathfrak T_\Gamma\), geometric vertices, or
   human ladder **L4–L7**. Frozen evidence is the opposite: local
   confluence at G1/R0, no certified Newton/Hermite DD of a thermal
   master, no PRB closed form
   (`research/grounded_proposer/RESULTS_P1.md`;
   `docs/experiments/2026-08-21-progress-vs-prb-closed-form.md`).
9. That Grounded-Proposer-v1 (`3fea222`) already is DD-OK or master-OK.
   P1 certified 11/11 **local confluence** relations. Verbal
   “divided difference” without members, nodes, \(F\), operators, and
   reconstruction is not discovery (`PROTOCOL.md`).
10. Prompt engineering, gold-name leakage (`Phi_Gamma`, L4–L7,
    generator names in proposer-visible files), or compiler/language
    gain relabeled as discovery gain.

---

## 3. What remains (a question, not a claim)

The frozen compactification audit already occupies “fail-closed
compactification of scientific expressions”
(`research/literature/novelty_boundary.md`, SHA `13814ba`).
Abstraction invention occupies substitution LGG
(`research/abstraction_invention/LGG_CLOSED.md`, SHA `efc0924`)
and records F5–F8 as **open**
(`research/abstraction_invention/BEYOND_LGG_TAXONOMY.md`).

This line asks a narrower empirical question:

> Given grounded catalog members \(\{A_i\}\) of an already-symbolic
> scientific expression, can an untrusted proposer emit a complete
> hypothesis \(H=(R,\{A_i\},\{\mathcal O_i\},F)\) with explicit
> operators and reconstruction, such that instance obligations
> certify `ZERO`, without gold names, and **beyond** what a
> symbolic baseline (CAS identity, Newton/Hermite constructor on an
> already-visible difference quotient, first-order LGG @ `efc0924`,
> CSE, IBP-style linear reduction) already does?

That combination is **not** present as a packaged, fail-closed
evaluation in DreamCoder, Stitch, babble, egg/LGuess, FunSearch,
IBP tools, or CAS `FullSimplify`. Absence of a packaged evaluation
is a **gap**, not a proof of novelty. The method claim is false if:

- DD-OK is reached only when members are already difference
  quotients (compiler/language gain, not invention);
- “masters” are tautological wrappers \(F:=A_1\);
- gold names or hidden answers leak into prompts/catalogs;
- a symbolic constructor with the same members and no LLM matches
  the certified representation class;
- the only scientific workload is one Guo DEV example.

---

## 4. Operational gates (what would count)

Imported from `PROTOCOL.md`; not satisfied by this literature pack.

**DD-OK (Phase 7).** All of: grounded `G####` members; explicit
\(F\); node list with multiplicities; explicit DD representation;
reconstruction rule; generated obligations; `ZERO`.
`local_confluence` / P1 `confluent_representation` is not DD-OK.

**Master-OK (Phase 8).** ≥2 structurally distinct grounded members;
one explicit \(F\); nontrivial operator maps; instance obligations
`ZERO`; quality above \(F:=A_1\) used once.

**Discovery vs compiler vs grounding.** If P2 emits a representation
type absent from frozen P1: discovery gain. If old P1 output becomes
checkable because the compiler improved: compiler gain. If the same
structure is bindable because members are `G####`: grounding gain.
Never mix these.

**No gold leakage.** Proposer-visible files must not contain Guo gold
names. Hidden gold is for evaluation only.

---

## 5. Claims a knowledgeable reviewer would reject immediately

| Claim | Why it dies | Who cites it |
|---|---|---|
| “We invented divided differences / Hermite interpolation” | Newton, Hermite, Conte–de Boor, de Boor 2005 | any numerical analyst |
| “We invented master functions” | IBP/Laporta; special-function seeds; naming | HEP CAS users |
| “First abstraction invention” | Plotkin/Reynolds; DreamCoder/Stitch/babble; this repo `efc0924` | PL + this repo's LGG freeze |
| “First LLM+verifier” | FunSearch, LeanDojo, LGuess, Moxia, … | frozen `novelty_boundary.md` |
| “E-graphs already do confluence, so this is EqSat” | rewriting confluence ≠ interpolation confluence | PL reviewer *and* NA reviewer |
| “Agent found \(\Phi_\Gamma\) / L4–L7” | frozen runs did not; gold names forbidden | authors' own logs |
| “P1 was already Newton DD” | P1 is G1 local limits, not DD-OK | `RESULTS_P1.md`, `LADDER.md` |
| “Formal certification” | SymPy residual + probes, fail-closed `UNKNOWN` | Lean/e-graph reviewer |
| Method paper without beating symbolic baselines | remaining claim *is* that delta | any ML reviewer |

---

## 6. Experiments that would be required (not run here)

Literature does not generate these numbers.

1. **Generic DD before Guo.** Certified Newton/Hermite reconstruction
   on non-Guo tasks whose members are *not* already spelled as
   \(F[x,y]\), with gold names absent.
2. **Symbolic baselines.** Same tasks, no LLM: (i) first-order LGG
   @ `efc0924`; (ii) CAS `simplify`/`limit`; (iii) an explicit
   Newton/Hermite constructor given \(F\) and nodes; (iv) restricted
   e-graph if available. Method claim needs a gap after (i)–(iii).
3. **DD-OK / Master-OK on Guo DEV** without gold, with ≥5 seeds,
   reporting PARSE/COMPILE/ZERO/NONZERO/UNKNOWN separately.
4. **Falsifiers.** Tautological \(F:=A_1\); swapped generic/degenerate
   roles; leaked gold names → `PARSE_FAILURE` or rejected quality.
5. **Generalization.** At least one non-Guo scientific family.

Until those exist, the honest status is: **contracts + literature;
no representation-invention method result.**

---

## Positioning sentence (not a title)

> Newton and Hermite divided differences, and the idea of a master
> object that generates a family, are classical. Library learning,
> anti-unification, and e-graphs already invent or search
> representations of *programs*. IBP tools already reduce *to*
> masters. This line asks whether a grounded, fail-closed proposer
> can *change the mathematical language* of an already-symbolic
> scientific expression (Piecewise strata → one DD/master family)
> beyond those symbolic baselines, without gold names. That is an
> open empirical question, not a claim.
