# Holomorphic Taylor remainder on affine paths

R1 — complex-analysis formalism. Isolated remainder-certification
line. Not Track V6. No LLM. Track D2 LOCKED.

This note records **classical** one-variable theorems and the
**verifier checks** they induce. None of the theorems is claimed as
novelty. The package goal is a **proof condition sufficient for
symbolic exact-limit certification**, not a numerically tight bound.

Remainder `CERTIFIED` is **not** hop `ZERO`. Hop composition is out
of scope (schema `remainder_cannot_be_hop_zero`).

Cauchy majorants (`M < ∞` on a circle) are **R4**. Polygamma poles
are **R2**. This package defines the predicates those agents must
satisfy; it does not compute `M` and does not locate polygamma poles.

Class-C genericity (`z0` is not a pole “because generic”) is
`ASSUMPTION_REQUIRED`, never `CERTIFIED`. See
`research/remainder_certification/ASSUMPTION_POLICY.md`.

---

## Notation

Let \(f\) be a function of one complex variable. Fix \(z_0,c\in\mathbb{C}\)
with \(c\) independent of the perturbation parameter \(t\), and write

```
z(t) = z0 + c t.
```

Open disk: \(D(z_0,\rho)=\{z:|z-z_0|<\rho\}\) with \(\rho\in(0,+\infty]\).
The case \(\rho=+\infty\) is the whole plane (entire functions).

For an integer \(N\ge 0\), the Taylor polynomial of \(f\) at \(z_0\)
along the affine path is

```
T_N(t) = Σ_{r=0}^N f^{(r)}(z0) (c t)^r / r!.
```

The remainder is \(R_{N+1}(t)=f(z_0+ct)-T_N(t)\). The **sufficient
proof condition** used for exact-limit certification is

```
R_{N+1}(t) = O(t^{N+1})    as t → 0,  |t| < δ.
```

An explicit Cauchy majorant for the implied constant is stronger and
is not required here (R4). “Sufficiently small \(t\)” with **no**
existence certificate for some \(\delta>0\) is forbidden
(`ASSUMPTION_POLICY.md`).

---

## T1. Taylor theorem for holomorphic functions

**Statement.** Let \(f\) be holomorphic on \(D(z_0,\rho)\) with
\(\rho>0\). Then for every \(z\in D(z_0,\rho)\) and every integer
\(N\ge 0\),

```
f(z) = Σ_{n=0}^N f^{(n)}(z0)/n! (z-z0)^n  +  R_{N+1}^Taylor(z),
```

the power series \(\sum_{n\ge 0} f^{(n)}(z_0)(z-z_0)^n/n!\) converges
to \(f(z)\) on the whole disk, and \(R_{N+1}^Taylor(z)=O((z-z_0)^{N+1})\)
as \(z\to z_0\). Equivalently \(f^{(n)}(z_0)=n!\,a_n\) with Cauchy
coefficients

```
a_n = (1/(2πi)) ∮_{|ζ-z0|=r} f(ζ)/(ζ-z0)^{n+1} dζ
```

for any \(0<r<\rho\).

**Hypotheses the verifier must discharge.**

| id | check |
|---|---|
| `H1_holomorphic_disk` | A positive-radius disk \(D(z_0,\rho)\) on which \(f\) is holomorphic is **declared** (class A) or **derived** from a certified distance to the nearest singularity (class B). |
| `H4_expansion_order` | \(N\) is a nonnegative integer (not a boolean, not symbolic, not negative). |

**What the verifier must not do.** Infer holomorphy at \(z_0\) from
Zariski-genericity of parameters (class C). That check is
`H5_no_class_cd`.

**Citations (classical; not novelty).** Cauchy’s integral formula and
the resulting Taylor expansion in one complex variable: Ahlfors,
*Complex Analysis*, 3rd ed., McGraw-Hill, 1979, Ch. 4 (complex
integration; Taylor’s theorem). Conway, *Functions of One Complex
Variable*, 2nd ed., Springer, 1978, Ch. IV (Cauchy theory and Taylor
expansion). Rudin, *Real and Complex Analysis*, 3rd ed., McGraw-Hill,
1987, Ch. 10. Historical source: Cauchy’s 1831 Turin memoir on power
series of holomorphic functions (textbook presentations above are the
working references).

**Code.** `holomorphic_disk(z0, rho)`; remainder form `O(t^{N+1})`.

---

## T2. Cauchy estimates

**Statement.** If \(f\) is holomorphic on \(D(z_0,\rho)\) and
\(|f(\zeta)|\le M<\infty\) on the circle \(|\zeta-z_0|=r\) with
\(0<r<\rho\), then

```
|f^{(n)}(z0)| ≤ n! M / r^n,    n ≥ 0.
```

A corresponding majorant for the Taylor remainder on \(|z-z_0|\le r'<r\)
follows (see T3). **Finite \(M\)** is an extra hypothesis: it is not
implied by holomorphy on the open disk alone until a compact circle
strictly inside the disk is chosen.

**Hypotheses the verifier must discharge (R4, not R1).**

| id | check |
|---|---|
| `H_cauchy_circle` | A radius \(r\) with \(0<r<\rho\) is produced. The Cauchy circle is **strictly inside** the holomorphic disk. Taking \(r=\rho\) is illegal if a singularity lies on \(|z-z_0|=\rho\). |
| `H_cauchy_finite_M` | \(M<\infty\) is proved, not sampled. `ASSUMPTION_POLICY.md` forbids inserting \(M<\infty\) without a finiteness proof. |

**This package.** Defines `CauchyBoundRequest` and
`CauchyBoundProvider` for R4. Does **not** compute \(M\), does not
pick a numeric \(r\), and does not emit a Cauchy majorant. The
`O(t^{N+1})` condition (T6) uses existence of some compact subdisk,
which follows from T1+T3 once `H1` and `H3` hold; it does not need
the value of \(M\).

**Citations.** Ahlfors 1979, Ch. 4 (Cauchy’s estimates). Conway 1978,
Ch. IV. Rudin, *Real and Complex Analysis*, 3rd ed., 1987,
Thm. 10.26 (Cauchy’s estimates).

---

## T3. Contour / Cauchy-integral remainder

**Statement.** Under T1, for \(0<r<\rho\) and \(|z-z_0|<r\),

```
R_{N+1}^Taylor(z)
  = (z-z0)^{N+1}/(2πi)
    ∮_{|ζ-z0|=r} f(ζ) / ((ζ-z0)^{N+1} (ζ-z)) dζ.
```

On the affine path \(z=z_0+ct\) with \(|c|\,|t|<r\),

```
R_{N+1}(t)
  = (c t)^{N+1}/(2πi)
    ∮_{|ζ-z0|=r} f(ζ) / ((ζ-z0)^{N+1} (ζ-z0-c t)) dζ.
```

If \(|f|\le M\) on the circle (T2), then for \(|ct|\le r'<r\),

```
|R_{N+1}(t)| ≤ M |c t|^{N+1} / (r^N (r-r')).
```

Hence \(R_{N+1}(t)=O(t^{N+1})\) as \(t\to 0\). The displayed majorant
is R4’s object. The **integral formula itself** is the holomorphic
justification of the \(O(\,\cdot\,)\) claim.

**Hypotheses the verifier must discharge.**

| id | check |
|---|---|
| `H1_holomorphic_disk` | as in T1 |
| `H3_path_stays_inside` | \(|c|\,\delta<r<\rho\) for some \(\delta>0\) (or \(\rho=+\infty\)). |
| `H4_expansion_order` | as in T1 |

**Citations.** Same as T1: the remainder is the tail of the geometric
series in Cauchy’s integral formula (Ahlfors Ch. 4; Conway Ch. IV;
Rudin RCA Ch. 10). Not a new formula.

**Code.** Certificate `remainder_form` may record
`cauchy_integral` as a justification alongside `O(t^{N+1})`. The
contour integral is not evaluated.

---

## T4. Lagrange remainder on a real segment

**Statement (real variable).** Let \(I\subset\mathbb{R}\) be an
interval, \(a\in I\), and let \(g:I\to\mathbb{C}\) be \(N+1\) times
differentiable. Then for \(x\in I\) there exists \(\xi\) strictly
between \(a\) and \(x\) such that, **when \(g\) is real-valued**,

```
g(x) = Σ_{r=0}^N g^{(r)}(a)/r! (x-a)^r
       + g^{(N+1)}(ξ) (x-a)^{N+1} / (N+1)!.
```

**Restriction to a holomorphic \(f\).** Let \(t\) be **real**, and
set \(g(t)=f(z_0+ct)\). If \(f\) is holomorphic on a neighborhood of
the real segment \(\{z_0+c s:s\text{ between }0\text{ and }t\}\), then
\(g\) is \(C^\infty\) on a real interval about \(0\), \(g^{(r)}(0)=
c^r f^{(r)}(z_0)\), and Lagrange applies to \(\mathrm{Re}\,g\) and
\(\mathrm{Im}\,g\) separately. If \(f\) is real on that segment, a
single real \(\xi\) exists for \(g\).

**The mean-value theorem fails in \(\mathbb{C}\).** There is in
general **no** \(\xi\) on the complex segment \([z_0,z_0+ct]\) with
\(f(z_0+ct)-f(z_0)=f'(\xi)\,ct\). The verifier **must not** apply
Lagrange with complex \(t\) or with \(\xi\) claimed in \(\mathbb{C}\)
along the segment.

**Hypotheses the verifier must discharge.**

| id | check |
|---|---|
| `H_lagrange_t_real` | \(t\) is declared real (class A). |
| `H_lagrange_segment` | The real segment from \(z_0\) to \(z_0+ct\) lies in the holomorphic disk (follows from `H3` when \(t\in\mathbb{R}\) and \(|t|<\delta\)). |

If either fails, Lagrange is **not applicable**. The holomorphic
Cauchy remainder (T3) remains the default justification.

**Citations.** Lagrange, *Théorie des fonctions analytiques*, 1797
(real Taylor remainder). Rudin, *Principles of Mathematical
Analysis*, 3rd ed., McGraw-Hill, 1976, Thm. 5.15 (Taylor’s theorem
with Lagrange remainder for real functions). Apostol,
*Mathematical Analysis*, 2nd ed., Addison-Wesley, 1974 (real Taylor
theorem). Complex MVT failure: any first course in complex analysis
(e.g. Ahlfors Ch. 2; Conway).

**Code.** `lagrange_remainder_applicable(t_is_real, segment_in_domain)`.

---

## T5. Integral remainder on a real segment

**Statement.** Under the same real-variable hypotheses as T4 (or
merely \(g^{(N+1)}\) continuous on the interval),

```
g(x) = T_N(x) + 1/N! ∫_a^x g^{(N+1)}(s) (x-s)^N ds.
```

For \(g(t)=f(z_0+ct)\) with **\(t\) real** and the segment inside the
holomorphic disk,

```
R_{N+1}(t)
  = c^{N+1}/N! ∫_0^t f^{(N+1)}(z0+c s) (t-s)^N ds
  = (c t)^{N+1}/N! ∫_0^1 f^{(N+1)}(z0+c t u) (1-u)^N du.
```

This identity is calculus along a \(C^1\) path in \(\mathbb{C}\); it
does not require Lagrange’s \(\xi\). It **does** require a real
parameter interval. For complex \(t\) in a disk, use T3.

**Hypotheses.** Same as T4 (`H_lagrange_t_real`,
`H_lagrange_segment`).

**Citations.** Apostol, *Mathematical Analysis*, 2nd ed., 1974
(Taylor theorem with integral remainder). Apostol, *Calculus*,
Vol. I (integral form of the remainder). Standard real analysis;
not novelty.

**Code.** `integral_remainder_applicable` shares T4’s predicate.

---

## T6. Distance to the nearest singularity as a disk radius

**Statement.** Let \(\Omega\) be a domain on which \(f\) is
holomorphic, \(z_0\in\Omega\), and let \(d=\mathrm{dist}(z_0,
\mathbb{C}\setminus\Omega)\in(0,+\infty]\). Then \(f\) is holomorphic
on the open disk \(D(z_0,d)\), and the Taylor series of \(f\) at
\(z_0\) has radius of convergence **at least** \(d\). If
\(\mathbb{C}\setminus\Omega\) is nonempty and \(f\) cannot be
continued holomorphically through any point of the boundary circle
(e.g. an isolated singularity on that circle), the radius equals
\(d\).

In particular, if the singularities of \(f\) are isolated and
\(d=\inf\{|z_0-s|:s\text{ singular}\}\) with \(d>0\), the **open**
disk of radius \(\rho=d\) is an admissible holomorphic disk for T1
(the singularity on the circle is not in the open disk).

**Cauchy circle vs open disk.** A Cauchy estimate (T2) needs
\(0<r<d\), strictly. R1 may set the holomorphic-disk radius equal to
\(d\). R1 does **not** choose \(r\) or \(M\).

**If \(d=0\).** Either \(z_0\) is itself a singularity, or
singularities accumulate at \(z_0\). Then no positive-radius
holomorphic disk exists: remainder verdict `NONANALYTIC`, not
`CERTIFIED`, and not hop `ZERO`.

**Affine paths and “crossing for arbitrarily small \(t\).”** The
image of \(|t|<\delta\) under \(z_0+ct\) is the disk
\(|z-z_0|<|c|\delta\) (a point if \(c=0\)). For isolated
singularities, the path hits a singularity for arbitrarily small
\(|t|\) if and only if \(d=0\). If \(d>0\) and \(c\) is finite, the
first hit occurs at \(|t|=d/|c|\) (or never, if \(c=0\) or
\(d=+\infty\)), so a positive \(\delta\) exists (T7).

**Hypotheses the verifier must discharge.**

| id | check |
|---|---|
| `H7_singularity_at_expansion` | If \(d=0\) or the declared \(\rho=0\), emit `NONANALYTIC`. |
| `H1_holomorphic_disk` | If \(d>0\) is class A/B, \(\rho=d\) is a derived open-disk radius (class B). |
| distance source | Distance for polygamma is R2. R1 only converts a **given** positive distance into a disk radius. |

**Citations.** Radius of convergence of a power series: Ahlfors 1979,
Ch. 2; Conway 1978, Ch. III. Identification with distance to the
complement of a holomorphic domain / nearest isolated singularity:
Ahlfors 1979, Ch. 5; Conway 1978, Ch. V; Rudin RCA Ch. 10–12.
Weierstrass’s theory of analytic continuation (textbook form in
Ahlfors Ch. 8). Not novelty.

**Code.** `open_disk_radius_from_distance(distance)`;
`DistanceToSingularity`; interface `SingularityDistanceProvider` (R2).

---

## T7. Affine holomorphic remainder (sufficient proof condition)

**Statement.** Let \(N\ge 0\) be an integer. Let \(f\) be holomorphic
on \(D(z_0,\rho)\) with \(\rho\in(0,+\infty]\). Let \(c\in\mathbb{C}\)
be finite and independent of \(t\). Let \(\delta>0\) satisfy
\(|c|\,\delta<\rho\) (vacuous if \(\rho=+\infty\)). Then for all
\(|t|<\delta\),

```
f(z0 + c t) = Σ_{r=0}^N f^{(r)}(z0) (c t)^r / r!  +  R_{N+1}(t)
```

with \(R_{N+1}(t)=O(t^{N+1})\) as \(t\to 0\).

**Existence of \(\delta\) (mandatory witness).** If \(\rho>0\) and
\(c\) is finite, the explicit choice

```
δ = ρ / (2 (1 + |c|))
```

satisfies \(|c|\,\delta\le\rho/2<\rho\). If \(\rho=+\infty\), any
finite positive \(\delta\) works (the code uses \(\delta=1\)). The
certificate must record the witness. It must not say “for
sufficiently small \(t\)” with an empty `required_small_t_condition`.

This \(\delta\) is **not** claimed to be maximal. Maximality is
irrelevant to exact-limit certification.

**Little-o vs big-O.** \(O(t^{N+1})\) is enough to match a finite
Laurent window through \(t^N\) (or through \(t^0\) after a polar
prefactor of order \(\le N\), which is order algebra: R5). No
numeric tightness is required.

**Hypotheses — full verifier checklist.**

| id | check | fail closed |
|---|---|---|
| `H1_holomorphic_disk` | Holomorphic on \(D(z_0,\rho)\), \(\rho>0\) or \(\rho=+\infty\), source class A or B | `UNKNOWN` if missing; `ASSUMPTION_REQUIRED` if source is class C |
| `H2_affine_path` | \(z(t)=z_0+ct\) with \(z_0,c\) independent of \(t\); \(c\) finite | `UNKNOWN` if not affine; `NONANALYTIC` if \(c\) infinite |
| `H3_path_stays_inside` | A \(\delta>0\) with \(|c|\,\delta<\rho\) is recorded | `UNKNOWN` if no witness (forbidden silent “small \(t\)”) |
| `H4_expansion_order` | \(N\in\mathbb{N}\cup\{0\}\) | `UNKNOWN` |
| `H5_no_class_cd` | No undeclared genericity / human physics assumption | `ASSUMPTION_REQUIRED` |
| `H6_remainder_order` | Conclude \(R_{N+1}(t)=O(t^{N+1})\) only if H1–H5 hold | never upgrade |
| `H7_singularity_at_expansion` | \(d=0\) or \(\rho=0\) or a declared excluded point lies in the open disk | `NONANALYTIC` |
| `H8_not_hop_zero` | Remainder verdict is never hop `ZERO` | structural |

**Entire functions.** If \(f\) is entire (class A named family:
`exp`, `sin`, `cos`, `sinh`, `cosh`, polynomials, or an explicit
`entire` declaration), \(\rho=+\infty\), `domain_conditions` include
`entire`, and H1 holds without a pole-exclusion lemma.

**Named branch / pole at a classical point (not polygamma).** For
`log` (and `sqrt`), \(0\) is a classical singularity. If the declared
open disk contains \(0\), the verdict is `NONANALYTIC`. Locating
**polygamma** poles is R2 and is not performed here.

**Citations.** T7 is the specialization of T1+T3 to the affine path
\(z_0+ct\). It is not a new theorem. Ahlfors Ch. 4; Conway Ch. IV;
Rudin RCA Ch. 10; plus the elementary bound \(|c|\,\rho/(2(1+|c|))
\le\rho/2<\rho\).

**Code.** `affine_taylor_remainder_certificate`,
`path_stays_inside(z0, c, delta, rho)`, `staying_delta(c, rho)`.

---

## What this package will not do

- Compute Cauchy bounds, max-modulus, or a numeric \(M\) (R4).
- Certify polygamma poles or \(\alpha_0\notin\mathbb{Z}_{\le 0}\) (R2).
- Insert class-C genericity or class-D physics positivity.
- Map remainder `CERTIFIED` to hop `ZERO` (R8 / hop composer).
- Claim numerical tightness or a maximal disk.
- Treat LEVEL B coefficient agreement as a remainder proof.

---

## Mapping onto `RemainderCertificate`

| field | filled from |
|---|---|
| `domain_conditions` | `entire` and/or `holomorphic_disk(\|z-z0\|<ρ)` and the path condition; never empty on `CERTIFIED` |
| `analyticity_certificate` | disk, source class, theorem ids T1/T3/T7 |
| `distance_to_singularity` | given \(d\) if any; else empty (R2 may fill) |
| `remainder_form` | `O(t^{N+1})`; optionally `cauchy_integral`; `lagrange` / `integral_real_segment` only when T4/T5 apply |
| `bound` | left empty for R4 |
| `required_small_t_condition` | explicit `|t|<δ` with the witness \(\delta\) |
| `assumptions_used` | class A/B only on a `CERTIFIED` path |
| `proof_dependencies` | `T1_holomorphic_taylor`, `T3_cauchy_integral_remainder`, `T7_affine_holomorphic_remainder`, and T4/T5/T6 when used |
| `verdict` | `CERTIFIED` / `ASSUMPTION_REQUIRED` / `NONANALYTIC` / `UNKNOWN` |
| `neighborhood_verdict` | `CERTIFIED_NEIGHBORHOOD` iff H1 and H3 hold; never hop `ZERO` |

Interfaces for other agents: `CauchyBoundProvider` (R4),
`SingularityDistanceProvider` (R2).

---

## Named identifiers (code)

Theorems: `T1_holomorphic_taylor`, `T2_cauchy_estimates`,
`T3_cauchy_integral_remainder`, `T4_lagrange_real_segment`,
`T5_integral_remainder_real_segment`,
`T6_radius_equals_distance_to_singularity`,
`T7_affine_holomorphic_remainder`.

Checks: `H1_holomorphic_disk`, `H2_affine_path`,
`H3_path_stays_inside`, `H4_expansion_order`, `H5_no_class_cd`,
`H6_remainder_order`, `H7_singularity_at_expansion`,
`H8_not_hop_zero`. Lagrange extras: `H_lagrange_t_real`,
`H_lagrange_segment`. Cauchy extras (R4): `H_cauchy_circle`,
`H_cauchy_finite_M`.
