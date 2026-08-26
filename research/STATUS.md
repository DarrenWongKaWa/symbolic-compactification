# Research status

Protocol freeze date: 2026-08-26
Engine commit at freeze: `73c127814af9b38db0cbeb48c4ca38b2e52c38a4`
Package / engine / agent protocol: 0.3.0 / 0.3.0 / 0.3.0
Benchmark version at freeze: `ssc-bench-v0.1`
Paper decision: **C — PROMISING BUT INSUFFICIENT**
  (`research/DECISION.md`)

This file is the running governance log. Claims, metrics, splits, budgets, and
baselines may not be silently edited after seeing results. A protocol change
requires a new version id and an explicit entry here.

## DONE

- Read repository contract and Supervisor-Skills governance procedures.
- Literature audit: `research/literature/` (verified citations; closest
  matrix includes LGuess, egg, FunSearch, AlphaGeometry, LeanDojo,
  O-Forge, Moxia, Shih 2026, CDS 2025, FORM).
- Idea-evaluator before: `research/reviews/idea_evaluator_before.md`
  (Accept with Revisions, mechanism-based).
- Frozen claims C1–C3, falsification, experiment freeze.
- Metrics + evaluator (`research/metrics/`). UNKNOWN never success.
- ssc-bench-v0.1 generated with engine-confirmed labels (128 items;
  test 42; hashes in `benchmark/validation/freeze_manifest.json`).
  Guo parked in **dev** (contaminated).
- Deterministic baselines B0, B1-cert/raw, B6, B7-det.
- One Grok B7-agent seed on 7 test compactify items (0 false promotions).
- Idea-evaluator after, tech skeleton (do not draft), benchmark audit,
  Reviewer 1 (sympathetic) and Reviewer 2 (hostile PL).
- Decision gate issued: C.

## EVIDENCE

Artifacts:

- `docs/experiments/2026-08-21-*.md` (Guo A/B, n=3, not frozen bench)
- `research/runs/protocol_v0/ANALYSIS.md`
- `research/runs/protocol_v0/engine_adjudicate_{dev,test}.json`
- `research/runs/protocol_v0/B{0,1-cert,1-raw,6,7-det}_{dev,test}.json`
- `research/runs/protocol_v0/B7-agent-grok_test_compactify_seed0.json`

Headline measurements (frozen test):

- Tier A engine: 35/35 label match, 0 false promotions, 28/28 NONZERO
  detection, 1 honest UNKNOWN.
- Compactify n=7: B1 mean Δops 0.143; B7-det 0.429 with one sum-merge;
  Grok agent 0.714 Δops, 0 false promotions. Dev n=17: B1 Δops 0.824 >
  B7-det 0.353.

C2 is **not supported**. C1 vs LLM/CAS is **untested** in batch. C3
**inconclusive**.

## FAILED

- B2 Mathematica unavailable.
- Lean kernel cross-check unavailable.
- egg/LGuess baseline unavailable (B6 is a restricted Python saturator).
- B3/B4/B5/B7-agent 5-seed multi-model table not run (no batch LLM
  client; Anthropic token present but unused for batch).
- Ablations A1–A7 not run (A1 would require an unsafe promote path).
- C2 strong form fails on v0.1 easy compactify vs B1.
- Compactify test set too easy; only one held-out scientific compactify
  item (`C-green-spectral`).

## SEARCH BOTTLENECK (2026-08-26)

See `research/search_bottleneck/`. B1 vs B7-det was **not** an agent test.
Hard DEV R1–R5 (seed 0): D2 kernel merge is ZERO for every arm including
named transforms; D3–D5 are mostly names/prose/UNKNOWN; blank drop-Piecewise
is UNKNOWN but claimed proven; Fermi recurrence is not ZERO. Isolated
scientific proposer improves hypothesis *type*, not certified D-level.
Single next change: multi-step isolated scientific proposer with mandatory
definition expansion; do not add unsound special-function ZEROs.

## OPEN QUESTIONS

1. Does C1 hold against B4/B5 on a **hard** set with 5 seeds?
2. Can a harder compactify tier reverse the B1 ≥ B7-det ops result
   without changing frozen v0.1 (would be v0.2)?
3. Second model family still missing for C3.
4. Certification remains Level 1 (SymPy engine semantics) only.

## NEXT STEP

Search-bottleneck phase (`research/search_bottleneck/DECISION.md`):
attack **stop-after-shallow-ZERO + unexpanded names** with an isolated
scientific proposer that must emit closed candidates. Do not weaken
the verifier and do not retune frozen test.

Paper gate remains C. Do not draft.

## Decision gate

**C — PROMISING BUT INSUFFICIENT**

No `paper/` directory. Title unfrozen and unused.
