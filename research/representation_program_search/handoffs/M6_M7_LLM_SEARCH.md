# M6 + M7 handoff — S4/S5 auditable LLM search

Date: 2026-08-30
Branch: `work/rps-symbolic-beam`
Base for this subtask: `4a5f178`
Scope: infrastructure plus mocked synthetic controls; zero live DeepSeek,
scientific DEV, TEST, or package calls

## Delivered

- `search/llm_contract.py`
  - frozen `RPSLLMSearchProtocolV1` configuration;
  - exact `deepseek-v4-pro` primary and `deepseek-v4-flash` robustness models;
  - Chat Completions, thinking enabled, reasoning effort high, JSON-object
    output, no temperature/top-p;
  - strict opaque-ID permutation validator;
  - projection of final JSON and complete usage/request provenance without
    accessing or retaining provider private reasoning;
  - proposer/evaluator firewall and atomic no-overwrite JSON writer;
  - injectable mock transport and optional OpenAI-compatible live transport.
- `search/llm_guided.py`
  - S4 state ranking and S5 action ranking over the exact shared M2 frontier;
  - globally fixed 32-candidate batch and 32-state layer beam;
  - deterministic canonical fallback, duplicate pruning, and frozen budgets;
  - atomic pre-call `run_header.json`, per-decision records, and terminal
    `search_result.json`;
  - full token/cache/reasoning-token accounting and explicit null
    states/time/tokens-to-first-success pending external exact evaluation.
- `search/LLM_SEARCH.md`, public exports, and search README integration.
- `tests/test_rps_llm_guided.py`, using mocked transports only.

## Scientific and privacy boundaries

The model sees only the `PublicCase` source catalog/expressions, assumptions,
namespace, grammar, current public partial state, and either legal child states
or legal typed actions. A second boundary audit rejects forged gold, target,
reference, verification, residual, counterexample, proof, audited-depth, or
verdict fields even if a caller manually constructs a `PublicCase` without
using `load_public_case`.

S4/S5 do not import or call the old free-form LLM client, SOL, the evaluator
package loader, or the verifier. They do not inspect compile/proof fields for
ordering and do not claim PROGRAM_SUCCESS. Every success-efficiency field is
left null with `success_evaluation=EXTERNAL_EVALUATOR_REQUIRED`.

Provider `reasoning_content` is not accessed—not even to compute length or a
hash. The implementation does not store a reasoning tail and never feeds
reasoning into another request. Mock responses include a private-reasoning
sentinel; tests prove it is absent from every decision/result artifact. Only
the numeric `reasoning_tokens` usage count is retained. A final JSON object
containing a reasoning/CoT field is itself rejected and not stored.

## Strict failure behavior

Accepted response shape is exactly `{"ranking":[...]}` with one occurrence
of every presented opaque ID. Unknown, duplicate, missing, free-form,
extra-field, malformed JSON, truncated finish, model mismatch, missing request
ID, or incomplete usage invalidates the whole response. No subset or nearest
ID is salvaged. `PRESENTED_CANONICAL_ORDER_V1` is recorded separately and is
then used to keep the search mechanically executable.

Per-decision evidence includes current hash/state, exact candidate batch,
batch hash, full public request, prompt/request hashes, raw safe structured
final response, accepted/fallback ranking, chosen next hash, model/config,
seed label, latency, request ID, complete usage, cumulative tokens, and a
canonical record hash. It is fsync'd to a temporary file and atomically
renamed before children enter the next frontier. Existing artifacts are never
overwritten.

`run_header.json` is written atomically before the first API call. It anchors
condition, config, case/proposer hash, public-context hash, candidate-pool
hash/incompleteness, exact SearchPolicy, grammar, budget, batch/beam/fallback
policy, and the comparison gate, so partial runs remain interpretable.

## Frozen shared S4/S5 policy

- M2 `extract_candidate_pool`, `expand_state`, `legal_actions`, and
  `SearchPolicy` unchanged;
- state budgets `10/50/100/500/1000`;
- first 32 M2-ordered legal children presented;
- layer beam width 32;
- accepted local rank then parent hash then child hash;
- five provenance labels `seed-0` through `seed-4`;
- grammar and latent-object ablations unchanged;
- candidate-batch and beam truncation explicitly reported;
- no exhaustive-search claim.

## Causal frontier mismatch gate

S4/S5 generate the same M2 legal frontier but expose only the first 32
M2-ordered children per parent. Current S2 ranks the full per-parent frontier
before its layer beam. Therefore the methods are not yet fully
frontier-matched. Every run and header records:

```text
symbolic_comparison_requires_matched_batch_control = true
symbolic_comparison_status = UNMATCHED_FRONTIER_DO_NOT_CLAIM_AI_ADVANTAGE
```

No S2-vs-S4/S5 or AI_SEARCH_ADVANTAGE conclusion is permitted until a frozen
`S2_MATCHED_BATCH32` diagnostic (or equivalent identical-subset control) is
run. Full-frontier S2 remains the strongest symbolic condition; the matched
diagnostic is an additional causal control, not a replacement.

## Documentation basis

Reviewed official DeepSeek documentation on 2026-08-30:

- `https://api-docs.deepseek.com/api/create-chat-completion/`
- `https://api-docs.deepseek.com/guides/thinking_mode/`
- `https://api-docs.deepseek.com/guides/json_mode/`

These pages document both required model identifiers, Chat Completions,
thinking-mode control, high reasoning effort, and JSON-object response mode.

## Tests

Focused M6/M7 + S2 + M2/M4 + M1:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q \
  tests/test_rps_llm_guided.py \
  tests/test_rps_symbolic_beam.py \
  tests/test_rps_enumerative_random.py \
  tests/test_rps_program_ir.py

68 passed in 13.20s
```

Repository-wide:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q

1790 passed in 211.99s
```

The 17 M6/M7 tests cover exact Chat Completions dispatch, both frozen models,
five seed labels, thinking/high/JSON configuration, strict response failures,
private-reasoning exclusion, complete usage, API/parse fallback, exact S4 and
S5 candidate presentations, M2 frontier matching before the explicitly
reported batch truncation, run-header-before-call ordering, atomic hashes and
no-overwrite behavior, fixed budgets/policy, grammar and latent ablation,
forged evaluator-context rejection, zero success self-certification, and the
mandatory unmatched-S2 causal gate.

## Integration boundary

No package, benchmark manifest, parser, verifier, SOL code, M1 program IR, M2
candidate/action generation, S2 weights/policy, or scientific result was
changed. Do not interpret mocked ranking tests as evidence that DeepSeek helps
search. A live DEV calibration is a later coordinator-controlled experiment.
