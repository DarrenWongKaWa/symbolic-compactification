# Baselines (frozen with protocol v0)

Matched input, hidden-answer policy, and budgets:
`research/protocol/EXPERIMENT_FREEZE.md`.

| ID | Arm | Status on freeze host |
|---|---|---|
| B0 | raw input / no simplification | implemented |
| B1 | SymPy conventional (`simplify`, `factor`, `cancel`, `together`, `collect`, plus named engine transforms) | implemented; `B1-raw` claimed, `B1-cert` only ZERO promotions |
| B2 | Mathematica FullSimplify / Simplify | **unavailable** (no WolframKernel) |
| B3 | blank LLM agent, no engine, no skill | runner stub; requires a callable model |
| B4 | LLM + unrestricted CAS (SymPy simplify without promotion gate) | runner stub |
| B5 | LLM + CAS + `verify_equivalent` but no session/provenance/hash binding | runner stub |
| B6 | restricted Python e-graph (associativity/commutativity/distributivity + a few trig/exp rules) | implemented; **not egg**; mismatch documented |
| B7 | full symbolic-compactification protocol | B7-det: greedy named transforms + `adjudicate_candidate`; B7-agent: skill protocol |

## Unavoidable mismatches

1. B2 absent. Do not substitute Wolfram **text adapter** as FullSimplify.
2. B6 is not Willsey egg / LGuess. It is a small congruence-style saturator
   for items whose AST is in the supported grammar; others get
   `status=skipped_unsupported`.
3. B3–B5–B7-agent need LLM access. If only one model family is callable,
   C3 is inconclusive.
4. Guo flagship is in **dev** because it contaminated engine development.

## Ablations (B7 only)

| ID | Change |
|---|---|
| A0 | full method |
| A1 | no exact verifier (treat simplify-success as promote) |
| A2 | no structure_summary in proposer context |
| A3 | no residual/counterexample feedback |
| A4 | representation destruction: expand/doit before proposal |
| A5 | no provenance/state binding (same as B5) |
| A6 | main proposer vs isolated STRUCTURAL_PROPOSER |
| A7 | no scientific structural transforms (`combine_identical_sums` etc.) |

A1 is expected to raise false promotions; if it does not, C1's
attribution to the verifier is unsupported.
