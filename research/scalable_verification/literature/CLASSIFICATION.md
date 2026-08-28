# Classification of Track V verification methods

Audit date: 2026-08-28.
Companion: `METHODS.md`. Labels are for **paper-facing honesty**, not
marketing.

Allowed labels (exactly one primary label per method):

| label | meaning |
|---|---|
| **known standard** | Textbook or published algorithm. Shipping it is reimplementation. |
| **engineering adaptation** | Standard method, wired into this engine’s obligation IR, budgets, and fail-closed three-way. Systems work, not a new theorem. |
| **potential novel contribution** | Not claimed. Would require measured `V_GAIN` with false ZERO = 0, beyond symbolic baselines, without gold names. Absence of a packaged evaluation is a **gap**, not a proof. |

**Hard rule.** Newton/Hermite divided-difference mathematics is **known
standard**. It is not an engineering adaptation of *mathematics* and it
is not a potential novel contribution. A reviewer who knows Hermite 1878
or de Boor 2005 will desk-reject any draft that leads with “we introduce
divided differences” or “we introduce Hermite interpolation.”

This pack classifies **verification methods** (layer V). Discovery of a
representation \(H=(R,\{A_i\},\{\mathcal O_i\},F)\) is Track D and is
locked until `TRACK_V_CLOSED.md` exists.

---

## Summary table

| # | Method | Mathematics | Track-V use (primary label) | May a paper call this novel? |
|---|---|---|---|---|
| 1 | Symbolic limits (Gruntz / `sympy.limit`) | known standard | **known standard** | no |
| 2 | Confluent divided differences | known standard | **engineering adaptation** | no (math); use is routing, not a theorem |
| 3 | Hermite identities | known standard | **engineering adaptation** | no |
| 4 | Compositional proof / obligation split | known standard | **engineering adaptation** | no, as a proof theory |
| 5 | Factoring before proof | known standard | **engineering adaptation** | no |
| 6 | Certificates (cheap checkers) | known standard | **engineering adaptation** | no, as a certificate calculus |
| 7 | E-graphs / equality saturation | known standard | **known standard** | no |
| 8 | Special-function identities | known standard | **engineering adaptation** | no |
| \* | Packaged fail-closed routing of frozen hypotheses (DIRECT / FACTOR_LOCAL / DD_CERTIFICATE / SPECIAL_FUNCTION_LOCAL + `V_GAIN` accounting) | — | **potential novel contribution** (conditional) | only if experiments in §Upgrade exist; still not a math contribution |

Primary labels for methods 1–8 are **not** “potential novel contribution.”
The only conditional novelty is the *package* (last row), and it is a
protocol/measurement claim, not a new identity.

---

## 1. Symbolic limits — known standard

**Why this label.** Computing symbolic limits is a solved CAS facility
for stated function classes: Gonnet–Gruntz hierarchical series (ISSAC
1988), Gruntz thesis (ETH 1996; Maple and SymPy implementations),
Shackell asymptotics, with an undecidability backdrop (Richardson 1968).
`sympy.limit` is the current confluence backend.

**Track-V delta.** Budgets, cascade, and “timeout → UNKNOWN never ZERO”
are **engineering adaptation** of an existing engine contract
(`verifier.py`, `CERTIFICATION_SCOPE.md`), not a new limit algorithm.
They do not upgrade the primary label. A cascade that fails closed is
how a responsible CAS wrapper behaves, not a publication claim.

**False-novelty sentences to delete.** “We give a new limit algorithm.”
“UNKNOWN is a new idea in computer algebra.” (Moxia abstain; CAS
unevaluated `Limit`; this engine’s three-way already exist.)

---

## 2. Confluent divided differences — engineering adaptation
(mathematics: known standard)

**Why the mathematics is known standard.**

\[
F[x,y]=\frac{F(x)-F(y)}{x-y},\quad
F[x,x]=F'(x),\quad
\lim_{y\to x}F[x,y]=F[x,x]
\]

Newton (1711 / 1670s), Conte–de Boor (1980), de Boor (2005). Continuity
in the nodes *is* interpolation confluence. Implementing `newton_first`
/ `limit_generic_to_degenerate` is a textbook constructor.

**Why Track-V use is engineering adaptation, not novelty.** Routing a
compiled `CONFLUENCE` / `NEWTON_DD` obligation to reconstruction of
\(F[x,y]\) and \(F[x,x]\) instead of Gruntz on the source Piecewise is
a *strategy choice* (`DD_CERTIFICATE`). It does not add an identity.
It may produce `V_GAIN` on obligations whose shape is already a DD
claim; that gain is empirical engineering.

**Why it is not potential novelty.** The identity being checked is
classical. Checking a classical identity on catalog members is a
verifier. If members are already spelled as difference quotients,
success is compiler/language gain (`C_GAIN`), not discovery and not
a new verification theory.

**Two-confluence trap.** Interpolation confluence ≠ Knuth–Bendix /
e-graph confluence. Do not cite egg as prior work *for this identity*,
and do not cite de Boor as prior work *for equality saturation*.

---

## 3. Hermite identities — engineering adaptation
(mathematics: known standard)

**Why the mathematics is known standard.** Hermite 1878; Traub 1964;
Conte–de Boor §2.7; de Boor 1978/2005; Genocchi–Hermite integral.
\(F[a,\ldots,a]_{k+1}=F^{(k)}(a)/k!\) is osculatory interpolation.

**Why Track-V use is engineering adaptation.** Obligation kind
`HERMITE_DD` rebuilds a multiplicity window and residual-compares.
Same certificate pattern as §2, higher multiplicity.

**Why it is not potential novelty.** “Hermite divided differences as
the confluence mechanism” is a correct *scientific reading* of some
physics kernels (human ladder L5 in the 2026-08-21 note). It is not
a new mathematical object. This track does not invent
\(\mathfrak M_\Gamma,\mathfrak T_\Gamma\). Using \(H_1,H_2\) as gold
names in a verifier is leakage, not contribution.

---

## 4. Compositional proof — engineering adaptation
(mathematics / CS: known standard)

**Why known standard.** Congruence of equality; Floyd–Hoare /
assume-guarantee; SMT lemmas; e-class congruence without a runtime.
Splitting a goal into independently checkable obligations is the
default of every proof assistant.

**Why Track-V use is engineering adaptation.** The experimental
obligation IR (`EQUALITY`, `LIMIT`, `NEWTON_DD`, …) plus the rule
that parent ZERO requires child ZERO under trusted combinators, with
`COMPILE_FAILURE` ≠ `UNKNOWN`. That IR is this repository’s language,
not a published proof calculus. Shipping it is systems work.

**Why it is not potential novelty as a method.** A paper that claims
“compositional verification of symbolic identities” as new will be
referred to SMT, ITP, and egg. The remaining question is empirical:
does the split turn Guo-scale `UNKNOWN` into honest `ZERO`/`NONZERO`
without false decomposition acceptance?

---

## 5. Factoring before proof — engineering adaptation
(mathematics: known standard)

**Why known standard.** Content/primitive split; multivariate `factor`;
FORM CSE/Horner; IBP pipelines stripping rational prefactors.

**Why Track-V use is engineering adaptation.** Strategy `FACTOR_LOCAL`:
exact spectator \(S\) with proven \(S\neq 0\) under declared
assumptions, then verify kernel \(K\). Contract: false decomposition
acceptance = 0; no invented positivity; no Guo gold spectators.

**Why it is not potential novelty.** Factoring a residual is algebra
101. The only interesting part is *soundness under this engine’s
assumption policy* (fail closed if \(S\) may vanish). That is
discipline, not a theorem.

---

## 6. Certificates — engineering adaptation
(idea: known standard)

**Why known standard.** Certifying algorithms (McConnell et al. 2011;
LEDA); WZ rational certificates (*A=B*, 1996); Freivalds / Schwartz–
Zippel as NONZERO witnesses; ITP kernels as the strong form.

**Why Track-V use is engineering adaptation.** Treat
\((F,\{z_i\},\{m_i\},\mathcal O)\) as a witness; the checker rebuilds
\(\mathcal O[F]\) and residual-compares. Composition trees and
spectator factorizations are the same idea. Level-1 engine semantics
only (`CERTIFICATION_SCOPE.md`).

**Forbidden upgrade.** Randomized PIT, `N[..., 30]`, or `PossibleZeroQ`
as a ZERO certificate. Those are known standard **for other problems**
and **out of contract** here. Using them would be a regression, not
an adaptation.

**Why it is not potential novelty.** “Certificate” is a crowded word.
WZ already means short algebraic witnesses for identities. LEDA already
means untrusted algorithm + trusted checker. Lean already means kernel
certificates. This track’s witnesses are reconstruction terms, not a
new proof object.

---

## 7. E-graphs / equality saturation — known standard

**Why this label.** Tate 2009; egg 2021; egglog 2023; Ruler; Enumo;
Guided EqSat 2024; LGuess 2025. Knuth–Bendix rewriting confluence is
older still.

**Track-V use.** Neighbor for polynomial/rational fragments. Not
installed here. Not the interpolation-confluence backend. A restricted
Python e-graph is a mismatch and must stay documented as such
(frozen `corpus.md`).

**Why it is not potential novelty.** Lack of an egg runtime on this
host is a limitation, not a contribution. Do not claim EqSat
completeness. Do not omit an e-graph baseline in a PL venue without
a restricted substitute already named B6.

---

## 8. Special-function identities — engineering adaptation
(mathematics: known standard)

**Why known standard.** DLMF; polygamma recurrence/reflection;
SymPy’s `polygamma` table; WZ/holonomic methods for sums; Rubi and
HEP packages as large tables.

**Why Track-V use is engineering adaptation.** Strategy
`SPECIAL_FUNCTION_LOCAL`: apply an identity **already in SymPy** to a
local call, then residual-check. V5: do not invent masters.

**Why it is not potential novelty.** Naming \(\psi\), a Meijer-\(G\),
or a thermal factor is ordinary. Hardcoded Guo identities would be
worse than non-novel: they would be gold leakage and protocol
violations. Table lookup is F4 in the frozen beyond-LGG taxonomy,
not F5/F6 invention.

---

## \*. Packaged fail-closed routing — potential novel contribution
(conditional, not a method in §§1–8)

**What it would be, if anything.** A measured protocol:

> Frozen, already-proposed scientific representation hypotheses are
> rescored by a router that may discharge confluence by Newton/Hermite
> reconstruction, factor spectators exactly, and apply local SymPy
> special-function tables, with timeout/size-guard remaining `UNKNOWN`,
> numeric agreement never ZERO, false ZERO = 0, and gains labeled
> `V_GAIN` vs `C_GAIN` vs `NO_GAIN` without mutating historical runs.

**Why this is the only row that may ever be called a contribution.**
No retrieved system jointly does (i)–(vi) in `METHODS.md` §10 on
`Sum`/`Piecewise`/indexed physics kernels. Closest fragments: Gruntz
(limits), Conte–de Boor (DD math), LEDA/WZ (certificates), egg/LGuess
(rewrite chains, wrong object), Moxia (abstain, wrong task), FORM/IBP
(domain CAS, no untrusted \(H\)).

**Why it is still not a claim.** This literature pack runs no rescore.
`STATUS.md` has not closed Track V. A gap is not a result. If `DD_CERTIFICATE`
only fires on members that already *are* difference quotients, the
package collapses to compiler gain. If Guo is the only scientific
family, C3-style generalization is false. If any false ZERO appears,
the merge gate fails and the package is a bug.

**Even if `V_GAIN` appears, do not say:**

- first LLM+verifier (crowded; frozen `novelty_boundary.md`);
- formal proof / machine-checked theorem;
- we invented divided differences / Hermite / masters;
- e-graph confluence of physics kernels;
- we discovered \(\Phi_\Gamma\) or L4–L7.

The remaining sentence, if experiments support it, is the frozen
compactification positioning restricted to layer V: *already-proposed*
hypotheses can be adjudicated at Guo scale without a giant global
limit, under engine semantics. That is a **verification-engineering**
result, not a mathematics result.

---

## Upgrade experiments (what would change a label)

Literature does not generate these numbers. Owned by V1–V8 + eval,
not by V9.

1. **Generic before Guo.** `DD_CERTIFICATE` ZERO on non-Guo confluence
   obligations whose members are *not* already spelled \(F[x,y]\),
   gold names absent, false ZERO = 0.
2. **Symbolic baselines.** Same frozen obligations, no new proposer:
   (i) `DIRECT` Gruntz/residual; (ii) textbook Newton/Hermite constructor
   given \(F\) and nodes; (iii) SymPy `simplify`/`factor`; (iv) restricted
   e-graph if available. Method claim needs a gap after (i)–(iii)
   labeled `V_GAIN`, not `C_GAIN`.
3. **Falsifiers (V7).** Wrong sign DD; coincident 0/0 sold as \(F'\);
   vanishing spectator; timeout sold as ZERO; numeric “certificate”;
   leaked gold names. All must stay NONZERO or UNKNOWN.
4. **Gain accounting.** Frozen 81 hypotheses rescored; report
   `V_GAIN`/`C_GAIN`/`NO_GAIN` separately; COMPILE_FAILURE never
   laundered into UNKNOWN or ZERO.
5. **Second family.** At least one non-Guo scientific expression
   family, or the package stays n=1.

Until those exist, the honest status is: **methods classified;
Newton/Hermite not novelty; no Track-V method result.**

---

## Claims a knowledgeable reviewer would reject immediately

| Claim | Why it dies | Who cites it |
|---|---|---|
| “We invented divided differences / Hermite interpolation” | Newton, Hermite, Conte–de Boor, de Boor 2005 | any numerical analyst |
| “Confluent DD is a new limit algorithm” | it is the definition of \(F[x,x]\) | Gruntz + de Boor readers |
| “We invented proof certificates” | LEDA; WZ; ITP kernels | PL / combinatorics / ITP |
| “E-graphs already do this confluence” | rewriting ≠ interpolation confluence | PL *and* NA reviewers |
| “Factoring residuals is the contribution” | Gauss; FORM; IBP | CAS / HEP users |
| “Local polygamma rewrite is representation invention” | DLMF; SymPy table | special-function users |
| “Formal certification” | SymPy residual + probes; UNKNOWN fail-closed | Lean/e-graph reviewer |
| “Timeout converted to ZERO is conservative” | it is a false ZERO | this engine’s own contract |
| “V9 literature is a method result” | no rescore, no tests required | ourselves |

---

## Positioning sentence (not a title)

> Symbolic limits, Newton and Hermite divided differences, compositional
> proof, spectator factoring, algebraic certificates, e-graphs, and
> special-function tables are standard tools. Track V asks whether those
> tools, routed fail-closed over already-proposed scientific
> representation obligations, can replace a giant global `sympy.limit`
> without false ZERO. That is an engineering question, not a claim that
> the mathematics is new.
