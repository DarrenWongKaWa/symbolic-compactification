# Figure 3 — Forward verified reasoning (public example)

Skill: `figure-designer`. Experimental-results / capability illustration.
Not a discovery benchmark. Not a live-LLM result.

Public evidence:
- Mode A demos: `demo_a_zero` (ZERO), mutation `(x+1)^2+1` (NONZERO, residual
  `-1`, counterexample `x=-2`), `demo_c_unknown` (UNKNOWN, no promotion).
- Multi-candidate gate: `tests/test_proposer_protocol.py` CASE B with a
  **scripted** proposer, not a language model.
  Current: `x**2 + 2*x + 1`
  Candidate B-wrong: `x**2 + 2*x - 1` → NONZERO, current unchanged
  Candidate B-right: `(x+1)**2` → ZERO, then promote
  Proposal records themselves cannot promote.

There is **no** committed multi-step researcher demo workspace. Label the
figure as a capability illustration of the gating contract.

---

### 1. Figure type

- Type: experimental-results (case illustration)
- Reason: RQ1 is gating, not accuracy. A small explicit candidate panel is
  the honest chart type.

### 2. Paradigm

- Paradigm: annotated case panel (not grouped bars)
- Why: three qualitative outcomes, not a metric.
- Rejected: bar chart of "pass rate"; invented multi-step physics derivation.

### 3. Layout sketch

- Canvas: ~150 mm × 80 mm, three columns.
- Header: current expression \(E_t = x^2+2x+1\) (or the equivalent Mode A
  factorization). Label **proposer output is untrusted**.
- Column A: candidate → engine `ZERO` → box "admissible / may promote".
  Use demo_a / CASE B right candidate `(x+1)^2`.
- Column B: candidate → engine `NONZERO` (show residual `-1` from the public
  mutation replay, or CASE B wrong candidate). Box "rejected; \(E_t\) unchanged".
- Column C: candidate → `UNKNOWN` (demo_c polygamma gap). Box "not promoted".
- Footer: "Scripted or researcher-supplied candidates. No live model. No
  representation-invention claim."
- Shapes: circle ZERO, X-mark NONZERO, triangle UNKNOWN.

### 4. Caption

> Figure 3. Untrusted next transformations are gated before they become
> accepted state. A `ZERO` candidate may advance; a `NONZERO` candidate is
> refuted and leaves \(E_t\) unchanged; an `UNKNOWN` candidate is recorded
> and is not promoted. The public Mode A demos are researcher-supplied
> one-shot hypotheses; the two-candidate panel follows the scripted
> proposer protocol test, not an autonomous discovery run.

### 5. Tool

- draw.io or PowerPoint → SVG/PDF. Not a matplotlib bar chart.

### 6. Integrity

- Honest labelling of proposer: pass (required).
- Do not invent a physics multi-step session: pass.
