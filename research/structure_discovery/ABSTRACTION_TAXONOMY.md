# Scientific abstraction taxonomy (D0–D6)

Structure is not “shorter.” Each level has an operational test.

## D0 — Local algebra

- **Definition:** factor, expand, cancel, collect that do not introduce a
  reusable named object.
- **Positive:** `(x-1)*(x+1)` from `x**2-1`.
- **Negative:** naming the whole expression `Phi := E`.
- **Eval:** transform applied, no typed H required.

## D1 — Structural regrouping

- **Definition:** merge identical sums, expose a common factor, group a
  permutation of already-written terms without a generator name.
- **Positive:** `Sum(K*a)+Sum(K*b) → Sum(K*(a+b))`.
- **Negative:** dropping a Piecewise branch.
- **Eval:** engine transform ZERO.

## D2 — Reusable kernel discovery

- **Definition:** a repeated subexpression is identified as one kernel used
  ≥2 times.
- **Positive:** `K(n)*a(n)+K(n)*b(n)` with kernel `K(n)`.
- **Negative:** two similar poles `1/(x-a)` and `1/(x-a-d)` treated as one K.
- **Eval:** gold type `repeated_kernel` and/or certified factorisation.

## D3 — Master-object discovery

- **Definition:** one auxiliary generates several repeated objects
  (specializations, derivative family, shared thermal/spectral master).
- **Positive:** `G(a)+G(b)+G(c)`; `polygamma(0,z)+polygamma(1,z)`.
- **Negative:** `F(x)+G(x)+H(x)` (independent heads).
- **Eval:** gold type `master_function` / `derivative_family` / `spectral_family`.

## D4 — Representation change

- **Definition:** the mathematical *language* changes: Piecewise → one object;
  difference quotient → divided difference; branches → generating function.
- **Positive:** `(f(x)-f(y))/(x-y)` as DD; identical-value Piecewise → value.
- **Negative:** `Piecewise((x,x>0),(-x-1,True))` as `Abs(x)`.
- **Eval:** type match; ZERO only if the new language is identity-equivalent
  under engine semantics.

## D5 — Scientific generator discovery

- **Definition:** symmetry-adapted basis, invariant generator, orbit of an
  indexed tensor, low-dimensional generating set.
- **Positive:** `F(n,m)+F(m,n)` as a swap orbit.
- **Negative:** `F(n,m)+2*F(m,n)` as an equal-weight orbit.
- **Eval:** type `permutation_orbit` / `symmetry_invariant` / `tensor_generator`;
  equal-weight reconstruction ZERO iff the orbit is genuine.

## D6 — Downstream scientific leverage

- **Definition:** the new form makes a further reasoning step easier
  (symmetry, limit, poles, scaling, channels). Not necessarily a rewrite.
- **Positive:** orbit form makes index-swap invariance immediate.
- **Negative:** a prettier name with no extra reasoning handle.
- **Eval:** frozen downstream probe or human rubric. **Not claimed in v1.**
