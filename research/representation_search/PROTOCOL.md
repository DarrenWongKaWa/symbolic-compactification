# Track A — F6 representation-change search

Independent of Track B. Do not retune SOL. Do not touch TEST.

## Goal

Propose a language change

\[
\mathcal L_{\mathrm{old}}\to\mathcal L_{\mathrm{new}}
\]

not a prettier \(F(x)\).

Examples: Piecewise → divided difference; components → invariant basis.

## Schema

\(H_{\mathrm{repr}}=(\mathcal R, F, \theta, \mathcal O, \text{node map})\)

See `SCHEMA.md`. Search over **representation class** \(\mathcal R\).

## Firewall

- No SOL ranking changes.
- No DeepSeek prompt retune on this track until A has a frozen schema
  and B can compile it.
- Frozen `llm_abstraction/runs/*/raw_content` is the discovery baseline.
  A new proposer only scores discovery gain if it emits a `H_repr`
  type absent from that frozen output.

## Not started here

Search algorithms, library learning, DreamCoder. Schema and protocol only.
