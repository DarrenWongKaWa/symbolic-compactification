# Idea evaluator (before new experiments)

Date: 2026-08-26
Skill: Supervisor-Skills `idea-evaluator` (governance, not copied prose)
Literature grounding: `research/literature/` (retrieval performed)

User idea: turn symbolic-compactification into a submission-ready AI
methodology paper on untrusted structural proposal → fail-closed
adjudication → certified state transition, applied to theoretical-physics
symbolic compactification.

Stated resources: one researcher+agent session; engine already
implemented; no WolframKernel/Lean/egg on host; Grok harness; uncertain
second/third model APIs; existing n=3 Guo A/B only.

---

### 1. First impression

- Paper type: **Novel Method** in a **New Setting** (scientific symbolic
  compactification as a distinct evaluation object). Not a Novel Problem
  in the sense of first proposer–verifier systems.
- One-sentence story: An untrusted agent may rewrite large scientific
  expressions only when a deterministic residual engine proves exact
  ZERO and a hashed state machine records the step; the open question
  is whether that protocol buys reliability and certified compactness
  against CAS and LLM+CAS, or merely certified shallowness.

---

### 2. Fatal-flaws audit (early gate)

| # | Flaw | Severity | Defense |
|---|---|---|---|
| 1 | F1 novelty vs FunSearch / LGuess / Moxia / LeanDojo / CAS ("LLM+verifier") | MAJOR | Position on task+protocol+measurement (scientific compactification of Sum/Piecewise/indexed expr with fail-closed residual and hashed promotion), not on "first verifier". Closest works named in `novelty_boundary.md`. |
| 2 | F8 unfocused (method + benchmark + physics discovery + formal cert) | MAJOR if uncut | Cut to ≤3 claims (C1–C3). Do not claim physics discovery or formal proof. Benchmark is supporting, not a second paper, unless method claims die. |

No CRITICAL flaw. Data-refuted rule does **not** fire: existing Guo A/B
does not show B1/blank beating the **isolated** fail-closed mechanism on
false-promotion; it does threaten C2 (compactness/abstraction). Untested
mechanism, not a refuted one.

Other scanned flaws: F3 (baselines) is a **planned** MAJOR until B4/B5/B6
exist — defense is the freeze file. F10 is already addressed by the
engine's UNKNOWN and the Guo negative result. F2 venue is undecided
until the gate.

---

### 3. Lifecycle and capability match

| Aspect | User's input | Assessment |
|---|---|---|
| Idea category | Innovative Technique + evaluation protocol | Cross of method and benchmark; keep method-primary |
| Lifecycle | top-venue method papers 4–8 months typical | 2–4 months realistic if claims stay empirical and negative results are allowed |
| Weekly effective hours | concentrated agent+human burst | Yellow: LLM multi-model and Mathematica/Lean gaps |
| Fit | engine exists; benchmark/eval/baselines do not | Yellow: execution is engineering-heavy, not theory-heavy |

Mismatch flag: Yellow. Recovery: freeze claims, ship deterministic
evals first, treat missing B2/Lean as documented mismatches.

---

### 4. Five-dimension radar

Scores start at 5. Mechanism-based scores are labelled. No invented
percentages.

| Dimension | Score 1-10 | Evidence | Lift suggestion |
|---|---|---|---|
| Higher | 8 (mechanism-based, not yet confirmed by data) | Fail-closed ZERO/NONZERO/UNKNOWN plus hash-bound promotion is a principled filter against false scientific transformations; 2026-08-21 skill arm had 0 engine false promotions vs blank arm treating CAS as proof. | Isolate this with B4 vs B5 vs B7; do not credit compactness to the same mechanism. |
| Faster | 4 | No mechanism for wall-clock or token reduction; verifier calls add cost. Existing blank runs were 19–31 min of CAS. | Do not sell speed. Report efficiency honestly. |
| Stronger | 7 (mechanism-based) | UNKNOWN fail-closed, assumption gates, representation preservation target OOD scientific structure. Single-workload so far. | C3 frozen test + ≥2 families. |
| Cheaper | 5 | No data-cost story; reverse-synthesis for Tier A is cheap but not the contribution. | no grounds to move |
| Broader | 7 (mechanism-based) | Protocol is domain-agnostic; physics is the stress test. Unification of compactification vs proving vs answering is conceptual, not yet shown. | Cross-family table required for C3. |

Dominant axes to emphasize if data arrive: **Higher (reliability)** then
**Stronger (fail-closed generalization)**. Faster is not the thesis.

---

### 5. Paradigm-shift probe

| Probe | Yes or No | Rationale |
|---|---|---|
| First Principles | Partial | Challenges "the CAS output is the result" and "numeric agreement is identity". Does not challenge rewrite theory itself. |
| Elephant in the Room | Yes | LLM scientific derivations are used as if true; false promotions in physics are costly and under-measured. |
| Technology Cycle | Yes | LLMs make structural conjecture cheap; checkers were always needed and are now the scarce trust. |
| Hamming's Rule | No | If solved, scientific computing becomes more auditable; the field of ML would not reorganize. |

Disruptive potential: **possible**, not strong. Two yes (elephant, cycle).

---

### 6. Feasibility

| Risk | Level | Mitigation |
|---|---|---|
| Compute | Medium | 5 seeds × models × items can blow budget; freeze caps; deterministic arms first |
| Data | Medium | Tier C must be author-owned or public-reconstructed; no copyrighted paper dumps |
| Engineering | Low–medium | Engine exists; evaluator/baselines to build; no egg/Lean/Wolfram |
| Timeline | Medium | Stop at workshop if C2 dies; do not expand to a second paper in this cycle |

---

### 7. Verdict

**Accept with Revisions** — worth pursuing, pending the validation
experiments named as N1–N3 in `novelty_boundary.md`.

Not Strong Accept: high scores are mechanism-based; F1/F8 are MAJOR until
positioning and claim-cut are frozen (now done in `research/protocol/`);
C2 is pre-threatened by the authors' own Guo log.

Not Reject and Pivot: closest work differs on object (physics compact
form vs MATH answer vs polynomial factor vs Lean proof) and on state
protocol; the engine is real; negative results are allowed.

Top three actions:

1. Freeze C1–C3, metrics, splits, budgets (this directory).
2. Build ssc-bench-v0.1 and the unified evaluator; run B0/B1/B6 and
   Tier A soundness **before** any prompt tuning.
3. Run B4 vs B7 on frozen test with ≥5 seeds; if C1 fails, issue gate
   C or D rather than inventing a new headline metric.

Integrity notes: novelty cites retrieved works (LGuess, FunSearch, Moxia,
egg, LeanDojo, AlphaGeometry, ToRA). Scores cite user/engine evidence or
are labelled mechanism-based. No invented accuracy numbers.
