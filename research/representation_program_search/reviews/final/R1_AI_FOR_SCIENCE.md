# R1 Final Review — AI for Science

## Review decision

**The DEV gate closure is scientifically honest. The experiment supplies no
scientific evidence that structured representation search discovers a new
representation, and no evidence that AI guidance improves such search. The
only permissible publication decision is F — STRUCTURED SEARCH ALSO FAILS TO
SUPPORT REPRESENTATION INVENTION — provided the report preserves the words
“fails to support” and does not recast the closure as an empirical failure of
the unrun search methods.**

This is an evidence-absence verdict caused by failure to construct the
mandatory calibration suite under the frozen rules. It is not a result that
enumeration, symbolic heuristics, SOL guidance, verifier feedback, or LLM
guidance searched valid scientific tasks and failed.

## Evidence boundary reviewed

- Branch head: `b54256766054b9ebdeaeaed9bbb6448cc9405ea0`
  (`RPS: close mandatory DEV calibration gate`).
- Gate authority inspected by the recorded independent audit: `a7ad6ab`.
- Frozen experiment contracts: `5321eaa`, with the COMPOSE access-path
  correction at `5216f77`.
- Search and evaluation implementation evidence reviewed: Program IR
  `3f0cf7f`; finite search frontier `d483767`; symbolic beam `e101009` plus
  isolation correction `a52e5a9`; verifier adapter `93cd86d`; post-hoc exact
  evaluation `73a9111`; S7 `ba6cdcf`; F0 evaluator `6e5fbef`; atomic runner
  `28745de`; statistics `c5dfa3c`; SOL search `b23b565`.
- Gate evidence:
  `audits/dev_gate_final/GATE_AUDIT.md` and `GATE_AUDIT.json`;
  `audits/gap_recovery_admission/INDEPENDENT_GAP_RECOVERY_ADMISSION_AUDIT.json`;
  `evaluation/clearances/C9H4.json`;
  `audits/r3_missing_final/R3_MISSING.json`;
  `audits/r4_r5_candidate_recovery/MINING_BOUNDARY.json`;
  `audits/r6_feasibility/INDEPENDENT_R6_FEASIBILITY_AUDIT.json`; and
  `falsifier/README.md` plus `falsifier/suite.json`.

The seven SHA-256 bindings in `GATE_AUDIT.json` were independently recomputed
and all matched. The gate validator returned `VALID`. An independent run of
all 35 `test_rps_*.py` files at the reviewed head completed with **321 passed**
in 234.24 seconds. These checks establish artifact and implementation
consistency only.

## Required separation of evidence

| Evidence class | What is supported | What is not supported |
|---|---|---|
| Software capability | Typed program/state IR, bounded legal-action search controls, symbolic/LLM/verifier/SOL condition boundaries, sessioned exact evaluation, fail-closed aggregation, and audit logging are implemented and exercised by tests. | Scientific usefulness, completeness of the generated search space, search efficiency, or generalization. The finite candidate policy explicitly records incompleteness. |
| Exact reference-program verification | The admitted `C9H4` R2 calibration package has 12 stored and 12 independently replayed ZERO verdicts across `G_FULL`, `G_NO_HERMITE`, and `G_PRIMITIVE`. The falsifier fixtures exercise exact rejection and one positive-control ZERO. | Search discovery. These are evaluator-side reference programs and synthetic controls, not programs found by S0–S7 or F0. ZERO certifies the stated equalities, not the claimed performance of a search policy. |
| Scientific search results | None. The final gate correctly prohibits scientific DEV execution, live LLM calls, TEST freeze, held-out runs, and method-result interpretation. | PROGRAM_SUCCESS, GRAMMAR_ADVANTAGE, search-budget curves, held-out R3+, verifier-feedback benefit, SOL benefit/anchoring, or comparison with F0. No method should receive either a success or a failure count. |
| AI contribution | The LLM roles are constrained to auditable legal rankings/actions, with fail-closed provenance and matched-control requirements implemented in software. | Any AI_SEARCH_ADVANTAGE, helpful mathematical judgment, harmful anchoring, token efficiency, model comparison, or even an empirical null. No eligible live S4, S5, or S7 scientific decision exists. |

## Strongest positive evidence

The strongest positive result is methodological infrastructure, not scientific
discovery. `C9H4` demonstrates that the frozen IR, compiler, assumption and
leakage clearance, grammar ablations, and exact session verifier can jointly
represent and certify a genuine public-source R2 family. Its primitive control
uses `VALUE` and `LINEAR_COMBINATION`, so the exact R2 reconstruction does not
depend on handing search a named Hermite primitive. This is useful evidence
that the system can encode and adjudicate at least one non-tautological
reference program.

That result must remain narrowly labeled: the public formulas are already
factorized, the case is DEV-calibration-only, it does not cross the primary
R3+ frontier, and no search method found the reference program.

## Strongest negative evidence

The strongest negative evidence is the failure to assemble the predeclared
scientific calibration suite without weakening freshness, source grounding,
assumption completeness, target-leakage, or executable-IR requirements:

- R3 remained missing after the bounded fresh-source audit; the strongest
  candidates were source-revealed divided-difference constructions or members
  of already inspected generic Hermite/Opitz families.
- R4/R5 remained missing because candidates were historical-template variants,
  required an unavailable positive-domain contract, produced NONZERO or
  UNKNOWN under the frozen verifier, or could not preserve the intended
  representation depth.
- R6 remained a `PACKAGING_GAP`: the mined mathematics requires matrix,
  noncommutative, block, integral, tensor, trace/determinant, or related
  semantics absent from the frozen executable scientific IR. Scalar lowering
  generally collapsed the proposed depth to R0–R3.
- The six falsifier traps are evaluator-only synthetic fixtures and therefore
  cannot serve as the required runnable scientific negative calibration task.

This is a meaningful negative result about the joint experimental design:
the frozen representation language, scientific packaging boundary, freshness
standard, and benchmark admission policy did not yield a viable R3–R6 DEV
suite. It does not isolate which of those components is responsible and does
not test the search algorithms themselves.

## Scientific honesty of gate closure

The closure passes this review because it does not substitute diagnostic,
historical, source-leaking, domain-unsound, depth-collapsed, or synthetic
fixtures for missing scientific slots. It also does not extend the parser or
grammar to rescue a desired result, reuse inspected TEST as fresh TEST, run
LLMs on an incomplete calibration suite, or count reference-program ZERO
receipts as search success. These are exactly the safeguards needed to avoid
manufacturing evidence for AI-for-Science capability.

The principal limitation must be prominent in every final report: gate
failure is not a clean causal test of the central decomposition. Because DEV
never executed, the experiment estimates none of the effects of grammar,
deterministic search, symbolic routing, verifier feedback, SOL, or AI. In
particular, the result cannot justify the stronger sentence “structured
search failed at R3+.” The defensible sentence is “this experiment failed to
produce evidence that structured search reaches R3+.”

## Publication-verdict assessment

- **A — TOP-TIER METHOD READY:** unsupported; there is no scientific method
  result or held-out evaluation.
- **B — SPECIALIZED METHOD READY:** unsupported for the same reason.
- **C — PROGRAM-SYNTHESIS / BENCHMARK PAPER READY:** unsupported; the required
  benchmark could not be assembled or frozen and no search curves exist.
- **D — SYSTEMS / VERIFICATION PAPER READY:** the software is substantial,
  but this experiment alone does not provide the scientific evaluation needed
  for that readiness claim.
- **E — PROMISING, MORE EVIDENCE NEEDED:** too positive as a scientific verdict;
  no eligible scientific search signal establishes promise.
- **F — STRUCTURED SEARCH ALSO FAILS TO SUPPORT REPRESENTATION INVENTION:**
  supported, strictly as a failure-to-support verdict for this closed
  experiment.

## Claims permitted at closure

1. A typed, exact-verification-aware representation-search software stack was
   implemented and tested.
2. One public-source R2 calibration reference program was independently
   admitted and exactly certified under three grammar variants.
3. The mandatory R3/R4–R5/R6/negative calibration suite could not be formed
   under the frozen scientific and leakage constraints.
4. Therefore no scientific search run, TEST freeze, held-out comparison,
   GRAMMAR_ADVANTAGE, or AI_SEARCH_ADVANTAGE was obtained.
5. The current executable scientific IR and case-packaging boundary are the
   observed bottleneck for several important matrix/operator/tensor families.

## Claims prohibited at closure

- Structured search was empirically worse than, equal to, or better than
  free-form proposal.
- Deterministic, symbolic, SOL-guided, verifier-guided, or LLM-guided search
  failed on eligible R3+ science.
- The LLM added no value, added value, or was harmed by anchoring in this
  experiment.
- Verifier feedback did or did not improve discovery.
- Any held-out generalization, search-efficiency, robustness, or causal
  component comparison was measured.
- Exact reference-program verification constitutes representation discovery.

## Final R1 recommendation

Accept the gate closure and issue **Publication F**, with an explicit subtitle
or lead sentence stating: **“The mandatory scientific DEV suite was
infeasible under the frozen executable IR and admission policy; no search
method or AI heuristic received a scientific trial.”** Preserve the software
as capability infrastructure and the exact packages as diagnostics/reference
evidence, but do not promote AI-guided search—or structured search itself—to
a supported scientific capability.
