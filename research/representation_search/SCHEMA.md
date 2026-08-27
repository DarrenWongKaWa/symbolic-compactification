# \(H_{\mathrm{repr}}\)

```json
{
  "representation_type": "divided_difference",
  "language_from": "Piecewise",
  "language_to": "divided_difference",
  "latent_function": "F(z)",
  "parameters": ["z"],
  "nodes": ["x", "x", "y"],
  "member_maps": [
    {"member": "branch_generic", "form": "F[x,y]"},
    {"member": "branch_degenerate", "form": "F[x,x]"}
  ],
  "operators": [
    {"member": "branch_generic", "O": "divided_difference"},
    {"member": "branch_degenerate", "O": "confluence"}
  ],
  "required_relations": ["repeated-node confluence"],
  "assumptions": ["x != y on generic branch"],
  "proof_obligations": []
}
```

`proof_obligations` are compiled by Track B. Track A must not claim ZERO.
