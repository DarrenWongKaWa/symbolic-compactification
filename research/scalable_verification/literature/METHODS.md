# Track V verification methods

Audit date: 2026-08-28.
Object: **scalable compositional verification** of *already-proposed*
representation hypotheses (`research/scalable_verification/PROTOCOL.md`).
This pack is literature for layer **V**, not discovery (layer D).

No LLM calls. Frozen hypotheses only. Retrieval: classic NA/CAS/PL
sources plus arXiv and venue pages already used in frozen compactification
and representation-invention audits. Unconfirmable titles are omitted.
Numeric tables from search snippets are not treated as results.

**Question.** Can a compiled obligation that is currently `UNKNOWN` under
a giant global `sympy.limit` / residual become `ZERO` or `NONZERO`
because the *verifier* improved, without a false ZERO?

**Not the question.** Inventing Newton/Hermite divided differences,
inventing special-function masters, or claiming a Lean/e-graph kernel.

Newton/Hermite DD mathematics is **known standard**. It is not a Track-V
contribution. See `CLASSIFICATION.md`.

Frozen literature this pack does not rewrite:

- Compactification proposer–verifier survey:
  `research/literature/{corpus,novelty_boundary}.md` (freeze `13814ba`).
- Representation-invention novelty:
  `research/representation_invention/literature/NOVELTY.md`.
- Certification language:
  `research/verification/CERTIFICATION_SCOPE.md`
  (engine semantics, not formal proof).

Intended reader: Track-V implementers (V1–V8) and authors, before any
paper sentence about “certificates” or “confluence.”

---

## 0. Two words that must not be mixed

| Sense | Field | Object | Closest systems |
|---|---|---|---|
| Interpolation confluence | NA | nodes coalesce; DD → derivatives | Newton, Hermite, Conte–de Boor, de Boor 2005 |
| Rewriting confluence | term rewriting / EqSat | joinability of rewrite paths | Knuth–Bendix, egg, egglog |

Track V uses the **first** sense when it says “confluent DD.” E-graphs
implement the second. Mixing them in a draft is a reviewer-kill
(already recorded in `research/representation_invention/literature/NOVELTY.md`).

Timeout / size-guard is `UNKNOWN`, never `ZERO`
(`PROTOCOL.md`; engine `verifier.py`). `COMPILE_FAILURE` ≠ `UNKNOWN`.
Numeric agreement, `PossibleZeroQ`, and Schwartz–Zippel probes are
**never** a ZERO path (`CERTIFICATION_SCOPE.md`).

---

## 1. Symbolic limits

**What.** Decide \(\lim_{z\to z_0} E(z)\) in a computer-algebra system,
including one-sided and \(\infty\) limits, then compare the result to a
claimed degenerate form.

**Canonical sources.**

- Heuristic series / L'Hôpital / cancellation-prone recursive expansion:
  the pre-1990s CAS default.
- Hierarchical / most-rapidly-varying (MRV) expansions:
  Gonnet and Gruntz, ISSAC 1988 (LNCS 358); Gruntz, “Limit Computation
  in Computer Algebra,” 1992.
- Gruntz algorithm: Dominik Gruntz, *On Computing Limits in a Symbolic
  Manipulation System*, ETH Zürich Diss. ETH No. 11432, 1996
  (doi:10.3929/ethz-a-001631582). Rewrite the expression in the MRV
  class, expand in a positive infinitesimal \(\omega\to 0^+\), read the
  leading term. Implemented in Maple; SymPy’s `sympy.series.gruntz`
  is an explicit rewrite of that thesis.
- Asymptotics of exp-log functions: Shackell, *J. Symbolic Comput.*
  1990; later transseries work (van der Hoeven).
- Undecidability of identity for a class of elementary real functions:
  Richardson, *J. Symbolic Logic* 33 (1968) 514–520. Equality of
  general exp/sin/abs expressions is not a decision procedure.
  “How to Recognize Zero,” *J. Symbolic Comput.* 24 (1997) 627–645.
- Davenport, “Equality in Computer Algebra and Beyond,” *J. Symbolic
  Comput.* 34 (2002) 259–270: CAS equality is *engine semantics*, not
  a complete theory of real functions.

**What CAS already does.** `sympy.limit` (Gruntz + heuristics), Maple
`limit`, Mathematica `Limit`. This is the current confluence backend
in `research/representation_invention/obligations/verify.py` (`_v_limit`
→ `take_limit` → `sympy.limit`). Unevaluated `Limit`, exceptions, and
indeterminate forms are `UNKNOWN`.

**Track-V use.** Strategy `DIRECT` / confluence cascade (V3). Budgeted
limit is the honest fallback. It is also the **failure mode** on
Guo-scale Piecewise polygamma kernels: expression swell, MRV rewrite
failure, or wall-clock timeout. Those must stay `UNKNOWN`. Never convert
timeout to ZERO.

**Limits of the method (why Track V exists).** Gruntz is complete for a
stated exp-log class, not for arbitrary `Sum`/`Piecewise`/polygamma
physics kernels. Direction and branch cuts are scientific assumptions
(`AGENTS.md` rules 14–15). A global limit of a 20 kB residual is not a
scalable verifier.

**Classification.** Known standard. See `CLASSIFICATION.md` §1.

---

## 2. Confluent divided differences (as a verification device)

**Mathematics (not novelty).** For a sufficiently smooth \(F\),

\[
F[x,y]=\frac{F(x)-F(y)}{x-y},\qquad
F[x,x]:=F'(x),\qquad
\lim_{y\to x} F[x,y]=F[x,x].
\]

Continuity of divided differences in the nodes is the reason a
difference quotient and a derivative are the same analytic object
(de Boor, “Divided Differences,” *Surveys in Approximation Theory* 1
(2005) 46–69, arXiv:math/0502036, especially §§1–2, 8–9). Newton form
coefficients *are* Hermite interpolants at the listed nodes with stated
multiplicities. Historical sources: Newton, *Methodus Differentialis*
(1711; unequal-interval interpolation treated by the 1670s); Conte and
de Boor, *Elementary Numerical Analysis*, 3rd ed. (1980), Ch. 2 and
§2.7 osculatory interpolation. (The brief’s “Conti/de Boor” is this
pair: **S. D. Conte and Carl de Boor**, not Costanza Conti’s spline
papers.)

**What CAS already does.** Any interpolation constructor
(`InterpolatingPolynomial`, Newton tables) already *builds* \(F[x,y]\)
when \(F\) and the nodes are given. A compiler that, given those
fields, checks \(A=(F(x)-F(y))/(x-y)\) is a checker, not a discovery
and not a new limit algorithm.

**Track-V use.** Strategy `DD_CERTIFICATE` (V4). If a compiled
obligation claims that a generic branch is a Newton DD of an explicit
\(F\) and that the coincident branch is the repeated-node value, then
the confluence identity is a **reconstruction check**, not a Gruntz
call on the whole kernel:

1. Rebuild \(F[x,y]\) from declared \(F\) and nodes.
2. Compare to the generic member (`ZERO`/`NONZERO` by residual).
3. Rebuild \(F[x,x]=F'(x)\) (or the declared multiplicity).
4. Compare to the degenerate member.
5. Optionally record the confluence identity as discharged *by the
   DD definition*, without `sympy.limit` on the source Piecewise.

This is the intended replacement for “giant global `sympy.limit`”
on obligations whose *shape* is already a confluence claim.

**Failure modes that must stay UNKNOWN / NONZERO.**

- Verbal “divided difference” without members, nodes, \(F\), and
  reconstruction (`representation_invention/PROTOCOL.md` rule 3).
- Coincident nodes substituted into `newton_first` (0/0, not \(F'\)).
- Swapped generic/degenerate roles; wrong sign; wrong denominator.
- Using interpolation confluence to paper over *rewriting* joinability.
- Guo-specific polygamma identities hardcoded as ZERO rules
  (`PROTOCOL.md`: no Guo-specific ZERO identities).

Local confluence (P1, G1/R0, `confluent_representation`) is **not**
DD-OK and is **not** a Hermite certificate.

**Classification.** Mathematics: known standard. Use as a limit-avoiding
checker: engineering adaptation. Not a novel identity.

---

## 3. Hermite identities

**Mathematics (not novelty).** Hermite interpolation matches derivatives
as well as values (C. Hermite, “Sur la formule d'interpolation de
Lagrange,” *J. Reine Angew. Math.* 84 (1878) 70–79). Repeated-node
Newton table:

\[
F[\underbrace{a,\ldots,a}_{k+1}]=\frac{F^{(k)}(a)}{k!}.
\]

So \(F[x,x]=F'(x)\) and \(F[x,x,x]=F''(x)/2\). Traub, “On
Lagrange—Hermite interpolation,” *J. SIAM* 12(4) (1964) 886–891;
de Boor 1978, *A Practical Guide to Splines*; Conte–de Boor 1980 §2.7.
The Genocchi–Hermite simplex integral (de Boor 2005, §9) makes
continuity in coalescing nodes analytic rather than formal.

Supported reconstruction windows in this repo’s constructor
(`research/representation_invention/dd/`): \(F[x,y]\), \(F[x,x]\),
\(F[x,x,y]\), \(F[x,y,y]\), \(F[x,x,x]\). Mixed unblocked sequences
such as \(F[x,y,x]\) are not guessed.

**Track-V use.** Same certificate engine as §2, for multiplicity \(>1\).
A Hermite identity is a *check* that a degenerate Piecewise stratum
equals the declared confluent DD of \(F\). It is not a new special
function and not a master-function invention.

**What must not be claimed.** “We introduce Hermite divided
differences.” Any numerical analyst will desk-reject that sentence.

**Classification.** Known standard. Engineering adaptation: wire the
textbook reconstruction into obligation kinds `HERMITE_DD` /
`CONFLUENCE` instead of Gruntz.

---

## 4. Compositional proof

**What.** Prove \(E=0\) by proving independently checkable pieces
whose combination implies the original identity, rather than simplifying
\(E\) as one term.

**Canonical sources.**

- Congruence: if \(A=A'\) and \(B=B'\) then \(A\circ B = A'\circ B'\)
  for constructors \(\circ \in \{+,\times,\circ,\ldots\}\). This is
  the same idea as e-class congruence (Tate et al., POPL 2009) without
  requiring an e-graph runtime.
- Floyd–Hoare / assume-guarantee compositional verification of
  programs (classic software verification; not CAS). Clarke, Grumberg,
  Peled, *Model Checking*; Pnueli-style modular temporal proofs.
- Proof-producing decision procedures and SMT (Z3, CVC5): a theory
  solver returns a lemma or an unsat core, not a monolithic “simplify
  the world.”
- Obligation IR in this repository: kinds `EQUALITY`, `SUBSTITUTION`,
  `PERMUTATION`, `DERIVATIVE`, `LIMIT`, `NEWTON_DD`, `HERMITE_DD`,
  `CONFLUENCE`, `RECURRENCE`, `MASTER_INSTANCE`,
  `BASIS_RECONSTRUCTION`
  (`research/representation_invention/obligations/`).

**Track-V use.** V1 decomposition. A global residual on a huge source
expression is not the unit of work. The unit is one compiled obligation
about named catalog members. Compositional soundness requires:

- each child verdict is the engine three-way;
- `ZERO` children combine only by trusted constructors (sum of ZEROs,
  product with an exact nonzero spectator, reconstruction
  \(A_i=\mathcal O_i[F]\));
- any child `UNKNOWN` or timeout makes the parent `UNKNOWN`;
- any child `NONZERO` makes the parent `NONZERO` unless the parent
  claim was disjunctive (it is not, in this IR);
- false decomposition acceptance = 0 (a split that does not imply
  the parent must not be labeled ZERO).

**What this is not.** A Lean tactic language. A new proof theory.
Discovery of \(F\). Compiler gain (old P1 output becoming checkable
because the IR improved) must be labeled `C_GAIN`, never `V_GAIN`
(`PROTOCOL.md`).

**Classification.** Known standard as a verification idea; engineering
adaptation as an obligation IR over scientific CAS residuals.

---

## 5. Factoring before proof

**What.** If a residual factors as \(R = S\cdot K\) and \(S\) is an
exact nonzero *spectator*, then \(R=0\) iff \(K=0\). Prove or refute
the smaller kernel.

**Canonical sources.**

- Polynomial content / primitive part; Gauss’s lemma; multivariate
  factorization (Kaltofen, 1980s; standard CAS `factor`).
- Common-subexpression / Horner compactification in FORM
  (Kuipers, Ueda, Vermaseren, “Compactifying formulas with FORM,”
  RADCOR 2013 and FORM documentation).
- IBP/Laporta pipelines factor out rational prefactors before reducing
  integral families (FIRE, Kira, Reduze): linear algebra on the kernel,
  spectators stripped first.
- CSE in compilers: semantically the same “don’t prove the boring
  factor,” different object.

**Track-V use.** Strategy `FACTOR_LOCAL` (V2). Exact spectator-factor
split on a compiled obligation. Typical spectators on scientific
kernels: rational functions of declared symbols, \(1/\pi\), thermal
occupation factors that are identical on both sides of an identity,
permutation signs already bound in the obligation.

**Soundness rules.**

- \(S\) must be proven nonzero under *declared* assumptions, or the
  split is `UNKNOWN` (do not invent `z>0`).
- The factorization must be exact (SymPy `factor` / structural product),
  not a numeric GCD, not a cancelled series tail.
- Dropping a factor that can vanish on the domain is a false ZERO.
- V2 contract: false decomposition acceptance = 0.
- No Guo-specific spectators (`Phi_Gamma`, gold kernel names).

**Classification.** Known standard algebra / HEP engineering.
Adaptation: apply the split to frozen representation obligations
before residual/limit, as a router input, not as a new identity.

---

## 6. Certificates

**What.** A checker that is simpler than the search that produced the
claim. The algorithm may be untrusted; the certificate plus a small
checker is the evidence.

**Canonical sources.**

- Poincaré-style: a proof is a witness that is easier to check than
  to find.
- Certifying algorithms: McConnell, Mehlhorn, Näher, Schweitzer,
  “Certifying algorithms,” *Computer Science Review* 5(2) (2011)
  119–161. Output \((y,w)\) such that a simple checker accepts
  \((x,y,w)\) iff \(y\) is a correct output for \(x\). LEDA used this
  as a software-reliability method. This is the right *slogan* for
  Track V: the proposer (and even the CAS limit engine) need not be
  trusted if a cheap checker re-verifies a witness.
- Wilf–Zeilberger certificates: Wilf and Zeilberger, “Rational
  functions certify combinatorial identities,” *J. Amer. Math. Soc.*
  3 (1990) 147–158; Zeilberger, “The method of creative telescoping,”
  *J. Symbolic Comput.* 11 (1991) 195–204; Petkovšek, Wilf,
  Zeilberger, *A=B* (1996). A rational \(R(n,k)\) is a short witness
  that a hypergeometric identity holds; checking it is rational
  arithmetic. **Wrong object** for Guo Piecewise polygamma kernels,
  right *pattern* (short witness, cheap checker).
- Polynomial identity testing: Schwartz (1980), Zippel (1979),
  DeMillo–Lipton; Freivalds’ technique for matrix products. Randomized
  probes give a **NONZERO** witness with one-sided error. In *this*
  engine, rational probes already implement the NONZERO side
  (`verifier.py`). They are **forbidden as a ZERO path**. Using PIT
  “probably zero” as ZERO would violate `CERTIFICATION_SCOPE.md`.
- Proof-producing CAS / ITP kernels (Isabelle/Sledgehammer, Lean,
  Coq): stronger than this project. Unavailable here; must not be
  claimed (`novelty_boundary.md` non-claim 2).

**Track-V certificates (engineering).** A DD/Hermite reconstruction
is a certificate of a confluence claim:

- witness = \((F,\{z_i\},\{m_i\},\mathcal O)\);
- checker = rebuild \(\mathcal O[F]\) and residual-compare to the
  catalog member;
- cost ≪ Gruntz on the source kernel when \(F\) is small.

A compositional proof (§4) is a certificate tree. A factorization
(§5) is a certificate that \(R=S\cdot K\) with \(S\neq 0\).

**Honesty.** These are Level-1 engine-semantics certificates, not
Lean proofs. Allowed sentence: “the engine certified
`current − candidate = 0` under SymPy semantics, policy snapshot S,
and declared assumptions A.” Forbidden: “we formally proved the
identity.”

**Classification.** Certificate *idea*: known standard. DD-as-certificate
for Piecewise confluence of already-proposed hypotheses: engineering
adaptation. Not a new certificate calculus.

---

## 7. E-graphs / equality saturation

**What.** Record equalities instead of destroying terms; extract a
profitable representative. Soundness is rewrite-rule soundness plus
congruence closure.

**Canonical sources.** Tate, Stepp, Tatlock, Lerner, POPL 2009 /
*LMCS* 2011, arXiv:1012.1802. egg: Willsey, Nandi, Wang, Flatt,
Tatlock, Panchekha, POPL 2021, doi:10.1145/3434304. egglog: Zhang
et al., PLDI 2023. Ruler (OOPSLA 2021) and Enumo (OOPSLA 2023)
synthesize rules. Guided equality saturation: Kœhler et al., POPL 2024
(human checkpoints). LGuess: Peng, Ji, Xiong, arXiv:2511.00403
(LLM checkpoints; multivariable **polynomial factorization**).
Knuth–Bendix (1970) is the classical completion procedure whose
confluence is *rewriting* confluence.

**Track-V use.** A serious neighbor for *polynomial/rational*
identity fragments and for rewrite-chain obligations. Not a neighbor
for interpolation confluence of polygamma Piecewise kernels unless
those kernels are first compiled into a trusted rewrite theory (they
are not). This host has no egg runtime (frozen `corpus.md`). A
restricted Python e-graph that cannot encode `Sum`/`Piecewise` is
not a fair baseline and must stay labeled as such.

**Must not claim.** Equality saturation, e-graph completeness, or
rewrite-confluence of a theory (`novelty_boundary.md` non-claim 6).
“E-graphs already do confluence” is a type error (§0).

**Classification.** Known standard. Using EqSat as one router arm for
polynomial subgoals, if a runtime appears: engineering adaptation.
Absence of egg is not novelty.

---

## 8. Special-function identities

**What.** Named identities of \(\psi^{(n)}\), \(\Gamma\), polylogarithms,
Fermi–Dirac factors, etc., used *locally* so a residual simplifies
without inventing a new master.

**Canonical sources.**

- NIST *Digital Library of Mathematical Functions* (DLMF); Abramowitz
  and Stegun.
- Polygamma recurrence, reflection, and multiplication formulas, e.g.
  \[
  \psi^{(n)}(z+1)=\psi^{(n)}(z)+(-1)^n n!\,z^{-n-1}.
  \]
  These are in every CAS special-function table, including SymPy
  `polygamma`.
- Hypergeometric / holonomic certificates: Wilf–Zeilberger / creative
  telescoping (§6); Karr’s algorithm for \(\Pi\Sigma\) fields; the
  holonomic systems approach (Zeilberger; Chyzak; Koutschan).
- Rule-based integration tables (Rubi) and HEP special-function
  packages (HypExp, HarmonicSums, PolyLogTools): large *tables*, not
  invention.
- V5 contract: “Polygamma-local identities already in SymPy. Do not
  invent masters.”

**Track-V use.** Strategy `SPECIAL_FUNCTION_LOCAL`. Apply a *named,
already-implemented* rewrite to a local kernel (e.g. one `polygamma`
call), then residual-check. Strategy `SERIES_LOCAL` is the same idea
with a budgeted series of a small factor, not of the whole Guo sum.

**Forbidden.**

- Hardcoded Guo gold identities (`Phi_Gamma`, \(\mathfrak M_\Gamma\),
  \(\mathfrak T_\Gamma\), nine generators) as ZERO rules.
- Treating `polygamma(1,z)=d/dz polygamma(0,z)` as representation
  invention (it is a table lookup; F4 in the beyond-LGG taxonomy).
- Promoting a series truncation or a 30-digit numeric match to ZERO.
- Inventing a meromorphic master \(F\) on this track (that is Track D,
  and even there naming a master is not novelty).

**Classification.** Known standard. Engineering adaptation: localize
SymPy’s existing table to a subexpression so the global residual
becomes cheap. Not a new special-function theory.

---

## 9. How Track V should compose these methods

Router (V6) chooses a strategy; it does **not** decide ZERO
(`research/scalable_verification/api.py`):

| Strategy | Primary method | Fallback |
|---|---|---|
| `DIRECT` | symbolic limit / residual | `UNKNOWN` on timeout |
| `FACTOR_LOCAL` | spectator split, then inner strategy | abort split if \(S=0\) possible |
| `SERIES_LOCAL` | budgeted local series | never global series of Guo |
| `DD_CERTIFICATE` | Newton/Hermite reconstruction | `DIRECT` limit if nodes/F missing |
| `SPECIAL_FUNCTION_LOCAL` | SymPy table identity | `UNKNOWN` if not in table |
| `UNKNOWN` | fail closed | — |

Gain labels (`PROTOCOL.md`):

- `V_GAIN`: same compiled obligation, previously `UNKNOWN`, now
  `ZERO`/`NONZERO` because the verifier improved.
- `C_GAIN`: previously uncompiled, now compiles then verifies.
- `NO_GAIN`: verdict unchanged.

False ZERO = 0 is a merge gate. Adversarial review is V7’s job, not
this pack’s.

---

## 10. Closest verification systems (not to copy slogans from)

Reuse frozen `research/literature/corpus.md` for proposer–verifier
crowding. Distance *as verifiers*:

| System | What it checks | vs Track V |
|---|---|---|
| Gruntz / `sympy.limit` | exp-log limits | current bottleneck, not the upgrade |
| egg / LGuess | rewrite chains on polynomials | wrong confluence sense; no egg here |
| WZ / *A=B* | hypergeometric sum certificates | wrong object (not Piecewise DD) |
| Lean/Isabelle kernels | formal proofs | stronger; unavailable; must not claim |
| Moxia/AXIOM CAS handler | contest-math answers + abstain | abstain ≈ UNKNOWN; not residual identity |
| O-Forge `Resolve` | asymptotic inequalities | not two-expression residual |
| FORM/FIRE/Kira | HEP algebra / IBP | domain CAS; no untrusted \(H\) contract |
| Engine `verifier.py` | structural residual + rational probes | global; does not scale to Guo limits |

No retrieved system jointly (i) takes frozen, already-proposed
scientific representation hypotheses, (ii) routes confluence
obligations to Newton/Hermite reconstruction instead of Gruntz,
(iii) factors spectators exactly, (iv) keeps `UNKNOWN` on timeout,
(v) forbids numeric ZERO, and (vi) accounts `V_GAIN` vs `C_GAIN`
without mutating historical runs.

That joint *packaging* is a **gap**, not a proof of novelty. The
eight methods above are not new. See `CLASSIFICATION.md`.

---

## 11. Self-adversarial notes

1. A DD certificate on members that are already spelled
   \((F(x)-F(y))/(x-y)\) is compiler/language gain, not V_GAIN.
2. `sympy.limit` succeeding on a *small* reconstructed DD is not
   evidence that Guo-scale limits are solved; it is evidence that
   the obligation was localized.
3. Randomized PIT / high-precision numerics must not be smuggled in
   as ZERO “certificates.”
4. E-graph extraction cost (AST size) is the wrong scientific
   compactness metric (frozen `novelty_boundary.md`).
5. Special-function table hits can look like master invention; they
   are not.
6. Guo n=1 cannot carry a generalization claim even if V_GAIN appears.
7. Track D remains locked until `TRACK_V_CLOSED.md` exists. This
   literature pack does not close Track V.

## Unconfirmed / not used

- Papers whose titles were recalled but not retrieved with matching
  authors/year/venue.
- Numeric Gruntz/WZ/LGuess solve-rate tables from search snippets.
- Any claim that V1–V8 already produced V_GAIN (those directories are
  owned elsewhere; this pack is documentation).
