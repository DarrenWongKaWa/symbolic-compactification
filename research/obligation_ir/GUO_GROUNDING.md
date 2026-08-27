# Track B authority: frozen Guo DD/confluence

Intra-hypothesis grounding only. No cross-hyp fingerprint theft.
No new LLM calls. Frozen raw outputs not mutated.

Source: 4 sums, 14 branches.

|C(H)|=1 required for UNIQUE. Gate counts (DD/confluence hyps): N_Z=1 N_N=0 N_U=0 N_C=9 P(ZERO|uniquely grounded)=1.0.

| cond | type | exact | unique | amb | nobind | unique_kind | verdicts | authority |
|---|---|---:|---:|---:|---:|---|---|---|
| A0s0 | confluent_representation | 0 | 0 | 14 | 0 | — | — | AMBIGUOUS_OR_NO_BIND |
| A0s1 | confluent_representation | 0 | 0 | 7 | 0 | — | — | AMBIGUOUS_OR_NO_BIND |
| A1s0 | divided_difference | 0 | 0 | 4 | 0 | — | — | AMBIGUOUS_OR_NO_BIND |
| A1s0 | confluent_representation | 0 | 0 | 9 | 0 | — | — | AMBIGUOUS_OR_NO_BIND |
| A1s1 | divided_difference | 0 | 0 | 4 | 10 | — | — | AMBIGUOUS_OR_NO_BIND |
| A1s2 | divided_difference | 0 | 0 | 4 | 0 | — | — | AMBIGUOUS_OR_NO_BIND |
| A2s0 | divided_difference | 0 | 0 | 2 | 0 | — | — | AMBIGUOUS_OR_NO_BIND |
| A2s0 | confluent_representation | 0 | 0 | 6 | 1 | — | — | AMBIGUOUS_OR_NO_BIND |
| A2s1 | confluent_representation | 0 | 4 | 0 | 0 | UNIQUE_BY_EXPLICIT_EXPR|UNIQUE_BY_LOCAL_FINGERPRINT | ZERO | UNIQUE_ZERO |
| A2s2 | divided_difference | 0 | 0 | 4 | 0 | — | — | AMBIGUOUS_OR_NO_BIND |

## Authority classes

| class | meaning |
|---|---|
| UNIQUE_ZERO | old discovery real (C→OK, not new LLM discovery) |
| UNIQUE_NONZERO | representation hypothesis wrong (D, unmasked) |
| UNIQUE_UNKNOWN | verifier bottleneck (V) |
| AMBIGUOUS_OR_NO_BIND | constructor/grounding bottleneck (C) |

G1=Y does **not** equal discovery success. Unbound rows stay C, not hallucination.

T1 A2=4/5 D remains a frozen negative. Do not retune SOL.

