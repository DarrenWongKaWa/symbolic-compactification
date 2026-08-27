# HANDOFF — Subagent E (Grounded-Proposer-v2)

## SHA

`c172fe17110eb4bad9c2364cd669e2e71111dbfe` on `work/representation-llm`
(parent freeze `45b2b4dc7c823901f4b79713d279c6be7bae2859`).

## Tests

```bash
.venv/bin/python -m pytest tests/test_representation_llm.py -q
```

## What landed

- `prompts.py`: not-a-verifier SYSTEM prompt; V2 fields (`member_ids` G####,
  `latent_object`, `operators`, `reconstruction_rule`, `proof_obligations`);
  allowed types from `schema.REPRESENTATION_TYPES`; no gold names; does not
  instruct “use Hermite divided differences on Guo”.
- `parser.py`: `extract_json_object` then `parse_document_v2`.
- `propose.py`: `propose_p2(..., condition in {P2,P3,P4})`; P3 RAW; P2/P4 SOL
  via `packets_for_item(backends="relations")`.
- `p1_baseline.py`: read-only load/summarize of
  `research/grounded_proposer/runs/`; type map is evaluation-only.
- `score.py`: parse/ground/compile/verify; `compile_status="not_wired"`
  until Subagent C is importable.
- `run_p2.py`: one-item CLI; tests mock `chat_complete`.
- `PROTOCOL.md`: P1–P4, seeds, recorded fields.

## Remaining risks

- Compiler/verifier not wired (C). Scores stay `not_wired`; that is not UNKNOWN.
- No live P2/P3/P4 LLM evidence yet (by design in this commit).
- Live P2/P4 calls SOL and may write `llm_abstraction/runs/_cache`; unit tests
  use P3 or injected `packets_text` and never call the packetizer.
- P1 baseline mapping does not make `confluent_representation` parse as V2.
