# M7 / S7 handoff — LLM + exact-verifier search

Date: 2026-08-30
Branch: `work/rps-symbolic-beam`
Scope: controller implementation plus deterministic mocked/synthetic controls;
zero live DeepSeek, scientific DEV, TEST, package, parser, verifier, or SOL
calls

## Delivered

- `verifier_search/llm_controller.py`
  - S7 LLM state ranking over the first 32 exact M2 legal children;
  - unchanged S6 compile/evaluate/session-receipt success gates;
  - aggregate four-class feedback as the only proof signal exposed to the LLM;
  - S6 feedback bands combined with local LLM rank in one shared banded merge;
  - width-32 layer beam and frozen state budgets;
  - atomic header, state evaluation, decision, receipt, and result artifacts;
  - real token accounting and fail-closed run-level AI validity.
- `S6_MATCHED_BATCH32`
  - identical first-32/beam/band/merge path with deterministic canonical local
    order and zero LLM tokens;
  - explicit non-replacement of strongest full-frontier S6.
- neutral shared banded merge contract in `search/beam_policy.py`.
- `verifier_search/LLM_VERIFIER_SEARCH.md`, README/public exports, and focused
  tests in `tests/test_rps_llm_verifier_search.py`.

## Scientific boundaries

S7 never generates a representation or legal action. DeepSeek receives only
the public case, current state, typed legal child states/actions, and aggregate
`ZERO`/`NONZERO`/`UNKNOWN`/`COMPILE_FAILURE` class (null for a partial state).
It never receives a residual, counterexample, obligation receipt, target,
reference program, or hidden role. Provider private reasoning is never read,
hashed, stored, or reused.

PROGRAM_SUCCESS is exactly the S6 result: assumptions must be declared or
derived, leakage explicitly cleared, compilation successful, the program
non-tautological and coverage-complete, and every required exact session
receipt ZERO. UNKNOWN is retained at the frozen lower band and is never
success. NONZERO and COMPILE_FAILURE prune only the evaluated state.

## Fail-closed causal claims

Under `RPSLLMCausalValidityV1`, any API/parse/schema fallback, incomplete
usage, or zero accepted LLM rankings makes the entire S7 run diagnostic-only.
Fallback can keep search executable but cannot count as LLM-guided evidence.
A ZERO success with no accepted LLM decision is explicitly not AI evidence.

Every S7 result requires the matched `S6_MATCHED_BATCH32` control before any
S6-vs-S7 efficiency or AI_SEARCH_ADVANTAGE claim. Full-frontier S6 remains
strongest and is not modified or replaced.

## Verification controls

The test suite uses no live client. It covers:

- exact ZERO, NONZERO, UNKNOWN, and COMPILE_FAILURE aggregation;
- exact persisted verifier receipts and hard success gates;
- assumption-incomplete, leakage-uncleared, and tautology rejection;
- feedback-only prompts with residual/counterexample firewall;
- private-reasoning exclusion;
- real token totals, seed binding, and terminal causal validity;
- API, malformed-JSON, incomplete-usage, and zero-decision invalidation;
- exact first-32 M2 frontier matching and state-for-state matched-control replay;
- atomic pre-call header, decision/evaluation/request/candidate hashes, tamper
  detection, frozen budgets, adapter type, and nonempty-output rejection.

Focused S7/S6/S4/S2/M2/M1 regression command:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q \
  tests/test_rps_llm_verifier_search.py \
  tests/test_rps_verifier_search.py \
  tests/test_rps_verifier_m2_adapter.py \
  tests/test_rps_llm_guided.py \
  tests/test_rps_symbolic_beam.py \
  tests/test_rps_enumerative_random.py \
  tests/test_rps_program_ir.py

98 passed in 148.44s
```

Repository-wide:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q

1820 passed in 363.36s
```

The implementation commit SHA is recorded by the coordinator after commit.
