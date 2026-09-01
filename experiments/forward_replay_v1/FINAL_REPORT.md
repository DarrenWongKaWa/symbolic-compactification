# FINAL REPORT — forward proposer replay v1

**Verdict:** `FORWARD_WORKFLOW_DEMONSTRATED_WITH_CAVEATS`

Product: `derivation-audit-v0.2.1-alpha` peel `783ec64`.
Engine: `python_sympy_exact_v1` / `0.3.0`.
Evidence paper: Guo et al., Phys. Rev. Lett. 136, 206303 (2026), arXiv:2511.16422v2.
`src/` was not modified. No v0.2.2. No new rule certificates.

The central object:

```
proposal → verify → promote/refuse → next step
```

The central claim tested: proposal authority ≠ verification authority.
Operationally: no admissible evidence ⇒ no scientific-state promotion.

This is **not** a benchmark paper and not a leaderboard. Supervisor-Skills
`benchmark-paper-template` was used in targeted mode only (experiment
design: G1–G4, leakage, diagnostics). Findings below describe capability
boundaries.

---

## Stop conditions

| Condition | Observed |
|---|---|
| False promotion of a known-invalid injected candidate | **0 / 36** |
| Exact-string leakage of hidden targets into context packages | **PASS** (`metrics/leakage_scan.json`) |
| Need to change verifier semantics | **No** (gaps recorded, not implemented) |
| Unreproducible evidence | Frozen candidates + `verification/records.json` (n=124; sha256 in `metrics/FROZEN_HASHES.txt`) |

---

## What ran

### Proposer families (heterogeneous, not three prompts of one LLM)

| Family | System | Status |
|---|---|---|
| A. Gold / human control | Hidden published target inserted **after** generation | 8 recovery tasks |
| B. LLM / agent | Isolated subagent `01a05a7d-4632-7a53-a777-6d64d396aa15`; prompt = `contexts/<task>/` only | K=4, 9 tasks |
| C. Third-party symbolic tool | **gplearn 0.4.3** actually pip-installed and executed (BSD-3; seed 0; pop 200; 8 gens; 80 samples of \(E_t\)) | mandatory requirement met |
| D. Rule / CAS | SymPy 1.14.0 `expand/factor/together/cancel/simplify` | deterministic |

ERRLESS (arXiv:2608.09617): `PAPER_ONLY_OR_NOT_REPRODUCIBLE`. Not emulated.
PySR: no Julia binary; `import pysr` fails. Not faked.
AI Feynman: not installed; same native class as gplearn.

Outcome is **not** `NO_COMPATIBLE_THIRD_PARTY_SYMBOLIC_PROPOSER`: gplearn
ran end to end. Its native class is still symbolic regression, not
derivation rewrite. That mismatch is a result, not a defect to hide.

### Tasks (frozen before proposers)

8 recovery + 1 remainder negative control + MS-01 (3 algebraic steps).
See `TASKS_FROZEN.yaml`. BZ global IBP was not a recovery target.
The \(\Gamma\) remainder was **not** expected to become `ZERO`.

---

## Experiment A — one-shot masked recovery

Primary safety object is promotion, not TargetRecovery@K.

| Proposer | K | TargetRecovery@K | Honest reading |
|---|---:|---|---|
| gold_control | 1 | 8/8 | Pipeline can recognise the published next expression. **Not** proposer success. |
| llm_masked | 4 | 8/8 | Includes substitution *forms*. Allowed notes name the intended operation (factor, cancel, use \(e_{21}=-e_{12}\)). Pretraining contamination unmeasured. |
| cas_sympy | 4 | 6/8 | Recovers the **equivalence class** of \(E_t\) when \(E_t \equiv E_{\mathrm{target}}\). Fails FR-06 and FR-08 (identities not applied). |
| gplearn (raw+identity) | 2 | 6/8 | **Identity copy** of \(E_t\) only. |
| gplearn-raw only | 1 | **0/8** | Actual SR output. `PARSE_FAILURE` or `NONZERO`. |

Mode A promotion is `ZERO(current, H_i)`, which is not the same question as
`ZERO(H_i, E_target)`:

| Control | Recovered vs hidden target | Promoted vs current |
|---|---|---|
| gold FR-01…05, FR-07 | yes | yes (`ZERO`) |
| gold FR-06, FR-08 | yes | **no** (`NONZERO`) |

**Finding 1.** Target recovery and promotion eligibility are different
questions. A proposer can emit the published next formula and still be
refused if the frozen Mode A workspace cannot compile the identity that
makes that formula equivalent to \(E_t\).

**Finding 2.** On purely algebraic regroup/prefactor/antisymmetry steps,
CAS rewrites of \(E_t\) are `ZERO` versus both current and target. That
is stay-put equivalence, not a printed-form match, and it is still a
valid recovery under the protocol ("equivalent mathematical forms count").

LLM case studies (not a model bake-off):

- FR-04 `llm-3` omitted a factor of two on the \(g_{bc}\) channel:
  `NONZERO`, refused. Sibling candidates `llm-0..2` recovered.
- FR-06 `llm-0,1` recovered the hidden \(e_{21}\) form, `NONZERO` vs
  current, refused.
- FR-06 `llm-2` promotion `UNKNOWN`, refused. `UNKNOWN` is not a
  safety failure.

---

## Experiment B — injected negatives

36 injected candidates: sign flip, \(\times 2\), collapse to `0`, add `+1`.

| Metric | Value |
|---|---|
| False promotions | **0** |
| False promotion rate | **0.0** |
| `NONZERO` | 36 |
| `UNKNOWN` (promotion) | 0 |
| `PARSE_FAILURE` | 0 |
| `COMPILE_FAILURE` | 0 |

One injected candidate (`FR-08 neg-times_two`) had **target-recovery**
`UNKNOWN` (long simplify) while promotion stayed `NONZERO`. It was not
promoted.

FR-NC-01 remainder collapse to `0`: 1 explicit zero-collapse candidate,
**0 promoted**. Algebraic stay-put rewrites of the remainder can still
promote as equivalence to current; that is not remainder certification
(PRODUCT_GAPS G4).

**Finding 3.** Under this injected-negative mix, known-invalid candidates
did not enter accepted scientific state. Observed false promotion rate is
exactly 0. Semantics were not altered to force that zero.

**Finding 4.** Fail-closed statuses other than `NONZERO` (`PARSE_FAILURE`,
`UNKNOWN`) also refuse. That is the intended safety behaviour, not a
missing `NONZERO`.

---

## Experiment C — multi-step rollout

MS-01: FR-01 → FR-02 → FR-03. Not paper-adjacent.

| Family | Accepted / 3 |
|---|---|
| gold | 3/3 |
| llm first candidate | 3/3 |
| CAS first candidate | 3/3 |

Poison trajectory: FR-01 sign-flip **refused**; gold of the original
FR-01 current then **accepted**.
`poison_refused_then_gold_ok = true`.

A refused invalid step did not replace \(E_t\), so a later valid
candidate of the original state remained eligible.

Experiment D (verifier-feedback iteration) was skipped.

---

## Leakage

Exact hidden-target string scan: PASS on 8 recovery context packages.

Semantic leakage **cannot be proven absent**:

- Notes state the intended operation ("factor v1c and v1b", "cancel
  (2*e12**2)/(8*e12)", "you MAY use e21 = -e12"). That is allowed
  scientific objective \(C_t\), not the hidden formula, but it is not a
  blind expression-only puzzle.
- FR-06 / FR-08 identities are required to *state* the step.
- A proposer that memorized Guo et al. in pretraining is unmeasured
  (benchmark-design Element 6). Recorded, not denied.

---

## Proposer-agnostic claim that is actually supported

Supported at the **interface and gating** level:

```
LLM | gplearn | SymPy CAS | gold | injected invalids
        → same Mode A verify_hypothesis
        → ZERO | NONZERO | UNKNOWN | PARSE_FAILURE
        → promote only on ZERO
```

Not supported: that symbolic-regression engines are good derivation
proposers; that an LLM autonomously discovered Guo's next representation;
that Mode A can promote substitution-conditioned paper steps without a
new assumption language.

---

## Caveats (why not unqualified DEMONSTRATED)

1. Substitution identities are not compiled in Mode A (G1). Gold/LLM
   next-states of FR-06/08 recover as expressions and are refused as
   current-state promotions.
2. gplearn-raw TargetRecovery 0/8; identity-copy must not be sold as SR
   success.
3. MS-01 is not a single-expression contiguous paper chain.
4. Operational notes in \(C_t\) help the LLM; contamination unmeasured.
5. CAS "recovery" is equivalence-class, not printed grouping.
6. The experiment tree is not a shipped product `propose` CLI.
7. Remainder stay-put `ZERO` is not remainder proof.

---

## Paper handoff

Verdict is `FORWARD_WORKFLOW_DEMONSTRATED_WITH_CAVEATS`, so the paper
Forward / RQ1 section **may** be updated to cite this experiment, with
the caveats above, without converting the manuscript into a Benchmark
paper.

Handoff path (paper branch):
`paper/derivation-audit-method/working/forward-evaluation-handoff.md`.
