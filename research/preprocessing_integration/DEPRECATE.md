# Custom preprocessor audit

Do **not** delete frozen historical implementations.

| custom | already provided by | action |
|---|---|---|
| `research/abstraction_invention/beyond/relations.py` | SOL sympy + LGG adapters | keep for frozen v0.2 reproduction; new code should call `observe()` |
| `research/abstraction_invention/beyond/canonicalize.py` | SymPy expand + AC sort in SOL | keep frozen; SOL sympy backend has a sort variant |
| B9 structure inventory | `structure_summary` + SOL nodes | keep B9 frozen |

Forward path: `symbolic_compactification.observations.observe`.
