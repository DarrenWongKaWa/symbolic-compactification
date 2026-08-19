# A/B Experiment Protocol (agent protocol v0.2.1)

Short protocol for comparing the v0.2 agent workflow against the v0.2.1
agent workflow on identical workloads. The **deterministic engine is
identical** in both arms (engine v0.2.0: parser, verifier, budgets,
transforms, rules — zero semantic difference); only the agent layer differs.
The agent-protocol version in force is recorded in every run manifest
(`agent_protocol_version` alongside `engine_version`).

## Arms

- **Arm A (v0.2, main-agent only).** The main agent performs structure
  inspection, candidate discovery, verification, and promotion itself, per
  AGENTS.md rules. No proposer role.
- **Arm B (v0.2.1, main agent + STRUCTURAL_PROPOSER).** After each
  CERTIFIED state the main agent assembles a conjecture packet
  (`build_conjecture_packet`) and hands it, with the role contract
  `roles/STRUCTURAL_PROPOSER.md`, to one harness-native subagent
  (Qoder / Codex / Claude Code native subagent facility). Proposals come
  back as validated candidates (`validate_candidate`), are recorded with
  `record_proposal` (status `HYPOTHESIS`), verified deterministically, and
  promoted by the main agent only on ZERO.

Harness note: the proposer is executed by the harness's **native**
subagent/task mechanism. This repository deliberately provides no agent
runtime, LLM API integration, orchestration server, message broker, or
planner framework — it stays standalone Python + SymPy.

## Execution rules

1. Same workload, same input files, same declared symbols/assumptions in
   both arms; separate run directories.
2. Engine policy defaults untouched in both arms (parse/verify/transform/
   budget policies at their shipped defaults).
3. Every step — successes AND failures, proposals included — recorded via
   session records (rule 17). In arm B proposals are recorded before
   verification.
4. The verifier decides everything; neither arm may promote without ZERO.

## Metrics to compare

| Metric | Definition | Source |
|--------|------------|--------|
| Time to first nontrivial candidate | wall clock from run start to the first recorded candidate | run manifest timestamps / step telemetry |
| Candidates proposed | recorded proposer candidates | `run_summary: candidates_proposed` |
| ZERO promotions | verification steps adjudicated ZERO | `run_summary: zero_promotions` |
| NONZERO count | refuted candidates | `run_summary: nonzero_count` |
| UNKNOWN count | unresolved verifications | `run_summary: unknown_count` |
| Verifier calls | real verification steps (proposals excluded) | `run_summary: verifier_calls` |
| Wall clock | total recorded verifier wall time | `run_summary: wall_time_seconds` |
| Structural complexity before/after | `count_ops` of first input vs. current | `run_summary: count_ops_first` / `count_ops_current` |
| Tool-call burden | observable harness tool calls, if the harness exposes them | harness observability (optional) |

`run_summary(<run-dir>)` (`session.py`) computes the counters above from
existing step records — cheap reads, no new framework, no reconstruction
from file mtimes.

No model-token telemetry is collected by this repository: token usage is
recorded only if the harness itself exposes it; the engine never measures
or stores it.

## Scientific content policy

This protocol is workload-neutral. Experiment reports produced under it
must not embed formulas, workload names, or results in engine code or
records beyond what the session machinery already stores.
