# Public Real-Paper Validation — arXiv:2511.16422v2

Product: `derivation-audit-v0.2.0-alpha` (`0.2.0-alpha`, engine `0.3.0`).
Workspace: `examples/real_papers/arxiv_2511_16422/`.

Decision: **REAL_PAPER_VALIDATION_PASS**

This report does not claim that Guo et al. is fully verified, and it does not
claim that the physics is correct.

---

## 1. Source identity

| Field | Value |
|---|---|
| arXiv | 2511.16422v2 |
| Title | Dissipation-Shaped Quantum Geometry in Nonlinear Transport |
| Authors | Zhichao Guo, Xing-Yuan Liu, Hua Wang, Li-kun Shi, Kai Chang |
| Journal | Phys. Rev. Lett. 136, 206303 (2026) |
| Abs | https://arxiv.org/abs/2511.16422v2 |
| PDF | https://arxiv.org/pdf/2511.16422 |
| Source | https://arxiv.org/src/2511.16422v2 |
| Retrieved (UTC) | 2026-08-31T22:16:01Z |
| Local PDF SHA-256 | `de29f96e77cac8daf3c16867a14eb73862f3b9a7056f399fa5188533532771a2` |
| Local `main.tex` SHA-256 | `d2f82d48b19816bffbae22330d89c64f95027c4228c8d6f342036e981079220d` |

PDF and the arXiv tarball are **not** committed. Reconstruct from `SOURCE.yaml`.
Public scientific authority is the arXiv v2 source, not the local hash.

## 2. Audit scope

Field validation of the frozen v0.2 public API on selected supplement edges.
Not an exhaustive referee report. Not a new verifier. Not a novelty judgment.

Frozen set: **25** edges (12–25 required).

## 3. Equation inventory

`ssc audit inventory` on the equation-only stub: **30** curated labelled
environments, 0 duplicate labels.

`equations/CATALOG.yaml` lists **189 numbered** public equations (main-text
(1)–(8) plus A–G), with printed HTML/PDF tags and appendix-local indices.
Correction C-1 rebuilt those printed tags from arXiv HTML after a first
TeX-counter pass omitted the eight main-text numbers.

Numbering fact: `\theequation{\thesection-\arabic{equation}}` does **not**
reset per appendix. Appendix D begins at printed Eq. **(D-57)**. Local `D-1`
in the user prompt is printed `(D-57)`. Reviewer tables cite printed numbers.

## 4. Frozen derivation edges

See `FROZEN_EDGES.yaml`. Predictions there are **not** verification authority.

Covered regions:

- Appendix B: second-order current split and conductivity map.
- Appendix D: $\Gamma$ expansion; $K_{1A}$ regroup and metric substitution;
  $T_A$+$T_{B,\mathrm{geo}}$ cancellation; $C_{1,2}$ regroup; $V_{ab}$
  Feynman–Hellmann algebra; $\sigma^{(-1)}$ $I\cdot I$ cancel and
  $\Omega^2=-\Omega^1$ compactification; $T_0+T_1$ regroup; local $T_0$ sign
  algebra; $\sigma^{\mathrm{geo}}$ after declared $T_2$ IBP; $\epsilon_{21}$
  symmetrization; $n\bar n$ compact rewrite.
- Appendix E: stated multiband diagonal second-derivative identity (not lowered).

## 5. Exact executable edges

**18** edges lowered to native residuals and judged by `python_sympy_exact_v1`.

## 6. ZERO results

**18** engine ZERO rows, all in generated `TABLE_VERIFIED.md`.

| Edge | Printed eqs | Type |
|---|---|---|
| D.K1A-regroup | (D-59)→(D-60) | ALGEBRAIC_EQUIVALENCE |
| D.metric-pair | Key Identities → (D-60) | PAIRWISE_REDUCTION |
| D.K1A-metric-subst | (D-60) | ALGEBRAIC_EQUIVALENCE |
| D.TA-prefactor | (D-60)→(D-61) | ALGEBRAIC_EQUIVALENCE |
| D.TBgeo-eps21 | (D-66)→(D-67) | ALGEBRAIC_EQUIVALENCE |
| D.TA-TBgeo-cancel | (D-61)+(D-67)→(D-68) | ALGEBRAIC_EQUIVALENCE |
| D.C12-regroup | (D-71)→(D-72) | ALGEBRAIC_EQUIVALENCE |
| D.Vab-expand | (D-73) | ALGEBRAIC_EQUIVALENCE |
| D.Vab-eps21 | (D-73) | ALGEBRAIC_EQUIVALENCE |
| D.A-antisym | (D-74) | ALGEBRAIC_EQUIVALENCE |
| D.A-to-Omega | (D-74)→(D-75) | ALGEBRAIC_EQUIVALENCE |
| D.sigma-m1-Ii | (D-70)→(D-77) | ALGEBRAIC_EQUIVALENCE |
| D.Omega2-relabel | (D-77)→(D-78) | INDEX_RELABELING |
| D.T0-local-sign | (D-119) local members | ALGEBRAIC_EQUIVALENCE |
| D.T0T1-regroup | (D-120)→(D-121) | ALGEBRAIC_EQUIVALENCE |
| D.geo-T2-subst | (D-122)+(D-124)→(D-125) | ALGEBRAIC_EQUIVALENCE |
| D.eps21-symmetrize | (D-125)→(D-126) | ALGEBRAIC_EQUIVALENCE |
| D.compact-nbar | (D-126)→(D-127) | INDEX_RELABELING |

`D.compact-nbar` is the compact rewrite **after** substituting the paper’s
stated convention $f_n'=2f_{0,n}'$. It is not an independent discovery of that
factor of two.

Six ZERO rows (`D.K1A-metric-subst`, `D.TBgeo-eps21`, `D.A-to-Omega`,
`D.Omega2-relabel`, `D.eps21-symmetrize`, `D.compact-nbar`) certify the
**substituted residual**, not unsubstituted identity of the cited lhs/rhs
files. That is the v0.2 assumption-surface limit, disclosed on those edges.

## 7. NONZERO results

None. `TABLE_NONZERO.md` is empty.

A legitimate NONZERO would not by itself fail the field validation.

## 8. UNKNOWN / NOT_LOWERED

| Edge | Printed eqs | Status | Why not TABLE_VERIFIED |
|---|---|---|---|
| D.gamma-asymptotic | (D-57) | UNKNOWN | `ASYMPTOTIC_CLAIM`; remainder $O(\Gamma)$ is not a local residual |
| D.T0-ibp-global | (D-114)→(D-119) | NOT_LOWERED | `INTEGRAL_ARGUMENT`; BZ integration by parts |
| D.T2-ibp-global | (D-123)→(D-124) | NOT_LOWERED | `INTEGRAL_ARGUMENT`; BZ integration by parts |

## 9. Structural edges

| Edge | Type | Status |
|---|---|---|
| B.split-j2 | SPLIT_PARENT | SPLIT |
| B.j2-to-sigma | BOOKKEEPING | RECORDED |
| D.mv-identity | DEFINITION_INSERTION | DEFINITION |
| E.diag-2nd | DEFINITION_INSERTION | DEFINITION |

## 10. Asymptotic handling

Eq. (D-57) is typed `ASYMPTOTIC_CLAIM`. It was **not** rewritten as
$\sigma$ minus the truncated series equal to zero. Coefficient identities
were certified separately where they lowered. The enclosing remainder stays
UNKNOWN.

## 11. Global integration handling

Eqs. (D-119) and (D-124) IBP arrows are `INTEGRAL_ARGUMENT` / `NOT_LOWERED`.
Local sign algebra after the chain rule on (D-119) is a separate ZERO edge.
Algebra that *uses* the declared $T_2$ IBP result is a separate ZERO edge.
Global IBP authority is not transferred to those local zeros.

## 12. Assumptions

`assumptions.yaml` declares 30 real commuting scalars. `e12` and `e21` are
`nonzero: true` (two-band interband denominators).

v0.2 cannot encode parameter identities as machine assumptions. These paper
identities were **substituted into residuals**:

- $\epsilon_{21}=-\epsilon_{12}$
- $\Omega_{ab}^{2}=-\Omega_{ab}^{1}$
- $f_n'=2 f_{0,n}'$
- metric-velocity pair when inserting $g_{ab}$

## 13. Transcription audit

Two independent read-only reviewers transcribed against public `main.tex`
and HTML printed numbers. They were forbidden from assigning ZERO.

Agreement with the frozen native residuals on the high-value Appendix D chain
and on B/E/fail-closed classifications. No residual was retuned after the
engine run to manufacture ZERO. `CORRECTIONS.md` is empty.

## 14. Machine-verified table

Generated: `reports/TABLE_VERIFIED.md` (18 rows).
Copied into `reviewer-verification-package/TABLE_VERIFIED.md`.

Inclusion used `schema.may_appear_in_verified_table` / `schema.table_bucket`
only. Markdown cannot create ZERO.

## 15. Evidence integrity

`ssc audit verify` token: `AUDIT_RUN_RECORDED`.
Status counts: ZERO 18, DEFINITION 2, RECORDED 1, SPLIT 1, NOT_LOWERED 2,
UNKNOWN 1.

No PARSE_FAILURE, COMPILE_FAILURE, GROUNDING_FAILURE, INVALID_RECORD, or
NONZERO.

## 16. Reviewer package

`examples/real_papers/arxiv_2511_16422/reviewer-verification-package/`

Contains generated tables, assumptions, obligations, machine_results,
replay workspace, `reproduce.sh`, `MANIFEST.json`, and bibliographic
`SOURCE.yaml` (copied; the generic packager does not emit it).

## 17. Clean-room reproduction

From a copy of researcher-owned sources only (no runs/reports/package):

```
status_counts: ZERO 18, DEFINITION 2, RECORDED 1, SPLIT 1, NOT_LOWERED 2, UNKNOWN 1
TABLE_VERIFIED ids: identical
TABLE_UNCERTIFIED ids: D.T0-ibp-global, D.T2-ibp-global, D.gamma-asymptotic
```

Packaged `reproduce.sh` replayed the same 18/4/3 split.

Authored markdown ZERO cannot add a verified row.

No private/unpublished data is required.

## 18. Product friction

No generic production code was changed (budget 300 LOC unused).

Recorded friction, not v0.3 work:

- `assumptions.yaml` cannot encode $\epsilon_{21}=-\epsilon_{12}$ (must substitute).
- `factorial` is not in the parser whitelist (`4!=24` was skipped).
- `max_symbols` = 40 (this audit used 30).
- Abstract band sums are not auto-cancelled; two-band scalars were used.
- `audit package` does not export bibliographic `SOURCE.yaml`.
- Inventory extracts labels only; native algebra is always manual transcription.

## 19. Reviewer verdicts

| Reviewer | Role | Verdict |
|---|---|---|
| R1 | theoretical physicist | CAVEATED — tracks real App. D algebra; not a paper proof |
| R2 | verification skeptic | CAVEATED — 18 ZEROs bind to displayed residuals; 6 are substitution-weak |
| R3 | product evaluator | ALPHA_READY — public CLI, no `src/` change, A/B/C untouched |

Coordinator PASS is the A–I machine criteria, not unanimous ALPHA_READY.

## 20. Final field-validation decision

| Criterion | Result |
|---|---|
| A. ≥10 public executable residuals | 18 |
| B. ≥8 ZERO | 18 |
| C. no unauthorized TABLE_VERIFIED row | pass |
| D. verified rows map to public eqs | pass |
| E. ≥4 edge types overall | 8 types |
| F. asymptotic/global not promoted to ZERO | pass |
| G. reviewer package reproduces | pass |
| H. no private/unpublished data | pass |
| I. no verifier-core change | pass |

**REAL_PAPER_VALIDATION_PASS**

## 21. Exact commit

Branch: `engineering/real-paper-validation-arxiv-2511-16422` (from
`derivation-audit-v0.2.0-alpha` / `origin/main` at `aaf1199`).
The example commit SHA is recorded in git after this file is committed.
