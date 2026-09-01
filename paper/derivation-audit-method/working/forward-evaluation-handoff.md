# Forward evaluation handoff

Source experiment: branch `experiment/forward-proposer-replay-v1`
starting from product peel `783ec64`.
Tree: `experiments/forward_replay_v1/`.
Report: `experiments/forward_replay_v1/FINAL_REPORT.md`.

**Verdict:** `FORWARD_WORKFLOW_DEMONSTRATED_WITH_CAVEATS`

The paper is still a Technique paper. Do not convert it into a Benchmark
paper. `benchmark-paper-template` disciplined the experiment only.

## What the paper may now say (RQ1 / §4 / §7)

Heterogeneous untrusted proposers — a masked-context language-model
agent, a released symbolic-regression tool (gplearn 0.4.3, actually
installed), deterministic SymPy rewrites, a post-hoc gold control, and
injected invalids — were adapted onto the **frozen** Mode A verifier.
The loop is:

proposal → typed grounding → `verify_hypothesis` →
`ZERO` / `NONZERO` / `UNKNOWN` / `PARSE_FAILURE` → promote or refuse.

On the public Guo derivation (the same paper as the retrospective audit),
eight masked single-step recoveries plus one remainder negative control
were frozen before proposers ran. Observed false-promotion rate on 36
injected invalids: **0**. Gold recovered 8/8 hidden targets as
expressions; 6/8 were `ZERO` versus current. The two substitution-
conditioned gold targets remained `NONZERO` versus current because Mode A
cannot compile declared identities. That is a product-interface gap, not
a verifier change.

## What the paper must not say

- That an LLM autonomously discovered Guo's next formulae.
- That gplearn (or ERRLESS / PySR / AI Feynman) is a competitive
  derivation proposer. gplearn-raw recovered 0/8; ERRLESS had no public
  implementation; PySR had no Julia binary.
- That TargetRecovery@K is the scientific headline. The headline is
  evidence-gated promotion.
- That Mode A now ships a `propose` command.
- That remainder stay-put `ZERO` certifies an asymptotic remainder.
- Any unpublished private manuscript.

## Suggested manuscript edits (applied in this pass)

- §7 RQ1: add the masked Guo replay after the Mode A demos, with caveats.
- Table 7: compact forward-replay numbers. Table 6 stays the demo/session
  gate.
- CLAIMS.md: public Forward Mode evidence now includes the replay.
- Limitations: replace "no committed multi-step demo on a published
  physics calculation" with the experiment-tree fact plus the
  substitution-identity gap.
- Do not add a leaderboard or a 10-model bake-off.

## Product gaps to mention, not implement

See `experiments/forward_replay_v1/PRODUCT_GAPS.md`, especially G1
(identities are not Mode A assumptions). This agrees with existing
`working/future-product-gaps.md` items 1, 2, and 7.
