# LLM hypothesis schema

Authoritative result is typed JSON, not prose.

Required fields:

- `hypothesis_type`
- `target_members`
- `latent_object`
- `parameters`
- `operators`
- `instance_maps`
- `construction_plan`
- `required_assumptions`
- `proof_obligations`
- `rationale`
- `confidence` (in [0, 1])

Allowed types: `repeated_kernel`, `parameterized_family`, `master_function`,
`derivative_family`, `recurrence_family`, `confluent_representation`,
`divided_difference`, `symmetry_invariant`, `basis_reduction`,
`tensor_generator`, `generating_function`, `other_structured`.

Unknown types, missing fields, non-list members, empty latent object, or
out-of-range confidence → `PARSE_FAILURE` for that hypothesis.
There is **no silent scientific repair** (no mapping `family` → `parameterized_family`,
no filling `latent_object` from the rationale). Extracting JSON from markdown
fences is format-only.

Abstention is valid: `{"abstain": true, "hypotheses": []}`.

Quality flag `UNNECESSARY_STRUCTURE` marks gratuitous interpolation/geometry.
It is **not** creative success.

Construction/verification is a separate stage using the existing fail-closed
engine (`ZERO` / `NONZERO` / `UNKNOWN`). UNKNOWN is not success.
