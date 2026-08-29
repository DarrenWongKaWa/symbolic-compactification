# Causal experiment

## Conditions (minimum)

| id | method | LLM? |
|---|---|---|
| S0 | random search under the grammar | no |
| S1 | enumerative search, increasing complexity | no |
| S2 | symbolic-heuristic beam | no |
| S3 | SOL-conditioned heuristic search | no (SOL frozen) |
| S4 | LLM **state ranking** among legal states | rank only |
| S5 | LLM **action proposal** among legal actions | actions only |
| S6 | verifier-in-the-loop search | no |
| S7 | LLM + verifier search | yes |
| F0 | old free-form P0 RAW (historical architecture) | free-form |

Do not implement A*/MCTS preemptively. Only if DEV branching evidence
requires them.

## Comparisons

| id | contrast | question |
|---|---|---|
| A | S1 vs S4/S5/S7 | Does the LLM improve search efficiency? |
| B | S2 vs S4/S5 | Does the LLM add judgment beyond structural rules? |
| C | F0 vs S1–S7 | Was free-form generation the bottleneck? |
| D | S1/S2 vs S6/S7 | Does exact adjudication guide discovery? |
| E | S2 vs S3 | Does SOL help or anchor program search? |

Plus grammar ablations G_FULL / G_NO_HERMITE / G_PRIMITIVE, and
latent-F allowed vs forbidden.

## Outcome cases

- **A** — held-out R3+; enumerative ≈ LLM. Structured search works; AI unsupported.
- **B** — LLM-guided reaches R3+ more efficiently. AI search heuristic.
- **C** — only named HERMITE/MASTER primitives succeed. Grammar gave the answer.
- **D** — primitive grammar composes R3+. Stronger synthesis evidence.
- **E** — all methods fail R3+. Grammar/search space still inadequate.
- **F** — DEV works, fresh TEST fails. No generalization.
- **G** — symbolic heuristic dominates LLM. LLM not useful for navigation.
- **H** — verifier feedback dramatically improves search. Verified search valuable even if AI is not.

## DEV gate (before broad runs)

Small calibration: one R2, one R3, one R4/R5, one R6, one negative trap.
All methods must execute. Then freeze implementation semantics.

Primary scientific target: **R3+**. Reproducing only R2 resolvent
identities is not an interesting positive for this line.

## Benchmark

`ssc-representation-search-bench-v0.1`: DEV / TEST / CHALLENGE.
Focus R2–R8. Target mix (quality over exact %): R2 20%, R3 25%,
R4/R5 25%, R6 20%, R7/R8 10%.

Fresh TEST after DEV method development. Previous AC TEST is
HISTORICAL_DIAGNOSTIC only. Do not mine variants of old TEST
identities. Structural duplicate audit vs previous benches, current
DEV, and historical Guo.

PACKAGING_GAP: do not extend the parser. Unparseable new cases stay
PACKAGING_GAP and out of fair method comparison.

## TEST freeze

After freeze: no grammar, search-policy, scoring, or verifier changes.
Manifest: `final/FREEZE_MANIFEST.json`.

## Publication (exactly one, after close)

A top-tier method · B specialized method · C program-synthesis /
benchmark · D systems/verification · E more evidence · **F structured
search also fails to support representation invention**.

No paper package before verdict. After close: repertoire V2,
CAPABILITIES.json, NEGATIVE_RESULTS.md — not before.
