# Guo DEV observation map (no Φ interpretation)

## preset `minimal`

- seconds: 67.987
- nodes: 80
- relations: 10
- families: 9
- types: ['CSE_SHARED', 'SAME_BRANCH_DEPENDENCY', 'SAME_FUNCTION_FAMILY']
- backends: ['sympy']

## preset `algebra`

- seconds: 0.844
- nodes: 80
- relations: 10
- families: 9
- types: ['CSE_SHARED', 'SAME_BRANCH_DEPENDENCY', 'SAME_FUNCTION_FAMILY']
- backends: ['sympy', 'matchpy']

## preset `relations`

- seconds: 1.211
- nodes: 80
- relations: 16
- families: 11
- types: ['CSE_SHARED', 'EGRAPH_EQUIVALENT', 'KNOWN_REWRITE_EQUIVALENT', 'LGG_FAMILY', 'SAME_BRANCH_DEPENDENCY', 'SAME_FUNCTION_FAMILY', 'SUBSTITUTION_INSTANCE']
- backends: ['sympy', 'matchpy', 'lgg', 'egglog']

The layer does not infer Φ_Γ, Hermite DDs, or nine generators.
