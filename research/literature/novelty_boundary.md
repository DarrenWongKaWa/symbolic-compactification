# Novelty boundary (frozen 2026-08-26)

This document is a positioning contract, not a marketing note. Closest works
are real. "We found no prior work" is not used. Every remaining claim names
the experiment that would establish it.

Literature corpus: `corpus.md`. Comparison table: `closest_work_matrix.csv`.

---

## 1. What has already been done

### Untrusted proposer + trusted checker

This architecture is **not new**. It is the default of several 2023–2026
systems:

| System | Proposer | Checker | What is accepted |
|---|---|---|---|
| FunSearch (Nature 2024) | LLM mutates programs | deterministic evaluator | programs with better **score** |
| AlphaGeometry / AG2 | neural language model | symbolic geometry engine | formal geometry proofs |
| AlphaProof (Nature 2025) | RL/LLM tactics | Lean kernel | kernel-checked Lean proofs |
| LeanDojo / DeepSeek-Prover-V2 | LLM tactics | Lean | kernel-checked proofs |
| Draft-Sketch-Prove (ICLR 2023) | LLM sketches | Isabelle/Sledgehammer | formal proofs |
| LGuess (arXiv:2511.00403, EGRAPHS 2025) | LLM checkpoints | e-graph rewrite chains | polynomial factorizations |
| Guided equality saturation (POPL 2024) | **human** guides | e-graph / Lean | rewrite proofs and compiler opts |
| Moxia/AXIOM (arXiv:2606.00671, 2026) | LLM as canonicalizer | CAS handler + abstain | MATH answers with "no confident wrong" |
| O-Forge (arXiv:2510.12350) | LLM domain split | Mathematica `Resolve` | asymptotic **inequalities** |
| ToRA / PAL | LLM + Python/CAS tools | code execution | numeric/symbolic **answers** |
| Shih 2026; Cheung–Dersy–Schwartz 2025 | learned rewrite policy | oracle simplified form | HEP amplitudes / dilogs |

The methodological skeleton "LLM proposes, something exact-ish checks" is
crowded. A paper that leads with that skeleton will be desk-rejected as
"LLM + verifier".

### Exact rewriting without LLMs

Equality saturation (Tate et al., POPL 2009; egg, POPL 2021) already searches
large equivalence classes of terms with **syntactic rewrite soundness**.
Ruler (OOPSLA 2021) and Enumo (OOPSLA 2023) synthesize those rewrite rules.
Herbie (PLDI 2015) searches rewrites for **floating-point accuracy**, not
scientific compactness. NeuRewriter (NeurIPS 2019) learns region/rule picking
for Halide-style **expression simplification** against Z3.

CAS systems (Mathematica FullSimplify, Maple, SymPy `simplify`, FORM, Cadabra,
xAct) already compactify scientific expressions. They do not, as a class,
emit an auditable fail-closed residual with UNKNOWN as a first-class
non-success.

### Scientific symbolic work

AI Feynman discovers formulas **from data**. Feynman-integral reduction
(IBP/Laporta: FIRE, Kira, Reduze) compactifies integrals by linear algebra
over families, not by untrusted agents. Tensor canonicalization
(Butler–Portugal, xPerm) is deterministic. None of these is an agentic
propose–adjudicate–promote loop over `Sum`/`Piecewise`/indexed physics
kernels with hash-bound state.

---

## 2. What we are NOT claiming

Do not write, imply, or let a figure title say:

1. First combination of an LLM with a verifier.
2. A theorem prover, a Lean/Isabelle competitor, or a "formal proof".
3. A CAS replacement, or that SymPy/FullSimplify are obsolete.
4. A new physics discovery, or reproduction of the PRB \(\sigma_{abc}\)
   closed form (existing evidence: **nobody produced L4–L7**).
5. Exactness beyond **declared engine semantics** (SymPy residual pipeline,
   rational probes, named budgets). UNKNOWN is not success; numeric
   agreement is not ZERO.
6. Equality saturation, e-graph completeness, or confluence of a rewrite
   theory.
7. Prompt engineering as the contribution.
8. Generic symbolic simplification SOTA on Halide / Herbie / MATH.
9. That structure-aware search currently **beats** unconstrained CAS on
   scientific abstraction (existing Guo probe: blank agents were
   narratively closer and **uncertified**).

---

## 3. What exact methodological contribution remains

The remaining contribution, if experiments support it, is a **task +
protocol + measurement**, not a new checker primitive:

**Task.** Scientific *symbolic compactification*: rewrite a large
already-symbolic physics expression into a more compact equivalent form
while preserving `Sum` / `Product` / `Piecewise` / indexed calls, rather
than answering a MATH problem, proving a Lean theorem, or fitting data.

**Protocol.** Untrusted structural proposal → exact fail-closed
adjudication (`ZERO` / `NONZERO` / `UNKNOWN`) → hash-bound certified
state transition, with:

- representation preservation (semantic source is never replaced by a
  flattened CAS diagnostic);
- orthogonal assumption vs proof axes (`HUMAN_REQUIRED` ≠ `PROOF_REQUIRED`);
- promotion bound to current-hash, candidate-hash, ZERO, PROVEN, no human
  gate;
- residual + counterexample feedback on NONZERO;
- UNKNOWN blocking promotion.

**Measurement.** A three-tier benchmark that **separates** soundness
(false promotion, UNKNOWN honesty) from certified compactness from
scientific ladder progress, instead of one accuracy number.

That combination is **not** present as a packaged evaluation in LGuess
(polynomials), FunSearch (scored programs), AlphaGeometry (geometry
deduction), LeanDojo (mathlib theorems), Moxia (MATH answers), O-Forge
(asymptotic inequalities), ToRA (tool-using contest math), or Shih/CDS
(learned HEP amplitude simplification). Closest **method** is LGuess +
O-Forge + Moxia + FunSearch. Closest **domain** is FORM/Cadabra plus
Shih/CDS. The paper must argue the *gap between those*, not absence of
neighbors.

---

## 4. Claims a knowledgeable reviewer would reject immediately

| Claim | Why it dies | Who cites it against us |
|---|---|---|
| "First LLM+verifier for math" | FunSearch, DSP, LeanDojo, AlphaGeometry, AlphaProof, LGuess, Moxia | any PL or NeSy reviewer |
| "Formal certification / machine-checked proof" | checker is SymPy `simplify` + rational probes, fail-closed UNKNOWN | Lean/Isabelle/e-graph reviewer |
| "We compactify better than CAS" without matched budgets and without counting uncertified CAS output as a loss | existing Guo blank arm already looks better narratively | CAS users; the 2026-08-21 report |
| "Agent discovered the Guo closed form" | L4–L7 absent in all six runs | the authors' own experiment log |
| "Generalizes across physics" on only \(\sigma_{abc}\) | n=1 scientific workload | any ML reviewer |
| "E-graph baseline infeasible so omitted" without a restricted substitute | egg is the obvious PL baseline | POPL/PLDI reviewer |
| Treating UNKNOWN or 30-digit numeric agreement as success | contradicts the engine contract | ourselves |

---

## 5. Experiments that would establish each remaining novelty claim

These map 1–1 onto frozen claims in `research/protocol/CLAIMS.md`.

### N1 — Fail-closed protocol reduces false scientific promotions

**Claim.** On the frozen test set, B7 (full protocol) has statistically
lower **false-promotion rate** than B3 (blank LLM) and B4 (LLM +
unrestricted CAS), with B5 (verify without state/provenance) as the
ablation that isolates the state machine.

**Establishing experiment.** Tier A (known ZERO/NONZERO labels) + Tier C
corruptions; report false promotion, UNKNOWN rate, NONZERO detection.
Falsified if B4/B5 match B7 on false-promotion within the pre-registered
interval.

### N2 — Certified compactness vs CAS under matched budgets

**Claim.** Under the same wall-time and iteration budgets, the
**certified** output of B7 is more compact (ops, sums, Piecewise
branches, repeated kernels) than the **certified** output of B1/B2, and
CAS forms that cannot be certified are counted as uncertified, not as
wins.

**Establishing experiment.** Tier B + Tier C, matched budgets, compactness
metrics from `METRICS.md`. Falsified if B1/B2 certified forms dominate
B7, or if the only B7 win is syntactic ops with no scientific structure
gain.

### N3 — Not an overfit to Guo / one model

**Claim.** The same protocol, without test-set retuning, improves
false-promotion and/or certified compactness on ≥2 scientific families
and ≥2 model families.

**Establishing experiment.** Frozen test split; model × method table.
Falsified if gains vanish off Guo or appear for only one proposer.

### N4 — Representation preservation is load-bearing

**Claim.** Ablating structure summary / representation preservation
increases eager expansion or decreases certified ladder level.

**Establishing experiment.** Ablations A2 and A4. Falsified if removing
them does not move reliability or progress outside noise.

### N5 — Certification scope is stated honestly

**Claim.** We can measure agreement of ZERO decisions with an independent
CAS or kernel on a **tractable subset**, and we report disagreements.

**Establishing experiment.** `research/verification/`. If no second kernel
exists, the paper must say "exact under SymPy engine semantics" and
**must not** say "formal proof". That honesty is part of the contribution
only if we do not overclaim; it is not novelty by itself.

---

## Positioning sentence (for later paper use, not a title freeze)

> Prior proposer–verifier systems either check **answers** (FunSearch,
> Moxia), **formal proofs** (Lean/Isabelle/geometry engines), or
> **polynomial rewrite chains** (LGuess). Computer algebra already
> rewrites scientific expressions without an auditable fail-closed
> residual or a certified state protocol. This project studies whether
> an untrusted agent can make **certified** progress on large
> structural physics expressions when every accepted step is an exact
> ZERO residual bound to hashed state.

Title remains unfrozen until after the decision gate.
