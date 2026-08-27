# Grounded \(H_{\mathrm{repr}}\)

```json
{
  "representation_type": "confluent_representation",
  "latent_object": "F(z) = ...",
  "generic_member": "G0005",
  "degenerate_member": "G0004",
  "limit_variable": "epsilon(m) -> epsilon(n)",
  "member_maps": [
    {
      "source_node_id": "G0005",
      "role": "generic",
      "source_fingerprint": {
        "functions": ["h1", "h2"],
        "indices": ["m", "n"],
        "branch_condition": "True"
      }
    }
  ],
  "operators": [{"member": "G0005", "O": "identity"}],
  "proof_obligations": [
    "limit(G0005, epsilon(m), epsilon(n)) == G0004"
  ],
  "required_assumptions": [],
  "rationale": "...",
  "confidence": 0.5
}
```

`source_node_id` MUST appear in the provided catalog.
Aliases (`S1_True`, `branch_generic`) are PARSE_FAILURE, not repaired.
