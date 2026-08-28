# MERGE GATE 1 — Track V3

Merged isolated worktrees V3-A..K onto `research/iterated-confluence-verification-v1`.
Frozen inputs unchanged.

| | |
|---|---|
| Freeze commit | `dcfb90cac087a47241aced2dc0c3b851f1a12e21` |
| `FROZEN_INPUTS_V3.json` sha256 | `e1fc6df85b0d293f3251ec87c1827409f402c01752a73251be8899f5b00c41db` |
| n frozen families | 7 |
| LLM calls | 0 |

## Tests

Package `tests/test_ic_*.py`: **174 passed** after coordinator patches
(mul-args AppliedUndef peel; `check_limit` not blocked by V2 OPS_CAP=200).
Generic suite + falsifier: **false FAMILY_ZERO = 0**.

## Coordinator patches (soundness, not Guo identities)

1. Spectator split peels common `AppliedUndef` from `Mul.args` without
   `cancel` expansion. Track V cancel-peel expanded 176-op Guo pairs to
   1355 ops; mul-args peel yields 172 / 83 with exact reconstruction.
2. Expanding splits (`local_ops > full_ops`) are rejected.
3. `certify_one_parameter` always runs Track V `check_limit` on the
   (possibly split) kernel. V2 `OPS_CAP=200` only skips `certify_edge`.

## Frozen-input integrity

`freeze_v3.build()` family ids match disk. Source run SHA match True.
No historical run JSON rewritten.
