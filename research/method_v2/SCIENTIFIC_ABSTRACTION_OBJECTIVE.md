# Scientific abstraction objective (generic)

Used by Method v2's isolated proposer. Domain-neutral. **No Guo gold
objects** (`Phi_Gamma`, nine generators, Hermite \(H_1,H_2\) as prescribed
names).

Prefer blackboard structure over LeafCount:

- reusable kernels (shared summands, shared denominators)
- master functions (named, then expanded for proof)
- invariants and symmetry-adapted pairings (object + permute)
- generators / tensor-like index structure
- confluence of Piecewise **as a hypothesis**, never as unproven deletion
- repeated physical motifs (thermal, spectral, response)

Shorter `count_ops` is not automatically better. Auxiliaries may grow the
AST. Promotion requires a **closed** expression whose residual is ZERO.
