# Classification of remainder-certification methods

Audit date: 2026-08-29.
Companion: `METHODS.md`. Labels are for **paper-facing honesty**,
not marketing.

Allowed labels (exactly one primary label per method):

| label | meaning |
|---|---|
| **STANDARD MATHEMATICS** | Textbook or handbook theorem. Shipping it is reimplementation. |
| **STANDARD CAS TECHNIQUE** | Published algorithm or production CAS/validated-numerics primitive. Shipping it is reimplementation. |
| **SYSTEMS INTEGRATION** | Standard methods wired into this engine’s RemainderCertificate IR, assumption classes, and fail-closed four-way. Systems work, not a new theorem. |
| **POTENTIAL RESEARCH CONTRIBUTION** | Not claimed. The only cell that may ever occupy this label is **machine-checkable remainder certificates for symbolic affine special-function arguments under explicit assumption classes**. It remains a **GAP** until a generic suite exists with false `CERTIFIED` = 0. Track V5 C0 match is **not** this cell. |

There is **no** claimed contribution in this pack. Taylor
remainder, Cauchy estimates, and polygamma poles **must not**
be quoted as novelty under any hedge.

**Hard rules.**

1. Taylor’s theorem (real or holomorphic) is **STANDARD
   MATHEMATICS**. A reviewer who knows Ahlfors will desk-reject
   any draft that leads with “we introduce Taylor remainder.”
2. Cauchy estimates are **STANDARD MATHEMATICS**. A remainder
   bound \(M(\rho/r)^{N+1}/(1-\rho/r)\) is not a contribution.
3. Polygamma poles at nonpositive integers, the derivative
   identity, and the Taylor series in the argument (DLMF 5.15)
   are **STANDARD MATHEMATICS**. Track V4 and Track V5 already
   recorded this ban. This line does not lift it.
4. Remainder `CERTIFIED` is **not** hop `ZERO`. Track V5 C0
   match is **not** a remainder certificate and **not** this
   line’s candidate contribution.
5. Do not revive retracted LEVEL_C ZERO (`fb3b929`). Track D2
   stays LOCKED. Publication status E.

This pack classifies **remainder-certification methods**.
Discovery of a representation \(H=(R,\{A_i\},\{\mathcal O_i\},F)\)
is Track D / D2 and stays locked.

---

## Summary table

| # | Method | Primary label | May a paper call this novel? |
|---|---|---|---|
| 1 | Holomorphic Taylor remainder | **STANDARD MATHEMATICS** | **no** |
| 2 | Cauchy estimates / tail bound from \(M,r\) | **STANDARD MATHEMATICS** | **no** |
| 3 | Polygamma meromorphic structure (DLMF 5.15) | **STANDARD MATHEMATICS** | **no** |
| 4 | Affine composition \(f(\alpha_0+ct)\); \(O(t^{N+1})\) order algebra | **STANDARD MATHEMATICS** | no |
| 5 | Symbolic asymptotics; CAS `series` + `O` token | **STANDARD CAS TECHNIQUE** | no |
| 6 | Interval/ball arithmetic; numeric certified series (Arb, Taylor models) | **STANDARD CAS TECHNIQUE** | no |
| 7 | Holonomic / D-finite tail bounds | **STANDARD CAS TECHNIQUE** (wrong object for polygamma in \(z\)) | no |
| 8 | Formal kernels (Isabelle/Lean Taylor) | **STANDARD MATHEMATICS** (unavailable here) | no |
| 9 | RemainderCertificate IR; assumption classes A/B/C/D; fail-closed verdicts | **SYSTEMS INTEGRATION** | no, as a certificate calculus |
| 10 | V5-G `remainder_ok` on numeric α; V5 C0 matcher | **SYSTEMS INTEGRATION** (prior track; C0 is **not** remainder) | no |
| \* | Machine-checkable remainder certificates for symbolic affine special-function arguments under explicit assumption classes | **POTENTIAL RESEARCH CONTRIBUTION** as **GAP** only | **no; not claimed** |

Primary labels for methods 1–10 are **not** contributions.
Methods 1–4 and 8 are not even systems work of the
*mathematics*. Methods 5–7 are published CAS / validated
numerics. Method 9 is ordinary fail-closed wiring.

The last row is a **GAP**. It is not a result that a draft may
hedge into existence. No generic suite has run. V5 primary hop
is LEVEL_B UNKNOWN (C0 matches; remainder not). Retracted
LEVEL_C ZERO stays retracted.

---

## 1. Holomorphic Taylor remainder — STANDARD MATHEMATICS
(not novelty; not a remainder-line contribution)

**Why this label (and why it is the point of this pack).**

\[
f(z)=\sum_{k=0}^{N}\frac{f^{(k)}(a)}{k!}(z-a)^k+R_{N+1}(z),
\]

with Cauchy integral remainder, on every disk of holomorphy,
is undergraduate complex analysis (Ahlfors; Conway; Rudin).
The real Lagrange form is older (Lagrange 1797; Taylor 1715)
and is the **wrong primary object** when poles may sit off a
real path.

The identity in `PROBLEM_STATEMENT.md` for
\(f(\alpha_0+ct)\) is this theorem plus affine composition.
**It is not a new remainder.**

**False-novelty sentences to delete.** “We introduce Taylor
remainder.” “Holomorphic remainder certificates are a new
analysis theorem.” “\(R_{N+1}(t)=O(t^{N+1})\) for holomorphic
\(f\) is the contribution.”

**Headline for authors.** Taylor remainder is standard
mathematics, not novelty.

---

## 2. Cauchy estimates — STANDARD MATHEMATICS
(not novelty)

**Why this label.** \(\lvert f^{(n)}(a)\rvert\le n!\,M/r^n\)
and the geometric tail bound
\(\lvert R_{N+1}\rvert\le M(\rho/r)^{N+1}/(1-\rho/r)\) follow
from Cauchy’s integral formula by the ML inequality. Every
complex-analysis course proves them on the way to Liouville.

**Why this line’s use does not upgrade the label.** R4 may
instantiate the bound. Instantiation is valid only after a
disk \(\lvert\zeta-\alpha_0\rvert\le r\) is proved to lie in
the holomorphic set, so that \(M=\max\lvert f\rvert<\infty\)
is a theorem, not an assumption. Silent \(M<\infty\) is class
C/D (`ASSUMPTION_POLICY.md`).

**False-novelty sentences to delete.** “We introduce Cauchy
estimates.” “Our remainder bound is a new inequality.”

---

## 3. Polygamma meromorphic structure (DLMF 5.15) — STANDARD MATHEMATICS
(not novelty)

**Why this label (and why it is the other point of this pack).**

Poles of \(\psi^{(n)}\) (\(n\ge 0\)) exactly at
\(\{0,-1,-2,\ldots\}\), order \(n+1\); derivative identity;
Taylor series in the holomorphic argument; recurrence
DLMF 5.15.5; polar leading term
\((-1)^{n+1}n!\,z^{-n-1}\). Abramowitz–Stegun §6.4.1;
Nielsen; Whittaker–Watson; SymPy table. Track V4:

> Polygamma derivative, Taylor expansion, and Laurent
> coefficients of a removable pole are **known standard**.

Track V5 repeated the ban. This line does not lift it.

**Why this line’s use does not upgrade the label.** Domain
checking “is \(\alpha_0\) a nonpositive integer?” is the
definition of the polar set. V5-G already does the numeric
case. A derived lemma that a declared symbol class misses
\(\mathbb Z_{\le 0}\) would be class B, still not a new
polygamma identity.

**False-novelty sentences to delete.** “We introduce polygamma
poles.” “We introduce polygamma Taylor series.” “DLMF 5.15 is
our remainder theorem.”

**Headline for authors.** Polygamma poles are standard special
functions, not novelty.

---

## 4. Affine composition and \(O(t^{N+1})\) — STANDARD MATHEMATICS

**Why this label.** If \(f\) is holomorphic at \(\alpha_0\)
and \(c\) is constant, then \(t\mapsto f(\alpha_0+ct)\) is
holomorphic at \(t=0\). Composition of holomorphic maps;
chain rule; big-O algebra of germs. Existence of some
\(\delta>0\) with \(\lvert ct\rvert<\mathrm{dist}(\alpha_0,\mathrm{Poles})/2\)
is the open-disk definition, not a research lemma.

**Forbidden upgrade.** Inserting “sufficiently small \(t\)”
without a \(\delta>0\) certificate (`ASSUMPTION_POLICY.md`).

---

## 5. Symbolic asymptotics and CAS `O` tokens — STANDARD CAS TECHNIQUE

**Why this label.** Gruntz 1996; Gonnet–Gruntz ISSAC 1988;
Maple `series`/`asympt`; Mathematica `Series`; SymPy
`.series` / `gruntz`; Geddes–Czapor–Labahn series arithmetic.
Track V §1 and Track V3 §5 already classified these as
known standard / standard CAS.

**Why the `O` token is not CERTIFIED.** It is an element of a
truncated series ring, not a proof that a symbolic parameter
avoids poles. `removeO()` as a removable-singularity
certificate was forbidden in Track V3 and remains forbidden.
`CERTIFICATION_SCOPE.md` forbids coefficient matching on
expanded series as Level-1 ZERO.

**False-novelty sentences to delete.** “First symbolic series
of polygamma.” “We replace Gruntz.” “Maple cannot do this,
therefore we are novel.”

---

## 6. Interval / ball arithmetic; numeric certified series — STANDARD CAS TECHNIQUE

**Why this label.** Moore 1966 (interval analysis: the
*theorems* are STANDARD MATHEMATICS; the *practice* this
line would call is CAS/validated numerics). van der Hoeven
ball arithmetic (2009); Johansson Arb (2017) including
\(\psi^{(s)}\) and series with rigorous error bounds; Makino–
Berz Taylor models (2003); INTLAB; MPFI.

**Why it is the wrong object for symbolic α.** These tools
enclose numbers (or functions on numeric boxes). They do not
emit a RemainderCertificate for a symbolic affine argument.
Numeric agreement is never CERTIFIED. R11 may refute only.

**Why it is not potential novelty.** “Arb does not take
symbolic \(\alpha_0\)” is a scope mismatch, not a theorem we
fill by renaming Cauchy estimates.

**False-novelty sentences to delete.** “We introduce certified
series.” “Ball-arithmetic remainder is our contribution.”

---

## 7. Holonomic / D-finite tail bounds — STANDARD CAS TECHNIQUE
(wrong object for polygamma in \(z\))

**Why this label.** Stanley 1980; Zeilberger; GFUN; NumGfun
(Mezzarobba ISSAC 2010); Mezzarobba, *Ann. Henri Lebesgue*
2019. Published truncation bounds for D-finite series.

**Why not polygamma.** D-finite functions have finitely many
singularities. \(\psi^{(n)}(z)\) has a pole at every
nonpositive integer. Holonomic remainder software is relevant
to generic-suite controls such as `exp` (D-finite) and
rational germs, not to the motivating polygamma atoms.

**False-novelty sentences to delete.** “We introduce holonomic
remainder bounds.” “Polygamma is certified D-finite.”

---

## 8. Formal kernels — STANDARD MATHEMATICS
(formalized textbook; unavailable)

**Why this label.** Isabelle `HOL-Complex_Analysis` Cauchy
integral formula and holomorphic power series; mathlib /
Coq real Taylor theorems. These are encodings of §§1–2.
`CERTIFICATION_SCOPE.md`: this engine is Level-1 SymPy
semantics, not a kernel. Must not claim “machine-checked
theorem” in the Lean/Isabelle sense.

---

## 9. RemainderCertificate IR and assumption classes — SYSTEMS INTEGRATION
(mathematics: STANDARD MATHEMATICS)

**Why the mathematics is standard.** List hypotheses; apply
Taylor-with-remainder on a proved disk; fail closed if the
disk is unproved. Four named verdicts do not mint a proof
theory.

**Why this line’s use is systems integration, not novelty.**
New IR names, not new math:

- nonempty `domain_conditions` (schema error if omitted);
- classes A/B only for CERTIFIED; C/D → ASSUMPTION_REQUIRED;
- NONANALYTIC when the path hits the polar set;
- UNKNOWN when hypotheses are unproved;
- remainder CERTIFIED ≠ hop ZERO;
- assumption hash; no silent genericity.

That four-way is this repository’s language
(`research/remainder_certification/schema.py`). Shipping it
is systems work. Track V5 LEVEL A/B/C was already labelled
engineering adaptation of Riemann + remainder. This IR is
the remainder-shaped analogue, still not a certificate
calculus for a paper.

---

## 10. V5-G numeric `remainder_ok` and V5 C0 — SYSTEMS INTEGRATION
(prior track; C0 is not remainder)

**Why this label.** V5-G (`research/coefficient_laurent/remainder/sufficiency.py`)
applies §1+§3 to **numeric** affine \(\alpha\): if \(\alpha\notin\mathbb Z_{\le 0}\),
polygamma is holomorphic at \(t=0\) and the tail after \(t^0\)
is \(O(t)\). Symbolic \(\alpha\) → False → remainder UNKNOWN.
That is a correct fail-closed wrapper of standard mathematics.

V5-F C0 matching is exact \([t^0]\) versus a diagonal target
after negatives vanish. METHODS of Track V5 already assigned
C0 to `constant_verdict` only. Review R2 recorded that
hardcoding remainder ZERO from vanished negatives + C0 is
the `forbidden_ignore_remainder` trap. **C0 match is not this
line’s contribution and not a remainder certificate.**

**Forbidden upgrade.** Relabeling the C0 lemma on
G0016→G0013 as remainder CERTIFIED or as LEVEL_C ZERO.

---

## \*. Machine-checkable remainder certificates for symbolic affine
special-function arguments under explicit assumption classes
— **POTENTIAL RESEARCH CONTRIBUTION** as **GAP** only
(not a method in §§1–10; not a claim)

**What it would be, if anything.** A measured *systems*
protocol, not a theorem:

> Germs \(f(\alpha_0+ct)\) with \(f\) in a declared special-function
> class (generic: entire / meromorphic with explicit polar set;
> test class: polygamma) are equipped with a
> `RemainderCertificate` that, from **declared** (A) and
> **derived** (B) predicates only, proves a neighborhood of
> \(t=0\) on which \(R_{N+1}(t)=O(t^{N+1})\) (optionally with
> an explicit Cauchy bound), fails closed to
> ASSUMPTION_REQUIRED when class C/D would be needed, to
> NONANALYTIC when the germ is not holomorphic, and to
> UNKNOWN when the disk is unproved; numeric agreement is
> never CERTIFIED; timeout is never CERTIFIED; remainder
> CERTIFIED is never hop ZERO; no Guo identity table; generic
> suite first, with false CERTIFIED = 0.

If that protocol ever worked, the only honest name would be
**verification-engineering**: machine-checkable remainder
certificates for symbolic affine special-function arguments
under explicit assumption classes, under engine semantics
(`CERTIFICATION_SCOPE.md`). It would still not be
mathematics novelty. Taylor remainder, Cauchy estimates, and
polygamma poles would remain standard. V5 C0 would remain a
different object.

**Why this cell is a GAP, not a claimed contribution.**

- No generic suite has run on this parent (`PROTOCOL.md`
  order of evidence: theorem, then suite, then affine class,
  then Guo atoms). False CERTIFIED is unmeasured.
- V5-G already refuses symbolic α. The motivating Guo-shaped
  \(\alpha_0\) is symbolic (`reviews/R2_ANALYSIS.md`: 14/14
  `remainder_ok` False). That is UNKNOWN, not a certificate.
- Retracted `fb3b929` LEVEL_C ZERO was remainder-unsound.
  Fail-close (`84b412d`) stands. This line must not restore it.
- Track D2 LOCKED. Publication status E.
- This literature pack runs no experiment.

The user-facing rule: a system-level combination may be named
as a *candidate* **only if** later the generic suite exists
and false CERTIFIED = 0. Until then the label is **GAP**.
Do not quote this row as novelty, conditional novelty, or
“the contribution, if experiments support it” in a paper
title or abstract.

**What would still not upgrade the label even after a suite.**

- Taylor remainder, Cauchy estimates, or polygamma poles sold
  as the novelty.
- V5 C0 match sold as remainder CERTIFIED or hop ZERO.
- `series` + `removeO()` sold as CERTIFIED.
- Numeric Arb enclosure of a sample sold as CERTIFIED.
- Silent \(\alpha_0\notin\mathbb Z_{\le 0}\).
- Class C/D assumptions left off the certificate.
- Remainder CERTIFIED sold as hop ZERO or as unlocking D2.
- Relabeling retracted LEVEL_C ZERO as restored.
- Holonomic bounds sold as a polygamma-in-\(z\) method.
- Timeout / majority / PIT as CERTIFIED.

**Even if later a generic remainder CERTIFIED exists, do not say:**

- first LLM+verifier (crowded; frozen `novelty_boundary.md`);
- formal proof / machine-checked theorem;
- we invented Taylor remainder / Cauchy estimates / polygamma
  poles / Gruntz / Arb / holonomic bounds;
- Track V5 C0 already was remainder certification;
- remainder CERTIFIED is hop ZERO;
- Hartogs licensed skipping polar checks;
- coefficient matching on a truncated series is Level-1 ZERO.

---

## Upgrade experiments (what would change the GAP cell)

Literature does not generate these numbers. Owned by R1–R11
+ eval, not by R12. Until they exist, **do not change the GAP
label** and **do not issue a publication letter**.

1. **Generic suite first.** Positive and negative controls
   (entire, log with declared disk, rational, polygamma at
   safe numeric \(z_0\), declared pole-exclusion, prefactor
   \(t^{-m}\); poles, undeclared symbolic \(z_0\), path
   crossing poles, short \(N\), hidden denominator,
   unprovable domain). Not Guo atoms.
2. **False `CERTIFIED` = 0.** Falsifiers (R9, R10, R11):
   class C/D sold as CERTIFIED; empty domain_conditions;
   numeric sample sold as CERTIFIED; `O` token sold as
   CERTIFIED; pole path sold as CERTIFIED; C0 sold as
   remainder. All must stay NONANALYTIC, ASSUMPTION_REQUIRED,
   or UNKNOWN.
3. **No silent genericity.** Every CERTIFIED lists A/B only.
   `α₀ ∉ {0,−1,−2,…}` is derived or declared, never inserted.
4. **Remainder ≠ hop.** CERTIFIED remainder does not change
   `compose_hop_verdict` by itself. LEVEL B + remainder
   UNKNOWN stays hop UNKNOWN.
5. **Motivating affine class after the suite**, as a test
   class, not a design oracle. Do not shape theorems toward
   a desired Guo ZERO.
6. **No restoration of `fb3b929`.** Primary hop remains
   UNKNOWN until LEVEL C composition *and* independent
   review, after every required atom remainder is CERTIFIED.
7. **Family still separate.** Remainder CERTIFIED is not
   `FAMILY_ZERO`. Do not open D2.

Until those exist, the honest status is: **methods
classified; Taylor remainder is standard mathematics; Cauchy
estimates are standard mathematics; polygamma poles are
standard mathematics; V5 C0 is not remainder; no remainder
CERTIFIED; packaged contribution is a GAP.**

---

## Claims a knowledgeable reviewer would reject immediately

| Claim | Why it dies | Who cites it |
|---|---|---|
| “We invented Taylor remainder” | Taylor 1715; Cauchy integral remainder; Ahlfors | any analyst |
| “We invented Cauchy estimates” | Cauchy; Ahlfors; Liouville’s lemma | any analyst |
| “We invented polygamma poles / polygamma Taylor” | DLMF 5.15; A&S 6.4.1; Track V4/V5 one-pagers | special-function users |
| “CAS `O(t^n)` is a remainder certificate” | truncated series ring; Track V3 ban; CERTIFICATION_SCOPE | CAS users + ourselves |
| “Arb/Taylor models certify symbolic α” | numeric balls / real boxes; wrong object | validated-numerics users |
| “Holonomic bounds certify polygamma(\(k,z\))” | infinitely many poles; not D-finite | combinatorics/CAS |
| “V5 C0 match is remainder CERTIFIED / hop ZERO” | different field; `forbidden_ignore_remainder`; L-D | ourselves (R2, V5-G) |
| “Remainder CERTIFIED is hop ZERO” | schema forbids it; PROTOCOL | ourselves |
| “LEVEL_B coefficients imply LEVEL_C” | remainder missing | ourselves |
| “Silent α₀ not a pole is conservative” | class C; ASSUMPTION_POLICY | ourselves |
| “We restored G0016→G0013 LEVEL_C ZERO” | retracted `fb3b929`; remainder UNKNOWN | ourselves |
| “Formal / Lean certificate” | engine semantics; CERTIFICATION_SCOPE | ITP reviewer |
| “Timeout converted to CERTIFIED is conservative” | it is a false CERTIFIED | this engine’s contract |
| “This literature pack is a method result / publication letter” | no suite; GAP cell; status E | ourselves |

---

## Positioning sentence (not a title)

> Taylor remainder, Cauchy estimates, and the polar structure
> of polygamma are standard mathematics. Production CAS emit
> truncated series with an `O` token; ball-arithmetic libraries
> enclose numeric remainders; holonomic software bounds
> D-finite tails — none of which certifies a symbolic affine
> polygamma argument. This line asks whether those standard
> tools, routed fail-closed as RemainderCertificates under
> explicit assumption classes, can prove \(R_{N+1}(t)=O(t^{N+1})\)
> without silent genericity and without false CERTIFIED.
> Taylor remainder is not the contribution. Cauchy estimates
> are not the contribution. Polygamma poles are not the
> contribution. Track V5 C0 match is not the contribution.
> A systems contribution — machine-checkable remainder
> certificates for symbolic affine special-function arguments
> under explicit assumption classes — does not exist until a
> generic suite returns false CERTIFIED = 0. That experiment
> has not run. The cell is a GAP.
