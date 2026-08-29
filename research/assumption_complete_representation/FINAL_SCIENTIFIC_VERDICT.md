# Final Scientific Verdict — Assumption-Complete Representation Discovery

Publication decision: **F — CORE AI REPRESENTATION ADVANTAGE NOT SUPPORTED**

Decision cases: **B** (R2 reproducible on DEV; R3+ fails) and **D** (DEV signal does not generalize). Auditor B leakage FAIL blocks AI_UNIQUE_CONFIRMED.

No paper directory.

Guo remains sealed: `G0016 -> G0013 = UNKNOWN LEVEL_B`. Not in DEV or TEST.

This freeze is closed. Do not start a V2 proposer, parser extension, or SOL retune from this file.

---

## 1. DEV audit and evaluation strata

14 DEV tasks, frozen before the causal matrix. Tags: TRIVIAL 0, SHALLOW 4, NONTRIVIAL 9, CHALLENGE 1. Easy tasks were kept. Guo excluded.

Strata (`EVALUATION_STRATA.json`):

- CORE_COMPARABLE: frozen stack can ingest the object; LLM hypotheses can be compiled and fail-closed adjudicated.
- PACKAGING_GAP: `UNPARSEABLE_WHITELIST`. Legitimate science; not AI_UNIQUE.

Parser was not extended after seeing the benchmark.

## 2. CORE_COMPARABLE vs PACKAGING_GAP counts

| split | CORE_COMPARABLE | PACKAGING_GAP |
|---|---|---|
| DEV | 6 | 8 |
| TEST headline | 4 | 6 |

DEV CORE: mp-resolvent-dd-01, ac-r01-resolvent-hilbert-identity, thermal-01, thermal-03, thermal-05, sciml-phi-hermite-01.

Frozen operational baseline **0/14** is not “LLM beat 14 symbolic baselines.” Eight tasks never entered the comparable stack.

## 3. Structural duplicate clusters

Near-duplicates kept, not dropped:

- RESOLVENT_CLUSTER: mp-resolvent-dd-01 ≈ ac-r01 (opposite resolvent convention)
- DALECKII_KREIN_CLUSTER: mp-daleckii-krein-01 ≈ sciml-daleckii-krein-01 (both PACKAGING_GAP)

No further DEV near-duplicates. Cluster-weighted CORE denominator is 5 (resolvent merged), not 6.

## 4. Frozen symbolic baseline results

DEV (`BASELINES_DEV.json`): operational_baseline 0/14. Two resolvents TYPE_ONLY (B9 name without F). Eight UNPARSEABLE_WHITELIST. Four NO_HYPOTHESIS. B0 residual ZERO is not representation discovery.

TEST CORE (`BASELINES_TEST.json`): operational_baseline 0/4, all NO_HYPOTHESIS.

## 5. P0 RAW results

135-run DEV matrix, scorer `ac-score-v1.3` (two-point F required for operational ZERO). P0 five seeds on 6 CORE tasks.

| | TASK_WEIGHTED | CLUSTER_WEIGHTED |
|---|---|---|
| TYPE_CORRECT | 0.87 | 0.86 |
| OPERATIONAL_SUCCESS | 0.20 | **0.12** |
| TAUTOLOGICAL | 0.40 | 0.46 |
| mean CERTIFIED_DEPTH | 2.0 | 2.0 |
| mean tokens | 7556 | 7715 |

Per-task operational ZERO: mp-resolvent 4/5, ac-r01 2/5, phi and three thermals 0/5.

## 6. P1 BASIC results

| | TASK_WEIGHTED | CLUSTER_WEIGHTED |
|---|---|---|
| TYPE_CORRECT | 0.90 | 0.88 |
| OPERATIONAL_SUCCESS | 0.17 | 0.10 |
| TAUTOLOGICAL | 0.43 | 0.48 |
| mean tokens | 8090 | 8460 |

P1 helps ac-r01 (3/5 vs P0 2/5) and hurts mp-resolvent (2/5 vs 4/5). Not a net gain over RAW. Inventory is not SOL.

## 7. P2 SOL results

| | TASK_WEIGHTED | CLUSTER_WEIGHTED |
|---|---|---|
| TYPE_CORRECT | 0.90 | 0.88 |
| OPERATIONAL_SUCCESS | 0.10 | **0.06** |
| TAUTOLOGICAL | 0.50 | 0.54 |
| mean tokens | 9064 | 9213 |

ac-r01 operational ZERO: 2/5 (P0) → **0/5** (P2). SOL is an observation-induced prior. It was not retuned.

## 8. P3 grounded-specialist results

| | TASK_WEIGHTED | CLUSTER_WEIGHTED |
|---|---|---|
| TYPE_CORRECT | 0.90 | 0.88 |
| OPERATIONAL_SUCCESS | 0.13 | 0.08 |
| TAUTOLOGICAL | 0.60 | **0.66** |
| mean tokens | 9476 | 9729 |

No certified depth above R2. False-abstraction rate is the highest of P0–P3.

## 9. P4 DD/Hermite specialist results

Predeclared eligible: mp-resolvent, ac-r01, sciml-phi. Not selected after P0–P3.

| | TASK_WEIGHTED (3) | CLUSTER_WEIGHTED (2) |
|---|---|---|
| TYPE_CORRECT | 1.00 | 1.00 |
| OPERATIONAL_SUCCESS | 0.27 | 0.20 |
| TAUTOLOGICAL | 0.40 | 0.50 |

mp-resolvent 4/5 ZERO (same as P0). ac-r01 0/5. **phi type-correct 5/5, certified R3: 0.** Naming divided-difference is not better unless ZERO rises.

## 10. RAW vs SOL causal effect

Controlled: same tasks, model, schema, seeds.

SOL **does not** improve operational discovery (cluster OP 0.12 → 0.06). Tautological rate rises. ac-r01 is harmed. Preserve the negative effect. Do not call SOL good or bad; it is an observation-induced hypothesis prior.

P0→P1 is mixed and smaller; the P2 drop is not explained by “more information” alone.

## 11. Specialist effect

P3 vs P0: more tautology, no extra certified depth.
P4 vs P3 on the eligible subset: more type-correct on phi, still zero certified R3. A specialist that says the type more often without ZERO is not better.

## 12. DEV representation-depth frontier

| R | eligible CORE | type-correct | operational ZERO | certified |
|---|---|---|---|---|
| R2 resolvent | 2 (1 cluster) | high | yes (cluster-reproducible) | R2 |
| R3 phi | 1 | P4 5/5; P0 2/5 | 0 | none |
| R5 thermal | 3 | ~5/5 | 0 | none (UNKNOWN or tautology) |
| R6+ | 0 CORE (packaging) | — | — | — |

Capability frontier: first-order (R2) only.

## 13. DEV_METHOD_SELECTION

**GENERAL_FINAL = P0 RAW**

Criteria: cluster-weighted OP, certified depth, false-abstraction, domain robustness, tokens. P0 wins OP, tautology, and cost among P0–P3. Depth tied at R2. SOL is not forced in.

**SPECIALIST_DD = P4** (not the headline method).

No prompt version 2.

## 14. TEST leakage audit

SOL-independent graph of 14 DEV + 18 HOLD. No LLM metrics used.

Do not headline: thermal-02 ≈ thermal-01; mp-mathias ≈ Van Loan; thermal-04 same Matsubara/coth family.

## 15. Frozen TEST / CHALLENGE composition

`final/FREEZE_MANIFEST.json` at `cff6763`. Prompts/parser/evaluator frozen.

Headline TEST (10): kato, parlett, tweedie, OU, DEQ-IFT, adjoint, Weyl SU(2), Ricci–Weyl, Clebsch, iso4.

CORE_COMPARABLE TEST (4): tweedie, OU, DEQ-IFT, Weyl SU(2).

DUPLICATE_CONTROL: thermal-02, mathias, thermal-04.

CHALLENGE: Sokhotski–Plemelj, Opitz, Lyapunov, polylog, Pauli.

P4 not run on TEST CORE (no unlabeled DD family there).

## 16. Held-out DeepSeek-v4-pro results

40 runs: P0 and P2, 4 CORE tasks, 5 seeds. Blocked 0.

**Operational success: 0.**

| task | P0 type | P0 OP | P2 type | P2 OP | dominant Q |
|---|---|---|---|---|---|
| tweedie | 0/5 | 0 | 0/5 | 0 | TAUTOLOGICAL |
| OU | 2/5 | 0 | 4/5 | 0 | TAUTOLOGICAL |
| DEQ-IFT | 1/5 | 0 | 1/5 | 0 | TAUTOLOGICAL / WRONG |
| Weyl SU(2) | 0/5 | 0 | 0/5 | 0 | TAUTOLOGICAL / WRONG |

Type names (OU under SOL) are vocabulary, not invention.

## 17. DeepSeek-v4-flash robustness

12 P0 runs, 3 seeds, frozen GENERAL_FINAL. Operational success 0. Within-provider: neither model certifies TEST CORE.

## 18. Confirmed AI_UNIQUE_SUCCESS cases

DEV resolvent operational H vs B9 TYPE_ONLY is a **candidate**.

| auditor | verdict |
|---|---|
| A baseline reduction | PASS (TYPE_ONLY / LGG ≠ F+maps+reconstruction) |
| B leakage | **FAIL** (`SYSTEM_V1.txt` contains “divided difference”) |
| C verification | PASS (rational numerator identically 0) |

**AI_UNIQUE_CONFIRMED = 0.** Do not count mp-resolvent and ac-r01 as two.

AUS-R2/R3/… confirmed counts: all 0.

## 19. Seed robustness

DEV mp-resolvent P0 4/5 (robust within that task). ac-r01 P0 2/5 (seed-sensitive). TEST: no successful seed. A single DEV family is not a capability.

## 20. Domain generalization

Resolvent R2 does not transfer to SciML masters, IFT, or Weyl characters. Thermal polygamma: type-correct, not certified. Matrix-function R3 (phi) and PACKAGING_GAP Daleckii–Krein/Hermite f(A) were never CORE-certified.

## 21. Highest proposed representation depth

R6 slogans (masters, pairs, “generic three-term combination”). Not achieved.

## 22. Highest certified representation depth

**R2** on DEV resolvent only. TEST certified depth: none.

## 23. D/G/C/V failure decomposition

| locus | typical failure |
|---|---|
| Resolvent DEV | D/G/C/V can all succeed (operational H) |
| Thermal R5 | D type-correct, G OK, C OK, **V UNKNOWN** (DLMF) or tautological restatement |
| Phi R3 | D mixed; two-point F obligations never ZERO |
| TEST CORE | D wrong or tautological catalog restatement |
| PACKAGING_GAP | not scored as representation superiority |

PROBLEM_UNDERSPECIFIED is not the bottleneck on admitted CORE tasks.

## 24. PACKAGING_GAP diagnostics

Optional one-seed P0 diagnostic was not spent (budget reserved for CORE). 8 DEV + 6 TEST headline remain `SYMBOLIC_PACKAGING_UNSUPPORTED`. LLM_READS_OBJECT is not AI_UNIQUE. Do not extend the parser in this version.

## 25. Strongest positive scientific example

Scalar resolvent: `F(t)=1/(t-a)`, `G0003=(F(lam)-F(mu))/(lam-mu)`, `G0004=F(lam)F(mu)`, exact ZERO. Task tag SHALLOW. System prompt names the type. Not confirmed unique. Not held-out.

## 26. Strongest counterexample

Held-out CORE (Tweedie / OU / IFT / Weyl): 0/40 operational ZERO, mostly tautological.
Phi P4: 5/5 type-correct, 0 certified R3.

## 27. Symbolic algorithms that matched/reduced LLM successes

Frozen B9: TYPE_ONLY `divided_difference` without F. Frozen LGG: pairwise templates on subterms. Auditor A: not the same operational H. After leakage, still not AI_UNIQUE_CONFIRMED.

## 28. Role of the sealed Guo control

Historical insufficiency / fail-closed demo only. Not used to tune prompts, not in DEV, not in TEST, not rescued. Authority UNKNOWN LEVEL_B. Remainder invariant: negatives ZERO ∧ C0 ZERO ∧ remainder UNKNOWN ⇒ UNKNOWN, never ZERO.

## 29. Reviewer findings

R6 benchmark skeptic: **FAIL** on “LLM invented operational representations beyond frozen symbolic baselines.” The only ZEROs are a dressed first-order identity whose catalog already writes the members; SYSTEM_V1 primes the type name.

## 30. Claims surviving review

- Assumption-complete screening can separate PROBLEM_UNDERSPECIFIED from D/G/C/V.
- Packaging/whitelist is a first-class stratum, not an AI win.
- SOL did not improve operational discovery here.
- R3+ did not certify on CORE.
- Held-out CORE did not replicate DEV R2.

## 31. Claims falsified

- Confirmed, held-out operational representation invention beyond comparable frozen baselines.
- SOL as a discovery gain.
- Specialist prompts as depth gain.
- Publication-ready method.

## 32. Publication decision

**F — CORE AI REPRESENTATION ADVANTAGE NOT SUPPORTED**

## 33. Exact commits / tags / manifests / benchmark hashes

| item | SHA / path |
|---|---|
| Phase III start | `54d0392` |
| DEV execution freeze | `8a616a0` |
| Compiler v1.1 (G0001/F(arg) expansion; COMPILER_GAIN) | `092ec56` |
| Scorer v1.2/v1.3 (tautology / two-point F) | `d8248c9` |
| TEST freeze | `cff6763` |
| DEV 135 runs | `895a501` |
| TEST + verdict | `bc06e73` |
| Pin / SOL cache | `bc7cf38` |
| Contracts | `1075d80` |
| Guo source-assumption audit | `9fc3c8a` |
| B9 / LGG | `4237f6b` / `efc0924` |
| Manifests | `DEV_EXECUTION_FREEZE.json`, `final/FREEZE_MANIFEST.json`, `EVALUATION_STRATA.json`, `TEST_MANIFEST.json` |
| Guo | not in DEV/TEST |

## 34. Recommended next scientific question

A **new method version**, not a silent patch of this freeze:

1. Parser-extension study so PACKAGING_GAP matrix-function and tensor tasks become CORE_COMPARABLE; or
2. Proposer contract that never utters representation-type names, then a fresh DEV/TEST.

Do not rescue Guo. Do not retune this freeze. Stop here.
