# Protocol

Parent: `9fc3c8a`. Branch: `research/assumption-complete-representation-v1`.

## Immutable authorities

B9 `4237f6b`, LGG `efc0924`, Beyond-LGG `3214a5a`, SOL `0a2905b`,
P-D-G-C-V-I `14c8f75`, Track B `d20c1a2`, Grounded-Proposer-v1
`3fea222`, repr V2 `45b2b4d`, DD/Hermite `45f1e46`, evidence
`91a401b`, V `38d6d4a`, V2 `fe53ebc`, V3 `d2752f9`, V4 `248d247`,
V5 reviews `9bff79b`, source-assumption audit `9fc3c8a`.

Do not mutate historical artifacts, SOL, frozen benches, or Guo hop
verdicts.

## Order

1. Contracts (this freeze).
2. Case mining C1–C6. Dossiers only. No Guo as a new scientific case.
3. Assumption audit A1–A4 on admitted candidates.
4. Admission gate → DEV / TEST / CHALLENGE.
5. Frozen symbolic baselines (no edits).
6. Freeze prompts/model/SOL **before TEST**.
7. LLM conditions P0–P5 on DEV, then frozen TEST.
8. Guo only as sealed negative control at the end.
9. Independent reviewers after final evidence.

## Partitions

`ssc-assumption-complete-science-v0.1`: DEV, TEST, CHALLENGE.
Guo does **not** enter TEST.

## Models

Primary `deepseek-v4-pro`. Secondary later `deepseek-v4-flash`.
Do not tune on TEST. Do not start with an ensemble.

## Fail-closed remainder

`neg ZERO ∧ C0 ZERO ∧ remainder UNKNOWN` ⇒ final UNKNOWN, never ZERO.
