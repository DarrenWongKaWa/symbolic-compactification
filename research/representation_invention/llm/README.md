# Owner: Subagent E — Grounded-Proposer-v2 harness

Reuse `research.llm_abstraction.client` / `config.ProposerConfig` /
`secrets.sanitize` / `packetizer.packets_for_item`. Never log API keys
or `.env`.

Parse through `parse_document_v2` / `parse_hypothesis_v2`. Aliases are
`PARSE_FAILURE` (no repair). P1 type `confluent_representation` is
rejected by the V2 schema on purpose.

Conditions: P1 (wrap frozen v1, do not mutate its runs), P2 (default,
SOL packets), P3 (RAW, no SOL), P4 (SOL).

No live API in unit tests. Mock `chat_complete`. Record
model / usage / reasoning tokens / latency / parse / hyp count /
grounded / compile / ZERO / NONZERO / UNKNOWN on real runs.

Flagship: ≥5 seeds (prefer 10). Primary model `deepseek-v4-pro`.

See `PROTOCOL.md`.
