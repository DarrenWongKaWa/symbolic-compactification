# Figure 4 — Fail-closed asymptotic remainder

**Caption (draft).** Finite Laurent or series coefficient checks may return
engine `ZERO` while the enclosing remainder claim stays `UNKNOWN`. The
system refuses to rewrite an asymptotic statement as an exact residual
`F − A/γ = 0` in order to manufacture a green row.

Two public illustrations, both from existing evidence:

1. **Demo C** (ships with the product tag): coefficient identities `ZERO`;
   parent `ASYMPTOTIC_CLAIM` remains `UNKNOWN`.
2. **Guo Eq. (D-57)** (evidence branch): `Γ` expansion typed
   `ASYMPTOTIC_CLAIM`; remainder `O(Γ)` is not a local residual; status
   `UNKNOWN`.

```text
coefficient / Laurent children  -->  TABLE_VERIFIED   (ZERO)
enclosing ASYMPTOTIC_CLAIM      -->  TABLE_UNCERTIFIED (UNKNOWN)
```

This panel is soundness evidence, not a failed paper.
