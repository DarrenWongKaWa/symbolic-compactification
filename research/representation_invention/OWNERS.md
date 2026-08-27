# File ownership (Phase 3 worktrees)

Shared (orchestrator only after the contract commit):

- `research/representation_invention/schema.py`
- `research/representation_invention/ladder.py`
- `research/representation_invention/labels.py`
- `research/representation_invention/SCHEMA.md`
- `research/representation_invention/PROTOCOL.md`
- `research/representation_invention/LADDER.md`
- `research/representation_invention/STATUS.md`
- `tests/test_representation_invention_schema.py`

Subagents **must not** edit the shared contract modules.
They **may** import them.

| agent | owns | tests |
|---|---|---|
| A DD/Hermite | `research/representation_invention/dd/` | `tests/test_representation_dd.py` |
| B Master | `research/representation_invention/master/` | `tests/test_representation_master.py` |
| C Obligations | `research/representation_invention/obligations/` | `tests/test_representation_obligations.py` |
| D Benchmark | `research/representation_invention/bench/` | `tests/test_representation_bench.py` |
| E LLM harness | `research/representation_invention/llm/` | `tests/test_representation_llm.py` |
| F Falsifier | `research/representation_invention/falsifier/` | `tests/test_representation_falsifier.py` |
| G Guo catalog | `research/representation_invention/guo/` | `tests/test_representation_guo.py` |
| H Literature | `research/representation_invention/literature/` | no live tests required |

Do not write into frozen trees. Do not update `STATUS.md` (orchestrator).
Write `HANDOFF.md` in the owned directory with SHA, tests, and remaining risks.

Cross-imports after merge:

- A and B produce constructors that C compiles.
- D tasks consume G catalogs for the Guo DEV case study only.
- E calls C; F only attacks.
- H is documentation.
