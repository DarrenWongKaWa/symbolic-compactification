# Final Review R2 — Program Synthesis

Reviewer role: independent program-synthesis reviewer  
Authority reviewed: `b542567` (gate evidence binds integrated head `a7ad6ab`)  
Review mode: read-only closure audit; no case, method, manifest, parser, or verifier changes

## Recommendation

**Publication verdict: F — STRUCTURED SEARCH ALSO FAILS TO SUPPORT REPRESENTATION INVENTION.**

This recommendation uses “fails to support” literally. The experiment did not
run structured search on the mandatory scientific DEV suite, so it did not
show that enumerative, symbolic, verifier-guided, SOL-guided, or LLM-guided
search algorithms fail. It showed that the experiment could not construct its
pre-required scientific calibration suite under its own frozen freshness,
assumption, leakage, parser/IR, and admission rules. There is therefore no
scientific evidence for representation invention, no AI-search comparison,
and no basis for verdict A, B, C, D, or an evidence-positive reading of E.

## Evidence inspected

- contracts and grammar: `5321eaa`, especially
  `research/representation_program_search/REPRESENTATION_GRAMMAR_V1.md`,
  `PROGRAM_IR.md`, `SEARCH_STATE_IR.md`, `SCORING_POLICY.md`, and
  `CAUSAL_EXPERIMENT.md`;
- legal `COMPOSE` access-path correction: `5216f77`;
- typed M1 constructor/compiler: `3f0cf7f`, under
  `research/representation_program_search/program_ir/`;
- finite S0/S1 frontier and S0 control: `c16b763`, with pre-DEV V2
  reachability repair `d483767`, under
  `research/representation_program_search/search/`;
- S2 symbolic beam: `e101009` and isolation correction `a52e5a9`;
- S3 frozen-SOL search: `b23b565`;
- S4/S5 LLM controls: `779377c` and fail-closed matched-control follow-up
  `dd2c1fc`;
- S6 verifier search and M2 adapter: `6e1aafc`, `93cd86d`, and post-hoc exact
  evaluation `73a9111`;
- S7 plus matched verifier-only control: `ba6cdcf`;
- F0 boundary, runner, and sessioned evaluator: `c9c8afe`, `bbcbed3`, and
  `6e5fbef`;
- atomic one-condition runner: `28745de` and dispatch tests `64dca54`, under
  `research/representation_program_search/evaluation/runner.py`;
- final gate: `b542567`, especially
  `research/representation_program_search/audits/dev_gate_final/GATE_AUDIT.{md,json}`.

I independently replayed the focused M1, S0–S7, F0, atomic-runner, and final
gate test files at `b542567`: **149 passed in 191.61 seconds**. This is software
conformance evidence only.

## What was demonstrated

### 1. A concrete formal representation language was implemented

`RepresentationGrammarV1` is more than prose. M1 represents hash-bound source
members, typed latent objects, explicit node multiplicity, operator DAGs,
member assignments, assumption references, and exact obligations. The
compiler constructs candidate expressions without issuing proof verdicts;
the verifier boundary remains explicit and fail-closed. Canonical JSON and
bound-parameter alpha normalization are implemented. Newton and Hermite nodes
are structurally separated, and compilation rejects illegal ablation/operator
combinations.

This demonstrates an executable representation-program IR and constructor.
It does **not** demonstrate that the language is sufficient for fresh R3+
science, that its programs can be discovered efficiently, or that its
complexity model identifies scientifically minimal abstractions.

### 2. The search conditions are executable on synthetic/diagnostic inputs

S0 and S1 share a finite generated frontier; S2 applies a deterministic
symbolic beam; S3 consumes a hash-bound frozen-SOL replay; S4 and S5 rank only
legal states/actions; S6 attaches exact four-class verifier feedback; S7
ranks a matched exact-evaluated batch and requires `S6_MATCHED_BATCH32`; F0
retains the historical free-form architecture behind a strict sessioned
evaluator. The atomic runner binds a public case and independent clearance,
dispatches one immutable condition job, persists method-native evidence, and
preserves exceptions as `METHOD_ERROR` rather than scientific failure.

The mock/synthetic tests support those interface and fail-closed claims. They
do not measure search success, efficiency, LLM judgment, verifier guidance,
SOL anchoring, or generalization. There was no live DeepSeek call, no
scientific S3 replay, and no scientific job output.

### 3. Exact known programs can be compiled and verified

M1 tests and case diagnostics show that explicitly authored Newton, Hermite,
recurrence, composition, and primitive reconstructions can compile and can be
submitted to exact verification. The independently admitted `C9H4` package
is a genuine R2 constructor/verification control: its named-Newton and
primitive VALUE/LINEAR_COMBINATION programs both have exact ZERO evidence.

That is constructor expressivity for a known R2 program, not program-search
discovery. `C9H4` was never placed in a complete DEV manifest and no S0–S7/F0
method was run on it.

## What was not demonstrated

### 1. No formal-search scientific result exists

The final independent audit at `b542567` records only 1/5 required calibration
slots ready: R2 `C9H4`. R3, R4/R5, R6, and the runnable negative trap are
missing. Consequently the mandatory first DEV gate is `GATE_BLOCKED`; the
repository has no DEV manifest, TEST freeze manifest, held-out result, or
scientific `JOB_RESULT.json`. The gate correctly forbids scientific search,
live LLM calls, TEST freeze, held-out runs, and method-result interpretation.

Therefore none of the following was tested: PROGRAM_SUCCESS@budget,
states/time/tokens to success, deterministic-versus-LLM efficiency,
symbolic-versus-LLM ranking, verifier-feedback benefit, SOL benefit/anchoring,
grammar advantage, AI search advantage, stochastic replication, or R3+
generalization.

### 2. Candidate/action reachability is not search discovery

The V2 repair in `d483767` added generic public-expression
parameterization, bounded source-derived coefficients, larger structural
bounds, two multiplicity orientations, and an earliest-plus-recent output
window. The corresponding tests manually select the exact legal action path
for diagnostic `rps-real-c8q2` and `rps-real-c3j9`; one test is explicitly
named `test_dlmf_reference_program_is_reachable_by_only_legal_public_actions`
and another follows the repeated-node reference program.

Those tests establish that a human-known path is present in the generated
graph and remains under the frozen complexity bound. They do not establish
that S1 reaches it within 10/50/100/500/1000 expansions, that a heuristic
selects it, or that the path is fresh. Later independent audits classify C8Q2
as R1 diagnostics and C3J9 as an old-TEST structural variant. These tests
must remain labeled method-development reachability checks, never empirical
search evidence.

S1 is also exhaustive only over `RPSCandidatePoolV2`'s capped, source-derived
frontier. The implementation records `branching_incomplete=true`; “enumerative
search” must not be reported as complete enumeration of the grammar or latent
expression space.

### 3. Named-primitive leakage was controlled in design, not tested in search

The grammar exposes `HERMITE_DD` as a named operator, and M1 directly
constructs its confluent derivative/factorial semantics. That can supply much
of the target representation. The frozen `G_NO_HERMITE` and `G_PRIMITIVE`
controls are the right causal response, and `G_PRIMITIVE` has an executable
`COMPOSE` path.

However, there is no admitted R3+ case and no search result under any grammar
ablation. Diagnostic reference programs compiling under an ablation show only
constructor expressivity. The admitted R2 primitive control shows that one
known Newton representation can be written without the named Newton operator;
it does not show that primitive search constructs it. No claim resembling
“Hermite invented compositionally” is supported.

Even `G_PRIMITIVE` is not representation-neutral: search receives bounded
latent schemas and reconstruction coefficients extracted from the public
source expressions. A future primitive success would be stronger than a
named-Hermite success, but still needs a leakage audit and matched search
baselines before being called invention.

## Residual program-synthesis risks

1. The non-tautology guard in
   `research/representation_program_search/program_ir/compiler.py` detects
   only a narrow independent exact-source `VALUE` wrapper. A full-expression
   parameter abstraction can reproduce a member through VALUE without being
   text-identical to that member's source. Complexity/exceptions penalize such
   constructions, and SOURCE_LITERAL controls are isolated, but the present
   detector does not prove minimum-description or semantic non-memorization.
   Before any future success claim, adversarial tests should show that
   parameterized self-reconstruction and compact member-index encodings cannot
   satisfy PROGRAM_SUCCESS merely by exact equality.

2. The score/complexity policy is implemented and task-invariant, but it has
   not been calibrated on the required DEV suite. Its scientific preference
   for reusable abstractions over short exact encodings is therefore a design
   hypothesis, not validated behavior.

3. The action vocabulary is implemented, but some actions/operators are only
   synthetically exercised. Absence of an admissible R4/R5/R6 package means
   BASIS, recurrence, and multi-operator-master reachability has no fresh
   scientific validation.

These risks do not overturn the gate; they strengthen the requirement not to
promote implementation coverage into a method result.

## Final assessment

The work successfully turns the previous free-form idea into auditable
program-synthesis infrastructure: a typed language, bounded search kernels,
strict LLM roles, exact-verifier integration, matched controls, and atomic
evidence. That is a real engineering result.

Scientifically, the experiment stopped before its first admissible
calibration. Formal search was **implemented but not evaluated**. The only
defensible closure is verdict **F**, accompanied everywhere by the explicit
qualification that the failure is absence of supporting scientific evidence
caused by an infeasible benchmark gate—not an observed failure of structured
search algorithms.
