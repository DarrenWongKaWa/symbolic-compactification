# Assumption policy — symbolic remainder certification

This policy is a freeze. Implementations that silently add class-C
or class-D assumptions cannot emit `CERTIFIED` and cannot promote
hop ZERO.

## Classes

### A. DECLARED

Assumptions already present in the source or problem statement.
Examples: symbol `real=True` flags that the parser actually attached;
explicit hypotheses passed into the certifier; reconstruction
identities already proved (`S * K = E`).

Declared assumptions MUST be listed on the certificate
(`assumptions_used`) and hashed (`assumptions_hash`).

### B. DERIVED

Statements proved from class A by exact symbolic reasoning (no
numeric sampling, no “almost all points”). Example: if `Im(z)` is
proved nonzero from declared symbols, then `z` is not a real
nonpositive integer.

Derived steps MUST appear in `proof_dependencies`.

### C. GENERICITY ASSUMPTION

Statements true on a Zariski-open set but not identities, and not
declared. Examples:

```
α₀ ∉ {0, −1, −2, …}
β ≠ 0
μ − ε(ℓ) ≠ 0
“generic parameters avoid poles”
```

Class C **may not be silently inserted**. If a theorem needs C and
C is not declared, the remainder verdict is `ASSUMPTION_REQUIRED`,
never `CERTIFIED`.

### D. HUMAN_REQUIRED

A physical or mathematical assumption not encoded in the frozen
problem (e.g. inverse temperature `β > 0`, energy arguments of the
form `1/2 + iE` never hitting poles). Record the exact predicate.
Do not ask for a human assumption unless it is mathematically
necessary. Do not encode it as ZERO.

## Promotion rules

| remainder needs | remainder verdict | hop ZERO allowed? |
|---|---|---|
| only A and B | may be `CERTIFIED` | only after LEVEL C composition + review |
| any C not declared | `ASSUMPTION_REQUIRED` | **no** |
| any D | `ASSUMPTION_REQUIRED` | **no** |
| domain proof fails | `UNKNOWN` or `NONANALYTIC` | **no** |
| LEVEL B coefficients only | remainder still required | **no** |

`ZERO_UNDER_DECLARED_ASSUMPTIONS` is a **hop** label. It may be
used only if every analytic-domain requirement of every required
atom follows from A or B. This line does not introduce a fourth
hop verdict in the V5 schema; hop ZERO already means that. Do not
add a side channel.

## Forbidden silent insertions

The following are class C/D unless they are already on the
declaration list:

- positive `beta`
- nonzero `gamma`
- real `mu` beyond the parser’s existing `real=True`
- energy differences nonzero
- argument not a polygamma pole
- `M < ∞` in a Cauchy bound without a finiteness proof
- real-only path when the perturbation is complex
- “sufficiently small t” without an existence certificate for
  some `δ > 0`

Subagent R10 must test these.

## Certificate obligation

Every `RemainderCertificate` lists:

1. `domain_conditions` (nonempty; “none needed” must be justified)
2. `assumptions_used` (class A, and B as derived lemmas)
3. `analyticity_certificate` (or why it is missing)
4. `verdict`

Omitting domain conditions is a schema error, not UNKNOWN.
