# Failure taxonomy beyond first-order syntactic LGG

LGG = least general generalization of two terms by replacing disagreeing
*leaves/subtrees* with holes, reusing a hole when the same disagreement
recurs. Frozen implementation: `prototype/antiunify.py` @ `efc0924`.

## F1 — Shallow syntactic holes

- **Definition:** a generalization whose residual operators are trivial
  (product/sum of holes and constants) and do not name a reusable object.
- **Minimal example:** `-I*mu` vs `I*beta*mu` → `I*mu*theta`.
- **Why LGG fails scientifically:** the LGG exists and is correct as a
  generalization; it is not a *useful* abstraction.
- **Machinery:** quality/MDL filter, not a stronger unifier.
- **Eval:** useful LGGs rank above shallow ones without gold in the scorer.

## F2 — Algebraically equivalent, syntactically misaligned

- **Definition:** members are equal modulo a declared theory (C, A, AC,
  distributivity) but trees differ.
- **Minimal example:** `x*(y+z)` vs `x*y+x*z`; `(p+q)*V` vs `V*(q+p)`.
- **Why LGG fails:** different heads (`Mul` vs `Add`) ⇒ a single hole;
  commutative pairing can yield `2*theta` from `p+q` vs `q+p`.
- **Machinery:** canonicalization; anti-unification modulo A/C/AC.
- **Eval:** after declared-safe canon, LGG recovers the common form.
  Recovery via canon is **not** scientific invention.

## F3 — Operator-related families

- **Definition:** \(A_i = \mathcal O_i[F]\) with \(\mathcal O_i\) in
  {id, ∂/∂x, shift, permute}, and \(F\) possibly latent.
- **Minimal example:** `F(x)` and a finite difference; or `polygamma(0,z)`
  vs `polygamma(1,z)` interpreted as derivative, not as “order hole”.
- **Why LGG fails:** it substitutes the integer order (`polygamma(theta,z)`)
  and never states \(\psi^{(n+1)}=\partial_z\psi^{(n)}\).
- **Machinery:** operator-aware hypotheses; relation graph.
- **Eval:** certified obligations `A2 - dA1/dz = 0`, not just a shared head.

## F4 — Recurrence-related families

- **Definition:** members linked by a recurrence on an index/order.
- **Minimal example:** `polygamma(n,z)` vs `polygamma(n+1,z)` as
  \(\partial_z\), not as a free hole in the first argument.
- **Why LGG fails:** same as F3 at the syntactic level.
- **Machinery:** recurrence/operator templates; special-function identities
  only if the engine can prove them.
- **Eval:** operator obligation ZERO under declared sympy.diff semantics.

## F5 — Confluent families

- **Definition:** several non-degenerate expressions are specializations
  of one object that is singular on a diagonal (divided difference).
- **Minimal example:** `(f(x)-f(y))/(x-y)` (`x≠y`) vs a coincident branch.
- **Why LGG fails:** branch values have different tree shape from the
  difference quotient; identical-value Piecewise fold is B9, not LGG.
- **Machinery:** representation change; not unique LGG.
- **Eval:** explicit template + specialization maps; ZERO on each branch
  under declared assumptions. Limit laws that the parser cannot state stay
  UNKNOWN (not success).

## F6 — Representation change

- **Definition:** the *language* of the expression changes (Piecewise ↔ DD,
  components ↔ invariant basis).
- **Minimal example:** indexed `T(i,j)+T(j,i)` vs `2*S(i,j)` with `S` symmetric.
- **Why LGG fails:** it cannot invent a new head `S`.
- **Machinery:** search over mathematical languages; synthesis.
- **Eval:** reconstruction ZERO plus a declared representation type.

## F7 — Generator / basis invention

- **Definition:** many terms lie in a low-dimensional span, not related by
  substitution of leaves.
- **Minimal example:** three contractions that are one bilinear generator
  evaluated on different index pairs — wait, that *is* LGG of a Mul. A true
  F7 example is linear dependence with coefficients not visible as holes.
- **Why LGG fails:** span is not a term generalization.
- **Machinery:** linear algebra over a term basis; invariant theory.
- **Eval:** reconstruct each term as \(\sum c_\alpha G_\alpha\) with
  \(\dim\{G\}\ll n\) and residual ZERO.

## F8 — Reusable cross-task abstraction

- **Definition:** one master object compresses *multiple tasks*.
- **Minimal example:** the same `V(θ)G0(θ)V(θ)` on two different inputs.
- **Why LGG fails:** LGG is pairwise inside one expression.
- **Machinery:** library learning (DreamCoder/Stitch/babble).
- **Eval:** description-length on a held-out *task*, not a pair of subtrees.

## Summary

| Class | Unique LGG? | Standard algorithm? | Search? |
|---|---|---|---|
| F1 | yes, but junk | ranking / MDL | no |
| F2 | no (wrong tree) | AC-AU, canon | limited |
| F3–F4 | no (wrong object) | HO-AU / operators | yes |
| F5–F6 | no | none unique | yes |
| F7 | no | linear algebra / invariants | yes |
| F8 | no | library learning | yes |
