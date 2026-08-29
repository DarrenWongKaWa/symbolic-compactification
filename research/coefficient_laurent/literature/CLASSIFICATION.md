# Classification of Track V5 coefficient-space Laurent methods

Audit date: 2026-08-28.
Companion: `METHODS.md`. Labels are for **paper-facing honesty**, not
marketing.

Allowed labels (exactly one primary label per method):

| label | meaning |
|---|---|
| **known standard** | Textbook or published algorithm. Shipping it is reimplementation. |
| **engineering adaptation** | Standard method, wired into this engine’s Laurent-coefficient IR, budgets, and fail-closed three-way (`LEVEL_A` / `LEVEL_B` / `LEVEL_C`). Systems work, not a new theorem. |
| **GAP** | Not claimed. Would require hop `LEVEL_C` `ZERO` on **G0016→G0013** with false hop `ZERO` = 0, without 27k `together()`, without Guo identities. The hop was run. After remainder fail-close it is `LEVEL_B` `UNKNOWN` (C0 matches; `remainder_ok` False on symbolic α). V4 closed CASE J-C. A C0 lemma is not hop ZERO. |

There is **no** “potential novel contribution” row that may be
quoted as a result. Track V and Track V2 allowed a *conditional*
package row. Track V3 refused that upgrade because Guo family
certificates did not exist. Track V5 refuses it because
G0016→G0013 is not `LEVEL_C` `ZERO` (C0 matches; remainder is
UNKNOWN). If that hop later is `LEVEL_C` `ZERO`, the only honest
remainder would be **coefficient-space routing at
scientific-expression scale** (verification-engineering, not
mathematics). Until then the cell is a **GAP**.

**Hard rules.**

1. Sparse Laurent series is **known standard**. It is not an
   engineering adaptation of *mathematics* and it is not a
   contribution. A reviewer who knows Laurent 1843, Ahlfors, or
   Geddes–Czapor–Labahn sparse polynomials will desk-reject any
   draft that leads with “we introduce sparse Laurent series.”
2. Polygamma Taylor expansion is **known standard** (DLMF 5.15;
   \(\frac{d}{dz}\mathrm{polygamma}(n,z)=\mathrm{polygamma}(n+1,z)\)).
   It is not a Track-V5 contribution. Track V4 already recorded
   this ban. Track V5 does not lift it.
3. `LEVEL_A` (atoms expanded) is **not** hop `ZERO`. A \(t^0\)
   match with a surviving \(t^{-1}\) is `NONZERO`. Only
   `LEVEL_C` may return `ZERO`.

This pack classifies **coefficient-space Laurent verification
methods** (Track V5). Discovery of a representation
\(H=(R,\{A_i\},\{\mathcal O_i\},F)\) is Track D / D2 and stays
locked (`PROTOCOL.md`; `PROGRAM_STATUS_V5.md`: Track D2 LOCKED;
publication status E).

---

## Summary table

| # | Method | Mathematics | Track-V5 use (primary label) | May a paper call this novel? |
|---|---|---|---|---|
| 1 | Laurent series | known standard | **known standard** | **no** |
| 2 | Sparse Laurent / sparse polynomial coefficient arithmetic | known standard | **known standard** | **no** |
| 3 | Polygamma Taylor / derivative / polar Laurent | known standard | **known standard** | **no** |
| 4 | Coefficient extraction / residues / \([t^k]\) | known standard | **known standard** | no |
| 5 | Formal / truncated power series in CAS | known standard (Gruntz; Maple/SymPy `series`) | **known standard** | no |
| 6 | Removable singularities via vanishing principal part | known standard (Riemann) | **known standard** | no |
| 7 | Linearity of coefficients / termwise accumulation | known standard | **engineering adaptation** | no (math); sparse IR is routing, not a theorem |
| 8 | Per-atom series then `together` (V4) | known standard series | **engineering adaptation** | no; already J-C on a different hop class |
| 9 | `LEVEL_A` / `LEVEL_B` / `LEVEL_C` hop certificates | known standard (Riemann + remainder) | **engineering adaptation** | no, as a certificate calculus |
| 10 | Fail-closed cache keyed on full member text | known standard (hash integrity) | **engineering adaptation** | no |
| \* | Packaged fail-closed coefficient-space routing of G0016→G0013 | — | **GAP** | **no; not claimed** |

Primary labels for methods 1–10 are **not** contributions.
Methods 1–6 are not even engineering adaptations of the
*mathematics*: the identities and algorithms are classical or
published CAS. Wiring them as per-atom coefficient maps is
ordinary systems work and does not upgrade the label.

The last row is a **GAP**. It is not a “potential novel
contribution” that a draft may hedge into existence. V4 is
J-C. G0016→G0013 is hop `UNKNOWN` (`LEVEL_B`: negatives and C0
certified, remainder not). The candidate system contribution,
*if* that hop later is `LEVEL_C` `ZERO`, would be
coefficient-space routing at scientific-expression scale —
still not sparse Laurent, still not polygamma Taylor.

---

## 1. Laurent series — known standard
(not novelty; not a Track-V5 contribution)

**Why this label (and why it is the point of this pack).**

\[
f(t)=\sum_{k=k_{\min}}^{\infty} a_k t^k
\]

in a punctured neighborhood of an isolated singularity is
Laurent’s 1843 extension of Cauchy’s Taylor theorem (Weierstrass
1841/1894 independently). Undergraduate complex analysis
(Ahlfors; Conway; Rudin). CAS `series` already emits truncated
Laurent polynomials.

Track V5’s intended reduction — a 573-op generic kernel broken
into atoms whose one-parameter germs are Laurent in
\(t=\mathrm{var}-\mathrm{point}\) — is exactly this object.
**It is not a new series.**

**Why Track-V5 use does not upgrade the label.** Reading
\(a_k\) of local atoms and asking whether \(k<0\) vanish and
\(a_0\) equals the diagonal target is a verifier for a
classical removable singularity. Success on *diagonal→triple*
Guo hops is already Track V4 (`248d247`). Doing the same
readout from a sparse map instead of from `together` is
bookkeeping.

**False-novelty sentences to delete.** “We introduce Laurent
series.” “Laurent certificates are a new limit algorithm.”
“Coefficient-space is a new analysis theorem.”

**Headline for authors.** Sparse Laurent series is not
novelty. Laurent series itself is not novelty.

---

## 2. Sparse Laurent / sparse polynomial arithmetic — known standard
(not novelty; not a Track-V5 contribution)

**Why this label.** Storing only nonzero \((k,a_k)\) and adding
by merging supports is the default distributed polynomial
representation in CAS (Geddes, Czapor, Labahn 1992, Ch. 2–4;
Knuth vol. 2; FORM, Maple, SymPy `Poly`). Formal Laurent series
with finite principal part are the same maps with a bounded
negative support.

**Why it is not potential novelty.** “Sparse” is a data
structure. Sparse *interpolation* (Zippel 1979; Ben-Or–Tiwari
1988) is a different, also published, algorithm Track V5 does
not run. Puiseux (Duval 1989) is a different series. Calling
the accumulator “sparse Laurent certificates” in a title is
false novelty.

**False-novelty sentences to delete.** “We introduce sparse
Laurent series.” “Sparse coefficient maps are a new certificate
calculus.”

---

## 3. Polygamma Taylor / derivative / polar Laurent — known standard
(not novelty; not a Track-V5 contribution)

**Why this label (and why it is the other point of this pack).**

\[
\frac{d}{dz}\mathrm{polygamma}(n,z)=\mathrm{polygamma}(n+1,z),
\qquad
\mathrm{polygamma}(n,z+t)
=\sum_{k\ge 0}\mathrm{polygamma}(n+k,z)\,\frac{t^k}{k!}.
\]

DLMF 5.15; Abramowitz–Stegun Ch. 6; Nielsen 1906; Whittaker–
Watson; SymPy’s `polygamma` table. Near non-positive integers
the germ is Laurent with leading term
\((-1)^{n+1} n!\, t^{-n-1}\). Track V already classified local
polygamma rewrite as table lookup, not master invention.
Track V4’s literature sentence is still binding: polygamma
derivative, Taylor, and Laurent \(t^0\) of a removable pole
are **known standard**.

**Why Track-V5 use does not upgrade the label.** Agent B
expands one atom; Agent I writes the same Taylor in a
derivative basis. Two code paths, one identity. Implementing
`.series` on `polygamma` is a textbook constructor.

**Why it is not potential novelty.** “Polygamma confluence”
is a correct *scientific reading* of some physics kernels
(human ladder L5). It is not a new mathematical object. This
track does not invent \(\Phi_\Gamma\) or L4–L7. Using those
names in a ZERO rule is leakage, not contribution.

**False-novelty sentences to delete.** “We introduce polygamma
Taylor series.” “We introduce polygamma confluence.” “Higher-
polygamma bases are a new representation invention.”

**Headline for authors.** Polygamma Taylor is standard special
functions, not novelty.

---

## 4. Coefficient extraction / residues / \([t^k]\) — known standard

**Why this label.** Residue theorem; Wilf’s \([z^n]\) operator;
Maple `coeff`, Mathematica `SeriesCoefficient`, FORM
`Coefficient`, SymPy `Poly.nth`. V4 already read poles and
\(t^0\) this way after `together`.

**Track-V5 delta.** Same operator, applied to a sparse sum
instead of a giant `Poly`. Not a new extractor.

**Forbidden upgrade.** Selling agreement of the first few
\([t^k]\) as hop `ZERO`. Frozen `CERTIFICATION_SCOPE.md`
already bans coefficient matching on expanded series as
Level-1 ZERO. Exact residual of \(a_0\) against the target,
after poles vanish, with remainder, is the LEVEL C bar.

---

## 5. Formal / truncated power series in CAS — known standard

**Why this label.** Gonnet–Gruntz ISSAC 1988; Gruntz 1996;
`sympy.series`; Maple `series`; truncated rings
\(R[[t]]/(t^n)\). Track V §1 and Track V3 §5 already classified
symbolic series/limits as known standard. Puiseux and Cadavid-
style multivariate rational limits are published CAS for a
**different object**.

**Why Track-V5 use does not upgrade the label.** Budgeted
per-atom `.series` is V4’s primitive. Refusing whole-kernel
series because it size-guards at 27327 ops is the engine
contract (timeout → `UNKNOWN`), not an algorithm.

**False-novelty sentences to delete.** “First symbolic series
of polygamma.” “We replace Gruntz.” “Maple cannot do this,
therefore we are novel.”

---

## 6. Removable singularities via vanishing principal part — known standard

**Why this label.** Riemann 1851; Ahlfors. If all \(a_k\) for
\(k<0\) vanish, the isolated singularity is removable and the
extension has value \(a_0\). If some \(a_k\) (\(k<0\)) is
nonzero, a finite holomorphic target is the wrong limit:
`NONZERO`. Hartogs is the wrong object for real Piecewise
polygamma (Track V3 §4).

**Why Track-V5 use does not upgrade the label.** `LEVEL_B` is
this test. `LEVEL_C` adds value-matching and remainder. The
schema sentence “\(t^0\) match with a surviving \(t^{-1}\) is
`NONZERO`” is the textbook converse.

**False-novelty sentences to delete.** “We introduce removable
singularities for polygamma kernels.” “Hartogs certifies
G0016→G0013.”

---

## 7. Linearity of coefficients / termwise accumulation — engineering adaptation
(mathematics: known standard)

**Why the mathematics is known standard.**
\([t^k]\sum T_i=\sum[t^k]T_i\) is the definition of series
addition.

**Why Track-V5 use is engineering adaptation, not novelty.**
Performing that add in a sparse map so that G0016→G0013 does
not `together` 27k ops, and refusing to treat the map as a
hop certificate until reconstruction of
\(K=\mathrm{pref}\cdot\sum T_i\) is itself `ZERO`. Strategy
choice: coefficient IR instead of expression IR. It does not
add an identity.

**Why it is not potential novelty.** Every CAS adds truncated
series by adding coefficients. V4 already expanded atoms
independently; it then reassembled an expression. Skipping
reassembly is systems work.

---

## 8. Per-atom series then `together` (V4) — engineering adaptation
(already shipped; not a V5 theorem)

**Why this label.** V4 CASE J-C: 12 polygamma atoms of 13–51
ops instead of one 327-op `sympy.series` certified
diagonal→triple hops. Generic 14-atom kernels still UNKNOWN
at together 27327. Track V4 literature already called this
an engineering adaptation of standard series.

**Why Track-V5 does not upgrade the label.** Replacing
`together` with sparse add is a continuation of the same
adaptation. Relabeling V4’s 20 diagonal ZEROs as the V5
primary hop is a protocol violation, not progress.

---

## 9. `LEVEL_A` / `LEVEL_B` / `LEVEL_C` hop certificates — engineering adaptation
(mathematics: known standard)

**Why known standard.** Riemann + Taylor-with-remainder;
LEDA-shaped “check a small witness”; assume-guarantee glue;
Track V reconstruction certificates. Three flags do not mint
a proof theory.

**Why Track-V5 use is engineering adaptation.** New IR names,
not new math:

- `LEVEL_A` — atoms expanded. **Not hop ZERO.**
- `LEVEL_B` — required negative coefficients vanish, or a
  negative coefficient is proven nonzero (`NONZERO`).
- `LEVEL_C` — poles gone, \(t^0\) equals the diagonal target,
  remainder sufficient. **Only LEVEL C may return ZERO.**
- Reconstruction failure, missing expansion, timeout,
  size-guard → `UNKNOWN`. Majority forbidden. Numeric
  agreement never ZERO.

That three-way is this repository’s language
(`research/coefficient_laurent/schema.py`). Shipping it is
systems work.

**Why it is not potential novelty as a method.** A paper that
claims “we introduce LEVEL A/B/C Laurent certification” will
be referred to Riemann and to V4’s already-shipped \(t^0\)
check. The remaining question is empirical: does sparse
routing turn G0016→G0013 `UNKNOWN` into honest `ZERO` /
`NONZERO` without false hop acceptance? That question is
unanswered. V4 is J-C.

---

## 10. Fail-closed cache keyed on full member text — engineering adaptation

**Why known standard.** Hash-bound identity of inputs is
ordinary integrity. Track V4’s false-ZERO hazard: a key of
`(None, None, var, point)` reused G0014→G0012 for
G0016→G0013 (`cache.py` docstring; V4 `VERDICT.md` §14).

**Why Track-V5 use is engineering adaptation.** Keys include
source/target full-text hashes, degeneration, target value,
assumptions hash, method version, atom-decomposition hash
(`PROTOCOL.md`). Missing `text_sha256` is computed from text.
Never reuse G0014→G0012 for G0016→G0013. That is a defect
fix, not a publication claim.

---

## \*. Packaged fail-closed coefficient-space routing — **GAP**
(not a method in §§1–10; not a claim)

**What it would be, if anything.** A measured *systems*
protocol, not a theorem:

> Frozen, already-proposed generic→diagonal Guo hops that
> timed out as whole-kernel / `together` series (primary:
> G0016→G0013, 573-op source, together 27327) are rescored by
> decomposing the kernel into local atoms, expanding each in
> the one-parameter degeneration, accumulating Laurent
> coefficients sparsely so intermediate ops stay comparable
> to V4’s 327-op successes, and composing fail-closed
> `LEVEL_A` / `LEVEL_B` / `LEVEL_C` with timeout/size-guard
> remaining `UNKNOWN`, numeric agreement never ZERO, majority
> forbidden, no Guo-specific identities, `LEVEL_A` never sold
> as hop ZERO, \(t^0\)+surviving pole sold as `NONZERO`, cache
> keys bound to full member text, false hop `ZERO` = 0,
> without mutating historical runs.

If that protocol ever worked, the only honest remainder would
be **verification-engineering**: coefficient-space routing at
scientific-expression scale under engine semantics. It would
still not be a mathematics contribution. Sparse Laurent series
and polygamma Taylor would remain standard.

**Why this cell is a GAP, not a “potential novel contribution.”**

- V4 closed CASE J-C (`248d247`): diagonal hops ZERO;
  generic→diagonal UNKNOWN; 7/7 families `FAMILY_UNKNOWN`.
- Track V5 freeze (`7102e8a`, `FROZEN_INPUTS_V5.json`,
  primary `guo-p2-s0-i3:G0016->G0013`) inherits that status.
  No V5 rescore exists.
- This literature pack runs no experiment.
- `PROTOCOL.md` has not produced hop `LEVEL_C` `ZERO` on
  G0016→G0013. Track D2 stays LOCKED. Publication status E.

The user-facing rule for this track: a system-level combination
may be named as a *candidate* **only if** later G0016→G0013 is
`LEVEL_C` `ZERO`. It is not. Therefore the label is **GAP**.
Do not quote this row as novelty, conditional novelty, or
“the contribution, if experiments support it” in a paper title
or abstract.

**What would still not upgrade the label even after a rescore.**

- `LEVEL_A` atoms-expanded sold as hop ZERO.
- \(t^0\) match with surviving \(t^{-1}\) sold as ZERO.
- Relabeling Track V4’s 20 diagonal ZEROs as G0016→G0013.
- Truncated `removeO()` without remainder verdict.
- Compiler gain on members already spelled as series.
- Guo-specific identity tables, gold names, numeric
  “certificates,” majority of atoms, timeout-as-zero.
- Cache hits that omit full member text.
- Claiming sparse Laurent, polygamma Taylor, Laurent series,
  or residues as the novelty (they are not).
- A single hop ZERO sold as `FAMILY_ZERO` or as unlocking D2.
  Path consistency is not auto-`CONSISTENT_ZERO`.

**Even if later G0016→G0013 is `LEVEL_C` `ZERO`, do not say:**

- first LLM+verifier (crowded; frozen `novelty_boundary.md`);
- formal proof / machine-checked theorem;
- we invented Laurent series / sparse polynomials / polygamma
  Taylor / residues / Gruntz;
- e-graph confluence of physics kernels;
- we discovered \(\Phi_\Gamma\) or L4–L7;
- Track V4 diagonal ZERO already was generic→diagonal
  certification;
- `LEVEL_A` is hop ZERO;
- Hartogs licensed skipping polar checks;
- coefficient matching on a truncated series is Level-1 ZERO.

---

## Upgrade experiments (what would change the GAP cell)

Literature does not generate these numbers. Owned by V5-A..L
+ eval, not by V5-M. Until they exist, **do not change the GAP
label**.

1. **Primary hop G0016→G0013, not V4 diagonals.** `LEVEL_C`
   `ZERO` (or honest `NONZERO`) on
   `guo-p2-s0-i3:G0016->G0013` in `FROZEN_INPUTS_V5.json`.
   Relabeling V4 diagonal ZERO is forbidden. `LEVEL_A` or
   `LEVEL_B` is not enough.
2. **False hop `ZERO` = 0.** Falsifiers (V5-L, V5-J): \(t^0\)
   match with surviving \(t^{-1}\); reconstruction failure
   sold as ZERO; timeout/size-guard sold as ZERO; numeric
   “certificate”; truncated series without remainder; leaked
   gold names; cache reuse of G0014 for G0016; majority of
   atoms. All must stay `NONZERO` or `UNKNOWN`.
3. **No 27k `together()`.** Intermediate ops comparable to
   V4’s certified 327-op class (`c0` ~47, together
   1592–3845), not `together_ops: 27327`.
4. **No Guo-specific identities.** Zero rules that name
   \(\Phi_\Gamma\), \(\mathfrak M_\Gamma\), \(\mathfrak T_\Gamma\),
   or the nine generators are leakage, not V_GAIN.
5. **Siblings are not a substitute.** G0016→G0014/G0015 and
   G0023→G0020/G0021/G0022 are the same *class*; they do not
   replace the primary hop, and they still do not unlock
   families.
6. **Symbolic baselines.** Same frozen hop, no new proposer:
   (i) V4 atom-series + `together`; (ii) whole-kernel
   `sympy.series` / Gruntz; (iii) textbook polygamma Taylor
   given the isolated atom; (iv) FORM/`coeff` on a human-
   assembled series. Method claim needs a gap after (i)–(iv)
   labelled hop V_GAIN, not C_GAIN.
7. **Second family.** At least one non-Guo scientific
   expression hop, or even a later G0016→G0013 ZERO stays n=1.
8. **Family still separate.** Hop ZERO is not `FAMILY_ZERO`.
   Do not open D2 on a single covering edge.

Until those exist, the honest status is: **methods classified;
sparse Laurent is not novelty; polygamma Taylor is not
novelty; `LEVEL_A` is not hop ZERO; no Track-V5 method result;
packaged contribution is a GAP because G0016→G0013 is not
`LEVEL_C` `ZERO`.**

---

## Claims a knowledgeable reviewer would reject immediately

| Claim | Why it dies | Who cites it |
|---|---|---|
| “We invented Laurent series” | Laurent 1843; Weierstrass; Ahlfors | any analyst |
| “We invented sparse Laurent series” | Geddes–Czapor–Labahn; FORM; every CAS poly | CAS users |
| “We invented polygamma Taylor / polygamma confluence” | DLMF 5.15; A&S; SymPy table; Track V4 one-pager | special-function users |
| “`LEVEL_A` (atoms expanded) is hop ZERO” | schema forbids it; series existence ≠ limit | ourselves |
| “\(t^0\) match with surviving \(t^{-1}\) is ZERO / almost ZERO” | it is a pole; schema returns `NONZERO` | any analyst |
| “Truncated `series`+`removeO` is a removable-singularity certificate” | remainder missing; Track V3 already forbade it | ourselves + V3-K |
| “First symbolic series / we replace Gruntz” | Gruntz 1996; `sympy.series`; Maple `series` | CAS users |
| “Sparse interpolation / Puiseux is our method” | Zippel; Ben-Or–Tiwari; Duval 1989 — wrong objects | CAS users |
| “Coefficient matching on expanded series is Level-1 ZERO” | `CERTIFICATION_SCOPE.md` forbids it | ourselves |
| “We invented proof certificates / residues” | LEDA; WZ; Cauchy | PL / combinatorics / analysis |
| “Hartogs certifies G0016→G0013” | SCV holomorphic \(\neq\) real Piecewise polygamma | several-complex-variables readers |
| “E-graphs already do this” | rewriting \(\neq\) Laurent coefficients | PL *and* analysis reviewers |
| “Formal certification” | SymPy residual + probes; UNKNOWN fail-closed | Lean/e-graph reviewer |
| “Timeout converted to ZERO is conservative” | it is a false hop ZERO | this engine’s own contract |
| “V4 diagonal ZERO is V5 G0016→G0013” | different texts; cache hazard already recorded | ourselves |
| “Hop ZERO is FAMILY_ZERO / unlocks D2” | `PROTOCOL.md`: V_GAIN only; no auto consistency | ourselves |
| “V5-M literature is a method result / a contribution” | no rescore; V4 is J-C; GAP cell | ourselves |

---

## Positioning sentence (not a title)

> Laurent series, sparse polynomial coefficient arithmetic,
> polygamma Taylor expansions, residues, and removable
> singularities are standard tools. Track V5 asks whether
> those tools, routed fail-closed as sparse per-atom Laurent
> coefficients over already-frozen generic→diagonal scientific
> hops, can replace a 27k-op `together()` without false hop
> `ZERO`. Sparse Laurent series is not the contribution.
> Polygamma Taylor is not the contribution. `LEVEL_A` is not
> hop `ZERO`. A systems contribution — coefficient-space
> routing at scientific-expression scale — does not exist
> until G0016→G0013 returns `LEVEL_C` `ZERO` with false hop
> `ZERO` = 0. That experiment has not run. The cell is a GAP.
