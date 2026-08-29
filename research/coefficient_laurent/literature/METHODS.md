# Track V5 methods — coefficient-space Laurent certification

Audit date: 2026-08-28.
Object: **certification of a frozen generic→diagonal hop by sparse
Laurent coefficients of local atoms**, without a 27k-op
`together()` and without Guo identities
(`research/coefficient_laurent/PROTOCOL.md`). This pack is
literature for Track **V5**, not discovery (layer D / D2), not a
rewrite of Tracks V–V4, and not a method result.

No LLM calls. Frozen generic→diagonal hops from Track V4
(`248d247`; `FROZEN_INPUTS_V5.json`, primary
`guo-p2-s0-i3:G0016->G0013`) only. Retrieval: classic complex
analysis / NA / CAS / special-function sources already used in
frozen compactification, Track V, Track V3, and Track V4 audits,
plus the sparse-polynomial / formal-power-series textbook line.
Unconfirmable titles are omitted.

**Question.** Can G0016 → G0013 be certified by sparse Laurent
coefficients of local atoms, without a 27k-op `together()` and
without Guo identities?

**Not the question.** Inventing Laurent series, inventing sparse
polynomials, inventing polygamma Taylor expansions, inventing
coefficient extraction, inventing residues, or claiming a
Lean/e-graph kernel. Sparse Laurent series is **known standard**.
Polygamma Taylor is **known standard**. `LEVEL_A` is not hop
`ZERO`. See `CLASSIFICATION.md`.

Frozen literature this pack does not rewrite:

- Compactification proposer–verifier survey:
  `research/literature/{corpus,novelty_boundary}.md`.
- Representation-invention novelty:
  `research/representation_invention/literature/NOVELTY.md`.
- Track V verification methods:
  `research/scalable_verification/literature/{METHODS,CLASSIFICATION}.md`.
- Track V2 family-certificate methods:
  `research/multibranch_verification/literature/{METHODS,CLASSIFICATION}.md`.
- Track V3 iterated-confluence methods:
  `research/iterated_confluence/literature/{METHODS,CLASSIFICATION}.md`.
- Track V4 one-pager:
  `research/polygamma_confluence/literature/CLASSIFICATION.md`
  (polygamma derivative, Taylor, Laurent \(t^0\) already labelled
  **known standard**).
- Certification language:
  `research/verification/CERTIFICATION_SCOPE.md`
  (engine semantics, not formal proof).

Intended reader: Track V5 implementers (V5-A..L) and authors,
before any paper sentence about “sparse Laurent certificates,”
“polygamma series,” or “coefficient-space routing.”

---

## 0. Words and scales that must not be mixed

| Sense | Field | Object | Closest systems |
|---|---|---|---|
| Laurent series | complex analysis | \(\sum_{k\ge k_{\min}} a_k t^k\) in an annulus, \(k_{\min}\) maybe \(<0\) | Laurent 1843; Weierstrass 1841/1894; Ahlfors; Conway |
| Sparse Laurent / sparse polynomial | CAS data structures | store only nonzero \((k,a_k)\); add by merging maps | Geddes–Czapor–Labahn 1992; Maple/FORM distributed polys |
| Sparse interpolation | computer algebra | recover a sparse polynomial from evaluations | Zippel 1979; Ben-Or–Tiwari 1988 |
| Puiseux series | algebraic curves / CAS | fractional exponents \(t^{p/q}\) | Newton–Puiseux; Duval 1989 |
| Hierarchical / MRV series | symbolic limits | most-rapidly-varying scale, then Taylor in \(\omega\to 0^+\) | Gonnet–Gruntz ISSAC 1988; Gruntz 1996 |
| Transseries | asymptotic analysis | well-ordered transfinite exp-log series | van der Hoeven; Écalle |
| PIT / numeric coeff probes | identity testing | Schwartz–Zippel; \(N[\cdot,30]\) | **never a ZERO path** |
| Interpolation confluence | NA | nodes coalesce; DD → derivatives | Newton, Hermite, de Boor 2005 |
| Rewriting confluence | term rewriting / EqSat | joinability of rewrite paths | Knuth–Bendix, egg |

Track V5 uses Laurent series *and* sparse coefficient maps of
one-parameter germs. Mixing either with sparse *interpolation*,
Puiseux, Gruntz completeness, or Knuth–Bendix confluence is a
reviewer-kill. Mixing a truncated coefficient table with a
limit certificate is the Track V5-specific reviewer-kill.

| Scale | Track | Object | Closed evidence |
|---|---|---|---|
| Pair | V | two-member local confluence | 3 frozen Guo pairs ZERO (`38d6d4a`) |
| Family | V2 | 4–5 member graphs + recurrence | **not closed**; H-C (`fe53ebc`) |
| Iterated path | V3 | ordered one-parameter steps | **not closed**; I-D (`d2752f9`) |
| Atom series | V4 | per-atom `series` then `together` + Laurent \(t^0\) | **J-C** (`248d247`): diagonal→triple ZERO; generic→diagonal UNKNOWN (together 27327) |
| Coefficient space | V5 | sparse \([t^k]\) of atoms; LEVEL A/B/C | **L-D** after remainder fail-close: G0016→G0013 LEVEL_B UNKNOWN (C0 matches; rem UNKNOWN) |

A hop is not certified because atoms have series (that is
`LEVEL_A`). Negative coefficients vanishing is not hop `ZERO`
(that is `LEVEL_B`). Only `LEVEL_C` — poles gone, \(t^0\) equals
the diagonal target, remainder sufficient — may return `ZERO`
(`schema.compose_hop_verdict`). A \(t^0\) match with a surviving
\(t^{-1}\) is `NONZERO`. Timeout / size-guard is `UNKNOWN`, never
`ZERO`. Numeric agreement is never `ZERO`. Majority of atoms or
of coefficients is forbidden. Cache keys include source/target
**full text** hashes: never reuse G0014→G0012 for G0016→G0013.

Track D2 stays locked. New edge verdicts, if any later appear,
are `V_GAIN` only. Path consistency is not auto-`CONSISTENT_ZERO`.
Composition reuses frozen V3/V4 graphs; topology does not change
(`PROTOCOL.md`).

---

## 1. Laurent series

**What.** If \(f\) is holomorphic in an annulus
\(r < |t| < R\), then

\[
f(t)=\sum_{k=-\infty}^{\infty} a_k t^k,\qquad
a_k=\frac{1}{2\pi i}\oint \frac{f(\zeta)}{\zeta^{k+1}}\,d\zeta.
\]

The sum over \(k<0\) is the *principal part*. If the principal
part is finite, the isolated singularity at \(0\) is a pole; if
it vanishes, the singularity is removable and the holomorphic
extension has value \(a_0\).

**Canonical sources.**

- P. A. Laurent, *Extension du théorème de M. Cauchy relatif à
  la convergence du développement d'une fonction suivant les
  puissances ascendantes de la variable*, presented 1843
  (Cauchy’s report: *Comptes rendus* 17 (1843) 938–940; full
  memoir unpublished in Laurent’s lifetime).
- Weierstrass, independent proof 1841, published in the
  collected works 1894.
- Ahlfors, *Complex Analysis*, 3rd ed. (1979); Conway,
  *Functions of One Complex Variable* (1978); Rudin, *Real and
  Complex Analysis*. Undergraduate residue calculus.

**What CAS already does.** `sympy.series(f, t, 0, n)`, Maple
`series`, Mathematica `Series` emit a truncated Laurent (or
Taylor) polynomial plus \(O(t^n)\). `SeriesCoefficient` /
`coeff` / FORM `Coefficient` read one \(a_k\). None of this is
a new expansion theorem.

**Track-V5 use.** Degeneration coordinate \(t=\)
`var - point` (e.g. \(\varepsilon(m)-\varepsilon(n)\)). Each
local atom is expanded in \(t\). The hop claim
\(\lim_{t\to 0} K_{\mathrm{G0016}}=K_{\mathrm{G0013}}\) is the
statement that the principal part of \(K_{\mathrm{G0016}}\)
vanishes and \(a_0=K_{\mathrm{G0013}}\) with a vanishing
remainder. That is the definition of a removable singularity
plus value matching, not a research contribution.

**What must not be claimed.** “We introduce Laurent series.”
“Sparse Laurent certificates are a new special-function
identity.” Any analyst will desk-reject those sentences.

**Classification.** Known standard. See `CLASSIFICATION.md` §1.

---

## 2. Sparse Laurent / sparse polynomial coefficient arithmetic

**What.** A univariate (Laurent) polynomial is *sparse* when
it is stored as a list or map of nonzero pairs \((k,a_k)\)
rather than a dense coefficient vector. Addition is a merge of
those maps; multiplication is a convolution over the support.
Every production CAS already does this for multivariate
polynomials (distributed representation) and for truncated
series (store the terms it computed).

**Canonical sources.**

- Geddes, Czapor, Labahn, *Algorithms for Computer Algebra*
  (Kluwer, 1992), Ch. 2–4: algebra, normal forms, and arithmetic
  of polynomials, rational functions, and power series, including
  sparse / distributed data structures and Newton iteration for
  series division.
- Knuth, *The Art of Computer Programming*, vol. 2: power-series
  manipulation as a standard seminumerical algorithm.
- Maple, FORM, Singular, and SymPy `Poly` / `Add` of `Pow`
  terms: sparse by default for multivariate input.

**Wrong objects that must not be cited as “our sparse Laurent.”**

- *Sparse interpolation* (Zippel, EUROSAM 1979; Ben-Or and
  Tiwari, STOC 1988): recover a polynomial from evaluations
  given a bound on the number of terms. Track V5 does not
  interpolate unknown atoms from probes.
- Compressed sensing / \(\ell_0\) recovery: wrong field.
- Puiseux (Duval, *Compositio Math.* 70 (1989) 119–154):
  fractional exponents for algebraic branches. Guo one-parameter
  degenerations in this freeze are integer-power Laurent of
  polygamma-rational germs, not curve uniformization.

**Track-V5 use.** Agent D (`sparse/`): accumulate
\([t^k]\) of atoms into a map, instead of
`together(pref * sum(cores))` on a 27k-op combined expression.
That is the textbook sparse-add of series, applied to V4’s
already-split atoms. It does not add an identity.

**What must not be claimed.** “We introduce sparse Laurent
series.” “Coefficient maps are a new certificate calculus.”
A CAS reviewer who has implemented `coeff` will desk-reject
those sentences. **Headline for authors: sparse Laurent is
standard math / standard CAS, not novelty.**

**Classification.** Known standard. See `CLASSIFICATION.md` §2.

---

## 3. Polygamma Taylor, derivative identity, recurrence, polar Laurent

**What.** Write \(\psi^{(n)}=\mathrm{polygamma}(n,\cdot)\).
Then, wherever the functions are holomorphic,

\[
\frac{d}{dz}\psi^{(n)}(z)=\psi^{(n+1)}(z),
\]

and Taylor’s theorem in the remaining holomorphic variable is

\[
\psi^{(n)}(z+t)=\sum_{k=0}^{\infty}\psi^{(n+k)}(z)\,\frac{t^k}{k!}.
\]

The recurrence \(\psi^{(n)}(z+1)=\psi^{(n)}(z)+(-1)^n n!\,z^{-n-1}\)
and the reflection formulae are the same table. Near a
non-positive integer the germ is Laurent, not Taylor: as
\(t\to 0\),

\[
\psi^{(n)}(t)\sim (-1)^{n+1}\,n!\,t^{-n-1}
\]

plus a holomorphic regular part (DLMF 5.15; the leading polar
term is the \(n\)-th derivative of \(1/t\)).

**Canonical sources.**

- NIST DLMF Chapter 5 (Askey–Roy), §5.15 polygamma; §5.2–5.5
  psi, recurrence, reflection. “Most properties follow
  straightforwardly by differentiation of properties of the
  psi function.”
- Abramowitz and Stegun (1964), Ch. 6.
- Nielsen, *Handbuch der Theorie der Gammafunktion* (1906);
  Whittaker and Watson, *A Course of Modern Analysis*.
- SymPy `polygamma` docstring / `series` method: table lookup
  plus Taylor/Laurent of the argument. Track V already recorded
  this as `SPECIAL_FUNCTION_LOCAL` / not master invention
  (`research/scalable_verification/literature/METHODS.md` §8).
- Track V4 one-pager: “Polygamma derivative
  `d/dz polygamma(n,z) = polygamma(n+1,z)`, Taylor expansion,
  and Laurent coefficients of a removable pole are **known
  standard**.” Track V5 does not lift that ban.

**Track-V5 use.** Agent B (`pg_series/`): expand one polygamma
atom in \(t\). Agent I (`basis/`): the same Taylor, written in
the derivative / higher-polygamma basis. Neither is a new
addition formula. Agent C (`rational/`) expands rational
prefactors by the ordinary geometric / partial-fraction series,
also undergraduate.

**Forbidden.** Hardcoded Guo gold identities
(\(\Phi_\Gamma\), \(\mathfrak M_\Gamma\), \(\mathfrak T_\Gamma\),
nine generators, L4–L7) as ZERO rules. Treating
`polygamma(1,z)=d/dz polygamma(0,z)` as representation
invention (F4 in the beyond-LGG taxonomy). Inventing a
meromorphic master \(F\) on this track (Track D, locked).

**What must not be claimed.** “We introduce polygamma Taylor
series.” “Polygamma confluence is a new identity.”
**Headline for authors: polygamma Taylor is standard special
functions, not novelty.**

**Classification.** Known standard. See `CLASSIFICATION.md` §3.

---

## 4. Coefficient extraction, residues, and the \([t^k]\) operator

**What.** The operator \([t^k]f\) reads the coefficient of
\(t^k\) in a Laurent / power series. Equivalently, for a pole,
\(a_{-1}\) is the residue. Linearity
\([t^k](f+g)=[t^k]f+[t^k]g\) is the definition of the sum of
series.

**Canonical sources.**

- Residue theorem: Cauchy; every complex-analysis textbook.
- Generatingfunctionology (Wilf); Flajolet–Sedgewick, *Analytic
  Combinatorics* — the \([z^n]\) operator as combinatorics
  (asymptotics of coefficients is a **different object**; do
  not cite singularity analysis as a hop certificate).
- CAS primitives: Maple `coeff` / `coeftayl`, Mathematica
  `SeriesCoefficient` / `Residue`, FORM `Coefficient`,
  SymPy `Poly.nth` / `series` then `coeff`. V4 already used
  `Poly(together(expanded * t**shift), t).nth` to read poles
  and \(t^0\) (`polygamma_confluence/engine.py`).

**Track-V5 use.** Agents E/F read \(k<0\) and \(k=0\) from a
sparse map instead of from a 27k-op combined `Poly`. Same
operator, different intermediate size.

**CERTIFICATION_SCOPE trap.** Frozen
`research/verification/CERTIFICATION_SCOPE.md` states that
“coefficient matching on expanded series” is **not** Level-1
ZERO. That sentence bans *heuristic* identity tests (agree on
the first few \([t^k]\), or agree numerically, and call the
two expressions equal). It does **not** license, and Track V5
must not perform, a truncated-table ZERO. LEVEL C still
requires exact vanishing of the principal part, exact residual
of \(a_0\) against the target (`expand==0` or `cancel==0`),
and a remainder sufficient for \(t\to 0\). Partial coefficient
agreement is `UNKNOWN` or, if a proven nonzero coeff
disagrees, `NONZERO`.

**Classification.** Known standard. See `CLASSIFICATION.md` §4.

---

## 5. Formal and truncated power series in CAS

**What.** Computer algebra already manipulates truncated power
series rings \(R[[t]]/(t^n)\) and, for poles, truncated Laurent
series \(R[t,t^{-1}]\) up to a finite principal part plus
\(O(t^n)\). Limits of exp-log expressions are computed by
hierarchical series (Gruntz), not by a new Laurent calculus.

**Canonical sources.**

- Gonnet and Gruntz, ISSAC 1988 (LNCS 358); Gruntz, ETH Diss.
  11432, 1996. Maple; SymPy `sympy.series.gruntz`. Already
  classified in Track V §1 and Track V3 §5: **known standard**,
  complete for a stated exp-log class, not for arbitrary
  `Sum`/`Piecewise`/polygamma kernels.
- Shackell, *J. Symbolic Comput.* 1990; van der Hoeven
  transseries / truncated-series arithmetic.
- Salvy and Zimmermann, GFUN (*ACM Trans. Math. Softw.* 1994):
  generating-function series, not Guo kernels.
- Maple `series`, Mathematica `Series`, SymPy `.series`.
- Puiseux / Cadavid-style multivariate limits: published CAS
  for *algebraic* or *rational* germs (Track V3 §5). Wrong
  object for 573-op Piecewise polygamma.

**Track-V5 use.** Budgeted per-atom `.series(t, 0, n)` is the
same primitive V4 used. The engineering bet is to **not** call
`.series` or `together` on the summed 14-atom generic kernel
(ops 27327, size-guard). Timeout / ops-cap → `UNKNOWN`. This
is a wrapper around existing series, not a replacement for
Gruntz.

**What must not be claimed.** “First symbolic series of
polygamma.” “We replace Gruntz.” “Maple cannot do this,
therefore we are novel.” Lack of a runtime is not novelty
(already recorded in Track V literature for egg/Lean/Wolfram).

**Classification.** Known standard as algorithms. Timeout →
UNKNOWN is this engine’s contract. Not a novel series algorithm.

---

## 6. Removable singularities via vanishing principal part

**What.** Riemann’s removable singularity theorem (one complex
variable, 1851): a holomorphic function bounded on a punctured
disk extends holomorphically. Equivalent computational tests
for a meromorphic germ: the principal part vanishes, or
\(t^N f(t)\) is holomorphic and vanishes at \(0\) to order
\(\ge N\). Then \(\lim_{t\to 0} f(t)=a_0\).

If some \(a_k\) for \(k<0\) is nonzero, \(f\) has a pole (or
worse) and **cannot** equal a finite holomorphic target. In
particular a matching \(a_0\) with a surviving \(a_{-1}\) is a
simple pole, not a limit: \(\lim_{t\to 0} t\,f(t)=a_{-1}\neq 0\).
That is `NONZERO`, not “almost ZERO.”

**Canonical sources.** Riemann 1851; Ahlfors; Track V3
`METHODS.md` §4 (already classified **known standard**; Hartogs
is the **wrong object** for real Piecewise polygamma).

**Track-V5 use.** `LEVEL_B` = all required negative coefficients
vanish (`negative_coefficients_verdict`). `LEVEL_C` additionally
matches \(t^0\) and the remainder. Schema sentence: “\(t^0\)
match with a surviving \(t^{-1}\) is `NONZERO`.” That is the
textbook converse, encoded as `compose_hop_verdict`.

**Type errors to refuse.**

- Citing Hartogs (\(\mathbb C^n\), \(n\ge 2\)) to skip a
  one-parameter polar check.
- Citing Riemann to skip a two-sided *real* limit that may
  disagree left/right (`AGENTS.md` rule 14 still applies to
  covering paths; V5 certifies one declared one-parameter hop).
- Calling a truncated `series` with `removeO()` a removable-
  singularity certificate without a remainder verdict (Track V3
  already forbade this). That is at most `LEVEL_A`/`LEVEL_B`.

**Classification.** Known standard. Wiring the test as
LEVEL B/C is bookkeeping.

---

## 7. Linearity of coefficients / termwise accumulation

**What.**

\[
\bigl[t^k\bigr]\sum_i T_i(t)=\sum_i\bigl[t^k\bigr]T_i(t).
\]

If each \(T_i\) is expanded independently, the coefficient of
the sum is the sum of the coefficients. Cancellation of poles
is then an identity among those finite sums, not a property
that appears only after `together` of a giant expression.

**This is the definition of addition in the ring of (formal)
Laurent series.** It is not an algorithm.

**Track-V5 use.** The whole point of sparse accumulation
(Agent D) versus V4’s `together(pref * sum(cores))`: perform
the linear combination in coefficient space, where support is
small (a handful of negative powers plus \(t^0\)), instead of
in expression space, where `together` on the generic kernel
was 27327 ops.

**Why this is not novelty.** Every CAS adds series this way
when the inputs are already series. V4 *had* per-atom series
and then re-assembled an expression before reading coeffs.
Avoiding that reassembly is an engineering choice about
intermediate representation, not a theorem.

**Reconstruction obligation.** Linearity applies to the atoms
one actually expanded. If \(K=\mathrm{pref}\cdot\sum T_i\) is
not reconstructed (\(K-\mathrm{pref}\sum T_i\neq 0\)), the
sparse sum is a different object and the hop stays `UNKNOWN`
(`reconstruction_ok=False` ⇒ `LEVEL_A` `UNKNOWN`, even if
coeffs look pretty). V4 already required reconstruction of
`pref * Add`.

**Classification.** Known standard as mathematics.
Engineering adaptation as the IR that *refuses* to
`together` the 27k-op sum.

---

## 8. Per-atom series then together (Track V4, inherited)

**What V4 already did.** Spectator peel → reconstruct
\(K=\mathrm{pref}\cdot\sum T_i\) (each \(T_i\) one polygamma)
→ \(T_i.\mathrm{series}(t,0,n)\) independently →
`together(pref(t)*sum cores)` → Laurent coeffs of \(t^{<0}\)
must vanish → \(t^0\) vs target. Closed CASE **J-C**
(`248d247`; `TRACK_V4_CLOSED.md`):

- diagonal→triple hops (327-op class) ZERO, 12 atoms, `c0`
  ops 47, together 1592–3845;
- generic→diagonal (G0016/G0023, freeze ops 573) UNKNOWN,
  together 27327 or 30 s timeout;
- families 7/7 `FAMILY_UNKNOWN`; Track D2 locked.

**Track-V5 delta is not a new identity.** It is the same
per-atom expansion with the `together` of cores replaced by
sparse coefficient addition, plus an explicit remainder
verdict, plus LEVEL A/B/C so that “atoms expanded” cannot be
sold as hop ZERO.

**Classification.** V4 method: engineering adaptation of
standard series (already labelled). Repeating it without
`together` does not mint a theorem.

---

## 9. LEVEL A / B / C hop certificates

**What.** `schema.compose_hop_verdict`:

| Level | Meaning | Hop verdict |
|---|---|---|
| `LEVEL_A` | reconstruction and/or atom series only | never `ZERO` |
| `LEVEL_B` | all required negative coeffs vanish (or a negative coeff is proven nonzero) | `NONZERO` if a pole survives; else not yet `ZERO` |
| `LEVEL_C` | poles gone, \(t^0\) equals target, remainder sufficient | only this level may be `ZERO` |

Reconstruction failure → `UNKNOWN`, `LEVEL_A`. Atoms not
expanded → `UNKNOWN`, `LEVEL_A`. Negative `NONZERO` with
matching \(t^0\) → `NONZERO` (surviving pole). Constant or
remainder not `ZERO` after poles vanish → `UNKNOWN`, `LEVEL_B`.

**Why the mathematics is known standard.** This is Riemann +
Taylor-with-remainder, discretized as three fail-closed flags.
It is not a new proof calculus.

**Why Track-V5 use is engineering adaptation.** The IR names,
the ban on majority, the ban on timeout-as-zero, the cache
key (source/target **full text**, degeneration, target value,
assumptions hash, method version `v5-coeff-laurent-1`, atom-
decomposition hash), and the explicit “LEVEL A is not hop
ZERO” test (`tests/test_cl_schema.py`). Shipping that is
systems work. The V4 cache bug (missing `text_sha256` reused
G0014→G0012 for G0016→G0013) is why text hashes are
mandatory; that is a defect class, not a contribution.

**Certificates.** LEDA / WZ / Track V reconstruction
witnesses: check a small object instead of Gruntz on the
573-op kernel. A `LaurentCertificate` is that witness under
**engine semantics** (`CERTIFICATION_SCOPE.md`), not a Lean
proof. Randomized PIT, `PossibleZeroQ`, and 30-digit
agreement remain forbidden ZERO paths.

**Classification.** Engineering adaptation of standard
analysis. Not a new certificate theory.

---

## 10. How Track V5 should compose these methods

| piece | owner | decides hop `ZERO`? | method (§) |
|---|---|---|---|
| atom decomposer | V5-A `atoms/` | no (`LEVEL_A` at most) | reconstruction; §7–8 |
| polygamma series | V5-B `pg_series/` | no | §3, §5 |
| rational series | V5-C `rational/` | no | §5 |
| sparse accumulator | V5-D `sparse/` | no (summed coeffs only) | §§2, 7 |
| pole certifier | V5-E `poles/` | `negative_verdict` only | §6, LEVEL B |
| c0 matcher | V5-F `c0/` | `constant_verdict` only | §§4, 6 |
| remainder | V5-G `remainder/` | `remainder_verdict` only | §6, LEVEL C |
| grouping | V5-H `grouping/` | no | like-term collect; CAS standard |
| derivative basis | V5-I `basis/` | no | §3 Taylor basis |
| numeric falsifier | V5-J `numeric/` | `NONZERO` only, never `ZERO` | probes |
| cache auditor | V5-K tests vs `cache.py` | no | text-hash keys |
| Laurent falsifier | V5-L `falsifier/` | no | adversarial |
| literature | V5-M (this pack) | no | classification |

No new LLM calls. Frozen inputs:
`research/coefficient_laurent/FROZEN_INPUTS_V5.json`
(primary hop G0016→G0013; siblings G0016→G0014/G0015 and
G0023→G0020/G0021/G0022). Historical run JSON is read-only.
Shared freeze/schema/cache/STATUS files are not owned here.

Only `compose_hop_verdict` with reconstruction OK, atoms
expanded, and negative/constant/remainder all `ZERO` may
return hop `ZERO` at `LEVEL_C`. No agent in the table
unilaterally decides that.

Gain labels stay those of Track V, at hop grain:

- **hop V_GAIN**: a frozen generic→diagonal hop previously
  `UNKNOWN`, now `ZERO`/`NONZERO` because the coefficient-space
  verifier improved, without 27k `together`;
- **C_GAIN**: previously uncompiled hop, now compiles then
  verifies;
- **NO_GAIN**: still hop `UNKNOWN`, including G0016→G0013 after remainder fail-close (C0 lemma is not hop ZERO).

False hop `ZERO` = 0 is a merge gate. This pack does not
produce that number. Relabeling V4’s 20 diagonal ZEROs as
G0016→G0013 is forbidden.

Track D2 stays locked until a frozen *family* is `FAMILY_ZERO`
or `FAMILY_NONZERO`. A single hop `LEVEL_C` `ZERO` is hop
V_GAIN, not a family certificate, and does not auto-promote
path consistency (`PROTOCOL.md`). This literature pack does
not open Track D.

Allowed local methods: exact substitution, spectator split
with reconstruction, per-atom series around *one* degeneration
parameter, sparse coefficient add, exact `expand`/`cancel` of
coeffs, local special-function identities already in SymPy,
typed DD already frozen in Track V/V2. Fallback UNKNOWN.

Forbidden: Guo-specific identity table, gold leakage, converting
timeout/size-guard to ZERO, numeric agreement as exact, majority
of atoms/coefficients, truncated series without remainder as
LEVEL C, cache keys that omit full member text, reusing
G0014 certificates for G0016.

---

## 11. Closest verification systems (not to copy slogans from)

Reuse frozen `research/literature/corpus.md` for proposer–
verifier crowding, Track V `METHODS.md` §10 for pair-scale
neighbors, Track V3 `METHODS.md` §10 for iterated-limit
neighbors, and Track V4’s one-pager for polygamma-local
series. Distance *as coefficient-space hop verifiers*:

| System | What it checks | vs Track V5 |
|---|---|---|
| Laurent / Riemann / Ahlfors | principal part, removable poles, \(a_0\) | the **math**; not a 573-op CAS hop certificate |
| DLMF / A&S / SymPy `polygamma` | Taylor, recurrence, polar leading term | the **math** of atoms; table lookup, not masters |
| Geddes–Czapor–Labahn / FORM `Coefficient` | sparse poly/series arithmetic | the **data structure**; not fail-closed hop levels |
| Zippel / Ben-Or–Tiwari | sparse interpolation from probes | **wrong object** |
| Gruntz / `sympy.limit` / `.series` | univariate exp-log / truncated series | inner primitive of an atom; whole-kernel series is the V4 bottleneck |
| Puiseux / Duval / Cadavid | algebraic / rational germs | wrong object for Piecewise polygamma |
| Track V4 atom-series | per-atom series then `together` + \(t^0\) | closed J-C on 327-op hops; **is** the 27k generic bottleneck V5 tries to avoid |
| Track V `SERIES_LOCAL` | budgeted local series of a small factor | ancestor slogan; never global series of Guo |
| PIT / Schwartz–Zippel / `N[...,30]` | probabilistic / numeric identity | **forbidden** ZERO path |
| WZ / *A=B* | hypergeometric sum certificates | wrong object |
| Lean/Isabelle kernels | formal proofs | stronger; unavailable; must not claim |
| egg / LGuess | rewrite chains on polynomials | wrong confluence sense |
| Engine `verifier.py` | structural residual + rational probes | global; does not scale to G0016→G0013 |

No retrieved system jointly (i) takes frozen, already-proposed
**generic→diagonal** scientific hops that timed out as
whole-kernel / together-series, (ii) routes them through
per-atom Laurent coefficients accumulated sparsely so that
intermediate ops stay comparable to V4’s 327-op successes,
(iii) refuses to treat `LEVEL_A` or a \(t^0\) match with a
surviving pole as hop `ZERO`, (iv) forbids numeric ZERO and
majority, (v) keys caches on full member text so G0014 cannot
stand in for G0016, and (vi) accounts hop V_GAIN without
mutating historical runs.

That joint *packaging* is a **GAP**, not a proof of novelty.
The methods in §§1–9 are not new. G0016→G0013 is not
`LEVEL_C` `ZERO`, so the package is not a candidate
contribution either. If that hop later is `LEVEL_C` `ZERO`,
the only honest remainder would be **verification-engineering**:
coefficient-space routing at scientific-expression scale under
engine semantics. It would still not be a mathematics
contribution. Sparse Laurent and polygamma Taylor would remain
standard.

---

## 12. Self-adversarial notes

1. Sparse addition of already-computed atom series is what
   V4 would have done if it had not called `together` on the
   cores. Success, if it happens, is an intermediate-
   representation win, not a new expansion theorem.
2. Relabeling V4’s 20 diagonal→triple ZEROs as G0016→G0013
   is a false hop ZERO. Those hops are a different
   `(source_text, target_text)` pair. The cache auditor exists
   because V4 already almost made this mistake.
3. `LEVEL_A` “we expanded every polygamma” is not a limit.
   Drafts that lead with atom counts as the result are
   marketing.
4. A matching \(t^0\) with a surviving \(t^{-1}\) is a pole.
   Reporting it as “the constant term is correct” is a false
   ZERO. The schema already returns `NONZERO`.
5. `removeO()` on a truncated series without a remainder
   verdict is not `LEVEL_C`. Track V3 forbade calling a
   truncation a removable-singularity certificate; Track V5
   repeats the ban.
6. Numeric probes of coefficients may refute (`NONZERO`).
   They may not certify. PIT is not a ZERO path
   (`CERTIFICATION_SCOPE.md`).
7. Polygamma Taylor in a derivative basis (Agent I) is the
   same identity as Agent B. Two implementations do not
   double the mathematics.
8. Even a later G0016→G0013 `LEVEL_C` `ZERO` is hop V_GAIN.
   It does not make covering paths `PATH_ZERO`, does not
   auto-`CONSISTENT_ZERO`, does not yield `FAMILY_ZERO`, and
   does not unlock Track D2.
9. Guo n=1 cannot carry a generalization claim even if hop
   V_GAIN appears.
10. This literature pack runs no rescore. Status remains
    literature-only until V5-A..L fire with false hop ZERO = 0.

## Unconfirmed / not used

- Papers whose titles were recalled but not retrieved with
  matching authors/year/venue.
- Numeric Gruntz / series solve-rate tables from search
  snippets.
- Any claim that V5-A..L already produced LEVEL C ZERO
  (those directories are owned elsewhere; this pack is
  documentation).
- 2026 arXiv historical essays on Laurent as a source of
  *mathematics* (the 1843 theorem is prior work; the essays
  are not).
