# AGENTS.md — Agent-Native Contract

You are operating the **symbolic compactification engine**: a deterministic
kernel that verifies whether a proposed "simplified" expression is *exactly*
equal to the current one. The repo contains the scientific **method**, never
scientific answers. No LLM judgment is ever accepted as mathematical proof —
the verifier decides, and it fails closed.

Read this file first. Follow every rule. When in doubt, fail closed and
escalate to the human.

---

## The loop (one sentence)

Ingest the human's expression from a file, propose a candidate simplification
as a file, ask the deterministic verifier whether the difference is exactly
zero, and advance **only** on a ZERO verdict.

```mermaid
graph TB
    A[Human drops files] --> B[Agent reads AGENTS.md]
    B --> C[Organize inputs: copy raw sources to workspace/input/raw/]
    C --> D[Identify machine-parsable expressions, declare symbols]
    D --> E[Reason / propose candidate as a .txt file]
    E --> F[Verifier: verify / step]
    F --> G{verdict}
    G -->|ZERO| H[Promote: candidate becomes current, continue]
    G -->|NONZERO| I[Read residual + counterexample, propose again]
    G -->|UNKNOWN| J[Fail closed: no promotion, escalate if needed]
    H --> E
    I --> E
```

### After reaching a CERTIFIED state (agent protocol v0.3.0)

The proposer path is configurable. Default is **main**.
Subagent is never the unique path.

Once a candidate is CERTIFIED and promoted, the next move is:

1. **Inspect the semantic structure** of the new current expression
   (`inspect --json` includes `structure_summary`; Wolfram sources use
   `--format wolfram`) — rules 18/21.
2. **Propose the next candidate** according to the configured proposer
   (`init-session --proposer-mode main|subagent|auto`; undeclared = main):
   - **Default (`main`).** The main agent writes the candidate `.txt` itself
     and records it (`record_proposal`, status `HYPOTHESIS`) when using the
     session pipeline.
   - **Optional (`subagent`).** Assemble a conjecture packet
     (`build_conjecture_packet`) for provenance. Hand
     `roles/STRUCTURAL_PROPOSER.md` plus **only** the current expression and
     `structure_summary` to ONE harness-native subagent (Qoder / Codex /
     Claude Code / Grok native subagent facility — this repo contains no
     agent runtime of its own). Do not pass the working tree. Record the
     returned proposal via `record_proposal` with the harness subagent id.
   - **Optional (`auto`).** Skill-layer heuristic only: use `subagent` when
     the expression is ≥ 8 KiB or `count_ops` ≥ 400, otherwise `main`.
     `auto` is not a fourth evidence-derived `run_summary.proposer_mode`.
3. **Targeted deterministic verification** of the candidate (`verify` /
   `step`) — the verifier is mandatory and remains the sole judge.
   Promote only on ZERO.
4. **Update state**: promote only on ZERO (main agent only); on NONZERO feed
   the residual + counterexample back; on UNKNOWN refine per rule 20.

Default remains **main**. You may recommend `--proposer-mode subagent`
when the working directory is noisy or the current expression is extremely long
— isolation keeps discovery on structure instead of workspace residue.
Honor an explicit user request. Use `auto` only when the user asked. Do
not switch unless the user asked for `subagent` or `auto`.

Global `simplify()` remains a bounded fallback for small expressions only —
never the primary discovery path. The A/B comparison protocol for this
workflow is documented in `docs/AB_EXPERIMENT_PROTOCOL.md`.
The project skill is `.grok/skills/symbolic-compactification/SKILL.md`.

`run_summary` reports `proposer_mode` strictly from recorded evidence:
`MAIN_AGENT_ONLY` (proposals recorded without a subagent id),
`HARNESS_SUBAGENT` (a harness subagent id was recorded),
`SUBAGENT_UNAVAILABLE` (an explicit record that the harness cannot expose
native subagent invocation for this run), or `UNKNOWN` (ambiguous/absent
evidence). Reading `roles/STRUCTURAL_PROPOSER.md` is never evidence of any
mode. An experiment may declare its A/B arm (`requested_arm` at init or via
`set_requested_arm`); `run_summary` then derives `ab_arm_valid`:
arm B is valid iff a subagent id was recorded (`SUBAGENT_NOT_INVOKED`
otherwise), arm A is valid iff there is no subagent evidence.

---

## Rules

### A. Input handling

1. **Classify every user attachment.** Decide for each file: machine-parsable
   symbolic expression, context/notes, or unrelated. Only the first category
   enters the verification loop.
2. **Preserve original scientific inputs under `workspace/input/raw/`.** Copy
   them there immediately. Never move, rename, or mutate the originals.
3. **Never alter raw sources, silently or otherwise.** The bytes you ingested
   are evidence. Work only on copies you create yourself
   (e.g. under `workspace/input/expressions/`).
4. **Identify machine-parsable symbolic expressions.** An expression must be a
   plain-text formula within the parser whitelist: declared symbols/functions,
   the named SymPy functions in `PARSE_POLICY`, constants `pi E I oo`, and
   structural `Sum Product Piecewise` plus relational/logical constructors.
   Token, depth, literal-size, character, and AST-operation limits all apply.
   Anything else is context, not verifier input.
5. **Never transcribe long expressions by hand.** Use `load_expression`
   (Python) or `inspect` (CLI) to read the file directly. The `.txt` file plus
   its recorded SHA-256 **owns** the canonical expression — your typed copy
   does not.

### B. Verification discipline

6. **Treat every proposed simplification as unverified.** A candidate is an
   unproven claim until the verifier returns ZERO. Never present it as a
   result before that.
7. **Call the deterministic verifier for EVERY transformation.** Use the
   `verify` CLI or `verify_equivalent()` — no exceptions, however "obvious"
   the step looks.
8. **Advance only on ZERO.** Use `step` or Python
   `adjudicate_candidate()`. Promotion is bound to the exact current and
   candidate hashes/text, CERTIFIED/PROVEN state, exact-zero evidence, and no
   HUMAN_REQUIRED gate.
9. **On NONZERO, inspect the exact residual and counterexample.** The output
   gives you `residual`, `simplified_residual` and an exact rational probe
   point where the two sides differ. Fix the proposal and verify again.
10. **On UNKNOWN, fail closed.** Do not promote. Do not argue the residual
    away. Simplify, split the problem, or escalate to the human — but the
    candidate stays rejected.

### C. Scientific integrity — no silent assumptions

11. **Do not invent assumptions.** If the user did not declare a symbol real,
    positive, nonzero, etc., do not assume it. Assumptions live in
    `symbols.json` and are explicit or absent.
12. **Do not silently introduce integration by parts.** Boundary terms are
    lost or gained; that is a scientific decision.
13. **Do not silently change symmetry assumptions.** Symmetrizing or
    antisymmetrizing changes the content of a claim.
14. **Do not silently reorder limits.** Limits do not commute in general.
15. **Do not silently change domains or boundary conditions.** Any such change
    changes what is being claimed.
16. **Escalate all such scientific choices to the human.** State the choice,
    its consequences, and wait for a decision. Record the decision.

### D. Provenance

17. **Record every step — successes AND failures.** Run everything through
    session records (`init-session` + `step`). A failure with its residual is
    evidence; an unrecorded attempt is a lie by omission.

### E. Structure-first conjecture policy

18. **Inspect structure before expanding.** Before expanding sums, flattening
    indexed objects, or invoking global CAS simplification, inspect the
    highest-level available representation: `inspect --format wolfram` (CLI)
    shows the translated structural form with its Sum/Product bound symbols
    and indexed function calls; `structure_summary` (Python) reports a cheap
    structural inventory — sums, products, Piecewise blocks and branches,
    indexed calls, free symbols, and op counts. Identify repeated kernels,
    repeated argument families, common tensor/index structures, permutation
    relations, Piecewise strata, and possible reusable subexpressions. The
    structural representation must remain visible to your reasoning even when
    a lower-level verifier representation is also constructed.
19. **Conjecture ≠ certification.** Bold structural hypotheses are explicitly
    encouraged: "these two sums may share one kernel", "these Piecewise
    branches may be confluent limits of one analytic object", "these
    arguments may belong to two canonical families". Record them with step
    status `HYPOTHESIS` / `UNVERIFIED`, and never promote them to certified
    science without a deterministic ZERO verdict.
20. **UNKNOWN does not prohibit reasoning.** UNKNOWN means do-not-promote,
    not stop-exploring. After UNKNOWN you may: reformulate the conjecture;
    look for a smaller or local identity; change representation; decompose
    the proof; or seek a more verifier-friendly candidate. You may NOT
    silently accept the claim (see also rule 10).
21. **Do not destroy structure to feed the CAS.** Concrete finite-index
    expansion is diagnostic only — `expand_finite` is explicitly labeled a
    finite-N replay, never a proof for symbolic bounds. Preferred order:
    structured representation → conjecture/transformation → local lowering
    if required → deterministic verification. Never: structured
    representation → eager full expansion → attempt to rediscover lost
    structure over thousands of scalar terms. The CAS-friendly representation
    must never become the only representation exposed to you.
22. **Respect the division of labor.** The LLM/coding agent discovers
    structure, proposes abstractions, and proposes transformations. The
    deterministic engine parses, normalizes, verifies, and rejects or
    certifies. Unrestricted `simplify()` is not the discovery mechanism.
23. **No new machinery.** This policy introduces no hypothesis database,
    planner, ontology, or orchestration system. It is recorded via the
    existing step records (`status`: `HYPOTHESIS` / `UNVERIFIED` /
    `CERTIFIED`) and this guidance document.

---

## Verdict semantics

| Verdict   | Meaning                                                        | Required action                          |
|-----------|----------------------------------------------------------------|------------------------------------------|
| `ZERO`    | `current - candidate` simplified to exact symbolic zero        | Promote; candidate becomes current       |
| `NONZERO` | An exact rational probe proved the difference nonzero          | Read residual + counterexample, retry    |
| `UNKNOWN` | Undecided: no proof either way (fail closed)                   | No promotion; refine or escalate         |

- ZERO is produced **only** by exact symbolic simplification (directly, or
  after complex normalization). Numeric tolerance never enters.
- NONZERO is produced **only** when SymPy can *prove* a probe value nonzero
  (`value.equals(0) is False`). Approximate evidence never counts.
- Every undecided or exceptional path returns UNKNOWN.
- Step **status** is orthogonal to verdict: `HYPOTHESIS` marks a proposed
  step, `UNVERIFIED` a step that ran without ZERO, and only an exact ZERO
  verdict sets `CERTIFIED`. Hypotheses may guide exploration; only CERTIFIED
  steps enter the promotion chain. Budget expiry (`TIME_BUDGET_EXCEEDED`) is
  an UNKNOWN path — never ZERO or NONZERO.
- Status taxonomy note (agent protocol v0.3.0): `PROOF_REQUIRED` marks a
  claim whose declared assumptions are already SUFFICIENT but which the
  current verifier cannot prove — a proof gap, not a human-decision gate.
  The inability to prove a limit/special-function identity must be labeled
  `PROOF_REQUIRED`, **never** `HUMAN_REQUIRED`. `HUMAN_REQUIRED` (a proposal
  `assumptions_status`, and a certification gate) is reserved for genuinely
  NEW assumptions or physical choices requiring human authorization.
- Split status axes (agent protocol v0.3.0): each verification step records
  two orthogonal axes in addition to the lifecycle `status`. The
  `assumption_status` axis (`NONE` / `DECLARED` / `HUMAN_REQUIRED`) says what
  assumptions the claim depends on; the `proof_status` axis
  (`NONE` / `HYPOTHESIS` / `PROOF_REQUIRED` / `REFUTED` / `PROVEN`) says
  whether the equivalence is actually proven (ZERO → `PROVEN`, NONZERO →
  `REFUTED`, UNKNOWN → `PROOF_REQUIRED`, a proposal → `HYPOTHESIS`).
  Engine-cannot-prove never
  implies `HUMAN_REQUIRED` — that value lives on the assumption axis only.

## Final reporting contract (agent protocol v0.3.0)

The human-facing deliverable of a run is the **FINAL CERTIFIED FORM**, built
by `render_final_report()` (Python) or `finalize` (CLI):

- The response must show a **readable top-level exact formula** — the
  current CERTIFIED expression — AND reference the complete artifact
  `final/FINAL_CERTIFIED_FORM.md`. Never answer "see `final/current.json`":
  internal JSON is provenance, not the scientific deliverable.
- If the human form uses abbreviations / named kernels, **every one must be
  explicitly defined** (name -> exact expression). Undefined aliases,
  `{...}` placeholders, `TODO`, or "same kernel" hand-waving raise
  `REPORT_INCOMPLETE` (with the offenders listed).
- Machine vs human representations are mathematically identical; the human
  form may only differ in presentation (named subexpressions). Substituting
  definitions back into the human form must verify exactly against the
  certified machine expression. NONZERO or UNKNOWN raises
  `REPORT_INCOMPLETE`; byte-identical text is already exact.
- Large results: the response carries the readable top-level formula while
  the artifact contains EVERY kernel/branch/definition, plus the provenance
  header — `run_id`, `engine_version`, `agent_protocol_version`, final
  certified state sha256, ZERO promotions, NONZERO attempts, UNKNOWN
  attempts. No hidden reasoning text enters the artifact.

## CLI quick reference

```bash
# Inspect an expression file (hash, symbols, size). Without --symbols,
# symbols are INFERRED — inspection only, never usable for verification.
symbolic-compactification inspect expr.txt
symbolic-compactification inspect expr.txt --symbols symbols.json --json

# Structure-first inspection (rule 18): --format wolfram keeps the
# structural representation (Sum / Piecewise / indexed calls) visible.
# JSON always includes structure_summary.
symbolic-compactification inspect expr.txt --format wolfram --json

# Verify candidate == current. Exit: 0=ZERO 2=NONZERO 3=UNKNOWN 4=error
symbolic-compactification verify \
    --current current.txt --candidate candidate.txt --symbols symbols.json

# Start a run (creates workspace/runs/<run-id>/); optionally set the initial
# current expression (--current requires --symbols).
symbolic-compactification init-session \
    --current current.txt --symbols symbols.json \
    --proposer-mode main

# One verified step inside a run; promotes the candidate only on ZERO.
symbolic-compactification step --run <run-id> \
    --candidate candidate.txt --symbols symbols.json

# Evidence counters for an existing run (does not certify).
symbolic-compactification summary --run <run-id> --json

# Render the FINAL CERTIFIED FORM deliverable for a run: prints the explicit
# certified top-level expression and writes final/FINAL_CERTIFIED_FORM.md.
symbolic-compactification finalize --run <run-id>
```

Notes:

- `--workspace W` is accepted by `init-session` and `step` (default
  `workspace`).
- `step --current file.txt` installs an initial current when none exists, or
  hydrates an exact byte-and-namespace match. It cannot override established
  state.
- Every subcommand accepts `--json` for one machine-readable output object.
- Exit codes: `0` ZERO, `2` NONZERO, `3` UNKNOWN, `4` parse/load/usage error.

## symbols.json

```json
{"symbols": ["x", {"name": "a", "real": false, "nonzero": true}]}
```

- A bare JSON list (`["x", "y"]`) is also accepted.
- String shorthand defaults to `real=true, nonzero=false`.
- `real` selects the verifier's probe lattice (real vs complex probes).
- Reserved names (`pi E I oo` and the allowed functions) may not be declared.
- Max 40 symbols; duplicates and empty lists are rejected.

## Workspace layout

```
workspace/
├── input/
│   ├── raw/          # pristine copies of the human's original files (rule 2)
│   ├── context/      # non-parsable notes / context attachments
│   └── expressions/  # agent-created expression .txt files (candidates etc.)
└── runs/<run-id>/
    ├── manifest.json # run metadata, current expression, step index
    ├── steps/        # step_NNN.json — every recorded step (all verdicts)
    ├── packets/      # packet_NNN.json — conjecture-packet provenance (v0.3)
    └── final/        # current.json — promoted expression (text + sha256)
                      # FINAL_CERTIFIED_FORM.md — human deliverable (v0.3)
```

## Python API (same guarantees)

```python
from symbolic_compactification import load_expression, verify_equivalent

rec = load_expression("current.txt", ["x", "y"])      # sha256 over raw bytes
res = verify_equivalent(rec.text, "(x+y)**2", ["x", "y"])
# res.verdict / res.residual / res.simplified_residual / res.evidence
# res.counterexample  (set only on NONZERO)
```

`verify_equivalent` never raises: every failure path returns an UNKNOWN
result. For a stateful run use `adjudicate_candidate(session, record)`, the
single verify-record-promote pipeline. When the code and this file disagree,
fail closed and report the contract defect; do not silently choose either.
