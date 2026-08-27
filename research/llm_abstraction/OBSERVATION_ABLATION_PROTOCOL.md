# Observation-conditioning ablation

Same model, matched budget.

| arm | input |
|---|---|
| A0 RAW | expression + assumptions + generic task |
| A1 RAW+SUMMARY | + ops, symbols, functions, branch count, index inventory |
| A2 RAW+SOL | + ranked SOL packets (not the full graph) |
| A3 SOL-only | packets and member snippets; full raw omitted |

Packetizer (experimental namespace; SOL v1 is not edited):

- union-find families on observation edges
- rank by gold-free coverage, depth, backend agreement, parameter coherence,
  relation diversity (no hidden labels)
- bounded `top-k` (default 10); ablation 5/10/20/24
- leak check: no master-function / divided-difference / confluence slogans,
  no `Phi_Gamma`

Primary causal contrast: **A0 vs A2**.

SOL-can-hurt: if A2 reduces representation-change proposals relative to A0,
that is anchoring (decision case D), not a hidden failure.

Frozen baselines on the same items (no LLM):

- B0 frozen B9
- B1 frozen LGG
- B2 LGG+canon/AC
- B3 operator graph

Do not retune on TEST. Flash repeats A0 vs A2 with frozen prompts.
