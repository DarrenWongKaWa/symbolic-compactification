# Owner: R12 — remainder-certification literature

Taylor remainder is **standard mathematics**. Cauchy estimates
are **standard mathematics**. Polygamma poles (DLMF 5.15) are
**standard mathematics**. None of these is novelty.

This directory is the literature pack for the **symbolic remainder
certification** line (not Track V6; not a revival of retracted
Track V5 LEVEL_C ZERO). It classifies methods that bound or
certify

```
f(α₀ + c t) = Σ_{r=0}^N f^{(r)}(α₀) (c t)^r / r!  +  R_{N+1}(t)
```

under **declared** analytic-domain hypotheses. A remainder
certificate is **not** a hop certificate: `CERTIFIED` remainder
does not mint hop `ZERO`.

The only *candidate* contribution — machine-checkable remainder
certificates for **symbolic affine** special-function arguments
under explicit assumption classes A/B (never silent C/D) — is a
**GAP** until a generic suite exists with false `CERTIFIED` = 0.
Track V5 C0 match is **not** that contribution.

No LLM. No paper directory. Publication letter is not issued
here (status remains E). Track D2 stays LOCKED.

## Documents

| file | role |
|---|---|
| `METHODS.md` | Taylor remainder, Cauchy estimates, polygamma (DLMF 5.15), CAS series/asymptotics, ball arithmetic, holonomic bounds, IR |
| `CLASSIFICATION.md` | each method: STANDARD MATHEMATICS \| STANDARD CAS TECHNIQUE \| SYSTEMS INTEGRATION \| POTENTIAL RESEARCH CONTRIBUTION (GAP) |
| `REFERENCES.bib` | citations used here |
| `HANDOFF.md` | SHA, files, residual risks |
| `__init__.py` | package stub |

## Frozen priors (cite, do not rewrite)

- Compactification proposer–verifier survey: `research/literature/`
- Certification scope: `research/verification/CERTIFICATION_SCOPE.md` (engine semantics, not formal proof; truncated series-coefficient matching is not Level-1 ZERO)
- Track V methods: `research/scalable_verification/literature/` (`SERIES_LOCAL`, special-function tables)
- Track V3 series/removable singularities: `research/iterated_confluence/literature/`
- Track V4 one-pager: `research/polygamma_confluence/literature/CLASSIFICATION.md` (polygamma derivative, Taylor, Laurent \(t^0\) already **known standard**)
- Track V5 coefficient-space Laurent: `research/coefficient_laurent/literature/` (sparse Laurent and polygamma Taylor already **not novelty**; C0 lemma is not hop ZERO)
- Track V5 remainder sufficiency: `research/coefficient_laurent/remainder/` (`remainder_ok` False on symbolic α → UNKNOWN)
- V5 close: `research/PROGRAM_STATUS_V5.md`, `research/coefficient_laurent/TRACK_V5_CLOSED.md` (CASE L-D; remainder UNKNOWN)
- This line’s freeze: `research/remainder_certification/{PROBLEM_STATEMENT,ASSUMPTION_POLICY,PROTOCOL,schema}.py`

Do not claim this repo discovered Taylor’s theorem, Cauchy estimates,
or polygamma poles. Do not restore `fb3b929` LEVEL_C ZERO. Do not
unlock Track D2.
