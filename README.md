# symbolic-compactification

**Propose a more compact expression, then prove `current − candidate` is
exactly zero.** Only a ZERO residual is promoted. The result is an auditable
certified compact form.

A coding agent inspects structure and proposes candidates. Deterministic
Python/SymPy code is the only judge.

This repository is not a CAS replacement, not an automatic theorem prover,
not an LLM runtime, and not a machine that discovers new physics. Approximate
numeric agreement never counts. UNKNOWN is not a pass.

**Current evidence** (`research/PUBLICATION_DECISION.md`): fail-closed
ZERO/NONZERO/UNKNOWN works; Method v2 can name closed auxiliaries after a
shallow ZERO; it does **not** currently beat CAS at discovery or certify
the Guo PRB closed form. Publication decision: **E** (more evidence
needed). No paper snapshot is frozen.

A **separate** structure-discovery line lives in
`research/structure_discovery/` (closed v0.1: typed exact-pattern protocol
works; invention unsolved). Frozen B9 is the Layer-1 baseline.

Layer 2 (`research/abstraction_invention/`): first-order LGG is **closed**
(`LGG_CLOSED.md`) — it solves substitution-level abstraction (v0.1 TEST
5/5 vs frozen B9 0/5), not scientific invention in general. Beyond-LGG
controls: distributivity is canonicalization (not invention); operator
graphs recover derivative/permutation edges; a gold-free score drops
`I*mu*theta0` below a polygamma family. LLM cell still BLOCKED. Decision
**E**. No paper.


The Grok skill is
[`.grok/skills/symbolic-compactification/`](.grok/skills/symbolic-compactification/SKILL.md).
Agents operating a run must also read [AGENTS.md](AGENTS.md).

## Proposer modes

Default is `main`: the main agent writes candidates. No sub-agent
infrastructure is required. Subagent is never the unique path.

| Mode | When |
|---|---|
| `main` (default) | Everyday use; stays main unless you ask otherwise |
| `subagent` | Optional isolation you request when the working directory is noisy or the expression is extremely long |
| `auto` | Only if you ask: Skill then picks `subagent` for large expressions |

Record intent: `init-session --proposer-mode main|subagent|auto`.
The verifier path is identical in every mode. Promote only on ZERO.

## Examples

- [`examples/basic/`](examples/basic/) — 5-minute identities
- [`examples/medium/`](examples/medium/) — `Sum` compactification
- [`examples/long/`](examples/long/) — real Guo σ_abc DC source (input only;
  not a certified compact form)

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

Committed fixtures do not need a workspace copy:

```bash
symbolic-compactification verify \
  --current examples/medium/current.txt \
  --candidate examples/medium/candidate.txt \
  --symbols examples/medium/symbols.json
```

Exit 0 is ZERO. A wrong candidate exits 2 (NONZERO):

```bash
symbolic-compactification verify \
  --current examples/medium/current.txt \
  --candidate examples/medium/mutation.txt \
  --symbols examples/medium/symbols.json
```

`verify` is stateless. For a reproducible run, copy inputs under
`workspace/input/` (runtime files stay untracked) and use the session
pipeline. Default proposer is `main`:

```bash
symbolic-compactification inspect \
  examples/medium/current.txt \
  --symbols examples/medium/symbols.json --json

symbolic-compactification init-session \
  --workspace workspace \
  --current examples/medium/current.txt \
  --symbols examples/medium/symbols.json \
  --proposer-mode main --json

symbolic-compactification step --run RUN_ID --workspace workspace \
  --candidate examples/medium/candidate.txt \
  --symbols examples/medium/symbols.json

symbolic-compactification finalize --run RUN_ID --workspace workspace
```

Long Wolfram input (inspect only; JSON `text` is the full native translation):

```bash
symbolic-compactification inspect \
  examples/long/Guo_Sigma_abc_dc_exact.txt --format wolfram --json
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
- [STRUCTURAL_PROPOSER](roles/STRUCTURAL_PROPOSER.md) — optional native
  subagent role contract; the repository provides no agent runtime
- [Project skill](.grok/skills/symbolic-compactification/SKILL.md) —
  operating skill; default proposer `main`, optional `subagent` / `auto`
- [A/B experiment protocol](docs/AB_EXPERIMENT_PROTOCOL.md) — experiment
  appendix, not the default user path
- [Skill vs blank (σ_abc)](docs/experiments/2026-08-21-skill-vs-blank.md) —
  live isolated-agent probe
- [Progress vs PRB closed form](docs/experiments/2026-08-21-progress-vs-prb-closed-form.md) —
  how far each agent got, and what is still missing
