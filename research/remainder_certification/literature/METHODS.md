# Remainder-certification methods — literature audit

Audit date: 2026-08-29.
Object: **machine-checkable remainder certificates** for local
Taylor/Laurent expansions of special functions with symbolic
affine arguments, under **declared** analytic-domain hypotheses
(`research/remainder_certification/PROBLEM_STATEMENT.md`).
This pack is literature for the remainder-certification line,
not Track V6, not discovery (layer D / D2), and not a method
result.

No LLM. Parent `adbfd9f` (RemainderCertificate IR freeze).
Track D2 LOCKED. Retracted V5 LEVEL_C ZERO (`fb3b929`) is not
to be restored. Retrieval: classic complex analysis, special
functions (DLMF 5.15), CAS series/limits, validated numerics,
and holonomic tail bounds. Unconfirmable titles are omitted.

**Question.** Can finite local Taylor/Laurent expansions of
special functions with symbolic affine arguments be equipped
with machine-checkable remainder certificates strong enough
to justify exact limit claims?

**Not the question.** Inventing Taylor’s theorem, inventing
Cauchy estimates, inventing polygamma poles, inventing Gruntz,
inventing ball arithmetic, or claiming a Lean kernel. Taylor
remainder is **standard mathematics**. A Track V5 C0 match is
**not** a remainder certificate
(`research/coefficient_laurent/literature/`).

Frozen literature this pack does not rewrite:

- Compactification survey: `research/literature/`.
- Certification language: `research/verification/CERTIFICATION_SCOPE.md`.
- Track V / V3 / V4 / V5 method packs (paths in `README.md`).
- Track V5 remainder sufficiency:
  `research/coefficient_laurent/remainder/` (numeric-α holomorphic
  test; symbolic α → UNKNOWN).

Intended reader: remainder-certification implementers (R1–R13)
and authors, before any paper sentence about “certified Taylor
remainders,” “Cauchy remainder certificates,” or “polygamma
analytic remainder.”

---

## 0. Words and scales that must not be mixed

| Sense | Field | Object | Closest systems |
|---|---|---|---|
| Taylor remainder (holomorphic) | complex analysis | \(R_{N+1}(z)=f(z)-T_N(z)\) on a disk of holomorphy | Cauchy integral remainder; Ahlfors; Conway |
| Cauchy estimates | complex analysis | \(\lvert f^{(n)}(a)\rvert\le n!\,M/r^n\) | Cauchy; every textbook after Ahlfors |
| Lagrange / integral remainder | real calculus | \(f^{(N+1)}(\xi)(x-a)^{N+1}/(N+1)!\) | Lagrange 1797; not the complex disk bound |
| CAS `O(t^n)` | truncated series rings | token in \(R[[t]]/(t^n)\) | Maple `series`; SymPy `.series`; Mathematica `Series` |
| Hierarchical / MRV series | symbolic limits | most-rapidly-varying scale, then Taylor in \(\omega\to 0^+\) | Gonnet–Gruntz 1988; Gruntz 1996 |
| Numeric certified series | validated numerics | ball/interval enclosure of a number or of a truncated series at a **number** | Moore 1966; van der Hoeven 2009; Arb (Johansson 2017); Taylor models |
| Holonomic tail bound | D-finite CAS | bound on \(\sum_{k\ge N}u_k z^k\) from a linear ODE | Mezzarobba; NumGfun; GFUN |
| Hop `remainder_verdict` | this engine | ZERO/UNKNOWN field on a Laurent hop | V5-G; `compose_hop_verdict` |
| RemainderCertificate | this line | atom-local IR: CERTIFIED / ASSUMPTION_REQUIRED / NONANALYTIC / UNKNOWN | `schema.py`; not hop ZERO |

Mixing a holomorphic remainder theorem with a CAS `O` token, a
numeric ball, or a hop C0 match is a reviewer-kill.

| Scale | Track / line | Object | Closed evidence |
|---|---|---|---|
| Pair | V | two-member local confluence | 3 frozen Guo pairs ZERO (`38d6d4a`) |
| Family | V2 | 4–5 member graphs | **not closed**; H-C |
| Iterated path | V3 | ordered one-parameter steps | **not closed**; I-D |
| Atom series | V4 | per-atom `series` then `together` + Laurent \(t^0\) | J-C: diagonal ZERO; generic UNKNOWN |
| Coefficient space | V5 | sparse \([t^k]\); LEVEL A/B/C | L-D after remainder fail-close: G0016→G0013 LEVEL_B UNKNOWN (C0 matches; rem UNKNOWN) |
| Remainder cert | this line | atom remainder order under declared assumptions | IR frozen; **no** CERTIFIED remainder; **no** hop ZERO |

A remainder certificate is not a hop certificate
(`PROTOCOL.md`). `CERTIFIED` means the atom remainder *order*
is proved under listed assumptions. Hop ZERO still requires
composition of negatives, C0, **every** required atom remainder,
and independent review. Never infer `LEVEL_B ⇒ LEVEL_C`.
Never infer remainder `CERTIFIED` ⇒ hop `ZERO`.

---

## 1. Holomorphic Taylor remainder

**What.** If \(f\) is holomorphic on a domain \(\Omega\subset\mathbb C\)
and the closed disk \(\lvert\zeta-a\rvert\le r\) lies in \(\Omega\),
then for \(\lvert z-a\rvert<r\)

\[
f(z)=\sum_{k=0}^{N}\frac{f^{(k)}(a)}{k!}(z-a)^k+R_{N+1}(z),
\]

with Cauchy integral remainder

\[
R_{N+1}(z)
=\frac{(z-a)^{N+1}}{2\pi i}
\oint_{\lvert\zeta-a\rvert=r}
\frac{f(\zeta)}{(\zeta-a)^{N+1}(\zeta-z)}\,d\zeta.
\]

In particular \(R_{N+1}(z)=O(\lvert z-a\rvert^{N+1})\) as \(z\to a\),
and the series converges to \(f\) on the whole disk of holomorphy.
The same statement for the affine germ \(f(\alpha_0+ct)\) is the
composition of a holomorphic function with an affine map: if
\(\lvert c t\rvert\) stays inside a pole-free disk about \(\alpha_0\),
then \(R_{N+1}(t)=O(t^{N+1})\) as \(t\to 0\).

**Canonical sources.**

- Taylor, *Methodus Incrementorum Directa et Inversa* (1715):
  the real finite-difference origin. Not a complex remainder
  theorem, and not novelty here.
- Cauchy integral formula and the derived power-series expansion
  (textbooks: Ahlfors, *Complex Analysis*, 3rd ed. 1979, Ch. 4;
  Conway, *Functions of One Complex Variable*, 1978; Rudin,
  *Real and Complex Analysis*). The integral remainder is the
  truncated geometric series inside Cauchy’s formula.
- Real Lagrange remainder: Lagrange, *Théorie des fonctions
  analytiques* (1797). Useful on a real segment; **not** a
  substitute for a complex disk that may miss poles off the
  real axis.

**What CAS already does.** `sympy.series`, Maple `series`,
Mathematica `Series` emit a truncated polynomial plus an `O`
token. The token records a truncation order in a formal series
ring. It does **not** prove that a symbolic parameter keeps the
germ holomorphic.

**This line’s use.** The motivating identity in
`PROBLEM_STATEMENT.md` is exactly this theorem applied to
\(f(z)=\mathrm{polygamma}(k,z)\) (or a generic holomorphic \(f\))
along \(z=\alpha_0+ct\). Shipping the identity is
reimplementation. The obligation is to *prove the disk exists*
from declared assumptions, or fail closed.

**What must not be claimed.** “We introduce Taylor remainder.”
“\(O(t^{N+1})\) for holomorphic \(f(\alpha_0+ct)\) is a new
lemma.” Any analyst will desk-reject those sentences.

**Classification.** STANDARD MATHEMATICS. See
`CLASSIFICATION.md` §1.

---

## 2. Cauchy estimates

**What.** If \(f\) is holomorphic on \(\lvert\zeta-a\rvert\le r\)
and \(\lvert f\rvert\le M\) there, then

\[
\lvert f^{(n)}(a)\rvert\le n!\,\frac{M}{r^n},\qquad
\lvert a_n\rvert=\Bigl\lvert\frac{f^{(n)}(a)}{n!}\Bigr\rvert\le\frac{M}{r^n}.
\]

Geometric summation of the tail gives the standard bound, for
\(\lvert z-a\rvert\le\rho<r\),

\[
\lvert R_{N+1}(z)\rvert
\le M\frac{(\rho/r)^{N+1}}{1-\rho/r}
= M\frac{\rho^{N+1}}{r^N(r-\rho)}.
\]

A contour-length form of the integral remainder is equivalent
up to the factor \(r/(r-\rho)\) versus \(1/(1-\rho/r)\).

**Canonical sources.** Cauchy’s integral formula plus the ML
inequality; Ahlfors; Conway. Undergraduate after the integral
formula. Used as Liouville’s input.

**This line’s use.** Agent R4 is specified to own a Cauchy bound
(`OWNERS.md`). A bound is only as honest as \(M<\infty\) and
as the proof that the circle \(\lvert\zeta-\alpha_0\rvert=r\)
avoids singularities. `ASSUMPTION_POLICY.md` forbids inserting
“\(M<\infty\) in a Cauchy bound without a finiteness proof”
and forbids “sufficiently small \(t\)” without an existence
certificate for some \(\delta>0\).

**What must not be claimed.** “We introduce Cauchy estimates.”
“A remainder bound \(M(\rho/r)^{N+1}/(1-\rho/r)\) is the
contribution.”

**Classification.** STANDARD MATHEMATICS. See
`CLASSIFICATION.md` §2.

---

## 3. Polygamma analytic structure (DLMF 5.15)

**What.** Write \(\psi^{(n)}=\mathrm{polygamma}(n,\cdot)\). For
integer \(n\ge 0\), \(\psi^{(n)}\) is meromorphic on \(\mathbb C\),
with poles exactly at \(\{0,-1,-2,\ldots\}\) of order \(n+1\),
and holomorphic elsewhere. For \(n\le -2\) the corresponding
negapolygamma / `loggamma` family is entire (engine convention
in V5-G). Wherever holomorphic,

\[
\frac{d}{dz}\psi^{(n)}(z)=\psi^{(n+1)}(z),
\qquad
\psi^{(n)}(z+t)=\sum_{k\ge 0}\psi^{(n+k)}(z)\,\frac{t^k}{k!}.
\]

Recurrence (DLMF 5.15.5)

\[
\psi^{(n)}(z+1)=\psi^{(n)}(z)+(-1)^n n!\,z^{-n-1}.
\]

Near a pole, the leading Laurent term is the \(n\)-th derivative
of \(1/z\):

\[
\psi^{(n)}(z)\sim(-1)^{n+1}n!\,z^{-n-1}\qquad(z\to 0,-1,-2,\ldots).
\]

Trigamma has the everywhere-valid series
\(\psi'(z)=\sum_{k\ge 0}(k+z)^{-2}\) for \(z\notin\{0,-1,\ldots\}\)
(DLMF 5.15.1). Poincaré asymptotics at infinity (5.15.8–5.15.9)
are a **different** expansion (large \(\lvert z\rvert\), not
small \(t\)).

**Canonical sources.**

- NIST DLMF Chapter 5 (Askey–Roy), §5.15; §5.2 psi; §5.4–5.5
  recurrence and reflection. “Most properties follow
  straightforwardly by differentiation of properties of the
  psi function.”
- Abramowitz and Stegun (1964), §6.4.1: poles of order \(n+1\)
  at nonpositive integers.
- Nielsen (1906); Whittaker and Watson.
- SymPy `polygamma` table / `.series`. Track V already recorded
  this as `SPECIAL_FUNCTION_LOCAL` / not master invention.
  Track V4 and Track V5 literature already labelled polygamma
  Taylor **known standard**. This pack does not lift that ban.

**Why infinitely many poles matter.** A function with infinitely
many singularities is **not D-finite** (Stanley 1980: D-finite
germs have finitely many singularities). Holonomic tail-bound
software therefore does not apply to \(\psi^{(n)}(z)\) as a
function of \(z\). See §8.

**This line’s use.** Domain side: \(\alpha_0\) must be proved
outside \(\{0,-1,-2,\ldots\}\), or the expansion is NONANALYTIC
/ UNKNOWN, never silently CERTIFIED. Derivative side: higher
polygamma at \(\alpha_0\) are the Taylor coefficients, not a
new addition formula. V5-G `remainder_ok` already implements
the numeric-α special case and returns False on symbolic α
(`sufficiency.py`; review R2).

**Forbidden.** Silent class-C insertion of
\(\alpha_0\notin\{0,-1,-2,\ldots\}\). Physics positivity
(\(\beta>0\), energy \(1/2+iE\)) as class D. Guo identity
tables. Restoring `fb3b929` by informal “energy arguments
never hit poles.”

**What must not be claimed.** “We introduce polygamma poles.”
“DLMF 5.15 is a remainder certificate.” “Polygamma confluence
is a new identity.”

**Classification.** STANDARD MATHEMATICS. See
`CLASSIFICATION.md` §3.

---

## 4. Symbolic asymptotics and CAS series

**What.** Computer algebra already (i) manipulates truncated
power / Laurent series \(R[[t]]/(t^n)\) or \(R[t,t^{-1}]\) plus
an `O` token, and (ii) computes limits of exp-log expressions
by hierarchical series (Gruntz), rewriting the most rapidly
varying subexpression as \(\omega\to 0^+\) and reading the
leading term.

**Canonical sources.**

- Gonnet and Gruntz, ISSAC 1988 (LNCS 358); Gruntz, ETH Diss.
  11432, 1996. Maple; SymPy `sympy.series.gruntz`. Already
  classified in Track V and Track V3 literature: **known
  standard**, complete for a stated exp-log class, **not**
  for arbitrary `Sum`/`Piecewise`/polygamma kernels.
- Shackell, *J. Symbolic Comput.* 1990; van der Hoeven
  transseries.
- Salvy and Zimmermann, GFUN (*ACM TOMS* 1994): generating
  functions / holonomic series — different object.
- Maple `series` / `asympt`, Mathematica `Series` /
  `SeriesCoefficient`, SymPy `.series`.
- Geddes, Czapor, Labahn, *Algorithms for Computer Algebra*
  (1992), Ch. 2–4: series arithmetic.

**What these systems do *not* do.** They do not, as a default
`series(polygamma(k, α0 + c*t), t, 0, N)` call, emit a
checkable proof that a *symbolic* \(\alpha_0\) stays off the
pole lattice. The `O(t^N)` is a truncation tag. Track V3
already forbade treating `removeO()` as a removable-singularity
certificate. `CERTIFICATION_SCOPE.md` forbids coefficient
matching on expanded series as Level-1 ZERO.

**This line’s use.** Per-atom series is an inner primitive
(V4/V5). The remainder line must not treat a CAS `O` token
as `RemainderCertificate.verdict == CERTIFIED`.

**What must not be claimed.** “First symbolic series of
polygamma.” “We replace Gruntz.” “Maple cannot do this,
therefore we are novel.” Lack of a runtime is not novelty.

**Classification.** STANDARD CAS TECHNIQUE. See
`CLASSIFICATION.md` §4.

---

## 5. Interval / ball arithmetic and numeric certified series

**What.** Interval analysis encloses the range of a function
on a box. Ball (midpoint-radius) arithmetic is the same idea
with a different representation, efficient at high precision.
Taylor models store a polynomial plus a remainder interval.
Libraries evaluate special functions, including polygamma /
gamma, at **numeric** complex balls and return enclosures;
some also enclose truncated power series with ball
coefficients and bound tails via Cauchy’s formula on a
numeric disk.

**Canonical sources.**

- Moore, *Interval Analysis* (Prentice-Hall, 1966); Moore,
  Kearfott, Cloud, *Introduction to Interval Analysis*
  (SIAM, 2009). Theory of interval extensions: **standard
  mathematics**.
- van der Hoeven, *Ball arithmetic* (HAL 2009 / 2011):
  serial balls, tail bounds via Cauchy’s formula on a
  numeric disk, Mathemagix.
- Johansson, “Arb: efficient arbitrary-precision
  midpoint-radius interval arithmetic,” *IEEE Trans.
  Comput.* 66 (2017) 1281–1292. Complex balls; power
  series; \(\Gamma\), \(\psi^{(s)}\), Hurwitz zeta with
  rigorous error bounds. Sage/FLINT wrappers.
- Makino and Berz, “Taylor models and other validated
  functional inclusion methods,” *Int. J. Pure Appl.
  Math.* 4 (2003) 379–456; COSY Infinity. Remainder
  *interval* for a \(C^{n+1}\) map on a real box.
- Tucker, *Validated Numerics* (Princeton, 2011); Rump
  INTLAB; MPFI.

**Wrong object for this line’s symbolic question.** Enclosing
\(\mathrm{polygamma}(k, 1.5+0.01i)\) to 50 bits is a numeric
certificate of a number. It does not prove
\(R_{N+1}(t)=O(t^{N+1})\) uniformly for a symbolic family
\(\alpha_0=\frac12+\beta(\gamma\pm i(\mu-\varepsilon))/(2\pi)\).
R11 numeric sanity may use balls to *refute* (never to mint
`CERTIFIED`). `ASSUMPTION_POLICY.md`: no numeric sampling
as a derived (class B) step.

**What must not be claimed.** “We introduce certified series.”
“Arb cannot do symbolic α, therefore remainder certificates
are a new analysis theorem.” Numeric enclosure of a sample
is not a symbolic remainder certificate.

**Classification.** STANDARD CAS TECHNIQUE for the software
and the numeric remainder practice. The underlying interval
inclusion theorems are STANDARD MATHEMATICS (do not upgrade
either to a contribution). See `CLASSIFICATION.md` §5.

---

## 6. Holonomic / D-finite remainder bounds (if relevant)

**What.** A series or function is D-finite (holonomic) when
it satisfies a linear ODE with polynomial coefficients, or
equivalently a linear recurrence with rational coefficients.
Truncation bounds for such series can be computed from the
ODE (van der Hoeven; Mezzarobba–Salvy; Mezzarobba 2019).
Software: GFUN, NumGfun, `ore_algebra`.

**Canonical sources.**

- Stanley, “Differentially finite generating functions,”
  *European J. Combin.* 1 (1980) 175–188: finitely many
  singularities.
- Zeilberger, holonomic systems approach (1990); Chyzak;
  Koutschan. WZ certificates: right slogan (small witness),
  **wrong object** (hypergeometric sums).
- Salvy–Zimmermann, GFUN (1994).
- Mezzarobba, NumGfun (ISSAC 2010); Mezzarobba, “Truncation
  bounds for differentially finite series,” *Ann. Henri
  Lebesgue* 2 (2019) 99–148.

**Relevance here.**

- **On-topic for generic entire/D-finite controls** (suite
  class A-exp, rational germs): exp is D-finite; a rational
  function is D-finite. A holonomic tail bound is a
  published way to get \(M,r\) for those objects. Using it
  would be STANDARD CAS TECHNIQUE, not a contribution.
- **Off-topic for polygamma in \(z\).** \(\psi^{(n)}(z)\) has
  poles at every nonpositive integer, hence infinitely many
  singularities, hence is not D-finite as a function of \(z\).
  (It is related to Hurwitz \(\zeta(n+1,z)\).) Applying
  NumGfun to a Guo polygamma atom as if it were Bessel is a
  type error.
- Log is Liouvillian, not D-finite. Local Taylor of
  \(\log(\alpha_0+ct)\) still needs a disk avoiding \(0\)
  (and a branch cut). That is Cauchy + domain, not holonomy.

**What must not be claimed.** “We introduce holonomic remainder
bounds.” “Polygamma remainder is a D-finite certificate.”

**Classification.** STANDARD CAS TECHNIQUE, and the **wrong
object** for the motivating polygamma class. See
`CLASSIFICATION.md` §6.

---

## 7. Formal kernels (Isabelle / Lean / Coq)

**What.** Isabelle `HOL-Complex_Analysis` contains Cauchy’s
integral formula, power series of holomorphic functions, and
related remainder facts
(`Cauchy_Integral_Formula.thy`). Lean mathlib and Coq
analysis libraries contain real Taylor-with-remainder and
partial complex analysis. These are formalizations of
**textbook** theorems.

**This line’s use.** None, on the freeze host
(`CERTIFICATION_SCOPE.md`: Level 3 unavailable). Engine
`RemainderCertificate` objects are **engine semantics**, not
kernel objects. Claiming “machine-checked” in the Lean sense
is forbidden.

**Classification.** STANDARD MATHEMATICS (formalized). Not a
CAS technique of this engine. Not a contribution.

---

## 8. RemainderCertificate IR and assumption classes

**What.** `research/remainder_certification/schema.py` names
an atom-local record: function family, affine argument,
expansion order, nonempty `domain_conditions`, analyticity
witness, distance to singularity, remainder form, bound,
small-\(t\) condition, `assumptions_used` with classes

```
A_DECLARED | B_DERIVED | C_GENERICITY | D_HUMAN_REQUIRED
```

and verdicts

```
CERTIFIED | ASSUMPTION_REQUIRED | NONANALYTIC | UNKNOWN.
```

`validate_certificate` never upgrades a verdict. Empty
`domain_conditions` → UNKNOWN. Class C or D → cannot stay
CERTIFIED. Remainder CERTIFIED is defined to be unequal to
hop ZERO.

**Why this is not a new analysis theorem.** Riemann + Taylor
with remainder + “list your hypotheses.” LEDA / WZ / Track V
reconstruction witnesses already use the slogan “check a
small object.” The four-way remainder verdict is this
repository’s fail-closed language, analogous to Track V5
LEVEL A/B/C (already labelled engineering adaptation, not a
certificate calculus).

**Why it is systems work.** Wiring R1–R11 outputs into one
IR, hashing assumptions, refusing silent genericity, and
keeping remainder verdicts off the hop ZERO channel is
discipline. `ASSUMPTION_POLICY.md` is a freeze, not a paper
result.

**Classification.** SYSTEMS INTEGRATION. See
`CLASSIFICATION.md` §7.

---

## 9. Closest verification systems (not to copy slogans from)

Reuse frozen `research/literature/corpus.md` for
proposer–verifier crowding, Track V `METHODS.md` for
`SERIES_LOCAL`, Track V5 `METHODS.md` for sparse Laurent /
C0. Distance *as remainder certifiers for symbolic affine
special-function germs*:

| System | What it checks | vs this line |
|---|---|---|
| Ahlfors / Conway / Cauchy remainder | holomorphic Taylor tail on a disk | the **math**; not a CAS certificate for symbolic \(\alpha_0\) |
| DLMF 5.15 / A&S / SymPy `polygamma` | poles, recurrence, Taylor in the argument | the **math** of the test class; table lookup |
| Maple/Mathematica/SymPy `series` | truncated series + `O` token | **no** domain proof for symbolic poles |
| Gruntz / `sympy.limit` | exp-log hierarchical series | inner primitive; not polygamma-affine remainder |
| Arb / MPFI / INTLAB / COSY | numeric balls / Taylor models | **numeric** enclosure; forbidden as CERTIFIED for symbolic α |
| NumGfun / `ore_algebra` | D-finite tail bounds | wrong object for polygamma(\(k,z\)) |
| Track V5-G `remainder_ok` | numeric α not in \(\mathbb Z_{\le 0}\) | **implemented** special case; symbolic α → UNKNOWN; hop field, not RemainderCertificate |
| Track V5-F C0 matcher | \([t^0]\) vs diagonal target | **not a remainder**; LEVEL B/C composition; not this contribution |
| WZ / *A=B* | hypergeometric sum certificates | wrong object |
| Lean/Isabelle kernels | formal proofs of textbook analysis | stronger; unavailable; must not claim |
| Engine `verifier.py` | structural residual + rational probes | global; does not certify Taylor tails |
| PIT / `N[...,30]` | probabilistic / numeric identity | **forbidden** ZERO/CERTIFIED path |

No retrieved system jointly (i) takes **symbolic affine**
arguments of meromorphic special functions, (ii) emits a
checkable remainder-order certificate under an **explicit**
assumption class that refuses silent genericity, (iii) fails
closed to ASSUMPTION_REQUIRED / UNKNOWN / NONANALYTIC rather
than inserting \(\alpha_0\notin\mathbb Z_{\le 0}\), (iv)
forbids numeric CERTIFIED, and (v) refuses to treat remainder
CERTIFIED as hop ZERO.

That joint *packaging* is a **GAP**, not a proof of novelty.
The methods in §§1–7 are not new. No generic suite has run.
False CERTIFIED is not yet measured. If that suite later
exists with false CERTIFIED = 0, the only honest remainder
would be **verification-engineering**: machine-checkable
remainder certificates for symbolic affine special-function
arguments under explicit assumption classes, under engine
semantics. It would still not be Taylor’s theorem, still not
Cauchy estimates, still not polygamma poles, and still not a
Track V5 C0 match.

---

## 10. How this line should compose these methods

| piece | owner | decides remainder CERTIFIED? | method (§) |
|---|---|---|---|
| holomorphic remainder | R1 `analysis/` | no (theorem only) | §1 |
| polygamma domain | R2 `polygamma/` | no (domain predicate) | §3 |
| neighborhood of \(t=0\) | R3 `neighborhood/` | no (disk existence) | §§1–2 |
| Cauchy bound | R4 `cauchy/` | no (bound given \(M,r\)) | §2 |
| order algebra \(O(t^{N+1})\) | R5 `order_algebra/` | no | §1 |
| polygamma derivatives | R6 `derivatives/` | no | §3 |
| affine normalizer | R7 `affine/` | no | composition |
| certificate compiler | R8 `compiler/` | may emit CERTIFIED only from A/B | §8 |
| analysis falsifier | R9 `falsifier/` | no (refute false CERTIFIED) | — |
| assumption audit | R10 `assumption_audit/` | no (class C/D → not CERTIFIED) | §8 |
| numeric sanity | R11 `numeric/` | NONZERO-class refutation only | §5 |
| literature | R12 (this pack) | no | classification |
| alternatives | R13 `alternatives/` | no | §§4–6 |

No new LLM calls. Frozen authorities: `84b412d` (V5 remainder
fail-close), `9da52fb` (problem + assumption freeze),
`adbfd9f` (IR), V4 `248d247`, V3 `d2752f9`. Historical run
JSON is read-only.

Order of evidence (`PROTOCOL.md`): generic theorem → generic
suite with false CERTIFIED = 0 → symbolic affine class
(motivating form, **not** Guo atoms) → frozen G0016 atoms
only after the generic method is frozen → LEVEL C hop
reconstruction only if every required atom remainder is
CERTIFIED **and** independent review passes. Ell-hops only
after the primary remainder question is decided.

Allowed local methods: exact substitution, affine
normalization, named special-function identities already in
SymPy, Cauchy estimates on a **proved** disk, order algebra
of \(O(t^{k})\), fail-closed UNKNOWN. Fallback UNKNOWN.

Forbidden: Guo-specific identity table, gold leakage,
converting timeout to CERTIFIED, numeric agreement as
CERTIFIED, silent class C/D, `M<\infty` without proof,
`removeO()` as CERTIFIED, treating V5 C0 as remainder,
restoring `fb3b929`, unlocking D2.

---

## 11. Self-adversarial notes

1. Taylor remainder on a disk of holomorphy is 19th-century
   analysis. Drafts that lead with “certified Taylor remainder”
   as the mathematics will be referred to Ahlfors.
2. Cauchy estimates need \(M\) and \(r\). Assuming them is
   class C/D. A bound without a disk is not CERTIFIED.
3. Polygamma poles at \(\mathbb Z_{\le 0}\) are in every
   handbook. A domain lemma that a *particular* affine family
   misses those poles, if ever proved from class A/B, is a
   derived predicate — not a new special-function identity.
   If it needs class C, the verdict is ASSUMPTION_REQUIRED.
4. V5 C0 match (primary hop constant term vs G0013) is a
   coefficient identity after negatives vanish. It is not
   \(R_{N+1}(t)=O(t^{N+1})\). Selling C0 as remainder is the
   `forbidden_ignore_remainder` trap already recorded by
   V5 review R2 and the remainder-regression test.
5. CAS `series` `O(t^n)` is a ring token. Treating it as
   CERTIFIED repeats the Track V3 truncation ban.
6. Arb/Taylor-model enclosures at a numeric sample of α
   may refute. They may not certify a symbolic family.
7. Holonomic tail bounds are real software. They do not
   apply to polygamma(\(k,z\)). Citing NumGfun as the
   polygamma remainder method is a type error.
8. Remainder CERTIFIED is not hop ZERO. LEVEL C composition
   still needs every atom, plus review. This pack issues no
   publication letter.
9. Guo n=1 cannot carry a generalization claim even if a
   later remainder CERTIFIED appears on a test atom.
10. This literature pack runs no suite. Status remains
    literature-only until R1–R11 fire with false CERTIFIED
    = 0.

## Unconfirmed / not used

- Papers whose titles were recalled but not retrieved with
  matching authors/year/venue.
- Numeric Gruntz / series solve-rate tables from search
  snippets.
- Any claim that R1–R11 already produced remainder CERTIFIED
  (those directories are owned elsewhere; this pack is
  documentation).
- Any claim that G0016→G0013 is LEVEL_C ZERO (retracted;
  fail-closed UNKNOWN remainder).
