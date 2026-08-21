---
name: symbolic-compactification
description: >
  Use when simplifying, compactifying, or certifying a symbolic
  expression with the symbolic-compactification engine; when a candidate
  simplification must be checked for exact ZERO residual; or when the
  user runs /symbolic-compactification.
argument-hint: "[main|subagent|auto]"
---

# Symbolic compactification

Exact propose-and-verify. Full rules: `AGENTS.md`. This skill is not a CAS,
not a theorem prover, and not a physics-discovery box. LLM judgment is never
proof.

## Proposer (configurable)

The proposer path is configurable. Subagent is never the unique path.

| Mode | Who writes the candidate |
|---|---|
| Default: `main` | The main agent |
| Optional: `subagent` | One isolated STRUCTURAL_PROPOSER |
| Optional: `auto` | Heuristic chooses `main` or `subagent` |

Resolution, first match wins:

1. User said `main` or `subagent` (argument or explicit request).
2. User said `auto`.
3. Default `main`.

Use `auto` only when the user asked. Default remains `main`. You may recommend `--proposer-mode subagent` when the working directory is noisy or the current expression is extremely long; do not switch unless the user asked for `subagent` or `auto`.

`auto` heuristic (Skill-layer only; does not change the verifier):

- expression ≥ 8 KiB or `count_ops` ≥ 400 → `subagent`
- otherwise `main`

Record intent with `init-session --proposer-mode`. Evidence-derived
`proposer_mode` in `run_summary` is separate.

## Verifier (mandatory)

Every candidate goes through `verify` or `step`. Promote only on ZERO.

| Verdict | Action |
|---|---|
| ZERO | Promote; candidate becomes current |
| NONZERO | Read residual + counterexample; propose again |
| UNKNOWN | Do not promote |

## Simplest path

Copy originals to `workspace/input/raw/`. Work on copies under
`workspace/input/expressions/` (`current.txt`, `candidate.txt`,
`symbols.json`). Never transcribe long expressions by hand.

```bash
symbolic-compactification inspect current.txt --symbols symbols.json --json
# Wolfram sources instead:
# symbolic-compactification inspect source.txt --format wolfram --json
# write the JSON "text" field (full native translation) to current.txt

symbolic-compactification init-session \
  --current current.txt --symbols symbols.json \
  --proposer-mode main --json
# capture run_id from the JSON

# write candidate.txt, then:
symbolic-compactification step --run RUN_ID \
  --candidate candidate.txt --symbols symbols.json --json

symbolic-compactification summary --run RUN_ID --json
symbolic-compactification finalize --run RUN_ID
```

`inspect --json` includes `structure_summary`. `step` promotes only on ZERO.

### If `proposer=subagent`

Spawn ONE read-only harness-native subagent. Its prompt contains only:

- `roles/STRUCTURAL_PROPOSER.md`
- the current expression
- `structure_summary` from `inspect --json`

On a NONZERO retry, also pass this step's residual and counterexample.
Do not give it the working tree, git history, tests, engine source, or
certificates. Do not paste the full conjecture packet. The child returns
JSON; the main agent writes `candidate.txt`.

```python
from symbolic_compactification import (
    build_conjecture_packet, record_proposal, validate_candidate,
)
packet = build_conjecture_packet(session)  # provenance only
candidate = validate_candidate(child_json)
record_proposal(session, candidate, harness_task_or_subagent_id=child_id)
```

Then `step` as above. The main agent verifies and is the only one that may
promote.

## Advanced path

Same CLI, one candidate at a time: inspect → write candidate → `verify` or
`step` → `summary` → `finalize`. Read residual and
`workspace/runs/<id>/steps/`.

## Red flags

- Treating a candidate as a result before ZERO
- Skipping `verify` because the rewrite looks obvious
- Requiring STRUCTURAL_PROPOSER on every step
- Dumping the repository into the proposer subagent
- Shipping a compact form from another repo as if it were already certified
