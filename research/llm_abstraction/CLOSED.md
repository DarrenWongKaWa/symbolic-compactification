# CLOSED: Structural observation × DeepSeek proposer

Line closed. Do not reopen to retune SOL, prompts, packet size, or TEST.

Frozen raw model outputs live under `runs/` (hypotheses + `raw_content`).
Do not mutate those fields. Later constructor/IR work must copy, not edit.

## What is established

1. T7 was **not** “DeepSeek cannot find a symmetry invariant.”
   The hypothesis was already present. The execution layer could not
   turn \(T(i,j)\leftrightarrow T(j,i)\) into a checkable obligation.
   After constructor v2: success \(0/0.4 \to 1.0/1.0\).
   **Discovery succeeded; execution failed.**

2. SOL does **not** raise aggregate invention:
   A0 success \(0.54\), A2 success \(0.52\) (CASE A, stable after rescore).

3. SOL is a **task-dependent inductive bias**, not a uniformly helpful
   representation:

   | cell | A0 → A2 |
   |---|---|
   | T5 confluence | \(0.20 \to 0.80\) |
   | T2 distributivity | \(0 \to 0.60\) |
   | T1 substitution | \(1.00 \to 0.20\) (CSE anchoring) |

   Branch observations can lift confluence hypotheses.
   CSE observations can pin the proposer on `repeated_kernel` and
   suppress `parameterized_family`.

## Closed claims (allowed)

- Observation alone does not solve abstraction invention.
- Too much low-level observation can anchor the proposer.

## Forbidden next steps on this line

- Cadabra / FORM detectors
- SOL ranking retune
- DeepSeek prompt tuning
- TEST-set packet-size tuning
- Fixing one task and reinterpreting the whole matrix

## Failure sources (must stay separate)

\[
\text{proposer failure}
\neq
\text{constructor failure}
\neq
\text{verifier-language failure}
\]

Label every later miss as **D** (discovery), **C** (construction /
compilation), or **V** (verification).

Commits: `416659f` (DEV ablation), `4dcb26f` (constructor rescore).
Protocol: `deepseek-abstraction-protocol-v1-dev`.
