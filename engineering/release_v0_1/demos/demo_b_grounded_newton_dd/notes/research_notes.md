# Research notes

This workspace instantiates one member of the already-frozen `C9H4` reference
object as a field-use demonstration. It demonstrates grounding, an explicit
proof obligation, and exact verification. It is **not** a discovery result,
does not show that an AI or search procedure found the Newton representation,
and does not certify the full symbolic `C9H4` family.

The shared latent kernel is

```text
F(z) = 1/sqrt(z)
```

The demo applies the following fixed rational substitution to frozen source
member `M9H1`:

```text
alpha = 1/3
x1_old = 0
x1_new = 1
x2_hold = 1
```

The resulting nodes are `10/9` and `25/9`; both are positive rational
constants and their difference is `5/3`. Every displayed denominator factor
is therefore a fixed nonzero constant. `scale` is a harmless real bookkeeping
factor multiplying both sides; the equality also holds when `scale = 0`.

The expected aggregate result is `ZERO` only when this one fixed obligation
returns `ZERO`.

The rational specialization removes the unsupported positivity, inequality,
parameter-identity, and excluded-denominator predicates from the submitted
obligation. The only machine-applied alpha assumption is the declared
`real: true` flag for `scale`; no additional domain predicate is needed for
this identity. The source citation grounds the origin of the fixed identity
but is not verifier proof.

Frozen canonical program id:
`0002761432e0bd2c6c0ea2050622b287ea817d00769555c30a08ee3022dd5b66`.
