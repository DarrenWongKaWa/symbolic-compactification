# DeepSeek abstraction DEV results

Infrastructure experiment. Frozen B9 (`4237f6b`), LGG (`efc0924`),
Beyond-LGG (`3214a5a`), and SOL v1 (`0a2905b`) were not mutated.

Model: `deepseek-v4-pro`, thinking enabled, `reasoning_effort=high`.
Schema parse failures: **1 / 276**. Unnecessary-interpolation rate: **0**.
API key never written into artifacts.

Primary contrast A0 RAW vs A2 RAW+SOL (calibration+DEV): **CASE A**
(aggregate type+target 0.476 vs 0.476; certified 0.68 vs 0.70).

Category-level the picture is **not** uniform. SOL helps some T2/T5/T7
cells and **hurts T1 by CSE anchoring**.

## Calibration (8 items × A0–A3 × 1 seed = 32)

| condition | n | success | type+target | certified | repr_chg | false_abs | abstain |
|---|---:|---:|---:|---:|---:|---:|---:|
| A0 | 8 | 0.50 | 0.50 | 0.75 | 0.75 | 0.125 | 0.125 |
| A1 | 8 | 0.38 | 0.50 | 0.88 | 0.75 | 0.25 | 0.00 |
| A2 | 8 | 0.50 | 0.62 | 0.50 | 0.38 | 0.00 | 0.125 |
| A3 | 8 | 0.50 | 0.38 | 0.75 | 0.25 | 0.125 | 0.125 |

Notes: CAL-B interpolation/geodesic did **not** reappear. CAL-F RAW/SOL
abstained (good); A1 over-proposed. CAL-G confluence: RAW missed, A2/A3
hit. CAL-H representation change: never `basis_reduction`. CAL-E negatives
rarely abstain.

## DEV multi-seed (11 items)

Flagship A0/A2: 5 seeds. A1/A3: 3 seeds. n=176.

| condition | n | success | type+target | certified | repr_chg | false_abs | abstain |
|---|---:|---:|---:|---:|---:|---:|---:|
| A0 | 55 | 0.40 | 0.47 | 0.67 | 0.64 | 0.18 | 0.09 |
| A1 | 33 | 0.45 | 0.58 | 0.64 | 0.70 | 0.15 | 0.12 |
| A2 | 55 | 0.42 | 0.45 | 0.73 | 0.58 | 0.16 | 0.04 |
| A3 | 33 | 0.36 | 0.39 | 0.76 | 0.52 | 0.18 | 0.09 |

### Flagship A0 vs A2 by category (5 seeds)

| cat | task | A0 success | A2 success | A0 cert | A2 cert | note |
|---|---|---:|---:|---:|---:|---|
| T0 | exact CSE | 0.4 | 0.2 | 0.6 | 0.6 | SOL not helpful |
| T1 | substitution | **1.0** | **0.2** | 1.0 | 1.0 | SOL anchors to `repeated_kernel` |
| T1-neg | unrelated | 0.0 | 0.0 | 1.0 | 0.8 | false shallow templates |
| T2 | distributivity | 0.0 | **0.6** | 0.2 | 0.8 | SOL helps F2 |
| T2-neg | not distrib | 0.0 | 0.0 | 1.0 | 1.0 | over-generalization |
| T3 | derivative | 0.8 | 0.4 | 0.8 | 0.6 | RAW better typed |
| T3-neg | independent F,G | 1.0 | 1.0 | 0.0 | 0.0 | abstains / no cert |
| T4 | polygamma master | 1.0 | 1.0 | 1.0 | 1.0 | both fine |
| T5 | confluence toy | 0.2 | **0.8** | 0.8 | 0.8 | SOL helps F5 type |
| T6 | new head / trace | 0.0 | 0.0 | 1.0 | 1.0 | F6 fail both |
| T7 | swap orbit | 0.0 | **0.4** | 0.0 | 0.4 | SOL sometimes certifies |

T1 mechanism: RAW emits `parameterized_family` 5/5. SOL emits
`repeated_kernel` 3/5 (CSE packets) even though members and ZERO
reconstruction remain. Local structure up, abstraction type down.

## Packet size (CAL-B, CAL-C, A2, seed 0)

cap 5/10/20/24. CAL-B useful at all caps. CAL-C useful only at default
cap 10; 5/20/24 missed or unverifiable. No evidence that dumping more
families helps; some evidence it hurts.

## Flash (`deepseek-v4-flash`, same prompts, calib A0 vs A2 × 3 seeds)

| condition | n | success | type+target | certified | repr_chg |
|---|---:|---:|---:|---:|---:|
| A0 | 24 | 0.38 | 0.46 | 0.58 | 0.50 |
| A2 | 24 | 0.21 | 0.42 | 0.58 | 0.33 |

Same prompts. SOL lowers success and representation-change rate (anchoring).
Not multi-model generalization.

## Frozen baselines (no LLM)

On the same items: B0/B9 finds exact CSE/permutation; B1 LGG certifies
Born-like substitution and some polygamma templates; B3 operator graph
finds derivative and swap. LLM RAW matches LGG on T1; LLM+SOL falls
behind LGG on T1. Neither LLM arm invents a new F6 head.

## Tokens (bookkeeping, off-peak list prices)

See `TOKEN_COSTS.csv`. Pro completion ~1.0M tokens across DEV+calib+guo;
estimated off-peak USD on the order of $2–3. Not a scientific metric.

## What this does **not** show

- AI discovering physics
- SOL as a general invention engine
- certified Φ_Γ / Hermite DD / nine generators on Guo
