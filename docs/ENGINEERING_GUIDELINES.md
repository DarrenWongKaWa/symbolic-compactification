# Engineering Guidelines

Permanent, workload-independent engineering guidance for the symbolic
compactification engine, distilled from the first real-workload experience and
codified in the v0.2 engine. Scientific content is deliberately excluded: this
document is about the engine and the workflow, referenced by component only.

Guidance here is normative for future engine work and future runs. Where a
guideline names a module, that module is the v0.2 implementation of the
principle.

---

## 1. Ingestion is multi-frontend: CAS-native sources need an adapter layer

Real theoretical-physics expressions arrive in CAS-native syntax (e.g. Wolfram
Language text: `Sum[...]`, `Piecewise[...]`, special functions, indexed
functions, comments), not in the engine's own dialect. A frozen engine that
only accepts its own dialect will reject essentially all real sources at the
character/whitelist gates.

- Design ingestion as multi-frontend. The canonical internal representation is
  engine-owned; each source language is an adapter.
- Translation is a first-class, tested, versioned engine capability — never
  something improvised in the workspace at run time.
- Translation is *ingestion only*. Verification remains engine-internal and
  exact; an adapter never becomes a verification backend.
- v0.2 implementation: `src/symbolic_compactification/adapters/wolfram_text.py`
  (tokenizer, recursive-descent parser, translator with its own error
  taxonomy), with the deterministic SymPy verifier as the sole judge.

## 2. Budget for ingestion and representation cost

File ingestion and representation can be harder than the mathematical
reasoning itself. In the first real workload, building the translation path
and getting the source into the engine consumed more effort than all verified
transformation steps combined; sources in the tens of kilobytes (thousands of
parsed operations) are realistic and must be expected.

- An expression engine whose front door only accepts its own dialect will
  spend most of a real workload outside the loop.
- Treat ingestion failures as engine gaps to close in releases, not as user
  errors to work around ad hoc.

## 3. Concrete-bound flattening is a diagnostic workaround, not a strategy

Expanding symbolic sums and piecewise branches at one concrete bound value is
sometimes necessary to make a problem tractable, but it:

- silently restricts every later result to that bound value (a scientific
  content change hidden inside an "engineering" step);
- destroys generality;
- grows symbol counts combinatorially when indexed objects are flattened into
  plain names, exhausting symbol slots at modest bound values.

Preserve `Sum` / `Piecewise` and indexed objects symbolically as long as
possible. Evaluating at a concrete bound is a labeled, recorded scientific
decision requiring escalation under the AGENTS.md rules — never an implicit
translation default.

## 4. Global `simplify()` is the wrong default for large special-function expressions

Evidence from real exploration: `simplify()` difficulty does not correlate
with expression size. Structured sub-sums of hundreds of operations can
simplify in seconds, while much smaller terms laden with nested rational
functions and special functions can run for many minutes without finishing.
Unbounded `simplify()`-driven exploration was the single largest cost center
in the first real workload — almost entirely wasted time.

- Expose targeted, named, bounded primitives and make them the default path:
  `collect`, `factor_terms`, `together`, `cancel`, structural grouping.
- Unrestricted `simplify()` requires an explicit, budgeted opt-in — never a
  default.
- v0.2 implementation: `src/symbolic_compactification/transforms.py` — a fixed
  set of bounded primitives, each op-count capped via `TRANSFORM_POLICY`
  (`get_transform_policy` / `set_transform_policy`); an over-cap result is
  discarded rather than silently accepted, and each primitive records its name
  for telemetry.

## 5. Structural factorization before expansion

Successful compaction moves are *structural*: merging identical terms,
grouping by shared structure (e.g. special-function order), factoring common
prefactors — executed on the still-factored form. The failing strategy is
letting the CAS globally expand and then trying to re-derive structure from
the flattened residue.

- Transformation planning should operate on the expression's block structure
  (sums, shared subexpressions, common prefactors) before it operates on the
  flattened polynomial-like residue.
- v0.2 primitives embody this: `combine_identical_sums`,
  `factor_common_kernel`, `collect_common_factor` in `transforms.py`.

## 6. Every symbolic operation needs a per-operation wall-clock budget

Improvised external timeouts and manually killed processes waste large amounts
of machine time, and an engine operation with no internal timeout can run
indefinitely.

- Every symbolic operation (simplification primitives, probing, the verifier
  itself) must have a per-call wall-clock budget.
- On expiry, the operation fails closed and returns UNKNOWN with an explicit
  evidence kind: `TIME_BUDGET_EXCEEDED`.
- v0.2 implementation: `src/symbolic_compactification/budgets.py`
  (`run_with_budget`, `BudgetExceeded` raising code `TIME_BUDGET_EXCEEDED`,
  `get_budget_policy` / `set_budget_policy`, process-pool enforcement).
  Fail-closed semantics already cover the meaning of a budget expiry; the
  budget makes it affordable.

## 7. UNKNOWN is a well-served fail-closed outcome

UNKNOWN correctly blocks promotion; its cost is time, not integrity. No
incorrect advance is possible while fail-closed semantics hold.

- Do not "fix" UNKNOWN by loosening the verifier. Fix it upstream: better
  rewrite rules (Guideline 8), better structural planning (Guideline 5),
  budgets (Guideline 6).
- UNKNOWN is the engine's honest state. Workflow design should make it cheap
  to reach and informative to read — the residual and the evidence list
  already support this.

## 8. Special-function identities must be explicit and assumption-aware

Generic CAS machinery does not reliably apply assumption-conditional
identities (conjugation/real-part identities, argument canonicalization) under
declared symbol assumptions inside a verification pipeline. Such identities
are mathematically exact under their declared assumptions but otherwise
undecidable for the verifier, costing compactions to UNKNOWN or timeout.

- Maintain an explicit rewrite table for special functions (conjugation,
  reflection, argument normalization), gated on declared symbol assumptions.
- Apply such rewrites as *recorded transformation steps* subject to
  verification — never as hidden hopes inside `simplify()`.
- v0.2 implementation: `src/symbolic_compactification/rules.py`
  (`RewriteRule`, `apply_rule` / `apply_rules`, assumption-gap detection, and
  assumption-conditioned transforms).

## 9. Parser limits are policy, not code to edit mid-run

Hardcoded parse/ops caps edited in source during a scientific run leave no
record of which limits applied to which step, breaking reproducibility and
provenance.

- Limits belong in a per-call / per-run policy object with defaults set at run
  init and echoed into the run manifest. Changing defaults is an engine
  release, not a run-time act.
- v0.2 implementation: policy accessors (`set_parse_policy` in the parser,
  `set_transform_policy` in `transforms.py`, `set_budget_policy` in
  `budgets.py`) — configure, never edit constants mid-run.

## 10. Separate engine changes from scientific steps — version everything

Scientific provenance must never straddle an engine change. A run produced by
an unversioned, uncommitted engine state is not reproducible.

- Every run manifest and every step record carries `engine_version` plus
  `engine_git_sha` (dirty tree recorded as such).
- Infrastructure work done during a scientific run closes the current run,
  bumps the engine version, and starts a new run.
- Agent-made engine edits are committed (or explicitly stashed with a record)
  before the next scientific step.
- v0.2 implementation: `engine_version` and `engine_git_sha` fields on the
  session/step records in `src/symbolic_compactification/models.py`, populated
  automatically at record creation.

## 11. Symbol namespaces need a collision policy

CAS reserved function names routinely collide with conventional domain symbol
names (a special function name can shadow a physical parameter, or vice
versa). Resolving collisions by silent whitelist edits is fragile: any future
workload needing the shadowed function breaks the symbol, or the reverse.

- Define a durable policy: reserved CAS names vs. user symbols, with either
  namespaced function syntax or an explicit collision error at declaration
  time.
- Never resolve collisions by silent whitelist edits.

## 12. Telemetry must be in the record — reconstructed after the fact is lossy

Audits that must reconstruct wall-clock from file mtimes and machine timings
from shell transcripts are archaeology sessions. Step records that store only
verdicts and evidence are insufficient.

- Every step record carries cheap JSON-native telemetry: `input_chars`,
  `output_chars`, `count_ops_before`, `count_ops_after`, `primitive`
  (transformation used or None), `wall_time_seconds`, `verdict`,
  `timeout_status`, `engine_version`.
- v0.2 implementation: the `telemetry` field on `StepRecord` in
  `src/symbolic_compactification/models.py`, populated by the session and CLI
  paths. Every future audit then costs minutes, not a reconstruction effort.

## 13. Structure-first conjecture policy: the conjecture layer is separate from certification

The v0.2 engine is structure-first at every layer, and agent workflow must be
too. The structural representation (`Sum` with symbolic bounds, `Piecewise`
with symbolic conditions, indexed function applications) is primary; lowered
or expanded views are opt-in diagnostics, never substitutes for symbolic
proof. The v0.2 mechanisms that embody this:

- `structure.py` — `structure_summary` gives a cheap JSON structural
  inventory before any decision to lower or expand; `expand_finite` is
  explicitly labeled a diagnostic finite-N replay, never proof for symbolic
  bounds.
- `verifier.py` — structure-first adjudication: residuals above
  `structure_first_threshold` receive no global `simplify()`; only budgeted
  `TARGETED_PRIMITIVES` are attempted, and the skip is recorded in evidence
  (`structure_first_skip_global_simplify`).
- `budgets.py` — every expensive symbolic operation is wall-clock budgeted;
  expiry fails closed as UNKNOWN with evidence kind `TIME_BUDGET_EXCEEDED`.
- `models.py` — `STEP_STATUSES = ("HYPOTHESIS", "UNVERIFIED", "CERTIFIED")`
  separates the conjecture layer from certification on every `StepRecord`.

Normative agent behavior:

1. **Inspect before expanding.** Before expanding sums, flattening indexed
   objects, or invoking global CAS simplification, inspect the highest-level
   available representation (`inspect --format wolfram` /
   `structure_summary`) and identify repeated kernels, repeated argument
   families, common tensor/index structures, permutation relations,
   Piecewise strata, and possible reusable subexpressions. The structural
   representation stays visible to the reasoning agent even when a
   lower-level verifier representation is also constructed.
2. **Conjecture boldly, certify deterministically.** Bold structural
   hypotheses are explicitly encouraged and are recorded as `HYPOTHESIS` /
   `UNVERIFIED`. They never become certified science without a deterministic
   ZERO.
3. **UNKNOWN is do-not-promote, not stop-exploring.** After UNKNOWN the
   agent may reformulate the conjecture, seek a smaller/local identity,
   change representation, decompose the proof, or seek a more
   verifier-friendly candidate. It may never silently accept the claim.
4. **Never destroy structure to feed the CAS.** Finite-index expansion is
   diagnostic only. The admissible order is: structured representation →
   conjecture/transformation → local lowering if required → deterministic
   verification. The failing order is: eager full expansion → attempt to
   rediscover lost structure over thousands of scalar terms. The
   CAS-friendly representation must never become the only representation
   exposed to the agent.
5. **LLM/CAS division of labor.** The LLM/coding agent discovers structure,
   proposes abstractions, and proposes transformations. The deterministic
   engine parses, normalizes, verifies, and rejects or certifies.
   Unrestricted `simplify()` is not the discovery mechanism.
6. **Policy, not machinery.** This guideline introduces no hypothesis
   database, planner, ontology, or orchestration system — the policy is
   recorded via existing step records and guidance documents only.

---

## Standing principles

1. **Fail closed.** Any undecided, exceptional, or unproven path returns
   UNKNOWN and blocks promotion. Approximate evidence never promotes.
2. **Verification is engine-internal and exact.** Adapters translate in; the
   deterministic verifier is the sole judge.
3. **Structure first.** Transformation planning works on block structure
   before flattened residue; primitives are bounded and named.
4. **Limits are policy.** Configured per run, echoed into manifests, changed
   only by engine releases.
5. **Everything is versioned.** Engine version + git SHA accompany every
   record; scientific provenance never straddles engine changes.
6. **Records are self-describing.** Telemetry lives in the step record, so
   audits are reads, not reconstructions.
7. **Conjecture ≠ certification.** Bold structural hypotheses are encouraged
   and recorded as `HYPOTHESIS` / `UNVERIFIED`; only a deterministic ZERO
   certifies. UNKNOWN blocks promotion, never exploration.
