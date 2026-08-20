# symbolic-compactification

An agent-native symbolic compactification and certification engine. A coding
agent may inspect structure and propose a clearer expression; deterministic
Python/SymPy code alone decides whether the proposal is exactly equivalent.

This repository is not a CAS replacement, an LLM runtime, or a scientific
answer store. It contains a small, harness-neutral method: ingest, preserve
semantic structure, propose, verify, record, and render explicit certified
mathematics.

Agents must read [AGENTS.md](AGENTS.md) before operating a scientific run. New
engineers should then read [the architecture map](docs/ARCHITECTURE.md).

## Install and test

Python 3.10 or newer is required. Check the interpreter explicitly because
some systems still map `python3` to an older release.

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest tests/ -q
```

The runtime dependency is only SymPy. The `dev` extra adds pytest.

## Five-minute workflow

The committed workspace is a skeleton. Runtime inputs and outputs below it are
ignored by Git, so the quickstart does not pollute the repository.

```bash
printf 'x**2 + 2*x*y + y**2' > workspace/input/expressions/current.txt
printf '(x+y)**2' > workspace/input/expressions/candidate.txt
printf '{"symbols": ["x", "y"]}' > workspace/input/expressions/symbols.json

symbolic-compactification inspect \
  workspace/input/expressions/current.txt \
  --symbols workspace/input/expressions/symbols.json

symbolic-compactification verify \
  --current workspace/input/expressions/current.txt \
  --candidate workspace/input/expressions/candidate.txt \
  --symbols workspace/input/expressions/symbols.json
```

`verify` is stateless. For a reproducible run, use the stateful pipeline:

```bash
symbolic-compactification init-session \
  --current workspace/input/expressions/current.txt \
  --symbols workspace/input/expressions/symbols.json

symbolic-compactification step --run RUN_ID \
  --candidate workspace/input/expressions/candidate.txt \
  --symbols workspace/input/expressions/symbols.json

symbolic-compactification finalize --run RUN_ID
```

`step` goes through one library pipeline: verify, persist the verdict, and
promote only when exact ZERO evidence is bound to that exact current/candidate
pair. `finalize` prints the explicit `FINAL CERTIFIED FORM` and writes both
`final/certified_expression.txt` and
`final/FINAL_CERTIFIED_FORM.md`.

Every command supports `--help`; every subcommand also accepts `--json` for a
single machine-readable result object.

## Verdicts and state

| Verdict | Meaning | CLI exit |
|---|---|---:|
| `ZERO` | Exact symbolic proof that current − candidate is zero | 0 |
| `NONZERO` | Exact counterexample proves the difference nonzero | 2 |
| `UNKNOWN` | Proof is unresolved or a resource/policy boundary was reached | 3 |

Parse, policy, persistence, and usage errors exit with 4. Approximate numeric
agreement never produces ZERO or NONZERO. UNKNOWN always blocks promotion.

The lifecycle (`HYPOTHESIS`, `UNVERIFIED`, `CERTIFIED`) is independent of the
verdict. Assumption state and proof state are separate as well; in particular,
`HUMAN_REQUIRED` is not the same as `PROOF_REQUIRED`.

## Representations

Reasoning representation and execution representation are deliberately
different. Ingestion retains `Sum`, `Product`, `Piecewise`, undefined/indexed
function calls, and common structure. The verifier may perform a targeted,
budgeted lowering for one proof attempt, but it never replaces the recorded
semantic source with a flattened diagnostic form.

The Wolfram adapter translates text only; it does not execute Mathematica or
use a Wolfram kernel.

## Python API

The stateful entry point is intentionally small:

```python
from symbolic_compactification import (
    adjudicate_candidate, init_session, load_expression, set_current,
)

current = load_expression("current.txt", ["x", "y"])
candidate = load_expression("candidate.txt", ["x", "y"])
session = init_session("workspace")
set_current(session, current)
outcome = adjudicate_candidate(session, candidate)
print(outcome.result.verdict, outcome.promoted)
```

`verify_equivalent()` remains available for stateless exact adjudication.
Direct `record_step()` and `promote()` are low-level persistence APIs and still
enforce sequence, state-hash, proof-status, assumption-gate, candidate-text,
and exact-evidence checks.

## Versions

Version 0.3.0 distinguishes three identities:

- repository/package version: release and installable API generation;
- engine version: deterministic parser/verifier/resource-policy generation;
- agent protocol version: proposer, state, provenance, and reporting contract.

All three are recorded in run artifacts. The meanings of
ZERO/NONZERO/UNKNOWN remain unchanged from engine v0.2.

## More detail

- [AGENTS.md](AGENTS.md) — authoritative harness-neutral operating contract
- [Architecture](docs/ARCHITECTURE.md) — module map, invariants, state machine,
  budgets, process guarantees, provenance, and errors
- [Engineering guidelines](docs/ENGINEERING_GUIDELINES.md) — change discipline
- [A/B experiment protocol](docs/AB_EXPERIMENT_PROTOCOL.md) — proposer-arm rules
- [STRUCTURAL_PROPOSER](roles/STRUCTURAL_PROPOSER.md) — optional native
  subagent role contract; the repository provides no agent runtime
