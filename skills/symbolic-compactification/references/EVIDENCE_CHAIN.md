# Evidence chain

```text
model: candidates, reconstructed edges, commentary
        ↓
certify / compact_verify: engine residual + bound receipt
        ↓
check_audit: fail-closed structural + receipt recomputation
        ↓
render: layout only
```

The model does not choose `EXACT`. A JSON object that says `ZERO` is not a
receipt. `input_hash` binds the receipt to lhs, rhs, assumptions, symbols,
and domain; authority comes from independent recomputation, not the hash.

Without the engine, machine Exact is illegal. Reconstruction-only reports
must stay orange.

`STRUCTURAL` and `CITED_RULE` are not machine Exact. A claim cannot be
Exact if a supporting edge is `NONZERO_RESIDUAL` or still unresolved.

ZERO on an encoded residual is not a paper-level proof, not a domain
certificate, and not an improvement certificate. Improvement is a second
axis (`IMPROVED` / `NO_IMPROVEMENT` / `DEPENDS`).
