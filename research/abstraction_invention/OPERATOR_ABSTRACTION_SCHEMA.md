# Operator-aware abstraction schema

Not a pretty-formula guess.

```json
{
  "family_members": ["A1", "A2"],
  "latent_object": "F(...)",
  "parameterization": ["z"],
  "operators": [
    {"member": "A1", "O": "identity"},
    {"member": "A2", "O": "d/dz"}
  ],
  "instance_maps": [{"z": "..."}],
  "assumptions": [],
  "proof_obligations": ["A1 - F = 0", "A2 - dF/dz = 0"]
}
```

The latent \(F\) may not appear verbatim. Edges on the relation graph
are *evidence*, not proof.
