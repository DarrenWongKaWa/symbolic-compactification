# Capability decomposition

```
P  Perception     SOL v1 (frozen). Do not retune ranking.
D  Discovery      representation class R
G  Grounding      which source members {A_i}
C  Compilation    proof obligations O_i
V  Verification   ZERO / NONZERO / UNKNOWN
I  Interpretation human physics (no promotion)
```

Operational scientific abstraction:

\[
H=(\mathcal R,\{A_i\},\{\mathcal O_i\},F)
\qquad
A_i=\mathcal O_i[F]
\]

Vocabulary without \(\{A_i\}\) is not discovery success.

Frozen DeepSeek-v1 outputs (`research/llm_abstraction/runs/`) are closed.
Track B grounding on those files is closed (`d20c1a2`).
Do not re-squeeze them.

New line: **Grounded-Proposer-v1** — grounding is part of the proposal
contract. Same SOL, same model, same budgets; only the output contract
changes (P0 aliases vs P1 catalog IDs).
