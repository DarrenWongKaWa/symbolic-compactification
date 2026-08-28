# Track V3 capability boundary

Track D2 remains **LOCKED**. Case **I-D**.

## What is missing

Not path enumeration. The 5-branch lattice is faithfully covered by
one-parameter edges between actual source `G####` members (I-E does not
hold). No intermediate interpolation was required.

The missing object is a **decision procedure for one-parameter confluence
of ~300–570-op polygamma kernels** after exact spectator peel.

Certified two-member scale (Track V, reused here):

| pair | full ops | local ops after mul-args peel | verdict | time |
|---|---:|---:|---|---:|
| G0005 → G0004 | 176 | 172 | ZERO (series) | ~13 s |
| G0009 → G0008 | 176 | 172 | ZERO (series) | ~13 s |

Five-branch hops after the same peel:

| hop | full ops | local ops | 25 s | 90 s |
|---|---:|---:|---|---|
| G0013 → G0012 | 333 | 327 | timeout UNKNOWN | timeout UNKNOWN |
| G0016 → G0013 | 573 | 567 | timeout UNKNOWN | not re-tried |

`h1(a,m,n) h1(b,ell,m) h1(c,n,ell)` peels exactly (reconstruction
`S*K = E`) but removes only ~6 ops. The kernel remains a polygamma
sum, not a 176-op two-member kernel.

## What is not the bottleneck (this track)

- Path independence / noncommuting multivariable limits: never reached
  on frozen Guo, because required local edges stayed UNKNOWN (not I-C).
  Reviewer 2: two PATH_ZERO paths to the same source member must **not**
  auto-promote to CONSISTENT_ZERO (counterexample `xy/(x^2+y^2)`).
  Rescore now leaves that obligation UNKNOWN until `check_two_paths`.
- Missing explicit latent F / Hermite recurrence: not discharged, but
  the first blocking obligation is already the one-parameter polygamma
  hop.
- Decomposition invalid: no. Source branches populate the 3-index
  coincidence lattice.

## Research decision

**STOP_VERIFICATION_LINE** for iterated-path verifier increments.

Do not build a larger path enumerator or a longer `sympy.series` timeout
as the next program. 90 s on the 327-op hop was still UNKNOWN.
Do not open Track D2. Do not add Guo-specific polygamma identities.

If verification research continues later, the next *object* is a generic
special-function local prover for polygamma confluence / repeated
argument, still without Guo tables — that is a new track, not V3.
