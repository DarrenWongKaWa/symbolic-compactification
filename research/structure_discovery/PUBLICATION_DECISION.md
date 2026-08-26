# Publication decision — structure-discovery line

Date: 2026-08-27

## Decision: E — PROMISING BUT MORE EVIDENCE NEEDED

Not A (top-tier method). Not B (workshop-ready method package). Not C
(benchmark/evaluation paper). Not D (more than a script: claims, bench,
negatives, freeze). Not F (C1–C3 hold on the frozen synthetic/semi-synthetic
split; the direction is not falsified).

### Strongest supported claim

A decomposed observe→typed-hypothesis→construct→fail-closed-verify pipeline
proposes gold D2–D5 structure types more often than SymPy transforms or
direct Method-v2 packaging, with **zero** forbidden reconstructions promoted,
on a 12-item frozen test (8/8 positive type-hit; 4/4 negative abstain).

### Strongest unsupported claim

That an *AI system* (LLM proposer) discovers high-level mathematical
structures useful to theoretical physicists. No LLM ran. Guo yields only
D2 CSE kernels, not master functions, divided differences, or generators.

### Main novelty (if any later)

Problem formulation: typed structural hypotheses on already-exact scientific
expressions with negative tasks and residual adjudication. Not “we beat CAS.”
Not library learning. Not first LLM+verifier.

### Closest prior work

DreamCoder / Stitch / babble (abstraction invention on programs);
FORM/CSE (exact scientific algebra without typed H);
LGuess (LLM+e-graph on polynomials);
Method v2 of this repo (fail-closed, tautological names).

### Key experiment

Held-out B9 vs B1 vs B6 on ssc-structure-bench-v0.1 TEST, plus DEV
observation ablations and negative-task C3.

### Worst counterexample

Guo σ_abc: 3911 ops, 4 Piecewise, 14 branches → 8 repeated-kernel hypotheses
(`epsilon(n)`, `1/pi`, …). No L4–L7. S2-pos-perturbation missed on DEV.

### Key limitation

n_test=12, author-constructed, 1 deterministic “model”, no LLM, no human D6,
no Wolfram/Lean/egg. Reviewer B can fairly call B9 “CSE + pattern match.”

### Recommended venue class

None this snapshot. After an LLM multi-seed study on a larger S3 set, with
Guo negative intact: AI-for-Science workshop / NeSy, **Story A only if the
LLM (not the observation layer) carries D3–D5**. Not ICLR/ICML/NeurIPS.

No `paper_structure_discovery/` directory.
