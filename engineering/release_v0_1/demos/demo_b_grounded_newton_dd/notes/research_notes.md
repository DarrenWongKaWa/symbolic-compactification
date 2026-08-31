# Research notes

This workspace repackages the already-frozen `C9H4` reference object as a
field-use demonstration. It is a demonstration of grounding, explicit proof
obligations, and exact verification. It is **not** a discovery result and does
not show that an AI or search procedure found the Newton representation.

The shared latent kernel is

```text
F(z) = 1/sqrt(z)
```

Each candidate is a two-node Newton divided difference of `F`, followed by a
linear coefficient. The four source members are checked independently, and
the expected aggregate result is `ZERO` only if all four obligations return
`ZERO`.

The frozen scientific contract retains real variables, positive and unequal
squared-distance radicands, nonzero displayed denominators, and the source
relation `alpha + beta = 1`. The v0.1 workspace schema machine-checks the real
symbol declarations but does not encode arbitrary relational predicates. The
verification report therefore certifies the displayed symbolic equivalences
under declared engine semantics; it does not independently prove the physical
domain contract.

Frozen canonical program id:
`0002761432e0bd2c6c0ea2050622b287ea817d00769555c30a08ee3022dd5b66`.
