# Baseline diagnosis (read-only of protocol v0)

Date: 2026-08-26
Sources: `research/baselines/BASELINES.md`, `research/baselines/runners/run_deterministic.py`,
`research/baselines/runners/run_llm_arms.py`, `research/runs/protocol_v0/ANALYSIS.md`,
`research/DECISION.md`, 2026-08-21 Guo experiment reports.

This note is recorded **before** any proposer-architecture change. It exists
so later work cannot pretend that protocol v0 already tested agentic
scientific-structure discovery.

---

## What each arm actually was

| ID | LLM proposer? | What ran | What it is allowed to mean |
|---|---|---|---|
| B0 | no | identity: certified text = input | syntactic floor |
| B1 / B1-cert | no | unstructured: budgeted `simplify/factor/cancel/together`; **structured Sum/Piecewise: skip global CAS, leave input**. One `verify_equivalent` on the final claimed form | conventional CAS on scalar algebra; **not** a scientific-structure searcher |
| B1-raw | no | same transforms, no ZERO gate; `claimed_proven=True` by construction | unsafe CAS claim |
| B2 | — | not run (no WolframKernel) | missing |
| B3 | intended yes | **stub**. `run_llm_arms.py` wrote `skipped_no_batch_llm_client` | **not measured** in v0 |
| B4 | intended yes | **stub** | **not measured** in v0 |
| B5 | intended yes | **stub** | **not measured** in v0 |
| B6 | no | tiny Python rewrite saturator; structured input skipped | not egg; not an agent |
| B7 | two different things (see below) | see B7-det vs B7-agent | must not be pooled |
| **B7-det** | **no** | greedy `combine_identical_sums` then `collect_common_factor`, each passed through `verify_equivalent`. `llm_calls=0`. Docstring: "No LLM." | deterministic named-transform baseline |
| B7-agent | yes (one seed) | this Grok session as **main** proposer on **7 frozen-test compactify items**, one candidate each, then `verify_equivalent` | the only v0 LLM compactify run; items were D0–D1 easy rewrites |

Ablations A1–A7 were specified and **not run**.

---

## Explicit answers (required)

### 1. Was `B7-det` actually using an LLM proposer?

**No.** `arm_b7_det` in `run_deterministic.py` applies two repository
primitives and the verifier. `llm_calls` is hard-coded 0.

### 2. Was it using only deterministic repository transforms?

**Yes.** Exactly `combine_identical_sums` and `collect_common_factor`.
No subagent, no STRUCTURAL_PROPOSER, no skill loop, no scientific-context
prompt.

### 3. Is `B1 mean Δops = 0.824` vs `B7-det mean Δops = 0.353` (dev compactify) a test of agentic scientific-structure discovery?

**No. It is a comparison of two deterministic simplification routines.**

- B1 wins ops on **unstructured** polynomials/rationals/trig because it
  may `simplify`/`factor`/`cancel`/`together`.
- B7-det only folds identical sums and collects a common factor. On
  unstructured items those primitives often no-op, so mean Δops is lower.
- B1 **deliberately skips** global CAS on Sum/Piecewise, so it cannot
  discover kernels there either.
- Neither arm proposes master functions, confluence, or geometry.
- The v0 paper-decision that "C2 is not supported" is therefore a statement
  about **named-transform vs CAS ops**, not about whether an untrusted
  scientific proposer can find D2–D5 structure.

Using that pair to conclude "the method cannot discover structure" is a
category error. Using it to conclude "the method beats CAS at scientific
abstraction" would also be a category error.

The only v0 **agentic** compactify measurement is B7-agent Grok seed 0 on
the **frozen test** 7-item easy set (all ZERO, trivial D0/D1). That set
is **not** to be reused for architecture tuning in this phase.

The only v0 **hard scientific** agent measurement remains the 2026-08-21
Guo skill-vs-blank probe (n=3 per arm, not this engine's B3/B7 table).

---

## Three capabilities (do not collapse)

| Capability | Who owns it | What v0 measured |
|---|---|---|
| Search power | proposer | **almost unmeasured** (stubs; easy test items; Guo qualitative) |
| Verification power | engine | **measured**: Tier A 35/35 test match, 0 false ZERO |
| Scientific abstraction | human ladder / D-level | **Guo: certified L2, blank uncertified L3 slogans; nobody L4–L7** |

Protocol v0 therefore **localizes verification as working** and **does not
localize search**. This phase exists to localize search.

---

## Implication for this phase

The working hypothesis "proposer/search architecture is the bottleneck,
not the exact-verification principle" is **not yet tested**. It is
consistent with Guo (skill used named transforms; blank invented kernels
without a ZERO) and **untested** against a hard DEV compactify set with
matched LLM arms.

Frozen `ssc-bench-v0.1` **test** files are not to be edited or used for
architecture selection.
