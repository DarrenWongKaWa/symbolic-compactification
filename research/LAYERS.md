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

Grounded-Proposer-v1 (`3fea222`) is frozen. Guo DEV: 11/11 local
confluence ZERO under catalog IDs.

New line: **Verified Representation Invention v1**
(`research/representation_invention/`). Same SOL/model/budgets; richer
`H=(R,{A_i},{O_i},F)` contract. Do not mutate P1 runs.
