# S4/S5 auditable LLM search policy

Status: implementation frozen for mocked calibration; no scientific DEV or
TEST calls have been made.

## Causal roles

- **S4 / M7**: DeepSeek ranks an exact bounded list of legal child search
  states. It returns only a complete permutation of opaque child IDs.
- **S5 / M6**: DeepSeek ranks an exact bounded list of legal typed actions. It
  returns only a complete permutation of opaque action IDs.

Neither method writes a representation, creates an action, sees evaluator
data, receives verifier feedback, or certifies success. The deterministic M2
kernel remains responsible for `extract_candidate_pool`, `legal_actions`,
`expand_state`, typing, canonical hashes, complexity bounds, grammar
ablations, and latent-object ablation.

## Frozen DeepSeek contract

`RPSLLMSearchProtocolV1` uses the OpenAI-compatible **Chat Completions** API:

- primary model: `deepseek-v4-pro`;
- robustness model: `deepseek-v4-flash`;
- thinking: `{"type":"enabled"}` through SDK `extra_body`;
- reasoning effort: `high`;
- response format: `{"type":"json_object"}`;
- maximum output: 4096 tokens;
- no temperature or top-p parameter;
- one call per nonterminal expanded state and no automatic retry.

The configuration follows the official DeepSeek
[Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/),
[thinking-mode](https://api-docs.deepseek.com/guides/thinking_mode/), and
[JSON-output](https://api-docs.deepseek.com/guides/json_mode/) documentation.
The prompt contains the word JSON and an exact output example, as required by
JSON mode.

Five fixed replication labels are available: `seed-0` through `seed-4`.
Every result binds `seed` deterministically to the label suffix (`0` through
`4`) while retaining `seed_label`. They are experiment seed identifiers, not
an unsupported API seed parameter.

## Strict output contract

The only accepted final object is:

```json
{"ranking": ["OPAQUE_ID_1", "OPAQUE_ID_2"]}
```

The list must be a complete permutation of every presented ID. Unknown,
duplicate, missing, non-string, free-form, extra-field, truncated, model
mismatch, missing-request-id, and incomplete-usage responses are invalid.
Invalid output is never repaired. Search applies the separately recorded
`PRESENTED_CANONICAL_ORDER_V1` fallback.

Fallback keeps a failed run replayable as a diagnostic; it does not make the
run LLM-guided evidence. `RPSLLMCausalValidityV1` marks a completed run
scientifically eligible only when it has at least one accepted LLM ranking,
zero fallback decisions, and complete usage for every decision. The terminal
result records `accepted_llm_decisions`, `llm_causal_valid`,
`llm_causal_validity_status`, exact invalid-reason codes, and
`llm_guided_scientific_run_eligible`. Any fallback, any incomplete usage, or
zero accepted decisions fails closed to
`INVALID_LLM_GUIDED_DIAGNOSTIC_ONLY`. The pre-call header records this policy
as `PENDING_FAIL_CLOSED`; it cannot prematurely assert run validity.

Provider `reasoning_content` is never accessed. No reasoning body, hash,
length, tail, or reused reasoning message is retained. The projector keeps
only the parsed final JSON object, its content hash/length, model, request ID,
finish reason, latency, and complete usage counts. A final JSON object that
itself contains a reasoning/chain-of-thought field is rejected and only its
whole-content hash/length are retained.

## Shared frozen frontier policy

`RPSLLMBeamBatchPolicyV1` is identical for S4 and S5:

- state budgets: 10, 50, 100, 500, 1000 expanded states;
- candidate batch: first 32 legal children in M2's existing
  `(complexity, canonical_hash)` order;
- layer beam width: 32;
- within a parent, use the accepted LLM permutation or canonical fallback;
- across parents, order by `(local_rank, parent_hash, child_hash)`;
- exact canonical-hash duplicate removal;
- no verifier, evaluator, SOL, target label, or hidden-gold ordering.

The method records every batch and beam truncation. It is not exhaustive:
`llm_search_complete=false`, the finite candidate pool remains
`branching_incomplete=true`, and global expression enumeration is never
claimed.

### Mandatory matched-frontier control

Current S2 applies its symbolic heuristic to the full generated child
frontier for each parent before selecting the layer beam. S4/S5 first truncate
each parent's M2-ordered frontier to 32 presented children. They are therefore
not fully frontier-matched to S2 even though their underlying legal generator
is identical. Every run/header records:

```json
{
  "symbolic_comparison_requires_matched_batch_control": true,
  "symbolic_comparison_status": "UNMATCHED_FRONTIER_DO_NOT_CLAIM_AI_ADVANTAGE"
}
```

`S2_MATCHED_BATCH32` is implemented as the required diagnostic. It uses the
identical first 32 M2-ordered legal children for each parent, the same beam
width, canonical duplicate handling, and the same shared
`(local_rank, parent_hash, child_hash)` merge function. Its only difference is
that the frozen symbolic heuristic supplies each parent's local permutation.
It records every presented and locally ranked batch plus every cross-parent
beam layer.

No S2-versus-S4/S5 efficiency or AI_SEARCH_ADVANTAGE claim is admissible
unless that matched diagnostic is executed on the same immutable inputs and
budget. Full-frontier S2 remains the strongest symbolic baseline;
`S2_MATCHED_BATCH32` is an additional causal control and explicitly records
`replaces_full_frontier_s2=false`.

## Atomic decision evidence

Before the first call, an atomic `run_header.json` records condition, model
configuration, case/proposer hashes, candidate-pool hash and incompleteness,
SearchPolicy, grammar, budget, batch/beam/fallback policy, and the mandatory
matched-frontier comparison gate. Thus a crash cannot leave contextless
decision files.

Each call then produces an atomic `decision_NNNNNN.json` before its ranked children
enter the next frontier. It contains:

- exact current public state and canonical hash;
- exact presented child states (S4) or actions plus audit-only mapping to
  resulting hashes (S5);
- full public request and request/prompt/batch hashes;
- raw parsed final JSON when safe to retain;
- accepted ranking or separate fallback record;
- chosen next-state hash;
- model/config, seed label, request ID, latency, and all token/cache/reasoning
  token counts;
- `private_reasoning_persisted=false` and no private reasoning content.

The completed in-memory result is also atomically written as
`search_result.json`. `states_to_first_success`,
`time_to_first_success_seconds`, and `tokens_to_first_success` remain null:
success evaluation is a separate exact evaluator stage, and S4/S5 never
self-certify.
