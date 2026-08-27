# Frozen Guo source grounding (Track B)

No new LLM calls. Frozen `runs/guo` hypotheses only.
Admissible binds: EXACT_BIND and UNIQUE_STRUCTURAL_BIND.
AMBIGUOUS_BIND and NO_BIND are not sent to the verifier.

Source inventory: 126 nodes (4 sums, 14 branches).

| cond | type | exact | unique | amb | nobind | DD | conf | deriv | verdicts | interpretation |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| A0s0 | derivative_family | 0 | 0 | 0 | 4 | 0 | 0 | 0 | — | no_bind |
| A0s0 | confluent_representation | 0 | 0 | 12 | 2 | 0 | 0 | 0 | — | ambiguous_bind |
| A0s1 | confluent_representation | 0 | 0 | 7 | 0 | 0 | 0 | 0 | — | ambiguous_bind |
| A1s0 | divided_difference | 0 | 0 | 4 | 0 | 0 | 0 | 0 | — | ambiguous_bind |
| A1s0 | confluent_representation | 0 | 0 | 9 | 0 | 0 | 0 | 0 | — | ambiguous_bind |
| A1s1 | divided_difference | 0 | 0 | 4 | 10 | 0 | 0 | 0 | — | ambiguous_bind |
| A1s2 | divided_difference | 0 | 0 | 2 | 2 | 0 | 0 | 0 | — | ambiguous_bind |
| A1s2 | master_function | 0 | 0 | 0 | 4 | 0 | 0 | 0 | — | no_bind |
| A2s0 | divided_difference | 0 | 0 | 0 | 2 | 0 | 0 | 0 | — | no_bind |
| A2s0 | confluent_representation | 0 | 0 | 5 | 2 | 0 | 0 | 0 | — | ambiguous_bind |
| A2s1 | confluent_representation | 0 | 2 | 2 | 0 | 0 | 1 | 0 | ZERO | old_discovery_real |
| A2s2 | derivative_family | 0 | 0 | 0 | 3 | 0 | 0 | 0 | — | no_bind |
| A2s2 | divided_difference | 0 | 0 | 3 | 1 | 0 | 0 | 0 | — | ambiguous_bind |
| A3s1 | derivative_family | 6 | 0 | 0 | 0 | 0 | 0 | 4 | ZERO|ZERO|ZERO|ZERO | old_discovery_real |

## Interpretation counts (DD / confluence / derivative / master only)

- `ambiguous_bind`: 8
- `no_bind`: 4
- `old_discovery_real`: 2

## Decisive split (G1 vocabulary vs source targeting)

| Frozen Guo hypothesis | Source binding | Compilation | Verification | Interpretation |
|---|---|---|---|---|
| A2s1 confluence (h1(b,n,m)*h2(a,c,m,n) + Eq/True) | unique | success | ZERO (limit generic→diag) | old discovery was real (C→OK) |
| A3s1 derivative (SOL ids N0014–N0016, N0023–N0025) | exact | success | ZERO (d/dβ identities) | old discovery was real (C→OK); packet node ids |
| A1s0 / A1s1 / A0s0 DD or confluence (`S1_True`, `S1_Eq_mn`) | ambiguous (4 generic / 4 diag branches) | not sent | — | still **C**: right words, no unique fingerprint |
| A2s0 DD (`O2(n,m)`, `G3`) | no bind | — | — | **C**: alias not in source |
| A0s0 derivative (`S1`…`S4` bare) | no bind | — | — | **C** |
| A1s2 master (`S1`…`S4` bare) | no bind | — | — | **C** |

No row is `wrong_abstraction` (bound + NONZERO Newton form). We **cannot** yet say DeepSeek’s DD story is false, because most DD hypotheses never uniquely bind. We **can** say:

- DeepSeek is not *only* reciting jargon: when it quotes unique `h1`/`h2` products or SOL node ids, grounding works and at least two frozen hypotheses certify.
- Most G1=Y DD/confluence hypotheses still fail unique targeting (`S1_True` among four True branches). That is constructor/grounding, not D and not V.

h-factor unique binds of all four Guo sums appear often on `repeated_kernel` / `symmetry_invariant` hyps (see CSV). Those are real source targeting of the kernels; they are not DD certificates.

## T1 anchoring (frozen negative)

A2 4/5 = **D**. Do not retune SOL to erase it.
Observation induces an abstraction prior \(P(H\mid E,\mathcal O(E))\).

## Claim boundary

These two ZEROs are **language/grounding gain** on frozen raw output.
They are not a new DeepSeek run and not Track A discovery gain.

