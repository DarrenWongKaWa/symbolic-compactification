# Remainder sufficiency (Track V5-G)

No LLM. This package decides whether a Laurent expansion of a
rational × polygamma atom through `t^0` has a remainder that vanishes
at `t = 0`. It is not a hop verifier: `remainder_ok is False` means
UNKNOWN, never NONZERO.

```python
from research.coefficient_laurent.remainder import remainder_ok, required_pmin
```

## Why series to t^0 is enough

Let `t` be the degeneration coordinate and

```
A(t) = R(t) * polygamma(n, z(t)),    z(t) = α + β t
```

with `R` rational and `α, β` independent of `t`.

Polygamma (order `n >= -1`) is meromorphic, with poles only at
nonpositive integers of the argument. (Order `n <= -2` is entire.)

**Certified regular argument.** If `α = z(0)` is not in
`{0, -1, -2, …}`, then `polygamma(n, z(t))` is holomorphic at `t = 0`.
The only possible pole of `A` at the origin is the rational pole of
`R`, of some order `pmin`. Then

```
A(t) = Σ_{k = pmin}^{∞} c_k t^k
```

and the tail after the constant term is

```
A(t) − Σ_{k = pmin}^{0} c_k t^k = Σ_{k ≥ 1} c_k t^k = O(t) → 0
```

as `t → 0`. Positive powers do not contribute to a regularized limit:
LEVEL B cancels `t^{<0}`, LEVEL C matches `t^0` to the diagonal target.
Hence the required window is `t^{pmin} … t^0` (`required_pmin = pmin`,
`REQUIRED_PMAX = 0`).

**Possible polygamma pole.** If `z(0)` might be a nonpositive integer,
polygamma may add up to `n+1` extra negative powers. A rational-only
`pmin` need not bound the valuation, so the “remainder” after that
truncation may still contain polar terms. `remainder_ok` is False and
callers must set `remainder_verdict = UNKNOWN`.

Toy checks: `z = 1+t` is regular (`α = 1`); `z = t` hits the pole
`α = 0`.

Affine in `t` is required. Symbolic `α`, non-affine `z`, or size-guard
failure are UNKNOWN.
