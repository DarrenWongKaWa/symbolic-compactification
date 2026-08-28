# Track V3 methods — iterated one-parameter confluence

Audit date: 2026-08-28.
Object: **reduction of a multi-parameter / five-branch confluent
family into a sequence of exact one-parameter confluence steps**
(`research/iterated_confluence/PROTOCOL.md`). This pack is
literature for Track **V3**, not discovery (layer D / D2), not a
rewrite of Track V or Track V2, and not a method result.

No LLM calls. Frozen 7 Guo families from Track V2 (`fe53ebc`;
`FROZEN_INPUTS_V3.json`, n=7) only. Retrieval: classic
analysis / NA / CAS / PL sources already used in frozen
compactification, representation-invention, Track V, and Track V2
audits, plus the iterated-vs-joint and multivariate-rational-limit
textbook/CAS line. Unconfirmable titles are omitted.

**Question.** Can a five-branch confluent family be reduced into
a sequence of exact one-parameter confluence steps whose local
symbolic complexity is comparable to the already-certified
two-member Guo cases, and can those local certificates be
composed into `FAMILY_ZERO` or `FAMILY_NONZERO` without
Guo-specific identities?

**Not the question.** Inventing iterated limits, inventing the
distinction between iterated and joint limits, inventing Newton
or Hermite divided differences, inventing a recurrence for
repeated nodes, or claiming a Lean/e-graph kernel. Iterated
limits are **known standard**. The Hermite recurrence is
**known standard**. Newton DD is **known standard**.
`PATH_ZERO` does not imply joint confluence. See
`CLASSIFICATION.md`.

Frozen literature this pack does not rewrite:

- Compactification proposer–verifier survey:
  `research/literature/{corpus,novelty_boundary}.md`.
- Representation-invention novelty:
  `research/representation_invention/literature/NOVELTY.md`.
- Track V verification methods:
  `research/scalable_verification/literature/{METHODS,CLASSIFICATION}.md`.
- Track V2 family-certificate methods:
  `research/multibranch_verification/literature/{METHODS,CLASSIFICATION}.md`.
- Certification language:
  `research/verification/CERTIFICATION_SCOPE.md`
  (engine semantics, not formal proof).

Intended reader: Track V3 implementers (V3-A..J) and authors,
before any paper sentence about “iterated confluence,”
“path independence,” or “local-to-global certification.”

---

## 0. Words and scales that must not be mixed

| Sense | Field | Object | Closest systems |
|---|---|---|---|
| Interpolation confluence | NA | nodes coalesce; DD → derivatives | Newton, Hermite, Conte–de Boor, de Boor 2005, Hermite–Genocchi |
| Rewriting confluence | term rewriting / EqSat | joinability of rewrite paths | Knuth–Bendix, egg, egglog |
| Iterated limit | real analysis | nested one-parameter limits | Apostol, Rudin, Moore–Osgood, nested `limit` |
| Joint / simultaneous limit | real analysis | \((x,y)\to(a,b)\) in the product topology | same textbooks; Cadavid-style multivariate CAS |

Track V3 uses interpolation confluence *and* iterated limits.
Mixing either with Knuth–Bendix confluence is a reviewer-kill
(already recorded in Track V, Track V2, and
representation-invention literature). Mixing iterated with joint
is the Track V3-specific reviewer-kill.

| Scale | Track | Object | Closed evidence |
|---|---|---|---|
| Pair | V | two-member `local_confluence` | 3 frozen Guo pairs ZERO; generic suite false ZERO = 0 (`38d6d4a`) |
| Family | V2 | 4–5 member graphs + recurrence + path consistency | **not closed**; 7 frozen hyps `FAMILY_UNKNOWN` (H-C, `fe53ebc`) |
| Iterated path | V3 | ordered one-parameter steps → `PATH_*` → `FAMILY_*` | **not closed**; freeze only (`dcfb90c`) |

A family is not certified because members share a list.
A path is not a family. `PATH_ZERO` is **never** `FAMILY_ZERO`
(`schema.py` `COMPOSITION_RULE`). `FAMILY_ZERO` is **never**
majority vote. Timeout / size-guard is `UNKNOWN`, never `ZERO`.
Numeric agreement, `PossibleZeroQ`, and Schwartz–Zippel probes
are **never** a ZERO path. `COMPILE_FAILURE` ≠ `UNKNOWN`.
Limit order is a scientific assumption (`AGENTS.md` rule 14):
path consistency is *checked*, not assumed.

---

## 1. Iterated limits

**What.** For \(f\) of several variables, an *iterated* (repeated)
limit is a nested sequence of one-parameter limits, for example

\[
\lim_{x\to a}\lim_{y\to b} f(x,y)
=\lim_{x\to a}\Bigl(\lim_{y\to b} f(x,y)\Bigr).
\]

Each inner limit is an ordinary one-variable limit in the remaining
free variables. The object Track V3 writes as a `PathCertificate`
— start member, ordered `PathStep`s, end member — *is* an
iterated limit along a declared coordinate order.

**Canonical sources.**

- Apostol, *Mathematical Analysis*, 2nd ed. (1974): double
  sequences and iterated vs simultaneous limits (including
  Theorem 8.39 on uniform convergence).
- Rudin, *Principles of Mathematical Analysis*, 3rd ed. (1976),
  Ch. 7: interchange of limits under uniform convergence.
- Every multivariable calculus course: iterated partial
  derivatives vs mixed partials (a sibling interchange); iterated
  integrals vs double integrals (Fubini as the integrable analog).
- CAS: nested `limit(limit(f, y, b), x, a)` in Maple / Mathematica
  / SymPy. This is the *default* way a univariate limit engine is
  applied in several variables.

**What CAS already does.** `sympy.limit` is univariate (Gruntz +
heuristics). A two-parameter Guo coalescence implemented as
`limit(limit(K, eps_m, eps_n), eps_ell, eps_n)` is an iterated
limit, not a joint one. Unevaluated `Limit`, exceptions, and
indeterminate forms are `UNKNOWN`.

**Track-V3 use.** Strategy: one `PathStep` = one one-parameter
confluence (optionally after spectator split). `compose_path_verdict`:
every required step `ZERO` ⇒ `PATH_ZERO`; any step `NONZERO` ⇒
`PATH_NONZERO`; else `PATH_UNKNOWN`. Empty path is `PATH_UNKNOWN`,
not `PATH_ZERO`.

**Already certified (do not re-prove as novelty).** Two-member
Guo local confluence after spectator factoring, ZERO on frozen
P2 pairs G0004/G0005 and G0008/G0009 (Track V `38d6d4a`). Those
same pairwise edges sit inside `guo-p2-s2-i4` and do **not** make
that 4-member family `FAMILY_ZERO` (Track V2 `fe53ebc`). They
are legal *steps* of a V3 path, not a family certificate.

**What must not be claimed.** “We introduce iterated limits.”
Any analyst will desk-reject that sentence. Reducing a double
limit to two single limits is the *definition* of an iterated
limit, not a research contribution.

**Classification.** Known standard. See `CLASSIFICATION.md` §1.

---

## 2. Joint limits versus iterated limits

**What.** The *joint* (simultaneous, double) limit
\(\lim_{(x,y)\to(a,b)} f(x,y)\) requires: for every \(\varepsilon>0\)
there is a neighborhood of \((a,b)\) in the product topology on
which \(|f-L|<\varepsilon\), except possibly at the point itself.
It is a stronger object than either iterated limit.

**Standard facts (not V3 theorems).**

1. If the joint limit exists and the inner one-parameter limits
   exist, then both iterated limits exist and equal the joint
   value.
2. The converse is false. Classic counter-example
   \(f(x,y)=xy/(x^2+y^2)\) at the origin: both iterated limits
   are \(0\); along \(y=mx\) the value is \(m/(1+m^2)\), so the
   joint limit does not exist.
3. Iterated limits may exist and *disagree*
   (e.g. \(f(x,y)=(x-y)/(x+y)\) along axes).
4. Sufficient condition for interchange: if one iterated limit
   exists *uniformly* and the other exists pointwise, then the
   joint limit exists and all three agree (**Moore–Osgood
   theorem**; Apostol; Rudin Ch. 7). Uniformity is an extra
   hypothesis, not a free gift from “the coordinates look like
   they commute.”

**Track-V3 use.** `PROTOCOL.md` / `schema.py`:

> Do not assume iterated limit = joint limit unless that equality
> is itself certified.

`require_path_independence=True` (the default on
`IteratedConfluenceCertificate`) means `FAMILY_ZERO` is forbidden
unless path consistency is `CONSISTENT_ZERO`. That is Moore–Osgood
honesty: without uniformity / \(C^k\) / an explicit consistency
check, nested one-parameter ZEROs do not certify a joint
coalescence such as \(\varepsilon(\ell),\varepsilon(m)\to\varepsilon(n)\)
together.

**Failure modes that must stay UNKNOWN / NONZERO.**

- Reordering limits silently to the order Gruntz happens to
  finish (`AGENTS.md` rule 14).
- Selling one successful iteration order as the joint limit.
- Invoking Moore–Osgood without a uniformity proof on the
  actual kernel.
- Treating Track V’s 2-member ZERO as a 2-parameter result.

**Classification.** Mathematics: known standard. The schema
flag is bookkeeping. Not a novel identity.

---

## 3. Path independence of limits

**What.** A statement that every declared route from a generic
member to a degenerate member yields the same reconstructed
value.

**Two standard meanings, both already known.**

| Meaning | Hypothesis | Conclusion |
|---|---|---|
| Real-analysis path independence | every continuous path \(\gamma(t)\to(a,b)\) gives the same \(\lim f\circ\gamma\) | still **not** the joint limit (there are functions with equal path limits along all curves of a restricted class, yet no joint limit) |
| Interpolation path independence | \(F\in C^k\); Hermite–Genocchi simplex integral | DD is jointly continuous in the nodes; order of coalescence does not matter |

Hermite–Genocchi (Genocchi; letter to Hermite; de Boor 2005 §9;
R. K. Alexander, “The Hermite–Genocchi Formula”):

\[
F[x_0,\ldots,x_k]
=\int_{\Sigma_k} F^{(k)}(t_0 x_0+\cdots+t_k x_k)\,dt.
\]

Textbook consequences when \(F\in C^k\): distinct-node DD extend
continuously to repeated nodes; simultaneous coalescence equals
every iterated one-parameter coalescence; the Newton table is
symmetric in the nodes.

**What must still be checked, not assumed.**

- The engine does not know that a Guo Piecewise polygamma
  kernel with occupation factors is \(C^k\) in the degeneration
  coordinates. Hermite–Genocchi is therefore **not** a free
  `CONSISTENT_ZERO`.
- Two coalescence paths to the same degenerate member must
  residual-compare (`PathConsistencyObligation`). Agreement is
  `CONSISTENT_ZERO`, one local fact, not a family verdict by
  itself. Disagreement is `INCONSISTENT_NONZERO`.
- One-sided vs two-sided limits, and
  \(\varepsilon(m)\to\varepsilon(n)\) vs \(m\to n\), are
  scientific assumptions. They live in `assumptions`, not in
  ZERO rules.
- Double-limit interchange on a kernel that still contains
  spectator poles is a false decomposition if the spectator is
  not certified nonzero (Track V `FACTOR_LOCAL` contract).

**Track-V3 use.** Owner V3-F (`consistency/`) records obligations;
it does **not** decide `FAMILY_ZERO`. V3-E composes a *path*.
V3-E+F together still do not decide a family: reconstruction and
the global rule live on the certificate.

**Classification.** Mathematics of path independence: known
standard. Use as a *checked* obligation because \(C^k\) is not
given: engineering adaptation. Completeness of the check for
Guo-scale polygamma is an experiment, not a theorem.

---

## 4. Multivariate removable singularities

**What.** A point at which an expression is syntactically
undefined (typically \(0/0\) or a coincident-node substitution
into a difference quotient) but admits a continuous or
holomorphic extension.

**Canonical sources.**

- **One complex variable.** Riemann’s removable singularity
  theorem: a function holomorphic and bounded on a punctured
  disk extends holomorphically across the puncture (Riemann
  1851; any complex-analysis textbook, e.g. Ahlfors). The
  rational special case is cancellation of a common factor.
- **Several complex variables.** Isolated singularities of
  holomorphic functions on \(\mathbb C^n\), \(n\ge 2\), are
  always removable (Hartogs, *Math. Ann.* 62 (1906) 1–88;
  Hartogs extension / Hartogs–Bochner). This is a genuinely
  several-variable phenomenon: in one variable, isolated
  singularities need not be removable (poles, essential
  singularities).
- **Real multivariable calculus.** A real function may fail to
  extend continuously even if every iterated limit exists (§2).
  Removability of a real \(0/0\) is exactly the existence of the
  joint limit plus a definition at the point. Path agreement is
  necessary, not sufficient.
- **Interpolation.** \(\lim_{y\to x} F[x,y]=F[x,x]\) *is* the
  statement that the difference-quotient singularity on the
  diagonal is removable, with value \(F'(x)\). That is de Boor
  2005, not a physics identity.

**Type errors to refuse.**

- Citing Hartogs to certify a *real* Piecewise polygamma
  family. Hartogs is about holomorphic functions of several
  *complex* variables. Guo kernels are not given as elements of
  \(\mathcal O(\mathbb C^n)\).
- Citing Riemann to skip a two-sided real limit that may
  disagree from the left and the right.
- Calling a `series` truncation a removable-singularity
  certificate (it is at best a candidate expansion; ZERO still
  requires an exact residual).

**Track-V3 use.** A one-parameter confluence step that (i)
factors an exact nonzero spectator, (ii) cancels a \(0/0\) in
the local kernel, (iii) residual-compares to the declared
degenerate member, is Riemann/rational removal along *one
line*, or interpolation confluence of *one* node. Repeating
that for several nodes is iterated removal, not Hartogs.

**Classification.** Known standard. Local cancel/together/series
on a `PathStep` is the Track V confluence cascade reused, not a
new singularity theory.

---

## 5. Symbolic algorithms for (multivariate) limits

**What.** Decide \(\lim_{z\to z_0} E(z)\) or
\(\lim_{x\to a} f(x)\) in a computer-algebra system, including
the several-variable case.

**Univariate (already classified in Track V).**

- Pre-1990s CAS: heuristic series / L’Hôpital / cancellation-
  prone recursive expansion.
- Gonnet and Gruntz, ISSAC 1988 (LNCS 358); Gruntz, ETH Diss.
  11432, 1996 (doi:10.3929/ethz-a-001631582). MRV class,
  expand in a positive infinitesimal, read the leading term.
  Maple; SymPy `sympy.series.gruntz`.
- Shackell, *J. Symbolic Comput.* 1990; later transseries
  (van der Hoeven).
- Richardson 1968, 1997; Davenport 2002: CAS equality is
  engine semantics, not a complete theory of real functions.

**Multivariate rational / analytic quotients (published CAS;
not this repo’s invention).**

Computing \(\lim_{x\to 0} f(x)/g(x)\) for real polynomials or
real-analytic germs, with \(g(0)=0\), is an active *standard*
computer-algebra problem. Existence of the joint limit is
semi-algebraic, not a one-line Gruntz call.

| System / paper | Object | vs Track V3 |
|---|---|---|
| Cadavid, Molina, Vélez, *J. Symbolic Comput.* 50 (2013) 197–207 | bivariate real-analytic quotients; isolated zero of the denominator; Hensel / Puiseux; Maple `limit/multi` | joint *rational/analytic* limit; not Piecewise polygamma |
| Xiao and Zeng, *Sci. China Math.* 57 (2014) 397–416 | multivariate rational, Wu method / critical points | same object class |
| Zeng and Xiao, *J. Symbolic Comput.* 96 (2020) 1–21 | bivariate rational via Sturm, no Puiseux | same |
| Alvandi, Ataei, Moreno Maza, ISSAC 2017; JSC 2020 (Extended Hensel) | multivariate rational via regular chains / RealTriangularize | RegularChains library; isolated denominator zero |
| Strzeboński, arXiv:2102.01242 | quotients of real-analytic functions; Łojasiewicz bound; Mathematica CAD methods | production CAS; still isolated-zero hypothesis |
| Nested `sympy.limit` | iterated univariate | the **failure mode** V3 must not confuse with a joint certificate |

**Track-V3 use.** Budgeted one-parameter limit remains the
honest fallback on a `PathStep` (Track V cascade: substitution,
together/cancel, valuation, series, L’Hôpital, Newton diagonal,
guarded `sympy.limit`; timeout → `UNKNOWN`; `count_ops`
guard). V3 does **not** ship a Cadavid/CAD joint-limit solver.
If a local kernel happens to be rational with an isolated
denominator zero, those algorithms are a *neighbor*, not a
baseline we outrun, and not a license to skip path consistency
on the non-rational remainder of a Guo kernel.

**Limits of the method (why Track V3 exists as engineering).**
Gruntz is complete for a stated exp-log class, not for arbitrary
`Sum`/`Piecewise`/polygamma physics kernels. Cadavid-style
algorithms need an isolated zero of a polynomial denominator.
Guo 5-branch generic members are ~573-op Piecewise kernels
(STATUS: “5-branch 573-op generic kernels; 2-parameter star
edges”). A global or even joint rational-limit algorithm does
not apply off the shelf. The engineering bet is *localization*
to one-parameter kernels comparable to the already-certified
pairs, not a new multivariate limit decision procedure.

**Classification.** Known standard as algorithms. Timeout →
UNKNOWN is this engine’s contract, already classified in Track V.
Not a novel limit algorithm.

---

## 6. Confluent divided differences

**Mathematics (not novelty).** For a sufficiently smooth \(F\),

\[
F[x,y]=\frac{F(x)-F(y)}{x-y},\qquad
F[x,x]:=F'(x),\qquad
\lim_{y\to x} F[x,y]=F[x,x].
\]

Continuity of divided differences in the nodes is interpolation
confluence (de Boor, “Divided Differences,” *Surveys in
Approximation Theory* 1 (2005) 46–69, arXiv:math/0502036,
especially §§1–2, 8–9). Newton form coefficients *are* Hermite
interpolants at the listed nodes with stated multiplicities.
Historical sources: Newton, *Methodus Differentialis* (1711);
Conte and de Boor, *Elementary Numerical Analysis*, 3rd ed.
(1980), Ch. 2. (The brief’s “Conti/de Boor” is this pair:
**S. D. Conte and Carl de Boor**, not Costanza Conti’s spline
papers.)

Track V and Track V2 already classified this as known standard.
Track V3 does not re-open the classification.

**Track-V3 use.** Edge relations `one_parameter_confluence`,
`limit`, `repeated_node_confluence` on a `PathStep`. If two
catalog members are claimed to be \(F[x,y]\) and \(F[x,x]\),
the checker rebuilds and residual-compares. That is a
reconstruction check, not Gruntz on the source Piecewise, and
not a new identity.

**Failure modes that must stay UNKNOWN / NONZERO.**

- Verbal “divided difference” without members, nodes, \(F\), and
  reconstruction (representation-invention `PROTOCOL.md` rule 3).
- Coincident nodes substituted into `newton_first` (0/0, not
  \(F'\)).
- Swapped generic/degenerate roles; wrong sign; wrong
  denominator.
- Using interpolation confluence to paper over *rewriting*
  joinability.
- Guo-specific polygamma identities hardcoded as ZERO rules
  (`PROTOCOL.md`: no Guo-specific ZERO identities).

Local confluence (P1, G1/R0, `confluent_representation`) is
**not** DD-OK and is **not** a Hermite certificate.

**Classification.** Known standard. Engineering: wire the
textbook identity as a one-parameter step. Not a novel identity.

---

## 7. Hermite interpolation and repeated nodes

**Mathematics (not novelty).** Hermite interpolation matches
derivatives as well as values (C. Hermite, “Sur la formule
d'interpolation de Lagrange,” *J. Reine Angew. Math.* 84 (1878)
70–79). Repeated-node Newton table:

\[
F[\underbrace{a,\ldots,a}_{k+1}]=\frac{F^{(k)}(a)}{k!}.
\]

The **Hermite recurrence** is the Newton recurrence with the
diagonal filled by the derivative formula rather than by
cancelling \(0/0\). Conte–de Boor 1980 §2.7; de Boor 1978,
*A Practical Guide to Splines*; Traub 1964. Track V2’s
literature pack exists so that no later track “introduces” this
recurrence by moving from pairs to families. Track V3 does not
introduce it by moving from families to paths.

**Repeated nodes.** A node list with multiplicities \(\{m_i\}\)
means the interpolant matches \(F,F',\ldots,F^{(m_i-1)}\) at
that node. Filling the Newton table on the diagonal is the
*definition* of confluent DD, not a regularization invented for
physics kernels. de Boor 2005 §2, §9: the repeated-node value
is a *limit of distinct-node values*.

**What CAS already does.** `InterpolatingPolynomial` with
derivative data; this repo’s `repeated_diagonal` and
`hermite_dd`. Mixed unblocked sequences such as \(F[x,y,x]\)
are not guessed (`hermite_dd` raises).

**Track-V3 use.**

- Degeneracy coordinates (V3-A) name the one-parameter
  coalescences; they do not invent multiplicities.
- Relation `repeated_node_confluence` on a step that raises
  multiplicity.
- Distinct from `substitution` of equal indices into the
  generic branch (usually 0/0) and from a two-parameter star
  treated as one step.

A path generic (multiplicity 1) → one pair equal (multiplicity
2) → all three equal (multiplicity 3) *is* the Hermite table
being filled one coalescence at a time. That reading is
scientific, not a new object. Naming `hermite_divided_difference`
on a frozen P2 JSON is not `HERMITE_OK` and is not L4–L7.

**What must not be claimed.** “We introduce Hermite interpolation.”
“We introduce the Hermite recurrence.” “We introduce repeated
nodes.” Any numerical analyst will desk-reject those sentences.

**Classification.** Known standard. The V3 coordinate/step
schema is bookkeeping.

---

## 8. PATH vs FAMILY: local-to-global certification

**What.** Infer a global family verdict from local step, path,
consistency, and reconstruction verdicts. This is the only
V3-specific *composition rule*. It is not a new theorem of
analysis: iterated \(\neq\) joint is Apostol/Rudin; uniqueness
of the Hermite interpolant already says that a consistent Newton
table determines one polynomial. The engine question is whether
the *frozen catalog members* really are that table, reached by
declared one-parameter routes whose local residuals are ZERO.

**Standard CS analog.** Assume-guarantee / Floyd–Hoare:
local contracts compose to a global spec only when every
contract holds and the glue holds. Any local failure blocks the
global claim. This is the default of SMT, ITP, and model
checking. It is **not** voting. Track V2 already shipped the
family-scale version. Track V3 inserts an intermediate grain
`PATH_*` so that a successful iteration order cannot be
laundered into a family.

**The V3 glue (`schema.compose_path_verdict` /
`compose_family_verdict`).**

`PATH_ZERO` iff **all** required steps on that path are `ZERO`
(and the path is non-empty). Any step `NONZERO` ⇒
`PATH_NONZERO`. Else `PATH_UNKNOWN`.

`FAMILY_ZERO` iff **all** of:

1. every required path is `PATH_ZERO`;
2. every required local edge is `ZERO`;
3. every branch-reconstruction obligation is `ZERO`;
4. if `require_path_independence` (default true), every
   path-consistency obligation is `CONSISTENT_ZERO`
   (missing consistency ⇒ not `FAMILY_ZERO`).

Then:

- any required `NONZERO` or `INCONSISTENT_NONZERO` ⇒
  `FAMILY_NONZERO`;
- otherwise `FAMILY_UNKNOWN`;
- **no majority**, no “4/5 paths,” no timeout-as-zero,
  no “the other order finished.”

**Why `PATH_ZERO` is not `FAMILY_ZERO`.** One iteration order
is one iterated limit. Joint confluence, and the family claim
that *all* degenerate strata are regularized limits of one
generic member, need every required path and the consistency
glue. Relabeling a single `PATH_ZERO` as `FAMILY_ZERO` would
be exactly the false converse of §2.

**Why reconstruction is required.** An iterated limit of a
*modified* kernel that does not rebuild the source expression
is a different claim. `PROTOCOL.md`: spectator split with
reconstruction \(E - \mathrm{reconstructed}(E) == 0\).
`IntermediateExpression` must be source-derived. Anonymous
algebraic interpolation of missing branches is forbidden.

**Why connectivity / required paths matter.** An isolated ZERO
pair inside a five-member list is Track V’s already-closed
case. Calling that `FAMILY_ZERO` would relabel V_GAIN as a
V3 result.

**Track-V3 use.** Family verdicts may be written only by the
published composition rule. Coordinates, path enumerators,
edge checkers, routers, and this literature pack do **not**
decide `FAMILY_ZERO`. Falsifiers (V3-J) must include: majority
of paths; one `PATH_ZERO` sold as family; skipped consistency;
interpolated intermediates; Guo gold \(F\); numeric “family
certificate”; timeout-as-zero.

**Classification.** Composition of equalities / iterated-vs-joint
honesty: known standard. The schema’s three-way wired to this
engine’s fail-closed residual: engineering adaptation. Not a
new local-to-global theorem.

---

## 9. How Track V3 should compose these methods

| piece | owner | decides `FAMILY_*`? | method (§) |
|---|---|---|---|
| degeneracy coordinates | V3-A `coordinates/` | no | names of §§1–3 |
| path enumerator | V3-B `paths/` | no | declared orders |
| spectator split | V3-C `spectator/` | no | Track V factoring |
| local edge cert | V3-D `edges/` | no | §§4–7 |
| path composition | V3-E `compose/` | `PATH_*` only | §§1, 8 |
| path consistency | V3-F `consistency/` | no (blocks glue) | §3 |
| intermediates | V3-G `intermediates/` | no | source-derived only |
| local complexity | V3-H `complexity/` | no | ops vs pair baseline |
| series control | V3-I `series/` | no | Track V series, local |
| falsifier | V3-J `falsifier/` | no | adversarial |
| literature | V3-K (this pack) | no | classification |

No new LLM calls. Frozen inputs:
`research/iterated_confluence/FROZEN_INPUTS_V3.json`
(n=7; inherited V2 families). Historical run JSON is
read-only. Shared freeze/schema/STATUS files are not owned
here.

Gain labels stay those of Track V, lifted to path/family grain:

- **path V_GAIN**: a declared one-parameter step previously
  `UNKNOWN`, now `ZERO`/`NONZERO` because the local verifier
  improved;
- family-level **V_GAIN**: same frozen hyp, previously
  `FAMILY_UNKNOWN`, now `FAMILY_ZERO` or `FAMILY_NONZERO`
  because the *iterated family verifier* improved;
- **C_GAIN**: previously uncompiled path/family, now compiles
  then verifies;
- **NO_GAIN**: `PATH_UNKNOWN` / `FAMILY_UNKNOWN`, including
  all seven hyps at freeze.

False `FAMILY_ZERO` = 0 is a merge gate. This pack does not
produce that number.

Track D2 stays locked until a frozen family is `FAMILY_ZERO`
or `FAMILY_NONZERO` (`PROTOCOL.md` I-A / I-B). Outcome classes
I-C (local edges ZERO, consistency UNKNOWN), I-D (local edge
UNKNOWN), and I-E (decomposition invalid) keep D2 locked.
This literature pack does not open Track D and does not define
those classes as results.

Allowed local methods (from `PROTOCOL.md`): exact substitution,
cancel/together, spectator split with reconstruction, series
around *one* degeneration parameter, derivative reduction,
local special-function identities, typed DD recurrence already
frozen in Track V/V2. Fallback UNKNOWN.

Forbidden: Guo-specific identity table, gold leakage
(`Phi_Gamma`, L4–L7, PRB masters), converting timeout/size-guard
to ZERO, numeric agreement as exact, majority `FAMILY_ZERO`,
anonymous algebraic interpolation of intermediate branches.

---

## 10. Closest verification systems (not to copy slogans from)

Reuse frozen `research/literature/corpus.md` for proposer–
verifier crowding, Track V `METHODS.md` §10 for pair-scale
neighbors, and Track V2 `METHODS.md` §8 for family-scale
neighbors. Distance *as iterated-confluence verifiers*:

| System | What it checks | vs Track V3 |
|---|---|---|
| Apostol / Rudin / Moore–Osgood | iterated vs joint limits | the **math**; not a CAS family certificate |
| Hermite–Genocchi / de Boor 2005 | path independence under \(C^k\) | the **math** of interpolation confluence; \(C^k\) not given here |
| Riemann / Hartogs | removable singularities (ℂ, \(\mathbb C^n\)) | wrong regularity class for Guo Piecewise |
| Gruntz / `sympy.limit` | univariate exp-log limits | inner engine of a `PathStep`; nested call ≠ joint |
| Cadavid / Xiao–Zeng / RegularChains / Strzeboński | joint limits of real rational/analytic *quotients* | published CAS; isolated polynomial denominator; not 573-op polygamma Piecewise |
| Track V cascade | local confluence of *two* members | closed 3 Guo pairs; 5-branch still UNKNOWN |
| Track V2 family glue | edges + recurrence + consistency | closed H-C; `FAMILY_UNKNOWN` × 7 |
| egg / LGuess | rewrite chains on polynomials | wrong confluence sense; no egg here |
| WZ / *A=B* | hypergeometric sum certificates | wrong object |
| Lean/Isabelle kernels | formal proofs | stronger; unavailable; must not claim |
| IBP/FIRE/Kira “families” | linear dependence of Feynman integrals | wrong family: masters in a vector space, not a Newton table |
| Assume-guarantee / LEDA | compositional contracts / certifying algs | right *glue slogan*; wrong domain object |
| Engine `verifier.py` | structural residual + rational probes | global; does not scale to 5-way Guo limits |

No retrieved system jointly (i) takes frozen, already-proposed
**multi-branch** scientific hypotheses, (ii) reduces them to
ordered one-parameter confluence *paths* whose local kernels
are intended to match pair-scale complexity, (iii) refuses to
treat `PATH_ZERO` as joint confluence, (iv) forbids majority
vote and numeric ZERO, (v) keeps timeout as `FAMILY_UNKNOWN`,
and (vi) accounts path/family V_GAIN without mutating
historical runs.

That joint *packaging* is a **GAP**, not a proof of novelty.
The methods in §§1–8 are not new. Guo family certificates do
not exist, so the package is not a candidate contribution
either. See `CLASSIFICATION.md`.

---

## 11. Self-adversarial notes

1. Nested `sympy.limit` succeeding on a *small* reconstructed
   DD is not evidence that Guo-scale 2-parameter limits are
   solved; it is evidence that the obligation was localized.
   Localization of an identity that is already a difference
   quotient is compiler/language gain, not family V_GAIN.
2. Re-reporting Track V’s 3 two-member ZERO as Track V3
   `FAMILY_ZERO` is relabeling. Those edges are legal
   `PathStep`s inside `guo-p2-s2-i4`; the family remains
   `FAMILY_UNKNOWN`.
3. `PATH_ZERO` on one coordinate order, with the other order
   `PATH_UNKNOWN`, is outcome I-C: D2 stays locked. Do not
   narrate it as “almost FAMILY_ZERO.”
4. Hermite–Genocchi path independence must not skip
   path-consistency obligations on untrusted Piecewise kernels
   (`AGENTS.md` rule 14). Hartogs must not be cited for the
   same skip.
5. Cadavid / Maple `limit/multi` / Mathematica multivariate
   `Limit` already compute *joint* limits for rational/analytic
   quotients. “We compute multivariate limits” is therefore
   not a slogan this project may use. The remaining engineering
   question is Guo-scale Piecewise polygamma *families*, and
   it is unanswered.
6. Randomized PIT / high-precision numerics must not be
   smuggled in as `PATH_ZERO` or `FAMILY_ZERO`.
7. Interpolating a missing intermediate branch from a Newton
   table, rather than reconstructing it from the source, is
   forbidden (`PROTOCOL.md`) and would be a false decomposition
   even if the residual later looks small.
8. Guo n=1 cannot carry a generalization claim even if
   `FAMILY_ZERO` later appears.
9. This pack runs no rescore. Status remains literature-only.
   V2 is H-C. The packaged-contribution cell is a GAP.
10. Track D2 remains locked. Naming an iterated path on a
    frozen P2 JSON is not I-A and is not L4–L7.

## Unconfirmed / not used

- Papers whose titles were recalled but not retrieved with
  matching authors/year/venue.
- Multivariate / simplex divided-difference extensions
  (Micchelli, Rabut, Floater) as if they were required for this
  *univariate iterated* index-coalescence claim. Track V3
  iterates one-parameter coalescences; it does not need a
  simplex DD theory.
- Numeric Gruntz/WZ/LGuess/Cadavid solve-rate tables from
  search snippets.
- Original 19th-century page-level Moore and Osgood memoirs
  beyond textbook Moore–Osgood / Rudin Ch. 7 / Apostol
  (textbook statement is enough; this pack does not rest on
  unpublished archival claims).
- Any claim that V3-A..J already produced `PATH_ZERO` or
  `FAMILY_ZERO` (those directories are owned elsewhere; this
  pack is documentation).
