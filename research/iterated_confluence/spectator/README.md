# Owner: V3-C — spectator split

Exact spectator structure of a one-parameter edge pair `(A, B)`.
Wraps Track V `split_multiplicative` / `split_additive`. No LLM. No
Guo-specific identities. This package does not claim a Guo family result;
Guo evaluation belongs to `eval/`.

## Public API

```python
from research.iterated_confluence.spectator import split_edge, count_ops

out = split_edge(A, B)
```

Return keys:

| key | meaning |
|---|---|
| `certified` | True only if reconstruction holds and `S` is not a unit/zero |
| `mode` | `"multiplicative"` \| `"additive"` \| `"none"` |
| `S`, `A_local`, `B_local` | spectator and local kernels |
| `full_ops_A`, `full_ops_B` | `count_ops` of the input pair |
| `local_ops_A`, `local_ops_B` | `count_ops` of the locals |
| `spectator_ops` | `count_ops` of `S` |
| `reduction_ratio_A/B` | `local/full` if `full > 0`, else `None` |
| `note` | provenance string (Track V note or reconstruction failure) |
| `reconstruction_ok` | True only if reconstruction is exact **and** certified |

Optional `split_report(A, B)` is the same payload with `str(S)` /
`str(A_local)` / `str(B_local)` for JSON.

## Reconstruction gate

A Track V split is accepted only after:

- multiplicative: `S * A_local == A` and `S * B_local == B`
- additive: `S + A_local == A` and `S + B_local == B`

checked with `cancel` / `together` (not `sympy.simplify` as a proof).
If reconstruction fails, `certified=False`, `mode="none"`, `S=1`, and
the originals are returned as locals — the rejected kernel is not kept
for proving. Units (`±1`) and zero are not spectators.

Multiplicative is tried first (AppliedUndef peel, then gcd with Track V
ops cap 80), then additive. Size-guard / gcd failure does not invent `S`.

Ops tracking is for local kernels toward the already-certified ~176-op
two-member Guo scale. This splitter does not run those kernels.
