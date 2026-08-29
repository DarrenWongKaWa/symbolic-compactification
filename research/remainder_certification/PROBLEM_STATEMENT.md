# Problem statement — symbolic remainder certification

This is **not Track V6**. It is an independent mathematical-verification
line. Its result MAY later become a verifier backend. It MUST NOT be
optimized toward restoring the retracted Track V5 LEVEL_C ZERO.

No LLM proposer calls. No Guo identity table. Track D2 stays **LOCKED**.

## Frozen parent

Branch parent: `84b412d` (V5 remainder fail-close).
Reviews merge: `9bff79b`. Unsound L-A: `fb3b929` (retracted).
V4 close: `248d247`. V3 soundness: `d2752f9`.

Primary frozen hop `G0016 → G0013` is **UNKNOWN LEVEL_B**:

| piece | verdict |
|---|---|
| negatives \(t^{-6}\ldots t^{-1}\) | ZERO |
| constant term vs G0013 | ZERO |
| remainder | UNKNOWN |
| hop | UNKNOWN |
| families | 7/7 FAMILY_UNKNOWN |
| D2 | LOCKED |
| publication | E |

Finite coefficient agreement does **not** prove an exact limit.

## Central question

Can finite local Taylor/Laurent expansions of special functions with
symbolic affine arguments be equipped with machine-checkable remainder
certificates strong enough to justify exact limit claims?

Formally, for

```
f(α₀ + c t)
  = Σ_{r=0}^N f^{(r)}(α₀) (c t)^r / r!  +  R_{N+1}(t)
```

the verifier needs a checkable condition that

```
R_{N+1}(t) = O(t^{N+1})
```

(or stronger) under **declared** analytic-domain hypotheses.

The motivating polygamma affine class is

```
α(t) = α₀ + c t
α₀ ~ 1/2 + β(γ ± i(μ−ε))/(2π)
f(z) = polygamma(k, z)
```

The **method must be generic**. That form is a test class, not a
design oracle. Do not use a desired Guo ZERO to shape theorems.

## Proof levels (unchanged)

- **LEVEL A** — local expansion generated. Not hop ZERO.
- **LEVEL B** — all required explicit Laurent coefficients certified.
- **LEVEL C** — remainder certified sufficiently for the exact limit.

Only LEVEL C may promote an edge to ZERO.

Never infer `LEVEL_B ⇒ LEVEL_C`.

## RemainderCertificate verdicts

A remainder certificate is **not** a hop certificate.

```
CERTIFIED | ASSUMPTION_REQUIRED | NONANALYTIC | UNKNOWN
```

`CERTIFIED` means the atom remainder order is proved under the
assumptions listed on the certificate. It does not mint hop ZERO.
Hop ZERO requires later composition of negatives, C0, and **every**
required atom remainder, plus independent review (program §12, §18).

`ASSUMPTION_REQUIRED` is a successful fail-closed outcome, not a
license to insert genericity.

`UNKNOWN` is a successful verifier outcome when hypotheses are
unproved.

`NONANALYTIC` means the expansion hypotheses fail on the path.

## What this line will not do

- Revive `fb3b929` LEVEL_C ZERO.
- Silently assume `α₀ ∉ {0,−1,−2,…}`.
- Insert “generic parameters” or physics positivity.
- Rerun the 12 ell-hops before the primary remainder question is
  decided.
- Unlock Track D2 on an edge ZERO.
- Create Remainder V2/V3/V4 without a new scientific idea.

See `ASSUMPTION_POLICY.md`.
