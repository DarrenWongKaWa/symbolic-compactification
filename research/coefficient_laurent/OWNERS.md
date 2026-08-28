# Track V5 ownership

Shared (orchestrator): `schema.py`, `cache.py`, `PROTOCOL.md`,
`FROZEN_INPUTS_V5.json`, `freeze_v5.py`, `STATUS.md`.

| agent | worktree | owns |
|---|---|---|
| A decomposer | `work/v5-atom-decomposer` | `atoms/` |
| B polygamma series | `work/v5-polygamma-series` | `pg_series/` |
| C rational series | `work/v5-rational-series` | `rational/` |
| D sparse accumulator | `work/v5-sparse-coeff` | `sparse/` |
| E pole certifier | `work/v5-pole-cert` | `poles/` |
| F c0 matcher | `work/v5-c0-matcher` | `c0/` |
| G remainder | `work/v5-remainder` | `remainder/` |
| H grouping | `work/v5-grouping` | `grouping/` |
| I derivative basis | `work/v5-derivative-basis` | `basis/` |
| J numeric falsifier | `work/v5-numeric-falsifier` | `numeric/` |
| K cache auditor | `work/v5-cache-audit` | tests against `cache.py` in `tests/test_cl_cache.py` (orchestrator owns cache.py) |
| L laurent falsifier | `work/v5-laurent-falsifier` | `falsifier/` |
| M literature | `work/v5-literature` | `literature/` |

Do not edit frozen V3/V4 files or historical runs. No LLM.
