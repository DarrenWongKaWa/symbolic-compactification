# Track V file ownership

Shared (orchestrator):

- `PROTOCOL.md`
- `FROZEN_INPUTS.json`
- `freeze_inputs.py`
- `STATUS.md`
- `research/PROGRAM_STATUS.md`

| agent | owns | tests |
|---|---|---|
| V1 decomposition | `decomposition/` | `tests/test_sv_decomposition.py` |
| V2 kernel factor | `factor/` | `tests/test_sv_factor.py` |
| V3 confluence | `confluence/` | `tests/test_sv_confluence.py` |
| V4 DD/Hermite cert | `dd_cert/` | `tests/test_sv_dd_cert.py` |
| V5 special functions | `special/` | `tests/test_sv_special.py` |
| V6 router | `router/` | `tests/test_sv_router.py` |
| V7 falsifier | `falsifier/` | `tests/test_sv_falsifier.py` |
| V8 Guo obligation map | `guo_map/` | `tests/test_sv_guo_map.py` |
| V9 literature | `literature/` | none required |

Do not edit `research/representation_invention/llm/runs/`.
Do not edit `research/grounded_proposer/runs/`.
Do not edit SOL.
Write `HANDOFF.md` in the owned directory.
