# Track V2 ownership

Shared (orchestrator): schema.py, PROTOCOL.md, FROZEN_INPUTS_V2.json,
freeze_v2.py, PROGRAM_STATUS_V2.md

| agent | owns | tests |
|---|---|---|
| V2-A graph | `graph/` | `tests/test_mb_graph.py` |
| V2-B edge cert | `edges/` | `tests/test_mb_edges.py` |
| V2-C Hermite recurrence | `recurrence/` | `tests/test_mb_recurrence.py` |
| V2-D family composition | `compose/` | `tests/test_mb_compose.py` |
| V2-E latent consistency | `latent/` | `tests/test_mb_latent.py` |
| V2-F piecewise normalizer | `piecewise/` | `tests/test_mb_piecewise.py` |
| V2-G special-function | `special/` | `tests/test_mb_special.py` |
| V2-H falsifier | `falsifier/` | `tests/test_mb_falsifier.py` |
| V2-I router | `router/` | `tests/test_mb_router.py` |
| V2-J literature | `literature/` | none required |

Do not edit historical run JSON. Do not edit schema.py.
