# Long workload: Guo σ_abc exact DC (input only)

This directory holds the **raw scientific input**, not a certified compact
form. Compact candidates must still go through `verify` / `step`. Promote
only on ZERO.

| Field | Value |
|---|---|
| File | `Guo_Sigma_abc_dc_exact.txt` |
| SHA-256 | `63742cc4e6bf401dd48e258ecb86676b0d7570cc075cae38b91dc188652afc44` |
| Bytes | 22061 |
| Format | Wolfram text (`CompleteDCSigmaABC = Sum[…]`) |
| Origin | `finite-gamma-supplement-scientific-line/sources/full_tensor/` |

Do not copy compact-form theorems or disagreement certificates into this
engine repository.

Ingest with `inspect --format wolfram`. Re-parse the translated native text
with `symbols.json` (free symbols plus bound indices `n`, `m`, `ell`).
Because the expression is extremely long, you may request
`--proposer-mode subagent`. Default remains `main`.
