# Track V3 ownership

Shared (orchestrator): `schema.py`, `PROTOCOL.md`, `FROZEN_INPUTS_V3.json`,
`freeze_v3.py`, `STATUS.md`, `OWNERS.md`. Do not edit these in subagent
worktrees.

| agent | worktree | owns | tests |
|---|---|---|---|
| V3-A coordinates | `work/v3-degeneracy-coordinates` | `coordinates/` | `tests/test_ic_coordinates.py` |
| V3-B paths | `work/v3-path-enumerator` | `paths/` | `tests/test_ic_paths.py` |
| V3-C spectator | `work/v3-spectator-split` | `spectator/` | `tests/test_ic_spectator.py` |
| V3-D edges | `work/v3-edge-verifier` | `edges/` | `tests/test_ic_edges.py` |
| V3-E compose | `work/v3-path-composition` | `compose/` | `tests/test_ic_compose.py` |
| V3-F consistency | `work/v3-path-consistency` | `consistency/` | `tests/test_ic_consistency.py` |
| V3-G intermediates | `work/v3-intermediate-builder` | `intermediates/` | `tests/test_ic_intermediates.py` |
| V3-H complexity | `work/v3-complexity` | `complexity/` | `tests/test_ic_complexity.py` |
| V3-I series | `work/v3-series-control` | `series/` | `tests/test_ic_series.py` |
| V3-J falsifier | `work/v3-falsifier` | `falsifier/` | `tests/test_ic_falsifier.py` |
| V3-K literature | `work/v3-literature` | `literature/` | none required |

Coordinator after merge: `eval/`, generic suite, Guo rescore, close docs.

Do not edit historical run JSON. Do not edit frozen V2/V files.
No LLM. No Guo gold names.
