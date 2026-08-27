# DeepSeek abstraction DEV results

Infrastructure experiment. Frozen B9 (`4237f6b`), LGG (`efc0924`),
Beyond-LGG (`3214a5a`), and SOL v1 (`0a2905b`) were not mutated.
Proposer prompts/config are frozen. Constructor was upgraded **after**
the LLM runs (no new API calls) to test CASE E.

Model: `deepseek-v4-pro`, thinking on, `reasoning_effort=high`.
n=276 scored runs. Parse failures: 1. Unnecessary-interpolation: 0.

Primary contrast A0 vs A2 (calibration+DEV, n=63 each): **CASE A**
(success 0.54 vs 0.52; type+target 0.57 vs 0.65; certified 0.83 vs 0.90).

Category-level: SOL **helps T2/T5**, **hurts T1 by CSE anchoring**,
**null on F6**. T7 permutation is certified on **both** arms once the
constructor does argument swap on parsed expressions (CASE E, then fixed).

## Constructor v2 (no new LLM calls)

Previous UNKNOWN obligations were dominated by string-replacing `i`/`n`
into English latents and by differentiating without substituting.

After expression-core + xreplace + function-hole maps + `d/dθ` then
instantiate:

- certified files 175 → 223
- UNKNOWN obligations 349 → 244
- T7 success A0/A2 both **1.0** (was 0.0 / 0.4)
- T0 CSE now certifiable when maps are `u → a(n)`
- remaining UNKNOWN: unparseable prose latents (`unparseable_latent`, Guo)

## Calibration (8 × A0–A3 × 1 seed)

See `runs/calibration/`. Schema held. CAL-B did not revive geodesic
interpolation. CAL-G: SOL helps confluence typing. CAL-H: no new head.

## DEV flagship A0 vs A2 by category (5 seeds)

| cat | task | A0 suc | A2 suc | A0 cert | A2 cert |
|---|---|---:|---:|---:|---:|
| T0 | exact CSE | 0.80 | 0.40 | 1.00 | 1.00 |
| T1 | substitution | **1.00** | **0.20** | 1.00 | 1.00 |
| T1-neg | unrelated | 0.00 | 0.00 | 1.00 | 1.00 |
| T2 | distributivity | 0.00 | **0.60** | 0.20 | 1.00 |
| T2-neg | not distrib | 0.00 | 0.00 | 1.00 | 1.00 |
| T3 | derivative | 1.00 | 0.80 | 1.00 | 1.00 |
| T3-neg | independent F,G | 1.00 | 0.60 | 0.00 | 0.40 |
| T4 | polygamma master | 1.00 | 1.00 | 1.00 | 1.00 |
| T5 | confluence toy | 0.20 | **0.80** | 1.00 | 0.80 |
| T6 | new head / trace | 0.00 | 0.00 | 1.00 | 0.80 |
| T7 | swap orbit | **1.00** | **1.00** | 1.00 | 1.00 |

T1: RAW emits `parameterized_family` 5/5. SOL emits `repeated_kernel`
from CSE packets 3/5. Reconstruction still ZERO. Local structure up,
abstraction type down.

## Packet size

CAL-B useful at caps 5/10/20/24. CAL-C useful at cap 10; 5/20/24 miss.
Dumping more families does not help.

## Flash (same prompts)

A0 success 0.54 vs A2 0.38; repr-change 0.50 vs 0.33. Anchoring
reproduces inside the provider. Not multi-model generalization.

## Guo (DEV, 12 runs)

Certified 2/12 (shallow polygamma/affine templates). Success 1/12.
UNKNOWN still on DD/master/confluence obligations. Verbal
divided-difference / derivative families appear in RAW and SOL.
Not Φ_Γ, not PRB, not certified generators.

## Tokens

`TOKEN_COSTS.csv`. Not a scientific metric.
