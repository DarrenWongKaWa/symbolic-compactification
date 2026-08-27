# Protocol — Verified Representation Invention v1

## Frozen authorities (read-only)

| line | SHA |
|---|---|
| Exact-pattern / B9 | `4237f6b` |
| First-order LGG | `efc0924` |
| Beyond-LGG | `3214a5a` |
| SOL v1 | `0a2905b` |
| P/D/G/C/V closure | `14c8f75` |
| Guo intra-hyp grounding | `d20c1a2` |
| Grounded-Proposer-v1 | `3fea222` |

Do not rewrite files under:

- `research/structure_discovery/` (except read)
- `research/abstraction_invention/`
- `research/llm_abstraction/runs/`
- `research/grounded_proposer/runs/`
- `src/symbolic_compactification/observations/`
- historical obligation-IR results

## Locked for this line

Same as P1 unless a phase explicitly changes one axis:

- SOL v1 ranking / backends
- `deepseek-v4-pro` (primary), thinking on, `reasoning_effort=high`
- scientific context strings already used on Guo DEV
- token/time budgets where comparable

Changed: **representation hypothesis contract** (V2).

## Conditions

| id | meaning |
|---|---|
| P1 | frozen Grounded-Proposer-v1 (local-confluence baseline) |
| P2 | Grounded Representation Proposer v2 (full schema) |
| P3 | P2 + RAW (no SOL packet) |
| P4 | P2 + SOL |
| P5 | specialist ensemble (only after single-agent P2) |

G-P1 / G-P2 / G-P3 are the Guo DEV instantiations.

## Non-negotiable rules

1. Aliases (`S1_True`, `generic_branch`, …) → `PARSE_FAILURE`. No repair.
2. `COMPILE_FAILURE` ≠ `UNKNOWN` ≠ `ZERO`.
3. Verbal “divided difference” without members, nodes, F, and reconstruction is not discovery.
4. No Guo gold names in proposer prompts or catalogs.
5. No Guo-specific ZERO rules.
6. No cross-hypothesis stealing.
7. No TEST tuning. Method work is DEV-only.
8. New claims need new evidence, not rereading frozen P0/P1 JSON.
9. Never convert compilation failure into UNKNOWN.

## Gain accounting

If P2 outputs a representation type/structure absent from frozen P1:
**discovery gain**.

If old P1 output becomes verifiable because the compiler improved:
**compiler/language gain**.

If the same structure is now bindable because members are G####:
**grounding gain**.

Never mix these.

## DD gate (Phase 7)

Success (`DD-OK`) requires all of: grounded G#### members, explicit F,
node list/multiplicities, explicit DD representation, reconstruction
rule, generated obligations, ZERO.

`confluent_representation` / `local_confluence` alone is not DD-OK.

## Master gate (Phase 8)

≥2 structurally distinct grounded members, one explicit F, nontrivial
operator maps, instance obligations ZERO, quality above tautological
wrapper `F := A1` used once.

## Seeds

Flagship stochastic conditions: ≥5 seeds, prefer 10.

## API

Reuse `research.llm_abstraction.client` / `secrets`. Never log `.env`.
