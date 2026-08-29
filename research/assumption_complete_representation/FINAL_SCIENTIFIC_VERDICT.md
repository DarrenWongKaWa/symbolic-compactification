# Final Scientific Verdict — Assumption-Complete Representation Discovery

Publication decision: **F — CORE AI REPRESENTATION ADVANTAGE NOT SUPPORTED**

Decision cases: **B** (R2 reproducible on DEV; R3+ fails) and **D** (DEV signal does not generalize). Auditor B leakage FAIL blocks AI_UNIQUE_CONFIRMED.

No paper directory.

Guo remains sealed: `G0016 -> G0013 = UNKNOWN LEVEL_B`. Not in DEV or TEST.

---

## 1. DEV audit and evaluation strata

14 DEV tasks. Difficulty: TRIVIAL 0, SHALLOW 4, NONTRIVIAL 9, CHALLENGE 1.
Strata: CORE_COMPARABLE 6 (parseable); PACKAGING_GAP 8 (`UNPARSEABLE_WHITELIST`).
Parser was not extended.

## 2. CORE_COMPARABLE vs PACKAGING_GAP counts

DEV: 6 vs 8. Frozen operational baseline 0/14 must not be read as “LLM beat 14 baselines.”
TEST headline 10: CORE 4 vs PACKAGING_GAP 6.

## 3. Structural duplicate clusters

DEV near-duplicates kept: RESOLVENT_CLUSTER; DALECKII_KREIN_CLUSTER.
No additional DEV near-duplicates. Cluster-weighted n=12 DEV / 5 CORE clusters.

## 4. Frozen symbolic baseline results

DEV: operational_baseline 0/14 (2 TYPE_ONLY resolvents; 8 unparseable; 4 NO_HYPOTHESIS).
TEST CORE: operational_baseline 0/4, all NO_HYPOTHESIS. B0 residual ZERO is not discovery.

## 5–9. DeepSeek-v4-pro DEV (135 runs, 0 blocked)

Operational ZERO (scorer v1.3, two-point F required) only on RESOLVENT_CLUSTER:

| task | P0 | P1 | P2 | P3 | P4 |
|---|---|---|---|---|---|
| mp-resolvent-dd-01 | 4/5 | 2/5 | 3/5 | 3/5 | 4/5 |
| ac-r01 | 2/5 | 3/5 | 0/5 | 1/5 | 0/5 |
| phi / thermal-01/03/05 | 0 | 0 | 0 | 0 | 0 (phi P4 type 5/5) |

## 10. RAW vs SOL

Cluster-weighted OP P0 0.12 → P2 0.06. SOL does not help. ac-r01 collapses under P2. Observation-induced prior; not retuned.

## 11. Specialist effect

P3 raises tautological rate (0.66 vs P0 0.46), no extra certified depth.
P4 names DD/phi more often; ZERO on phi remains 0.

## 12. DEV representation-depth frontier

Highest CERTIFIED_DEPTH = **R2**. Proposed R3–R6 slogans do not certify.
Collapse: R2 (resolvent kernel) vs R3+ (phi, DLMF, masters).

## 13. DEV_METHOD_SELECTION

**GENERAL_FINAL = P0 RAW** (best cluster OP among P0–P3, lowest taut, lowest tokens).
**SPECIALIST_DD = P4** (not headline). No prompt v2.

## 14–15. TEST leakage and freeze

thermal-02 and mathias excluded from headline (near-dups).
Headline n=10. CORE_COMPARABLE TEST: tweedie, OU kernel, IFT scalar, SU(2) character.
CHALLENGE: Sokhotski–Plemelj, Opitz, Lyapunov, polylog, Pauli.
`final/FREEZE_MANIFEST.json`. Prompts not retuned.

## 16. Held-out DeepSeek-v4-pro

40 runs (P0+P2 × 4 tasks × 5 seeds). Blocked 0. **Operational success 0.**
Mostly TAUTOLOGICAL (catalog restatement). Type match is not certification.

## 17. DeepSeek-v4-flash robustness

12 P0 runs, 3 seeds. Operational success 0. Within-provider: no TEST operational ZERO.

## 18. Confirmed AI_UNIQUE_SUCCESS

Candidates: DEV resolvent R2 operational H vs B9 TYPE_ONLY.
Auditors: A PASS, **B FAIL** (SYSTEM_V1 contains “divided difference”), C PASS.
**AI_UNIQUE_CONFIRMED = 0.** Do not double-count the resolvent pair.

## 19. Seed robustness

DEV resolvent mp-resolvent P0 4/5; ac-r01 P0 2/5. Seed-sensitive on one member of the cluster.
TEST: no successful seed.

## 20. Domain generalization

Resolvent (scalar kernel) does not transfer to SciML masters, IFT, or Weyl character.
Thermal special functions: type names, verifier UNKNOWN or tautology.

## 21–22. Depth

Highest proposed: R6 slogans. Highest certified: **R2**. TEST certified: none.

## 23. D/G/C/V failure decomposition

DEV non-resolvent: D often type-correct (thermal), G OK, C OK, **V UNKNOWN** (DLMF) or tautological.
Phi: D mixed, V never two-point ZERO.
TEST: D mostly wrong or tautological restatement; not a packaging miss on CORE.

## 24. PACKAGING_GAP diagnostics

Not scored as AI_UNIQUE. 8 DEV + 6 TEST headline remain `SYMBOLIC_PACKAGING_UNSUPPORTED`.
Future parser-extension study = new method version.

## 25. Strongest positive scientific example

Scalar resolvent: `F(t)=1/(t-a)`, `G0003=(F(lam)-F(mu))/(lam-mu)`, `G0004=F(lam)F(mu)`, exact ZERO.
SHALLOW tagged. System prompt names “divided difference.” Not confirmed unique.

## 26. Strongest counterexample

Held-out CORE (Tweedie / OU / IFT / Weyl): 0/40 operational ZERO, mostly tautological.
Phi P4: 5/5 type-correct, 0 certified R3.

## 27. Symbolic algorithms that matched/reduced LLM successes

Frozen B9 TYPE_ONLY `divided_difference` without F. LGG pairwise templates on subterms.
Auditor A: not the same operational H. Still not unique after leakage.

## 28. Role of the sealed Guo control

Historical insufficiency control only. Not used for prompts, DEV, TEST, or rescue.
Authority UNKNOWN LEVEL_B unchanged. Remainder invariant untouched.

## 29. Reviewer findings

R6 benchmark skeptic: **FAIL** on “LLM invented operational representations beyond frozen symbolic baselines.” The only ZEROs are a dressed first-order identity whose catalog already writes the members.

## 30. Claims surviving review

- Assumption-complete screening can separate PROBLEM_UNDERSPECIFIED from D/G/C/V.
- Frozen whitelist packaging is a first-class stratum, not an AI win.
- SOL did not improve operational discovery on this DEV.
- R3+ did not certify.

## 31. Claims falsified

- LLM operational representation invention beyond comparable frozen baselines, confirmed and held-out.
- SOL as a discovery gain.
- Specialist prompts as depth gain.
- Publication-ready method.

## 32. Publication decision

**F**

## 33. Exact commits / tags / manifests

| item | SHA / path |
|---|---|
| Phase III start | `54d0392` |
| DEV execution freeze | `8a616a0` |
| Compiler v1.1 | `092ec56` |
| Scorer v1.2 | `d8248c9` |
| TEST freeze | `cff6763` |
| DEV 135 runs | `895a501` |
| TEST + verdict | `bc06e73` |
| Contracts | `1075d80` |
| Guo source-assumption | `9fc3c8a` |
| B9 / LGG | `4237f6b` / `efc0924` |
| Manifests | `DEV_EXECUTION_FREEZE.json`, `final/FREEZE_MANIFEST.json`, `EVALUATION_STRATA.json` |
| Guo | not in DEV/TEST |

## 34. Recommended next scientific question

A **new method version** (not a silent patch of this freeze): either (i) a parser-extension study so PACKAGING_GAP matrix-function / tensor tasks become CORE_COMPARABLE, or (ii) a proposer contract that never utters representation-type names, then a fresh DEV/TEST. Do not rescue Guo. Do not retune this freeze.
