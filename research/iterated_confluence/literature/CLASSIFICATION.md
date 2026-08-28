# Classification of Track V3 iterated-confluence methods

Audit date: 2026-08-28.
Companion: `METHODS.md`. Labels are for **paper-facing honesty**, not
marketing.

Allowed labels (exactly one primary label per method):

| label | meaning |
|---|---|
| **known standard** | Textbook or published algorithm. Shipping it is reimplementation. |
| **engineering adaptation** | Standard method, wired into this engine’s iterated-confluence IR, budgets, and fail-closed three-way (`PATH_*` vs `FAMILY_*`). Systems work, not a new theorem. |
| **GAP** | Not claimed. Would require later `FAMILY_ZERO` (or honest `FAMILY_NONZERO`) on the **frozen Guo 5-branch** set with false `FAMILY_ZERO` = 0. That experiment has **not** run. V2 closed CASE H-C. Absence of a packaged evaluation is a gap, not a proof. |

There is **no** “potential novel contribution” row that may be
quoted as a result. Track V and Track V2 allowed a *conditional*
package row. Track V3 does not: Guo family certificates do not
exist, so that cell is a **GAP**.

**Hard rules.**

1. Iterated limits are **known standard**. They are not an
   engineering adaptation of *mathematics* and they are not a
   contribution. A reviewer who knows Apostol, Rudin, or
   Moore–Osgood will desk-reject any draft that leads with “we
   introduce iterated limits.”
2. The Hermite recurrence and Newton divided differences remain
   **known standard** (Track V, Track V2). Composing them along
   a path does not mint a theorem.
3. `PATH_ZERO` does **not** imply joint confluence, path
   independence, or `FAMILY_ZERO`.

This pack classifies **iterated-confluence verification methods**
(Track V3). Discovery of a representation
\(H=(R,\{A_i\},\{\mathcal O_i\},F)\) is Track D / D2 and stays
locked (`PROTOCOL.md`; `PROGRAM_STATUS_V3.md`: Track D2 LOCKED;
publication status E).

---

## Summary table

| # | Method | Mathematics | Track-V3 use (primary label) | May a paper call this novel? |
|---|---|---|---|---|
| 1 | Iterated one-parameter limits | known standard | **known standard** | **no** |
| 2 | Joint vs iterated limits / Moore–Osgood | known standard | **known standard** | no |
| 3 | Path independence of limits | known standard (counterexamples; Hermite–Genocchi under \(C^k\)) | **engineering adaptation** | no (math); checking paths is discipline, not a theorem |
| 4 | Multivariate removable singularities | known standard (Riemann; Hartogs SCV; real 0/0) | **known standard** | no |
| 5 | Symbolic multivariate-limit algorithms | known standard (Gruntz; Cadavid–Molina–Vélez; Xiao–Zeng; RegularChains; Strzeboński) | **known standard** | no |
| 6 | Confluent divided differences | known standard | **known standard** | no |
| 7 | Hermite interpolation / Hermite recurrence | known standard | **known standard** | **no** |
| 8 | Repeated-node Newton filling | known standard | **known standard** | no |
| 9 | `PATH_*` vs `FAMILY_*` composition | known standard (analysis + assume-guarantee) | **engineering adaptation** | no, as a proof theory |
| 10 | Local-to-global symbolic certification | known standard idea (LEDA / WZ pattern; interpolant uniqueness) | **engineering adaptation** | no, as a certificate calculus |
| \* | Packaged fail-closed iterated certification of frozen Guo 5-branch | — | **GAP** | **no; not claimed** |

Primary labels for methods 1–10 are **not** contributions.
Methods 1, 2, 4–8 are not even engineering adaptations of the
*mathematics*: the identities and algorithms are classical or
published CAS. Wiring them as one-parameter `PathStep`s is
ordinary systems work and does not upgrade the label.

The last row is a **GAP**. It is not a “potential novel
contribution” that a draft may hedge into existence. V2 is H-C.
Frozen Guo family certificates do not exist.

---

## 1. Iterated one-parameter limits — known standard
(not novelty; not a Track-V3 contribution)

**Why this label (and why it is the point of this pack).**

\[
\lim_{x\to a}\Bigl(\lim_{y\to b} f(x,y)\Bigr)
\qquad\text{and}\qquad
\lim_{y\to b}\Bigl(\lim_{x\to a} f(x,y)\Bigr)
\]

are the *iterated* (repeated) limits. They are defined by
performing one one-parameter limit, then another. This is
undergraduate multivariable calculus (Apostol 1974; Rudin 1976).
CAS systems already compute them by nesting `limit`.

Track V3’s intended reduction — a multi-parameter / five-branch
claim broken into a *sequence* of exact one-parameter confluence
steps — is exactly this object. **It is not a new limit.**

**Why Track-V3 use does not upgrade the label.** Checking
\(\lim_{y\to x} K_{\mathrm{generic}} = K_{\mathrm{diag}}\) on one
declared coordinate, then repeating on the next, is a verifier
for a classical iterated limit. Success on a two-member Guo pair
is already Track V (`38d6d4a`). Sequencing those pair checks is
bookkeeping.

**False-novelty sentences to delete.** “We introduce iterated
limits.” “Iterated one-parameter confluence is a new algorithm.”
“Reducing a double limit to two single limits is the contribution.”

**Headline for authors.** Iterated limits are standard math, not
novelty.

---

## 2. Joint vs iterated limits / Moore–Osgood — known standard

**Why this label.** If the *joint* (simultaneous, double) limit
\(\lim_{(x,y)\to(a,b)} f(x,y)\) exists and the inner one-parameter
limits exist, the iterated limits exist and equal the joint value.
The converse is **false**. Textbook counter-example:

\[
f(x,y)=\frac{xy}{x^2+y^2}\quad(x,y)\neq(0,0):
\]

both iterated limits are \(0\); the joint limit does not exist
(path \(y=mx\) depends on \(m\)). Uniformity of one iterated limit
restores the joint limit (Moore–Osgood; Apostol 1974, uniform
convergence / double sequences; Rudin 1976 Ch. 7).

**Why Track-V3 use does not upgrade the label.** The schema
sentence “iterated limit is not joint limit unless consistency is
certified” is this textbook converse, encoded as
`require_path_independence`. It is `AGENTS.md` rule 14, not a
theorem of this repository.

**False-novelty sentences to delete.** “We prove that iterated
limits need not equal joint limits.” “PATH vs FAMILY is a new
analysis theorem.”

---

## 3. Path independence of limits — engineering adaptation
(mathematics: known standard)

**Why the mathematics is known standard.**

- Real analysis: agreement of two iterated orders is not the
  joint limit. Agreement along every line is not the joint
  limit (parabolic paths). Path-independence is a *lemma* toward
  a joint limit, not the limit.
- Interpolation: Hermite–Genocchi (de Boor 2005 §9; Alexander)
  gives joint continuity of \(F[x_0,\ldots,x_k]\) in the nodes
  for \(F\in C^k\), hence path-independent coalescence *under
  that hypothesis*.
- The engine does **not** have \(C^k\) a priori on Piecewise
  polygamma / occupation / `AppliedUndef` kernels.

**Why Track-V3 use is engineering adaptation, not novelty.**
`PathConsistencyObligation`: two declared iterated paths with a
common start and end must residual-compare. `CONSISTENT_ZERO` is
never assumed from commuting-looking coordinates. Disagreement
is `INCONSISTENT_NONZERO` ⇒ `FAMILY_NONZERO`. Missing or
`UNKNOWN` consistency, when the claim needs order independence,
blocks `FAMILY_ZERO`. That is fail-closed discipline wired to
`schema.compose_family_verdict`.

**Why it is not potential novelty.** Checking both orders is
what a responsible analysis wrapper does after Moore–Osgood.
Track V2 already required path-consistency obligations. Track V3
names them at PATH grain; it does not add an identity.

**Forbidden upgrade.** Invoking Hermite–Genocchi, Hartogs, or
Moore–Osgood to *skip* path-consistency on an untrusted kernel
(`AGENTS.md` rule 14).

---

## 4. Multivariate removable singularities — known standard

**Why this label.**

- One complex variable: Riemann’s removable singularity theorem
  (bounded holomorphic on a punctured disk extends). Filling a
  \(0/0\) by cancellation is the rational special case.
- Several complex variables: isolated singularities of
  holomorphic functions on \(\mathbb C^n\), \(n\ge 2\), are
  removable (Hartogs 1906). **Wrong object** for real Piecewise
  polygamma. Citing Hartogs to skip real path-consistency is a
  type error.
- Real multivariable calculus: a point where a rational
  function is undefined is removable iff the function extends
  continuously. That decision problem is classical; CAS
  algorithms for it are §5.

**Why Track-V3 use does not upgrade the label.** A one-parameter
confluence step that cancels a spectator and takes
\(\lim_{y\to x} K = K_{\mathrm{diag}}\) is Riemann/rational
removal along a line, plus interpolation confluence
\(\lim_{y\to x} F[x,y]=F[x,x]\). Track V’s confluence cascade
already does substitution / together / valuation / series /
L’Hôpital / Newton diagonal. Repeating that along a path is not
a new singularity theorem.

**False-novelty sentences to delete.** “We introduce removable
singularities for Piecewise kernels.” “Hartogs certifies the
Guo 5-branch.”

---

## 5. Symbolic multivariate-limit algorithms — known standard

**Why this label.** Univariate symbolic limits: Gonnet–Gruntz
(ISSAC 1988); Gruntz thesis (ETH 1996); `sympy.limit`.
Multivariate *rational* / isolated-denominator limits are a
published CAS topic, not a gap this repo fills:

- Cadavid, Molina, Vélez, *J. Symbolic Comput.* 50 (2013)
  197–207 (bivariate analytic quotients; Maple `limit/multi`).
- Xiao and Zeng, *Sci. China Math.* 57 (2014) 397–416.
- Zeng and Xiao, *J. Symbolic Comput.* 96 (2020) 1–21 (Sturm).
- Alvandi, Ataei, Moreno Maza (ISSAC 2017 / JSC 2020 Extended
  Hensel) and RegularChains multivariate rational limits.
- Strzeboński, arXiv:2102.01242 (Mathematica; Łojasiewicz /
  CAD methods).

**Why Track-V3 use does not upgrade the label.** Nested
one-parameter `sympy.limit` *is* how many CAS systems already
approximate a multivariate limit when they do not run Cadavid /
CAD. That approximation is exactly the iterated-vs-joint trap
of §2. Track V3’s honesty is to *refuse* to treat the nested
call as a joint certificate. Refusal is contract, not an
algorithm.

Those published algorithms also do **not** decide Guo-scale
`Sum`/`Piecewise`/polygamma families. Wrong object, not a
missing theorem we supply.

**False-novelty sentences to delete.** “First symbolic
multivariate limit.” “We replace Gruntz.” “Maple cannot do
this, therefore we are novel.” (Lack of a runtime is not
novelty; frozen Track V literature already recorded that for
egg/Lean/Wolfram.)

---

## 6. Confluent divided differences — known standard

**Why this label.** \(F[x,y]=(F(x)-F(y))/(x-y)\),
\(F[x,x]=F'(x)\), \(\lim_{y\to x}F[x,y]=F[x,x]\). Newton 1711;
Conte–de Boor 1980; de Boor 2005. Continuity in the nodes *is*
interpolation confluence.

**Track-V3 delta.** A `PathStep` with relation
`one_parameter_confluence` / `repeated_node_confluence` is the
same identity Track V already used as `DD_CERTIFICATE` and
Track V2 already used as a local edge. Sequencing several of
them is not a new formula.

Track V and Track V2 already recorded: do not lead with “we
introduce divided differences.” Track V3 does not lift that
ban.

---

## 7. Hermite interpolation / Hermite recurrence — known standard
(not novelty; not a Track-V3 contribution)

**Why this label.** Hermite 1878; Traub 1964; Conte–de Boor
§2.7; de Boor 1978/2005. The recurrence with repeated-node
diagonal \(F[a,\ldots,a]_{k+1}=F^{(k)}(a)/k!\) is osculatory
interpolation. Track V2’s entire literature pack exists to say
this sentence: **Hermite recurrence is standard math, not
novelty.** Iterating one-parameter coalescences does not
un-classify it.

**Why Track-V3 use does not upgrade the label.** A path
generic → one pair equal → all three equal is the Newton table
being filled one multiplicity at a time. That is the definition
of a Hermite table, not a research contribution.

---

## 8. Repeated-node Newton filling — known standard

**Why this label.** Osculatory interpolation: repeated nodes
encode derivative data. de Boor 2005 §§1–2, 8–9; Kowalewski
(cited there) treats multiplicities from the start.

**Track-V3 use.** Edge relation `repeated_node_confluence`;
schema field `degeneracy_coordinates`. Bookkeeping so a
two-parameter star is not silently substituted as \(0/0\).
Not a theorem.

---

## 9. `PATH_*` vs `FAMILY_*` composition — engineering adaptation
(mathematics / CS: known standard)

**Why known standard.**

- Analysis: iterated \(\neq\) joint (§§1–3).
- Interpolation: a consistent Newton/Hermite table is a unique
  interpolant; path independence under \(C^k\) is
  Hermite–Genocchi, not V3.
- Verification: congruence of equality; Floyd–Hoare /
  assume-guarantee; SMT lemmas. Global spec from local
  contracts only when *every* contract and the glue hold.
  Majority vote is not a sound rule. Track V2 already shipped
  `compose_family_verdict` with no-majority tests.

**Why Track-V3 use is engineering adaptation.** New IR names,
not new math:

- `PATH_ZERO` iff every required step on one declared path is
  `ZERO`; any step `NONZERO` ⇒ `PATH_NONZERO`; else
  `PATH_UNKNOWN`. Empty path is `PATH_UNKNOWN`, not
  `PATH_ZERO`.
- `FAMILY_ZERO` iff every required path is `PATH_ZERO`, every
  required local edge is `ZERO`, branch reconstruction is
  `ZERO`, and — when the claim needs order independence —
  path consistency is `CONSISTENT_ZERO`.
- Any required `NONZERO` or `INCONSISTENT_NONZERO` ⇒
  `FAMILY_NONZERO`. Otherwise `FAMILY_UNKNOWN`.
- **`PATH_ZERO` is not `FAMILY_ZERO`.** Majority is forbidden.
  Timeout / size-guard / missing consistency stay `UNKNOWN`.

That three-way is this repository’s language
(`research/iterated_confluence/schema.py`). Shipping it is
systems work.

**Why it is not potential novelty as a method.** A paper that
claims “we introduce PATH vs FAMILY verification” will be
referred to iterated-vs-joint limits and to Track V2’s family
rule. The remaining question is empirical: does the iterated
split turn Guo-scale 5-branch `FAMILY_UNKNOWN` into honest
`FAMILY_ZERO` / `FAMILY_NONZERO` without false family
acceptance? That question is unanswered. V2 is H-C.

---

## 10. Local-to-global symbolic certification — engineering adaptation
(idea: known standard)

**Why known standard.** LEDA certifying algorithms; WZ short
witnesses; ITP kernels as the strong form; Track V reconstruction
certificates; Track V2 edge-bundle certificates. “Check a small
witness instead of Gruntz on the 5-way Piecewise” is the same
slogan.

**Why Track-V3 use is engineering adaptation.** A `PathStep` is
a witness for one one-parameter edge (possibly after spectator
split). A `PathCertificate` is an ordered list of such
witnesses. An `IteratedConfluenceCertificate` is a bundle of
paths plus consistency plus reconstruction. Level-1 engine
semantics only (`CERTIFICATION_SCOPE.md`). Intermediates must
be source-derived (`IntermediateExpression`); anonymous
algebraic interpolation of missing branches is forbidden
(`PROTOCOL.md`).

**Forbidden upgrade.** Randomized PIT, `N[..., 30]`, or
`PossibleZeroQ` as `PATH_ZERO` or `FAMILY_ZERO`. Numeric
agreement is never ZERO. Timeout converted because “the other
path finished” is a false family ZERO.

**Why it is not potential novelty.** Moving from one certificate
to a *path* of certificates is still LEDA-shaped. Local-to-global
glue is assume-guarantee. Neither is a new proof object.

---

## \*. Packaged fail-closed iterated certification — **GAP**
(not a method in §§1–10; not a claim)

**What it would be, if anything.** A measured *systems* protocol,
not a theorem:

> Frozen, already-proposed 5-branch Guo families are rescored
> by decomposing multi-parameter confluence into a sequence of
> exact one-parameter steps whose local symbolic complexity is
> comparable to the already-certified two-member Guo pairs,
> composing those steps fail-closed into `PATH_*` and then
> `FAMILY_*`, with timeout/size-guard remaining `UNKNOWN`,
> numeric agreement never ZERO, majority vote forbidden, no
> Guo-specific identities, `PATH_ZERO` never sold as joint
> confluence, false `FAMILY_ZERO` = 0, without mutating
> historical runs.

If that protocol ever worked, the only honest remainder would
be **verification-engineering**: proof decomposition / routing /
scientific-expression-scale machine certification under engine
semantics. It would still not be a mathematics contribution.
Iterated limits, Hermite, and Newton DD would remain standard.

**Why this cell is a GAP, not a “potential novel contribution.”**

- V2 closed CASE H-C (`fe53ebc`): 7/7 frozen families
  `FAMILY_UNKNOWN`.
- Track V3 freeze (`dcfb90c`, `FROZEN_INPUTS_V3.json`, n=7)
  inherits that status. No V3 rescore exists.
- This literature pack runs no experiment.
- `PROTOCOL.md` outcome classes I-A / I-B have not fired.
  Track D2 stays LOCKED. Publication status E.

The user-facing rule for this track: a system-level combination
may be named as a *candidate* **only if** later `FAMILY_ZERO`
on the frozen Guo 5-branch exists. It does not. Therefore the
label is **GAP**. Do not quote this row as novelty, conditional
novelty, or “the contribution, if experiments support it” in a
paper title or abstract.

**What would still not upgrade the label even after a rescore.**

- `PATH_ZERO` on one order, consistency `UNKNOWN`.
- Relabeling Track V’s 3 two-member ZERO as family
  certification.
- Cubic / toy probes (`z^3`, \(F[x,x,x]=3x\)).
- Compiler gain on members already spelled as DDs.
- Guo-specific identity tables, gold names, numeric
  “certificates,” majority of paths, timeout-as-zero.
- Claiming iterated limits, Hermite recurrence, or Newton DD
  as the novelty (they are not).

**Even if later `FAMILY_ZERO` appears, do not say:**

- first LLM+verifier (crowded; frozen `novelty_boundary.md`);
- formal proof / machine-checked theorem;
- we invented iterated limits / divided differences / Hermite /
  the Hermite recurrence / masters;
- e-graph confluence of physics kernels;
- we discovered \(\Phi_\Gamma\) or L4–L7;
- Track V pair-ZERO already was 5-branch certification;
- `PATH_ZERO` is joint confluence;
- Hartogs / Hermite–Genocchi licensed skipping path checks.

---

## Upgrade experiments (what would change the GAP cell)

Literature does not generate these numbers. Owned by V3-A..J +
eval, not by V3-K. Until they exist, **do not change the GAP
label**.

1. **Frozen Guo 5-branch, not pairs.** `FAMILY_ZERO` (or honest
   `FAMILY_NONZERO`) on the five-member families in
   `FROZEN_INPUTS_V3.json`. Relabeling Track V pair-ZERO is
   forbidden. A single `PATH_ZERO` is not enough.
2. **False `FAMILY_ZERO` = 0.** Falsifiers (V3-J): majority of
   paths; one `PATH_ZERO` sold as family; skipped consistency;
   coincident \(0/0\) sold as \(F'\); vanishing spectator;
   timeout sold as ZERO; numeric “certificate”; leaked gold
   names; interpolated (not source-derived) intermediates.
   All must stay `FAMILY_NONZERO` or `FAMILY_UNKNOWN`.
3. **No Guo-specific identities.** Zero rules that name
   \(\Phi_\Gamma\), \(\mathfrak M_\Gamma\), \(\mathfrak T_\Gamma\),
   or the nine generators are leakage, not V_GAIN.
4. **Local complexity.** One-parameter kernels comparable in
   ops to the already-certified two-member Guo cases, not a
   giant 573-op generic residual Gruntz’d in one shot.
5. **Symbolic baselines.** Same frozen families, no new
   proposer: (i) nested `DIRECT` Gruntz; (ii) textbook
   Newton/Hermite given \(F\) and nodes; (iii) Cadavid-style
   rational multivariate limit if the kernel is even rational;
   (iv) Track V pair cascade without iterated glue. Method
   claim needs a gap after (i)–(iv) labeled family V_GAIN,
   not C_GAIN.
6. **Second family.** At least one non-Guo scientific
   expression family, or even a later `FAMILY_ZERO` stays n=1.

Until those exist, the honest status is: **methods classified;
iterated limits are not novelty; Hermite recurrence is not
novelty; Newton DD is not novelty; `PATH_ZERO` is not joint
confluence; no Track-V3 method result; packaged contribution
is a GAP because Guo family certificates do not exist.**

---

## Claims a knowledgeable reviewer would reject immediately

| Claim | Why it dies | Who cites it |
|---|---|---|
| “We invented iterated limits” | Apostol; Rudin; every Calc III course | any analyst |
| “Iterated limit = joint limit” | textbook converse; Moore–Osgood needed | any analyst |
| “`PATH_ZERO` is `FAMILY_ZERO` / joint confluence” | schema forbids it; `AGENTS.md` rule 14 | ourselves |
| “We invented divided differences / Hermite interpolation / the Hermite recurrence” | Newton, Hermite, Conte–de Boor, de Boor 2005 | any numerical analyst |
| “Confluent DD is a new limit algorithm” | it is the definition of \(F[x,x]\) | Gruntz + de Boor readers |
| “Repeated nodes are a new regularization” | osculatory interpolation | NA textbooks |
| “First symbolic multivariate limit” | Cadavid 2013; Xiao–Zeng 2014; RegularChains; Strzeboński; Maple `limit/multi` | CAS users |
| “Hartogs certifies Guo coalescence” | SCV holomorphic \(\neq\) real Piecewise polygamma | several-complex-variables readers |
| “Hermite–Genocchi lets us skip path checks” | \(C^k\) not given on the kernel | NA *and* this engine’s contract |
| “Local-to-global family verification is new” | interpolant uniqueness; assume-guarantee; Track V2 | NA *and* FV reviewers |
| “We invented proof certificates” | LEDA; WZ; ITP kernels | PL / combinatorics / ITP |
| “E-graphs already do this confluence” | rewriting \(\neq\) interpolation confluence | PL *and* NA reviewers |
| “IBP families already do this” | linear masters \(\neq\) Newton table | HEP users |
| “Formal certification” | SymPy residual + probes; UNKNOWN fail-closed | Lean/e-graph reviewer |
| “Timeout / 4-of-5 paths converted to FAMILY_ZERO is conservative” | it is a false FAMILY_ZERO | this engine’s own contract |
| “Track V pair-ZERO is V3 FAMILY_ZERO” | different object; PATH is not FAMILY | ourselves |
| “V3-K literature is a method result / a contribution” | no rescore; V2 is H-C; GAP cell | ourselves |

---

## Positioning sentence (not a title)

> Iterated limits, the distinction between iterated and joint
> limits, path independence, removable singularities, Newton and
> Hermite divided differences, and assume-guarantee glue are
> standard tools. Track V3 asks whether those tools, routed
> fail-closed as one-parameter paths over already-proposed
> 5-branch scientific families, can replace a giant global
> `sympy.limit` without false `FAMILY_ZERO`. Iterated limits
> are not the contribution. Hermite recurrence is not the
> contribution. Newton DD is not the contribution.
> `PATH_ZERO` is not joint confluence. A systems contribution
> does not exist until the frozen Guo 5-branch set returns
> `FAMILY_ZERO` with false `FAMILY_ZERO` = 0. That experiment
> has not run. The cell is a GAP.
