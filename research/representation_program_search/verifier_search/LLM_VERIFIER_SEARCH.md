# S7 LLM + verifier search contract

Status: infrastructure and mocked synthetic controls only. No live DeepSeek,
scientific DEV, TEST, or benchmark call has been made.

## Frozen causal role

S7 is **LLM state ranking**, not free-form representation proposal. For each
expanded M2 state, the unchanged S6 evaluator applies the exact compilation,
assumption, leakage, tautology, required-obligation coverage, dominance, and
session-receipt gates. Only the aggregate class `ZERO`, `NONZERO`, `UNKNOWN`,
or `COMPILE_FAILURE` can enter the next ranking request. Partial states carry
null feedback. Residuals, counterexamples, obligation details, verifier
receipts, evaluator targets, and hidden labels never enter the LLM boundary.

The LLM receives exactly:

- the public source catalog and assumption contract;
- the current public search state;
- the aggregate feedback class only;
- the first 32 M2-ordered legal child states and their typed actions;
- the strict opaque-ID permutation schema.

The response projector is the S4 final-only contract. It uses the frozen
DeepSeek Chat Completions settings, accepts one complete permutation of opaque
IDs, never reads or stores provider `reasoning_content`, and never repairs an
invalid response. API, parse, schema, model, request-ID, finish, or usage
failure invokes the separately recorded canonical fallback.

## Search and feedback policy

`RPSVerifierBatchedBeamPolicyV1` fixes:

- state-expansion budgets 10, 50, 100, 500, and 1000;
- the first 32 M2 legal children per parent;
- a width-32 layer beam;
- S6's unchanged aggregate-feedback bands;
- cross-parent ordering by
  `(feedback_priority_band, local_rank, parent_hash, child_hash)`;
- exact canonical duplicate pruning;
- continuation after ZERO exactly as frozen in `RPSVerifierSearchPolicyV1`.

The LLM supplies only `local_rank`. It cannot change the feedback band, create
a child, change typing, alter the grammar, weaken compilation, or declare
success. PROGRAM_SUCCESS still requires every S6 gate and ZERO for every
required obligation with persisted exact session receipts.

## Fail-closed AI validity

S7 reuses `RPSLLMCausalValidityV1`. A run is eligible as LLM-guided evidence
only if it has at least one accepted LLM decision, zero fallback decisions,
and complete usage for every decision. Any fallback, incomplete usage, or zero
accepted decisions marks the whole run
`INVALID_LLM_GUIDED_DIAGNOSTIC_ONLY` with
`llm_guided_scientific_run_eligible=false`. A verifier success in a run with
zero accepted LLM decisions remains a verifier result but is not AI evidence.

`llm_tokens_used` is the real sum of recorded prompt and completion tokens,
not a zero placeholder. Prompt, completion, reasoning, and cache counts are
also recorded separately, with `tokens_to_first_success` captured when exact
success is first established and before any successor-ranking call for that
successful state. Numeric seed 0--4 is deterministically bound to the retained
`seed-0`--`seed-4` label.

## Matched non-LLM control

`S6_MATCHED_BATCH32` uses the identical first-32 subset, feedback bands,
width-32 beam, duplicate handling, and shared banded cross-parent merge
function. Its local order is the canonical M2 `(complexity, state_hash)`
order, and it records zero LLM tokens.

This diagnostic does not replace full-frontier S6. Every S7 result records
`verifier_comparison_requires_matched_batch_control=true`, requires condition
`S6_MATCHED_BATCH32`, and names S6 as the strongest verifier baseline. No
S6-versus-S7 causal or AI_SEARCH_ADVANTAGE claim is admissible without running
the matched control on identical immutable inputs and budget.

## Atomic audit trail

Before verification or an API call, atomic `controller.json` binds the public
case, adapter/candidate-pool hash, grammar, search policy, verifier policy,
DeepSeek configuration, causal-validity policy, budget, batch/beam/merge
policy, and success gates.

Each expanded state writes:

- exact session artifacts below `states/state_NNNNN/obligations/`;
- atomic `states/state_NNNNN/evaluation.json`, binding compilation, aggregate
  class, obligation receipt paths/hashes, and semantic evidence hashes;
- atomic `decisions/decision_NNNNN.json`, binding the current state hash,
  presented legal states/actions, batch hash, request hash, safe final
  structured response, accepted/fallback ranking, ordered and chosen next
  states, aggregate feedback class, token usage, evaluation hash, and exact and
  semantic decision hashes.

The LLM request is stored for audit, but no residual or counterexample appears
there. Those remain only inside the exact verifier's own NONZERO step artifact.
