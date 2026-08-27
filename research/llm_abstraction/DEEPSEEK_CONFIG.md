# DeepSeek proposer config (frozen for DEV)

Protocol: `deepseek-abstraction-protocol-v1-dev`
Config id: `deepseek-v4-pro-thinking-high-v1`

This is infrastructure for an **experimental proposer**. It does not modify
SOL v1 (`0a2905b`), frozen B9 (`4237f6b`), frozen LGG (`efc0924`), or
Beyond-LGG (`3214a5a`).

## Model

| field | value |
|---|---|
| primary | `deepseek-v4-pro` |
| later robustness only | `deepseek-v4-flash` |
| vision | **not used** |
| base URL | `https://api.deepseek.com` |

## Decoding / thinking

| field | value | note |
|---|---|---|
| thinking | `{type: enabled}` | required |
| reasoning_effort | `high` | required |
| temperature | **omitted** | unsupported in thinking mode |
| top_p | **omitted** | same |
| max_tokens | 16384 | completion budget including reasoning |
| response_format | `json_object` | format only, not scientific repair |
| timeout_s | 180 | per request |
| retries_network | 1 | transport only |
| retries_parse | 0 | never retry to fix scientific content |

## Experiment

| field | value |
|---|---|
| n_hypotheses_max | 5 |
| packet_cap_default | 10 |
| flagship seeds (A0 vs A2) | 5 |
| secondary seeds (A1, A3) | 3 |
| SOL backends | `relations` (sympy, matchpy, lgg, egglog) |
| SOL timeout | 12s (180s Guo) |

## Secrets

API key lives in gitignored `.env` as `DEEPSEEK_API_KEY`.
Never printed, never written into `runs/`, CSV, or markdown.
Records store request id, token usage, latency, and redacted content only.
