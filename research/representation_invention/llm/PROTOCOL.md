# Grounded-Proposer-v2 protocol

Harness: `research/representation_invention/llm/`.
Parse: `parse_document_v2` / `parse_hypothesis_v2`. Aliases are
`PARSE_FAILURE` and are never repaired.

## Conditions

| id | meaning |
|---|---|
| P1 | frozen Grounded-Proposer-v1 (read-only `research/grounded_proposer/runs/`) |
| P2 | Grounded Representation Proposer v2 (default: catalog + RAW + SOL packets) |
| P3 | P2 + RAW (catalog + raw expression; **no** SOL packet) |
| P4 | P2 + SOL (catalog + raw expression + SOL packets) |

P2 default and P4 call `packets_for_item(..., backends="relations")` the
same way as `grounded_proposer.propose.propose_p1` (P1 A2).

P1 type name `confluent_representation` is **rejected** by the V2 schema
(`p1_type_not_accepted`). Evaluation-only mapping
`confluent_representation → local_confluence` lives in `p1_baseline.py`
and is not a parse repair.

## Locked axes

Same as P1 unless a phase explicitly changes one:

- SOL v1 ranking / backends (`relations`)
- Primary model `deepseek-v4-pro`, thinking on, `reasoning_effort=high`
- `research.llm_abstraction.config.ProposerConfig`
- Client `research.llm_abstraction.client.chat_complete`
- Secrets `research.llm_abstraction.secrets.sanitize` — never log API keys or `.env`

Changed: **RepresentationHypothesisV2** (catalog `G####` members, operators,
reconstruction_rule, proof_obligations).

## Seeds

Flagship stochastic conditions: **≥5 seeds, prefer 10**.

## Recorded fields (each run JSON)

- `model`, `config_id`, `protocol`, `condition`, `seed`, `item_id`
- `usage`: `prompt_tokens`, `completion_tokens`, `total_tokens`, `reasoning_tokens`
- `latency_s`, `request_id`, `reasoning_len` / `reasoning_sha` when present
- `parse_status`, `n_hypotheses`, `n_ok`, `n_parse_failure`
- `n_grounded` (parse-OK catalog `G####` members)
- `compile_status` (`COMPILE_OK` / `COMPILE_FAILURE` / `not_wired`)
- `n_zero`, `n_nonzero`, `n_unknown`

`COMPILE_FAILURE` ≠ `UNKNOWN` ≠ `ZERO`. Unwired compiler is `not_wired`,
not UNKNOWN.

## Non-negotiable

1. Aliases (`S1_True`, `generic_branch`, …) → `PARSE_FAILURE`. No repair.
2. Prompts may list allowed `representation_type` strings (the contract).
   They must **not** say “use Hermite divided differences on Guo”.
3. Proposer-visible prompts and user blobs must not contain `Phi_Gamma`,
   `L4`–`L7`, or `gold_types`.
4. No live API in unit tests; mock `chat_complete`.
5. Do not mutate `research/llm_abstraction/runs` or
   `research/grounded_proposer/runs`.
6. No TEST tuning. Method work is DEV-only.

## Gain accounting (vs frozen P1)

If P2 emits a representation type/structure absent from frozen P1:
**discovery gain**. If the same structure is now bindable because members
are `G####`: **grounding gain**. If old P1 output becomes verifiable
because the compiler improved: **compiler/language gain**. Never mix these.
