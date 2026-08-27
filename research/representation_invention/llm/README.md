# Owner: Subagent E — Grounded-Proposer-v2 harness

Reuse `research.llm_abstraction.client` / secrets. Never log API keys.

Parse through `parse_hypothesis_v2`. Aliases are PARSE_FAILURE.

Conditions P1 (wrap frozen v1, do not mutate its runs), P2, P3 (RAW), P4 (SOL).

No live API in unit tests. Record usage/tokens/latency on real runs.

Flagship: ≥5 seeds (prefer 10). Primary model `deepseek-v4-pro`.
