# Remainder numeric sanity (R11)

High-precision samples of remainder \(R_{N+1}(t)/t^{N+1}\) as \(t\to 0\)
for \(f(z_0 + c t)\) after Taylor order \(N\).

This package is **not a verifier**. Numeric agreement is never
`CERTIFIED` and never `ZERO`. Strong mismatch is
`EXACT_INVESTIGATION` for an exact path only; disagreement does
**not** mint `NONANALYTIC`.

```python
from research.remainder_certification.numeric import numeric_probe

numeric_probe(f, z0, c, n)  # "agree" | "disagree" | "undecided"
```

Probe only parameter points that satisfy **declared** assumptions.
Timeout / parse / size-guard / undeclared spectators → `undecided`.
No LLM.
