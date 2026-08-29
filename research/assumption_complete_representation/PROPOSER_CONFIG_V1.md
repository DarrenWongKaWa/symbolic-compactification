# Proposer config v1 (DEV)

Reuse frozen DeepSeek protocol. No retune.

| field | value |
|---|---|
| model | `deepseek-v4-pro` |
| thinking | enabled, `reasoning_effort=high` |
| max_tokens | 16384 |
| response_format | json_object |
| timeout_s | 180 |
| retries_network | 1 |
| retries_parse | 0 |
| temperature | omitted (thinking mode) |
| n_hypotheses_max | 5 |
| authority | `research/llm_abstraction/DEEPSEEK_CONFIG.md` |

Guo is not an input. TEST tasks are not inputs until freeze.
Secrets never logged.
