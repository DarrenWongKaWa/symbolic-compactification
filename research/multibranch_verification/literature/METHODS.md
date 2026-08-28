# Track V2 methods — family certificates for multi-branch confluence

Audit date: 2026-08-28.
Object: **compositional certification of a family** of already-proposed
Piecewise branches (`research/multibranch_verification/PROTOCOL.md`).
This pack is literature for Track **V2**, not discovery (layer D) and
not a rewrite of Track V.

No LLM calls. Frozen 5-branch and Hermite-typed Guo P2 hypotheses only.
Retrieval: classic NA/CAS/PL sources already used in frozen
compactification, representation-invention, and Track-V audits, plus
the Hermite–Genocchi / Newton-recurrence textbook line. Unconfirmable
titles are omitted.

**Question.** Can a five-branch family be certified by composing
*local* exact edges plus the *textbook* Hermite recurrence, without
Guo-specific identities?

**Not the question.** Inventing Newton or Hermite divided differences,
inventing a recurrence for repeated nodes, or claiming a Lean/e-graph
kernel. The Hermite recurrence is **known standard**. See
`CLASSIFICATION.md`.

Frozen literature this pack does not rewrite:

- Compactification proposer–verifier survey:
  `research/literature/{corpus,novelty_boundary}.md`.
- Representation-invention novelty:
  `research/representation_invention/literature/NOVELTY.md`.
- Track V verification methods:
  `research/scalable_verification/literature/{METHODS,CLASSIFICATION}.md`.
- Certification language:
  `research/verification/CERTIFICATION_SCOPE.md`
  (engine semantics, not formal proof).

Intended reader: Track V2 implementers (V2-A..I) and authors, before
any paper sentence about “family certificates,” “Hermite recurrence,”
or “local-to-global confluence.”

---

## 0. Two words, two scales

| Sense | Field | Object | Closest systems |
|---|---|---|---|
| Interpolation confluence | NA | nodes coalesce; DD → derivatives | Newton, Hermite, Conte–de Boor, de Boor 2005, Hermite–Genocchi |
| Rewriting confluence | term rewriting / EqSat | joinability of rewrite paths | Knuth–Bendix, egg, egglog |

Track V2 uses the **first** sense. Mixing the two in a draft is a
reviewer-kill (already recorded in Track V and representation-invention
literature).

| Scale | Track | Object | Closed evidence |
|---|---|---|---|
| Pair | V | two-member `local_confluence` | 3 frozen Guo pairs ZERO; generic suite false ZERO = 0 |
| Family | V2 | 4–5 member graphs + recurrence + path consistency | **not closed**; 7 frozen hyps remain previous-UNKNOWN |

A family is not certified because members share a list.
`FAMILY_ZERO` is **never majority vote** (`schema.py`;
`tests/test_mb_schema.py`: four ZERO edges plus one UNKNOWN is
`FAMILY_UNKNOWN`).

Timeout / size-guard is `UNKNOWN`, never `ZERO`. Numeric agreement,
`PossibleZeroQ`, and Schwartz–Zippel probes are **never** a ZERO path.
`COMPILE_FAILURE` ≠ `UNKNOWN`. Limit order is a scientific assumption
(`AGENTS.md` rules 14–15): path consistency is *checked*, not assumed.

---

## 1. Newton divided differences

**What.** For a sufficiently smooth \(F\) and distinct nodes,

\[
F[x]=F(x),\qquad
F[x,y]=\frac{F(x)-F(y)}{x-y},
\]

and the **Newton recurrence** (distinct endpoints)

\[
F[x_0,\ldots,x_k]
=\frac{F[x_1,\ldots,x_k]-F[x_0,\ldots,x_{k-1}]}{x_k-x_0}.
\]

The numbers \(F[x_0,\ldots,x_j]\) are the coefficients of the Newton
form of the interpolant. They are symmetric in the nodes. The first
divided difference is the difference quotient; it is *not* a new
limit algorithm.

**Canonical sources.**

- Newton, *Methodus Differentialis* (1711; unequal-interval
  interpolation treated by the 1670s). Quoted via de Boor 2005.
- Conte and de Boor, *Elementary Numerical Analysis*, 3rd ed.
  (1980), Ch. 2 (divided-difference table). The brief’s
  “Conti/de Boor” is this pair: **S. D. Conte and Carl de Boor**,
  not Costanza Conti’s spline papers.
- de Boor, “Divided Differences,” *Surveys in Approximation Theory* 1
  (2005) 46–69, arXiv:math/0502036. Newton form *is* a Hermite
  interpolant at the listed nodes with stated multiplicities.
  Recurrence, Leibniz/Opitz, and symmetry are §§1, 4–5.
- Traub, “On Lagrange—Hermite interpolation,” *J. SIAM* 12(4)
  (1964) 886–891.

**What CAS already does.** Any interpolation constructor
(`InterpolatingPolynomial`, Newton tables, SymPy interpolants)
already *builds* \(F[x,y]\) when \(F\) and the nodes are given.
This repository already ships textbook constructors
(`research/representation_invention/dd/`): `newton_first`,
`newton_table`. `newton_table` does **not** rewrite coincident
nodes to derivatives (0/0 stays 0/0).

**Track-V2 use.** Edge relation `dd_recurrence` in
`ConfluentFamilyCertificate.local_edges`. If two catalog members are
claimed to be consecutive Newton-table entries, the checker rebuilds
the recurrence residual and residual-compares. That is a
reconstruction check, not Gruntz on the source Piecewise.

**Failure modes that must stay UNKNOWN / NONZERO.**

- Verbal “divided difference” without members, nodes, \(F\), and
  reconstruction (representation-invention `PROTOCOL.md` rule 3).
- Coincident nodes substituted into `newton_first` (0/0, not \(F'\)).
- Swapped generic/degenerate roles; wrong sign; wrong denominator.
- Using interpolation confluence to paper over *rewriting* joinability.
- Guo-specific polygamma identities hardcoded as ZERO rules
  (Track V2 `PROTOCOL.md`: no Guo-specific ZERO identities).

**Classification.** Mathematics: known standard. Use as an edge
checker: engineering adaptation. Not a novel identity.

---

## 2. Hermite / confluent divided differences

**Mathematics (not novelty).** Hermite interpolation matches
derivatives as well as values (C. Hermite, “Sur la formule
d'interpolation de Lagrange,” *J. Reine Angew. Math.* 84 (1878)
70–79). The Newton table with repeated nodes *is* the Hermite
interpolant. de Boor 2005: the Newton form provides an efficient
representation of Hermite interpolants.

Confluent (repeated-node) value:

\[
F[\underbrace{a,\ldots,a}_{k+1}]=\frac{F^{(k)}(a)}{k!}.
\]

So \(F[x,x]=F'(x)\) and \(F[x,x,x]=F''(x)/2\). Mixed blocked windows
such as \(F[x,x,y]\) are the same recurrence with one coincident
pair; they are *not* guessed from unblocked sequences such as
\(F[x,y,x]\) (this repo’s `hermite_dd` raises rather than invents).

The **Hermite recurrence** is the same Newton recurrence, with the
diagonal case filled by the derivative formula rather than by
cancelling \(0/0\):

\[
F[x_0,\ldots,x_k]
=
\begin{cases}
\dfrac{F[x_1,\ldots,x_k]-F[x_0,\ldots,x_{k-1}]}{x_k-x_0},
& x_k\neq x_0,\\[1em]
F^{(k)}(x_0)/k!,
& x_k=x_0=\cdots=x_{k-1}.
\end{cases}
\]

That case-split is in every NA textbook that treats osculatory
interpolation (Conte–de Boor 1980 §2.7; de Boor 1978, *A Practical
Guide to Splines*; Traub 1964). **It is not a Track-V2 contribution.**
Shipping `hermite_dd_recurrence` as an edge kind is reimplementation.

**Track-V2 use.** Same certificate engine as §1, for multiplicity
\(>1\). Frozen claimed types `hermite_divided_difference` (two of the
seven V2 hyps) name this reading of the Guo triple-sum Piecewise.
Naming the type is not G3 and is not `HERMITE_OK`
(`research/scalable_verification/VERDICT.md`: Hermite-typed frozen
hyps, 0 ZERO under Track V).

**What must not be claimed.** “We introduce Hermite divided
differences.” “We introduce the Hermite recurrence.” Any numerical
analyst will desk-reject those sentences. Track V already recorded
the same ban for pair-scale certificates; Track V2 does not lift it
by moving from pairs to families.

**Classification.** Known standard. Engineering adaptation: wire the
textbook recurrence into family *edges* instead of one global
`sympy.limit`.

---

## 3. Repeated nodes

**What.** A node list with multiplicities \(\{m_i\}\) means the
interpolant matches \(F,F',\ldots,F^{(m_i-1)}\) at that node.
Filling the Newton table on the diagonal is the *definition* of
confluent DD, not a regularization trick invented for physics
kernels.

**Canonical sources.** Same as §2. de Boor 2005, §2 (continuity and
smoothness in the sites) and §9 (Genocchi–Hermite) make the
repeated-node value a *limit of distinct-node values*, not a
separate object. Kowalewski’s leading-coefficient definition
(cited in de Boor, “An Efficient Definition of the Divided
Difference,” 2004) treats multiplicities from the start.

**What CAS already does.** `InterpolatingPolynomial` with derivative
data; Newton tables with \(f'(x)\) written on coincident first
columns; this repo’s `repeated_diagonal` and `hermite_dd`.

**Track-V2 use.**

- `ConfluentFamilyCertificate.node_multiplicities`.
- Edge relation `repeated_node_confluence`.
- Schema flag `multiplicities_consistent` in `compose_family_verdict`.
- Distinct from `one_parameter_confluence` (a single node moving
  onto another, multiplicity 1→2) and from naive `substitution`
  of equal indices into the generic branch (usually 0/0).

**Soundness rules.**

- Structural node equality (`==` / `expand(a-b)==0`), not an
  invented `simplify` that might hide a pole.
- Multiplicity \(k+1\) requires a \(C^k\) reading of \(F\) under
  *declared* assumptions; otherwise the diagonal is `UNKNOWN`.
- Substituting coincident nodes into the generic Newton formula is
  `NONZERO` or `UNKNOWN`, never a silent promotion to \(F^{(k)}/k!\).
- Mixed unblocked sequences are not guessed.

**Classification.** Known standard. The V2 schema field is bookkeeping.

---

## 4. Limit decomposition

**What.** A multi-branch Piecewise claim is decomposed into *typed
limits* of a generic member, rather than one giant
`sympy.limit` of a 5-way residual.

For three coalescence parameters (the frozen Guo 5-branch shape:
indices \(\ell,m,n\) or \(\varepsilon(\ell),\varepsilon(m),\varepsilon(n)\)),
the intended decomposition is:

| member role | typical condition | claimed operator |
|---|---|---|
| generic | `True` | identity |
| one pair equal | `m = n` (etc.) | one-parameter limit of generic |
| all three equal | `ℓ = m = n` | two-parameter / iterated limit |

That is interpolation confluence at family scale: the degenerate
strata are regularized limits of the generic stratum. It is the
same identity as \(\lim_{y\to x} F[x,y]=F[x,x]\), with more nodes.

**Joint continuity vs iterated limits.** The Hermite–Genocchi
formula (Genocchi; letter to Hermite; de Boor 2005 §9; elementary
writeup: R. K. Alexander, “The Hermite–Genocchi Formula”) writes

\[
F[x_0,\ldots,x_k]
=\int_{\Sigma_k} F^{(k)}(t_0 x_0+\cdots+t_k x_k)\,dt
\]

over the simplex \(\Sigma_k\). The integrand is jointly continuous
in the nodes when \(F\in C^k\). Consequences that are **textbook**,
not V2 theorems:

1. Distinct-node DD extend continuously to repeated nodes.
2. Simultaneous coalescence of several nodes has a well-defined
   limit, equal to the iterated one-parameter limits, *when* the
   \(C^k\) hypothesis holds.
3. Path independence: the order of coalescence does not matter
   *when* that hypothesis holds.

**What must still be checked, not assumed.**

- `AGENTS.md` rule 14: limits do not commute in general. A CAS
  kernel that is not known to be \(C^k\) (Piecewise polygamma,
  occupation factors, unevaluated `AppliedUndef`) does **not**
  inherit Hermite–Genocchi for free.
- Therefore Track V2 records **path-consistency obligations**:
  two coalescence paths to the same degenerate member must
  residual-compare. Disagreement is `FAMILY_NONZERO` (or
  `FAMILY_UNKNOWN` if a path is undecided). Agreement is one
  local ZERO, not a family verdict by itself.
- One-sided vs two-sided limits, and \(\varepsilon(m)\to\varepsilon(n)\)
  vs \(m\to n\), are scientific assumptions. They live in
  `assumptions`, not in ZERO rules.
- Double-limit interchange on a kernel that still contains
  spectator poles is a false decomposition if the spectator is
  not certified nonzero (Track V `FACTOR_LOCAL` contract).

**Track-V2 edge kinds for this decomposition.**

- `limit` — typed `lim_{var → value}` of a source member.
- `one_parameter_confluence` — one node moving onto another.
- `repeated_node_confluence` — diagonal after coalescence.
- `derivative` — explicit \(F^{(k)}/k!\) reconstruction.
- `substitution` — index or symbol swap (appears on the mixed
  4-member frozen hyp `guo-p2-s2-i4`); substitution is not a
  limit.

Track V already certified *some* one-parameter limits of
*two-member* Guo pairs after spectator factoring (V_GAIN, 3 ZERO).
Those pair certificates are local edges if they reappear inside a
5-branch graph. They do **not** imply the triple-coincident
member, and they do not imply `FAMILY_ZERO`.

**Failure modes.**

- Selling a timeout on one path as ZERO because another path
  succeeded (majority / “best path”).
- Reordering limits silently to the path Gruntz happens to finish.
- Treating Track V’s 2-member ZERO as a 5-member result.
- Hardcoding Guo gold masters as the \(F\) in Hermite–Genocchi.

**Classification.** Mathematics of joint continuity: known
standard. Use as a *checked* decomposition of a Piecewise family:
engineering adaptation. Completeness of the decomposition for
Guo-scale polygamma is an experiment, not a theorem.

---

## 5. Compositional certificates

**What.** A checker that is simpler than the search (or the giant
limit) that produced the claim. The algorithm may be untrusted;
the certificate plus a small checker is the evidence.

**Canonical sources.**

- Certifying algorithms: McConnell, Mehlhorn, Näher, Schweitzer,
  “Certifying algorithms,” *Computer Science Review* 5(2) (2011)
  119–161. Output \((y,w)\) such that a simple checker accepts
  \((x,y,w)\) iff \(y\) is a correct output for \(x\). LEDA used
  this as software reliability. Right *slogan* for V2: the
  proposer (and even `sympy.limit`) need not be trusted if a
  cheap checker re-verifies a witness.
- Wilf–Zeilberger rational certificates (*A=B*, 1996). Short
  witness, cheap checker. **Wrong object** for Guo Piecewise
  polygamma kernels (not hypergeometric sums in \(n,k\)), right
  *pattern*.
- Poincaré / ITP kernels (Lean, Isabelle, Coq): stronger than
  this project. Unavailable here; must not be claimed
  (`novelty_boundary.md` non-claim 2).
- Track V `dd_cert/`: reconstruction witnesses
  \((F,\{z_i\},\{m_i\},\mathcal O)\) with residual compare.
  Pair-scale; V2 reuses the idea on *edges*, not as a new
  calculus.

**Track-V2 certificates (engineering).**

A `LocalEdge` is a certificate of one claimed relation:

- witness = `(source, target, relation, variable, target_value,
  reconstruction)`;
- checker = rebuild the relation (Newton/Hermite recurrence,
  typed limit, substitution, derivative) and residual-compare;
- cost ≪ Gruntz on the 5-way source Piecewise when \(F\) and the
  two members are small.

A recurrence obligation is a certificate that two reconstructed
DDs satisfy the textbook identity. A consistency obligation is a
certificate that two paths reconstruct the same degenerate
member. The `ConfluentFamilyCertificate` is a *tree of such
witnesses*, not a new proof object.

**Honesty.** Level-1 engine-semantics certificates, not Lean
proofs. Allowed sentence: “the engine certified each required
edge residual \(=0\) under SymPy semantics, policy snapshot S,
and declared assumptions A, and composed them by the published
family rule.” Forbidden: “we formally proved the family identity.”

**Forbidden upgrades.**

- Randomized PIT / `N[..., 30]` as a ZERO certificate.
- Majority of cheap numeric probes as `FAMILY_ZERO`.
- Timeout converted to ZERO because “the other four edges passed.”

**Classification.** Certificate *idea*: known standard.
Edge-as-certificate for Piecewise family confluence: engineering
adaptation. Not a new certificate calculus.

---

## 6. Local-to-global verification

**What.** Infer a global family verdict from local edge, recurrence,
and path-consistency verdicts. This is the only V2-specific
*composition rule*. It is not a new theorem of interpolation:
uniqueness of the Hermite interpolant already says that a
consistent Newton table determines one polynomial. The engine
question is whether the *frozen catalog members* really are that
table.

**Standard CS analog.** Assume-guarantee / Floyd–Hoare
compositional verification: local contracts \(\langle A_i\rangle M_i
\langle G_i\rangle\) compose to a global spec only when every
contract holds and the glue (here: connectivity, multiplicity
consistency, latent \(F\)) holds. Any local failure blocks the
global claim. This is the default of SMT, ITP, and model checking.
It is **not** voting.

**The V2 glue (`schema.compose_family_verdict`).**
`FAMILY_ZERO` iff **all** of:

1. the required edge graph is connected (every member reached
   from the generic member by required edges);
2. every required edge is `ZERO`;
3. every recurrence obligation is `ZERO`;
4. every path-consistency obligation is `ZERO`;
5. `node_multiplicities` are consistent;
6. latent \(F\) / node set is compatible across members.

Then:

- any required `NONZERO` ⇒ `FAMILY_NONZERO`;
- otherwise, if any required input is missing/`UNKNOWN`, or the
  graph is disconnected, or multiplicities/latent fail ⇒
  `FAMILY_UNKNOWN`;
- **no majority**, no “4/5 edges,” no timeout-as-zero.

Pairwise ZERO is not enough. A connected graph of ZERO edges
without recurrence and path checks is not enough. Track V’s
two-member ZERO is a possible *subgraph*, not a family certificate.

**Why connectivity is required.** An isolated ZERO pair inside a
five-member list is exactly Track V’s already-closed case. Calling
that `FAMILY_ZERO` would relabel V_GAIN as a V2 result.

**Why path consistency is required.** Interpolation uniqueness
gives path independence only under a \(C^k\) hypothesis the engine
does not have a priori. Checking two reconstructed paths is the
fail-closed substitute for invoking Hermite–Genocchi on an
untrusted kernel.

**Why latent compatibility is required.** If two edges reconstruct
*different* \(F\)s, the family is not one interpolant. Latent
ownership is V2-E; this pack only records that the composition
rule treats latent mismatch as blocking `FAMILY_ZERO`
(`latent_compatible=False` ⇒ not `FAMILY_ZERO`).

**Track-V2 use.** V2-D (`compose/`) is the only place a family
verdict may be written. Routers, graph builders, and edge checkers
do **not** decide `FAMILY_ZERO`. Falsifiers (V2-H) must include:
majority vote; disconnected ZERO; missing recurrence; swapped
paths; Guo gold \(F\); numeric “family certificate.”

**Classification.** Composition of equalities: known standard.
The schema’s three-way family rule wired to this engine’s
fail-closed residual: engineering adaptation. Not a new local-to-global
theorem.

---

## 7. How Track V2 should compose these methods

| piece | owner | decides `FAMILY_*`? | method (§) |
|---|---|---|---|
| required graph | V2-A `graph/` | no | connectivity of §6 |
| local edge cert | V2-B `edges/` | no | §§1–5 |
| Hermite recurrence | V2-C `recurrence/` | no | §§1–3 (textbook) |
| family composition | V2-D `compose/` | **yes** | §6 |
| latent consistency | V2-E `latent/` | no (blocks glue) | §6 latent |
| piecewise normalizer | V2-F `piecewise/` | no | preprocessing |
| special-function local | V2-G `special/` | no | Track V §8 tables |
| falsifier | V2-H `falsifier/` | no | adversarial |
| router | V2-I `router/` | **no** | strategy only |
| literature | V2-J (this pack) | no | classification |

No new LLM calls. Frozen inputs:
`research/multibranch_verification/FROZEN_INPUTS_V2.json`
(n=7; 5-branch `local_confluence` / `hermite_divided_difference`
plus one 4-member mixed substitution family). Historical run JSON
is read-only.

Gain labels stay those of Track V, lifted to the family object:

- family-level **V_GAIN**: same frozen hyp, previously member-wise
  `UNKNOWN`, now `FAMILY_ZERO` or `FAMILY_NONZERO` because the
  *family verifier* improved;
- **C_GAIN**: previously uncompiled family, now compiles then
  verifies;
- **NO_GAIN**: family verdict `FAMILY_UNKNOWN`, including all
  seven hyps at freeze.

False `FAMILY_ZERO` = 0 is a merge gate. This pack does not
produce that number.

Track D2 stays locked until CASE H-A or H-B (`PROTOCOL.md`).
This literature pack does not open Track D and does not define
those cases as results.

---

## 8. Closest verification systems (not to copy slogans from)

Reuse frozen `research/literature/corpus.md` for proposer–verifier
crowding and Track V `METHODS.md` §10 for pair-scale neighbors.
Distance *as family verifiers*:

| System | What it checks | vs Track V2 |
|---|---|---|
| Newton / Hermite textbooks | interpolant uniqueness, recurrence, coalescence | the **math**; not a CAS family certificate |
| Gruntz / `sympy.limit` | exp-log limits | pair-scale bottleneck; does not compose a 5-graph |
| Track V cascade | local confluence of *two* members | closed 3 Guo pairs; 5-branch still UNKNOWN |
| egg / LGuess | rewrite chains on polynomials | wrong confluence sense; no egg here |
| WZ / *A=B* | hypergeometric sum certificates | wrong object |
| Lean/Isabelle kernels | formal proofs | stronger; unavailable; must not claim |
| IBP/FIRE/Kira “families” | linear dependence of Feynman integrals | wrong family: masters in a vector space, not a Newton table |
| Assume-guarantee / LEDA | compositional contracts / certifying algs | right *glue slogan*; wrong domain object |
| Engine `verifier.py` | structural residual + rational probes | global; does not scale to 5-way Guo limits |

No retrieved system jointly (i) takes frozen, already-proposed
**multi-branch** scientific hypotheses, (ii) treats them as a
Newton/Hermite *table* with required edges, (iii) checks the
textbook recurrence and coalescence *paths* fail-closed, (iv)
forbids majority vote and numeric ZERO, (v) keeps timeout as
`FAMILY_UNKNOWN`, and (vi) accounts family-level V_GAIN without
mutating historical runs.

That joint *packaging* is a **gap**, not a proof of novelty. The
methods in §§1–6 are not new. See `CLASSIFICATION.md`.

---

## 9. Self-adversarial notes

1. A DD/Hermite certificate on members that are already spelled
   \((F(x)-F(y))/(x-y)\) or \(F'(x)\) is compiler/language gain,
   not family V_GAIN.
2. Re-reporting Track V’s 3 two-member ZERO as Track V2
   `FAMILY_ZERO` is relabeling.
3. Hermite recurrence succeeding on a cubic probe (`z^3`,
   \(F[x,x,x]=3x\)) is a unit test, not Guo 5-branch evidence.
4. Path independence from Hermite–Genocchi does **not** license
   skipping path-consistency obligations on polygamma Piecewise.
5. Randomized PIT / high-precision numerics must not be smuggled
   in as family ZERO “certificates.”
6. Guo n=1 cannot carry a generalization claim even if
   `FAMILY_ZERO` appears.
7. This pack runs no rescore. Status remains literature-only
   until V2-A..I fire with false `FAMILY_ZERO` = 0.
8. Track D remains locked. Naming `hermite_divided_difference`
   on a frozen P2 JSON is not `HERMITE_OK` and is not L4–L7.

## Unconfirmed / not used

- Papers whose titles were recalled but not retrieved with matching
  authors/year/venue.
- Multivariate / simplex divided-difference extensions (Micchelli,
  Rabut, Floater) as if they were required for this univariate
  index-coalescence claim.
- Numeric Gruntz/WZ/LGuess solve-rate tables from search snippets.
- Any claim that V2-A..I already produced `FAMILY_ZERO` (those
  directories are owned elsewhere; this pack is documentation).
