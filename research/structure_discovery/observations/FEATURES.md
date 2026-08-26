# Observation features (facts only)

Implemented in `prototype/observations.py`. None of these features encode a
hidden target name. Ablations toggle families via `feature_mask`.

| Feature | What it reports | Used by |
|---|---|---|
| `repeated_subtrees` | srepr, count, ops of non-leaf subexpressions with count≥2 | `repeated_kernel` |
| `common_factors` | multiplicative factors present in every top-level term | `repeated_kernel` |
| `denominators` / `poles` | unique denom bases and occurrence counts | `spectral_family`, `identical_kernel_merge` |
| `function_families` | AppliedUndef names with distinct argument lists | `master_function`, `spectral_family` |
| `builtin_families` | polygamma/exp/log/sin/cos call sets | `master_function`, `derivative_family` |
| `permutation_pairs` | same function, permuted args | `permutation_orbit`, `symmetry_invariant` |
| `piecewise` | branch values/conds; `all_values_equal` | `confluent_representation` |
| `divided_difference_hits` | `(F(u)-F(v))/(u-v)` up to sign | `divided_difference` |
| `polygamma_calls` | order and argument | `derivative_family` |
| `coefficient_clusters` | terms sharing a skeleton | diagnostics |
| `term_symbol_bipartite` | function name → argument tuples | diagnostics |
| `structure_summary` | engine structural inventory | diagnostics |

Not implemented (recorded as OPEN): tensor-index occurrence heatmaps beyond
the bipartite map; branch topology beyond Piecewise args.
