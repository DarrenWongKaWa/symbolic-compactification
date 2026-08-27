# RepresentationHypothesisV2

Minimum proposer output:

```json
{
  "representation_type": "divided_difference",
  "member_ids": ["G0001", "G0007"],
  "member_roles": {
    "G0001": "generic",
    "G0007": "degenerate"
  },
  "latent_object": "F(z) = ...",
  "latent_variables": ["z"],
  "nodes": [
    {"name": "x", "expression": "epsilon(m)", "multiplicity": 1},
    {"name": "y", "expression": "epsilon(n)", "multiplicity": 1}
  ],
  "operators": [
    {"member_id": "G0001", "kind": "newton_dd", "args": {"nodes": ["x", "y"]}}
  ],
  "instance_maps": {
    "G0001": {"theta": {}, "nodes": ["epsilon(m)", "epsilon(n)"]}
  },
  "reconstruction_rule": "A = (F(x)-F(y))/(x-y)",
  "required_assumptions": ["x != y"],
  "proof_obligations": [
    {
      "kind": "NEWTON_DD",
      "member_ids": ["G0001"],
      "operator": "newton_dd",
      "expected": "member == F[x,y]"
    }
  ],
  "scientific_rationale": "structural, not physical",
  "confidence": 0.5
}
```

## Allowed `representation_type`

`local_confluence`, `divided_difference`, `hermite_divided_difference`,
`derivative_family`, `recurrence_family`, `master_function`,
`generating_function`, `invariant_basis`, `tensor_generator`,
`other_explicit`.

P1 name `confluent_representation` is **not** accepted. That is
`PARSE_FAILURE` with `p1_type_not_accepted`.

## Member IDs

`member_ids` is required and nonempty. Each id must match `G\\d{4}` and
appear in the provided catalog.

Invalid (never repaired):

- `S1_True`
- `generic_branch`
- `branch_2`
- `G1` (not four digits)
- any id not in the catalog

## Parse vs compile vs verify

| status | layer | meaning |
|---|---|---|
| `PARSE_FAILURE` | G/D syntax | contract broken |
| `COMPILE_FAILURE` | C | cannot build a checkable obligation |
| `UNKNOWN` | V | checker cannot decide |
| `ZERO` / `NONZERO` | V | decided |

These are never collapsed.

## Completeness (not parse)

A scientific hypothesis is `H = (R, {A_i}, {O_i}, F)` with `A_i = O_i[F]`.

Vocabulary without `{A_i}` is not discovery.
`R + {A_i}` without operators is incomplete.
Verification requires explicit `O_i` and `F`.
