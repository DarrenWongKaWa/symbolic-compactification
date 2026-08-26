# Idea evaluator (after protocol-v0 data)

Date: 2026-08-26
Input: `research/runs/protocol_v0/ANALYSIS.md` plus 2026-08-21 Guo logs.

### 1. First impression

- Paper type: still Novel Method / New Setting.
- One-sentence story after data: The engine is a reliable fail-closed
  residual checker on synthetic identities and corruptions; it has not
  been shown to beat CAS on certified compactness, nor to take
  untrusted agents past shallow structure on the physics flagship.

### 2. Fatal-flaws audit

| # | Flaw | Severity | Defense |
|---|---|---|---|
| 1 | F1 LLM+verifier crowding (LGuess, O-Forge, Moxia, FunSearch, Shih) | MAJOR | Unchanged; data did not create a new axis |
| 2 | Data-refuted **C2** on v0.1 easy compactify (B1 mean Δops 0.824 > B7-det 0.353 on dev) | MAJOR for a method paper selling compactness | Do not headline C2. Optionally pivot to a **benchmark + soundness** paper |

Not automatic Reject-and-Pivot under the data-refuted rule for the **core
fail-closed mechanism**: C1's checker half is supported (0 false
promotions on test A). The compactness claim is the one the data beat.

### 4. Five-dimension radar (updated)

| Dimension | Score | Evidence |
|---|---|---|
| Higher | 6 | Checker soundness confirmed; agent-vs-B4 reliability untested; compactness not higher than B1 |
| Faster | 3 | No efficiency win |
| Stronger | 6 | 0 false promotion on labelled test; UNKNOWN used honestly (1 test item) |
| Cheaper | 5 | unchanged |
| Broader | 5 | 1 test scientific compactify item; C3 inconclusive |

### 7. Verdict

**Accept with Revisions** for a *narrower* project: protocol + verifier
stress benchmark + honest negative compactness/Guo results. **Not**
Strong Accept. Do not write a NeurIPS/ICLR method paper on current
evidence.

If the authors insist on C2 as stated, the idea-evaluator
data-refuted rule would **Reject and Pivot** that claim only.

Top actions: (1) do not draft; (2) either drop C2 or redesign the
compactify tier to be hard enough that CAS fails; (3) run B4 vs B7
with ≥5 seeds on a harder set before any venue targeting.
