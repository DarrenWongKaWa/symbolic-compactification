# Search-bottleneck decision

Date: 2026-08-26
Paper gate remains **C** (`research/DECISION.md`). This file only
localizes *why* certified workflows look shallow.

## 1. Where is the bottleneck?

**Primary: proposer / agent architecture (stop-after-easy-ZERO), plus
scientific-objective under-use, with a secondary verifier/parser gap
only for confluence of generic kernels.**

Not: “the verifier is too weak so we should turn it off.”
Not: “B1 vs B7-det showed agents cannot find kernels” (that pair was
deterministic routines; see `BASELINE_DIAGNOSIS.md`).

Evidence:

- D2 shared-kernel merge is already solved by named transforms and by
  every LLM arm (R1–R5). Verification **accepts** those ZEROs.
- Shallowness on D3–D5 is failure to emit **closed, expanded** candidates
  that the existing ZERO gate could accept, plus stopping once a D1/D2
  ZERO exists (Guo 2026 skill).
- R5 produces more D3–D5 *hypothesis types* (named master, keep-Piecewise
  confluence, index orbits) than R3. R1 produces similar bold types but
  marks them proven.
- Adding unsound recurrences or drop-Piecewise as engine ZERO would
  **lower** scientific reliability (Fermi/D4).

Regimes (protocol §): **A (proposer architecture) mixed with B
(scientific objective)**. C only for generic-kernel confluence / Guo
timeouts, which should stay UNKNOWN or HUMAN_REQUIRED. D on D5
checkable IR (prose not expressions). E: ops is the wrong headline;
already treated as secondary.

## 2. Does isolated subagent search materially outperform main-agent?

**On certified D-level: no** for D2 (tie) and **not yet** for D3–D5
(nobody certified above D1/D2).

**On search content: yes, modestly.** R4/R5 name masters and discuss
orbits; R3 usually factors and stops. Isolation is not magic: R3 still
proposed drop-Piecewise on D4.

Guo this run: R5’s hypotheses are closer in *type* to L3–L5 (shared
kernel, thermal master, keep branches until proved) than 2026 skill L2,
without gold names. They were not instantiated on the real 22 kB
expression. Do not call that a certified advance.

## 3. Does scientific-context guidance help without gold leakage?

**Yes for hypothesis family, no for certified ladder.** R5 vs R4: both
got domain context; R5’s role pushed named `Phi` and confluence language.
No `Phi_Gamma` / nine-generator leakage observed in packets. Guo R5
invented `V`, `F_master`, `W_*` rather than gold identifiers.

## 4. Are blank transformations wrong, or is the verifier incomplete?

Both, split by class:

| Blank-style move | Engine | Meaning |
|---|---|---|
| D2 kernel merge | ZERO | blank was right; skill also finds it |
| D3 factor | ZERO | right |
| D3 cot / reflection | parse fail; would need extra assumption | blank overclaimed |
| D4 drop generic Piecewise | UNKNOWN | **incomplete for generic confluence**; not licensed ZERO |
| Fermi `-1/z` | not ZERO | **wrong** on declared domain |
| Guo drop Piecewise as limits | historically UNKNOWN/timeout | incomplete *and* historically uncertified |

R2 (R1 text + our verifier) therefore **does its job**: keeps D2 ZEROs,
blocks or refuses the rest. Blank “bolder” ≠ blank correct.

## 5. Long-term goal still supported?

**Yes, as an architecture, not as a current empirical win.** The split
“imaginative proposer / conservative verifier / human assumptions”
matches the D4/Fermi/Guo pattern: we *want* R5-style hypotheses and we
*want* UNKNOWN/NONZERO to stop promotion. The missing piece is a proposer
that continues after L2 and always hands the verifier a **closed**
expression (definitions substituted).

## 6. SINGLE next method change

**Make an isolated scientific-structure proposer the searcher in a
multi-step loop that (i) expands `hypothesis_definitions` into a closed
candidate before `verify`, (ii) does not stop at the first D1/D2 ZERO,
and (iii) feeds NONZERO/UNKNOWN residuals back — without adding new
special-function ZERO rules.**

Do not, next:

- weaken the verifier;
- add `1/z` or drop-Piecewise as built-in identities;
- retune frozen test;
- implement an ensemble (R6), a new IR, and a Lean backend at once.

Attack **stop-after-shallow-ZERO + unexpanded names**. That is the
bottleneck this DEV run actually supports.
