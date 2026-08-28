# Classification of Track V2 family-certificate methods

Audit date: 2026-08-28.
Companion: `METHODS.md`. Labels are for **paper-facing honesty**, not
marketing.

Allowed labels (exactly one primary label per method):

| label | meaning |
|---|---|
| **known standard** | Textbook or published algorithm. Shipping it is reimplementation. |
| **engineering adaptation** | Standard method, wired into this engine’s family IR, budgets, and fail-closed three-way. Systems work, not a new theorem. |
| **potential novel contribution** | Not claimed. Would require measured `FAMILY_ZERO` on the **frozen Guo 5-branch** set with false `FAMILY_ZERO` = 0, without gold names, without majority vote. Absence of a packaged evaluation is a **gap**, not a proof. |

**Hard rule.** The Hermite recurrence (Newton table, including the
repeated-node diagonal \(F[a,\ldots,a]_{k+1}=F^{(k)}(a)/k!\)) is
**known standard**. It is not an engineering adaptation of
*mathematics* and it is not a potential novel contribution. A
reviewer who knows Hermite 1878, Conte–de Boor §2.7, or de Boor 2005
will desk-reject any draft that leads with “we introduce the Hermite
recurrence,” “we introduce divided differences,” or “we introduce
Hermite interpolation.”

Track V already recorded this ban at pair scale
(`research/scalable_verification/literature/CLASSIFICATION.md`).
Track V2 does not lift the ban by composing several textbook edges
into a family.

This pack classifies **family-verification methods** (Track V2).
Discovery of a representation \(H=(R,\{A_i\},\{\mathcal O_i\},F)\) is
Track D and stays locked until CASE H-A or H-B (`PROTOCOL.md`).

---

## Summary table

| # | Method | Mathematics | Track-V2 use (primary label) | May a paper call this novel? |
|---|---|---|---|---|
| 1 | Newton divided differences | known standard | **known standard** | no |
| 2 | Hermite recurrence / confluent DD | known standard | **known standard** | **no** |
| 3 | Repeated-node filling | known standard | **known standard** | no |
| 4 | Limit decomposition (typed coalescence paths) | known standard (Hermite–Genocchi) | **engineering adaptation** | no (math); use is routing, not a theorem |
| 5 | Compositional certificates (local edges) | known standard (LEDA / WZ pattern) | **engineering adaptation** | no, as a certificate calculus |
| 6 | Local-to-global family rule | known standard (assume-guarantee / interpolant uniqueness) | **engineering adaptation** | no, as a proof theory |
| \* | Packaged fail-closed `FAMILY_ZERO` on frozen Guo 5-branch | — | **potential novel contribution** (conditional) | **only if** later experiments in §Upgrade exist; still not a math contribution |

Primary labels for methods 1–6 are **not** “potential novel
contribution.” Method 2 is not even an engineering adaptation of the
*recurrence*: the identity is 19th-century. Wiring it as
`hermite_dd_recurrence` is ordinary systems work and does not upgrade
the label.

The only conditional novelty is the *package* (last row): a
fail-closed family verdict on the frozen 5-branch Guo hypotheses
that Track V left `UNKNOWN`. That is a protocol/measurement claim,
not a new identity.

---

## 1. Newton divided differences — known standard

**Why this label.** Newton 1711; Conte–de Boor 1980 Ch. 2; de Boor
2005. \(F[x,y]=(F(x)-F(y))/(x-y)\) and the distinct-node recurrence
are the definition of the Newton table.

**Track-V2 delta.** Edge kind `dd_recurrence` residual-checks two
catalog members against that recurrence. Constructors already exist
in `research/representation_invention/dd/`. Pair-scale certificates
already exist in Track V `dd_cert/`. None of that is a new formula.

**False-novelty sentences to delete.** “We give a new divided-difference
algorithm.” “Family recurrence is a new limit algorithm.”

---

## 2. Hermite recurrence — known standard
(not novelty; not a Track-V2 contribution)

**Why this label (and why it is the point of this pack).**

\[
F[x_0,\ldots,x_k]
=
\begin{cases}
(F[x_1,\ldots,x_k]-F[x_0,\ldots,x_{k-1}])/(x_k-x_0),
& x_k\neq x_0,\\
F^{(k)}(x_0)/k!,
& \text{all nodes equal.}
\end{cases}
\]

Hermite 1878; Traub 1964; Conte–de Boor §2.7 osculatory
interpolation; de Boor 1978/2005. Continuity in the nodes *is*
interpolation confluence. Implementing `hermite_dd` /
`hermite_dd_recurrence` is a textbook constructor.

**Why Track-V2 use does not upgrade the label.** Checking that two
frozen Piecewise branches differ by this identity is a verifier.
If members are already spelled as difference quotients or
derivatives, success is compiler/language gain (`C_GAIN`), not
discovery and not a new verification theory. If members are *not*
so spelled, success is still a check of a classical identity.

**Why it is not potential novelty.** “Hermite divided differences as
the confluence mechanism” is a correct *scientific reading* of some
physics kernels (human ladder L5 in the 2026-08-21 note). It is not
a new mathematical object. This track does not invent
\(\mathfrak M_\Gamma,\mathfrak T_\Gamma\). Using \(H_1,H_2\) as gold
names in a verifier is leakage, not contribution.

**Headline for authors.** Hermite recurrence is standard math, not
novelty.

---

## 3. Repeated nodes — known standard

**Why this label.** Osculatory interpolation: repeated nodes encode
derivative data. \(F[a,a]=F'(a)\). Filling the first column of the
Newton table with derivatives is undergraduate NA.

**Track-V2 use.** `node_multiplicities` and edge kind
`repeated_node_confluence`. Bookkeeping so the composition rule can
reject inconsistent multiplicity graphs. Not a theorem.

**Why it is not potential novelty.** de Boor 2005 §§1–2, 8–9 already
treats arbitrary site multiplicities and their continuity. Kowalewski
(cited there) defines DD with multiplicities from the start.

---

## 4. Limit decomposition — engineering adaptation
(mathematics: known standard)

**Why the mathematics is known standard.** Hermite–Genocchi: DD is a
simplex integral of \(F^{(k)}\), jointly continuous in the nodes for
\(F\in C^k\). Simultaneous and iterated coalescence therefore agree
*under that hypothesis*. One-parameter confluence
\(\lim_{y\to x}F[x,y]=F[x,x]\) is the \(k=1\) case (Track V §2).

**Why Track-V2 use is engineering adaptation, not novelty.** Splitting
a 5-branch claim into typed `limit` / `one_parameter_confluence` /
`repeated_node_confluence` edges, plus **path-consistency**
obligations because the engine does not have \(C^k\) a priori
(`AGENTS.md` rule 14: do not silently reorder limits). That split is
a *strategy choice*: local certificates instead of one Gruntz call
on the 5-way Piecewise. It does not add an identity.

**Why it is not potential novelty.** Decomposition of a limit along
coordinate axes is ordinary analysis. Checking both paths is
fail-closed discipline, not a theorem. Track V already did the
one-parameter case for two-member Guo pairs.

**Two-confluence trap.** Interpolation confluence ≠ Knuth–Bendix /
e-graph confluence. Do not cite egg as prior work *for this
identity*, and do not cite de Boor as prior work *for equality
saturation*. Do not cite IBP “integral families” as prior work *for
Newton tables*.

---

## 5. Compositional certificates — engineering adaptation
(idea: known standard)

**Why known standard.** LEDA certifying algorithms; WZ short
witnesses; ITP kernels as the strong form; Track V reconstruction
certificates for pair-scale DD.

**Why Track-V2 use is engineering adaptation.** Treat each
`LocalEdge` as a witness; the checker rebuilds the claimed relation
and residual-compares. Recurrence and path-consistency obligations
are the same idea. Level-1 engine semantics only
(`CERTIFICATION_SCOPE.md`).

**Forbidden upgrade.** Randomized PIT, `N[..., 30]`, or
`PossibleZeroQ` as a ZERO *or* `FAMILY_ZERO` certificate. Those are
known standard **for other problems** and **out of contract** here.

**Why it is not potential novelty.** “Certificate” is a crowded word.
WZ, LEDA, and Lean already own it. This track’s witnesses are
reconstruction terms, not a new proof object. Moving from one
certificate to a *bundle* of certificates is still LEDA-shaped.

---

## 6. Local-to-global family rule — engineering adaptation
(mathematics / CS: known standard)

**Why known standard.**

- Interpolation: a consistent Newton/Hermite table determines a
  unique interpolant of declared degree. Path independence under
  \(C^k\) is Hermite–Genocchi, not V2.
- Verification: congruence of equality; Floyd–Hoare /
  assume-guarantee; SMT lemmas. Global spec from local contracts
  only when *every* contract and the glue hold. Majority vote is
  not a sound rule.

**Why Track-V2 use is engineering adaptation.**
`compose_family_verdict`: `FAMILY_ZERO` iff connected required
graph, all required edges ZERO, recurrence ZERO, path consistency
ZERO, multiplicities consistent, latent compatible; any required
NONZERO ⇒ `FAMILY_NONZERO`; else `FAMILY_UNKNOWN`. The three-way
and the “no majority” tests (`tests/test_mb_schema.py`) are this
repository’s language.

**Why it is not potential novelty as a method.** A paper that claims
“we introduce local-to-global verification of identities” will be
referred to assume-guarantee, ITP, and interpolant uniqueness. The
remaining question is empirical: does the glue turn Guo-scale
5-branch `UNKNOWN` into honest `FAMILY_ZERO` / `FAMILY_NONZERO`
without false family acceptance?

---

## \*. Packaged fail-closed family certification — potential novel
contribution (conditional, not a method in §§1–6)

**What it would be, if anything.** A measured protocol:

> Frozen, already-proposed 5-branch (and Hermite-typed) Guo P2
> hypotheses are rescored by composing local exact edges with the
> *textbook* Hermite recurrence and checked coalescence paths,
> with timeout/size-guard remaining `FAMILY_UNKNOWN`, numeric
> agreement never ZERO, majority vote forbidden, no Guo-specific
> identities, false `FAMILY_ZERO` = 0, and gains labeled at family
> grain without mutating historical runs.

**The only experiment that may ever upgrade this row.** Later
`FAMILY_ZERO` on the **frozen Guo 5-branch** set
(`FROZEN_INPUTS_V2.json`, the five-member families; not the already
closed two-member Track V pairs), with **false `FAMILY_ZERO` = 0**.
Anything else — cubic unit probes, two-member subgraphs, compiler
gain on members already spelled as DDs, a 4-member substitution
family sold as 5-branch, or `FAMILY_UNKNOWN` with a narrative — does
**not** upgrade the label.

**Why this is the only row that may ever be called a contribution.**
No retrieved system jointly does (i)–(vi) in `METHODS.md` §8 on
`Sum`/`Piecewise`/indexed physics *families*. Closest fragments:
Newton/Hermite (math), Track V (pairs), LEDA/assume-guarantee
(glue slogan), IBP families (wrong object), egg/LGuess (wrong
confluence).

**Why it is still not a claim.** This literature pack runs no
rescore. `PROGRAM_STATUS_V2.md` has not closed Track V2. A gap is
not a result. If recurrence only fires on members that already
*are* Newton-table entries, the package collapses to compiler gain.
If Guo is the only scientific family, C3-style generalization is
false. If any false `FAMILY_ZERO` appears, the merge gate fails and
the package is a bug.

**Even if `FAMILY_ZERO` appears, do not say:**

- first LLM+verifier (crowded; frozen `novelty_boundary.md`);
- formal proof / machine-checked theorem;
- we invented divided differences / Hermite / the Hermite
  recurrence / masters;
- e-graph confluence of physics kernels;
- we discovered \(\Phi_\Gamma\) or L4–L7;
- Track V’s 3 pair-ZERO already was 5-branch certification;
- Hermite recurrence is the novelty (it is not).

The remaining sentence, if experiments support it, is: *already-proposed
5-branch hypotheses can be adjudicated by composing textbook
local edges, under engine semantics, without a giant global limit
and without false family ZERO.* That is a
**verification-engineering** result, not a mathematics result.

---

## Upgrade experiments (what would change a label)

Literature does not generate these numbers. Owned by V2-A..I +
eval, not by V2-J.

1. **Frozen Guo 5-branch, not pairs.** `FAMILY_ZERO` (or honest
   `FAMILY_NONZERO`) on the five-member families in
   `FROZEN_INPUTS_V2.json`. Relabeling Track V pair-ZERO is
   forbidden. Hermite-typed hyps count only if the family rule
   fires, not if the type string matches.
2. **False `FAMILY_ZERO` = 0.** Falsifiers (V2-H): majority of
   edges; disconnected graph; missing recurrence; path reorder;
   coincident 0/0 sold as \(F'\); vanishing spectator; timeout
   sold as family ZERO; numeric “certificate”; leaked gold names.
   All must stay `FAMILY_NONZERO` or `FAMILY_UNKNOWN`.
3. **No Guo-specific identities.** Zero rules that name
   \(\Phi_\Gamma\), \(\mathfrak M_\Gamma\), \(\mathfrak T_\Gamma\),
   or the nine generators are leakage, not V_GAIN.
4. **Symbolic baselines.** Same frozen families, no new proposer:
   (i) `DIRECT` Gruntz/residual on the 5-way Piecewise; (ii)
   textbook Newton/Hermite constructor given \(F\) and nodes;
   (iii) SymPy `simplify`/`factor`; (iv) Track V pair cascade
   without family glue. Method claim needs a gap after (i)–(iv)
   labeled family V_GAIN, not C_GAIN.
5. **Second family.** At least one non-Guo scientific expression
   family, or the package stays n=1 even after `FAMILY_ZERO`.

Until those exist, the honest status is: **methods classified;
Hermite recurrence is not novelty; no Track-V2 method result;
potential novelty only if later `FAMILY_ZERO` on frozen Guo
5-branch with false `FAMILY_ZERO` = 0.**

---

## Claims a knowledgeable reviewer would reject immediately

| Claim | Why it dies | Who cites it |
|---|---|---|
| “We invented divided differences / Hermite interpolation / the Hermite recurrence” | Newton, Hermite, Conte–de Boor, de Boor 2005 | any numerical analyst |
| “Confluent DD is a new limit algorithm” | it is the definition of \(F[x,x]\) | Gruntz + de Boor readers |
| “Repeated nodes are a new regularization” | osculatory interpolation | NA textbooks |
| “Local-to-global family verification is new” | interpolant uniqueness; assume-guarantee | NA *and* FV reviewers |
| “We invented proof certificates” | LEDA; WZ; ITP kernels | PL / combinatorics / ITP |
| “E-graphs already do this confluence” | rewriting ≠ interpolation confluence | PL *and* NA reviewers |
| “IBP families already do this” | linear masters ≠ Newton table | HEP users |
| “Formal certification” | SymPy residual + probes; UNKNOWN fail-closed | Lean/e-graph reviewer |
| “Timeout / 4-of-5 edges converted to FAMILY_ZERO is conservative” | it is a false FAMILY_ZERO | this engine’s own contract |
| “Track V pair-ZERO is V2 FAMILY_ZERO” | different object; schema forbids majority | ourselves |
| “V2-J literature is a method result” | no rescore, no tests required | ourselves |

---

## Positioning sentence (not a title)

> Newton and Hermite divided differences, the Hermite recurrence,
> repeated-node filling, coalescence limits, compositional
> certificates, and assume-guarantee glue are standard tools.
> Track V2 asks whether those tools, composed fail-closed over
> already-proposed 5-branch scientific families, can replace a
> giant global `sympy.limit` without false `FAMILY_ZERO`. The
> Hermite recurrence is not the contribution. A contribution exists
> only if the frozen Guo 5-branch set later returns `FAMILY_ZERO`
> with false `FAMILY_ZERO` = 0.
