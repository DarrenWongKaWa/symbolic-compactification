# Paper decision gate

Date: 2026-08-26
Protocol: v0
Benchmark: ssc-bench-v0.1

## Decision: C — PROMISING BUT INSUFFICIENT

Do **not** write `paper/` yet. Do not target ICLR/ICML/NeurIPS/AAAI/IJCAI
on this evidence.

### Evidence that keeps the project alive (not a D)

- Engine contract is real and tested (328 unit tests + Tier A 35/35
  frozen-test label match, 0 false promotions).
- Novelty boundary is honest: closest works named (LGuess, O-Forge,
  Moxia, FunSearch, Shih 2026, egg, LeanDojo, FORM).
- Guo negative result is recorded, not faked.
- Fail-closed UNKNOWN is operational.

### Evidence that blocks A and B as of today

- C2 not supported: B1 compactness ≥ B7-det on v0.1 unstructured items;
  Guo remains certified-shallow (2026-08-21).
- C1 vs unconstrained LLM/CAS (B3/B4/B5) not batch-measured; only
  qualitative n=3 Guo.
- C3 inconclusive: one Grok seed, no second model family table, one
  held-out scientific compactify item.
- B2/Lean/egg unavailable; B6 is not egg.
- Compactify test set is too easy (7 items, all solvable in one
  obvious rewrite).

### What would move the gate

- To **B (workshop / NeSy / AI-for-Science workshop)**: drop or reverse
  C2; complete B4 vs B7 with ≥5 seeds on a **harder** compactify set;
  keep certification language as engine semantics; keep Guo as a
  negative case study.
- To **A**: additionally show a reliability vs progress Pareto move
  against LGuess-style and LLM+CAS baselines on multiple physics
  families and ≥2 model families. Not in hand.
- To **D**: only if the authors insist on claiming C2 and "formal
  certification" and "first LLM+verifier" despite this file.

### Venue if later B

NeSy, AI-for-Science workshops, or a symbolic-computation venue with
the AI claim demoted. Not a top ML conference on current data.
