# Final Scientific Verdict — Verified Representation Invention

## 1. What did Grounded-Proposer-v1 already establish?

On Guo DEV, same SOL / DeepSeek-v4-pro / budgets, catalog `G####` members:
**11/11** local confluence hypotheses ZERO, 0 NONZERO, 0 UNKNOWN, 0 grounding
failures (`3fea222`). That is systematic **local grounded confluence** (G1),
not \(\Phi_\Gamma\), not Newton/Hermite DD, not L4–L7.

## 2. Can the system move from local confluence to Newton DD?

**Sometimes, on clean controls.** DEV `dev-a-newton-first`, 5 seeds, P2:

| seed | type | DD class | ZERO / NONZERO / UNKNOWN |
|---:|---|---|---|
| 0 | `divided_difference` | DD-OK | 2 / 0 / 0 |
| 1 | `divided_difference` | DD-OK | 3 / 0 / 0 |
| 2–4 | `divided_difference` | mixed / DD-V0 | 1 / 2 / 0 |

Explicit \(F(z)=f(z)\), nodes, reconstruction \((F(x)-F(y))/(x-y)\), grounded
`G####`. Not 5/5. Not Guo.

## 3. Can it recover repeated-node / Hermite DD?

**Not as DD-OK.** Repeated-node and Hermite-two: the model often *names*
`hermite_divided_difference` or `divided_difference`, but obligations mix
ZERO/NONZERO/UNKNOWN. No seed was full Hermite DD-OK.

## 4. Can it discover a nontrivial master analytic object?

**Weak substitution masters only.** `dev-b-master-induct`: 3/5 seeds ZERO with
\(F(z)=G(z)\) and three substitutions \(a,b,c\). One operator kind. The
tautological bait (`F:=A` used once) was **5/5 ABSTAIN**. Not C3-strong
(need ≥2 operator kinds or structurally distinct operators).

## 5. What happened on Guo?

P2 (SOL), 5 seeds: parse OK, 3–5 grounded hyps/seed, types include
`local_confluence` (8 hyps) and `hermite_divided_difference` (seed 1).
**0 ZERO.** After scoring with full (non-truncated) source texts, compiled
confluence is **UNKNOWN** (generic `sympy.limit` / size guard), not P1's
specialized ZERO. P3 RAW: 1/5 PARSE_FAILURE, others same C/V wall.

This is **compiler/verifier-bound**, not “the model stopped proposing confluence.”

## 6. What representation level R0–R8 was reached?

| level | status |
|---|---|
| R0 local confluence | certified on P1 Guo; P2 Guo proposed, not re-certified by V2 |
| R1 Newton DD | certified on 2/5 DEV Newton seeds; 1/5 polygamma |
| R2–R3 Hermite | proposed, not DD-OK |
| R4 Piecewise→DD | mixed; not clean DD-OK |
| R5 special-function DD | 1/5 polygamma DD-OK |
| R6 master | shallow substitution only |
| R7–R8 | not reached |

Guo DEV boundary: still **G1**, not G2/G3.

## 7. What was discovery gain?

P2 emits `divided_difference` / `hermite_divided_difference` with explicit \(F\)
and `newton_dd` operators — types P1 Guo did **not** emit (`confluent_representation`
only). That is discovery-contract gain on synthetic tasks. On Guo, P2 still
mostly talks local confluence; seed 1 *typed* Hermite without certification.

## 8. What was grounding gain?

V2 `member_ids: [G####]` parsed on all P2 DEV and Guo P2 seeds (except P3 s0).
Aliases remain PARSE_FAILURE. G is no longer the Guo bottleneck it was under P0.

## 9. What was compiler/language gain?

New NEWTON_DD / HERMITE_DD / CONFLUENCE IR, Phase 5 all ZERO/NONZERO as
designed. Guo-scale expressions hit a **generic size/limit wall** (UNKNOWN /
COMPILE_FAILURE). P1's Guo ZERO used a specialized confluence compiler — that
is **not** silently copied here (no Guo-specific ZERO rule).

Truncated 220-char catalog texts originally caused false COMPILE_FAILURE;
rescoring with full source texts is compiler-side, hypotheses frozen.

## 10. What remained verifier-bound?

Guo confluence limits; some Hermite reconstructions; any member/latent longer
than the size guard (800 characters) → UNKNOWN, not ZERO.

## 11. Did SOL help or anchor representation search?

T1 A2=4/5 D remains frozen (SOL inductive bias on CSE). New P2 uses the same
SOL packets. Guo P2 (SOL) parsed more reliably than P3 s0 (RAW PARSE_FAILURE).
Not enough to claim SOL helps DD invention; it remains an observation prior.

## 12. Did the LLM beat frozen symbolic baselines?

| task | B9 | LGG | P2 DD-OK |
|---|---|---|---|
| Newton first | typed `divided_difference`, **no explicit \(F\)**, n_zero=2 (name-the-quotient) | 0 | 2/5 seeds, explicit \(F\) |
| Hermite two | `repeated_kernel` | 0 | 0/5 DD-OK |
| Piecewise→DD | `confluent_representation`, n_zero=0 | 0 | 0/5 DD-OK |
| polygamma DD | **0 hyps** | 0 | **1/5 DD-OK** |

**AI_UNIQUE_SUCCESS** is plausible only for the polygamma seed: baselines empty,
LLM grounded Newton DD, ZERO. Newton first is **not** unique vs B9's type label;
it *is* stronger operationally (\(F\), maps, reconstruction).

## 13. Which results generalized to held-out TEST?

Held-out `ssc-representation-bench-v0.1` TEST, P2, 5 seeds, **no prompt
change**:

| task | DD-OK seeds | notes |
|---|---|---|
| `test-a-newton-first` | **3/5** (s1, s3, s4) | C2 partial **replicates off DEV** |
| `test-a-hermite-two` | 0/5 | matches DEV failure |
| `test-a-wrong-sign-dd` | 0/5 | never DD-OK (good) |
| `test-b-piecewise-dd` | 0/5 | mixed confluence, not DD-OK |

Do not tune on these rows.

## 14. Which results replicated across seeds?

- Tautological abstain: 5/5
- Newton type `divided_difference`: 5/5; DD-OK: 2/5
- Guo P2 parse OK: 5/5; ZERO: 0/5
- Master substitution ZERO: 3/5

## 15. What did deepseek-v4-flash show?

`dev-a-newton-first` P2, 3 seeds, `deepseek-v4-flash` (matched contract):

| seed | DD-OK | ZERO/NONZERO/UNKNOWN |
|---:|---|---|
| 0 | yes | 3/0/0 |
| 1 | no | 1/2/0 |
| 2 | no | 1/2/0 |

Flash **can** emit certified Newton DD (1/3). Not more reliable than pro
(2/5). Claim: **within-provider robustness**, not multi-model generalization.

## 16. Which claims survived?

- C1 (grounded local confluence) — P1 Guo, already closed.
- Phase 5 machinery sound (false ZERO = 0).
- Grounding-in-the-proposal removes P0 alias ambiguity.
- Vocabulary ≠ discovery; \(H=(R,\{A_i\},\{O_i\},F)\) is the right object.

## 17. Which claims were falsified?

- “P1 11/11 implies systematic Newton/Hermite DD” — falsified.
- “Richer V2 contract alone yields Guo DD-OK” — falsified (C/V wall).
- “B9 cannot mention DD” — falsified on the Newton control (type only).

## 18. Strongest positive example

`dev-b-special-fn` P2 seed 2: `divided_difference`,
\(F(t)=\mathrm{polygamma}(0,t)\), members G0001/G0002/G0003,
reconstruction \((F(x)-F(y))/(x-y)\), three ZEROs. B9/LGG empty.

Also `dev-a-newton-first` P2 seeds 0–1: explicit Newton DD-OK.

## 19. Strongest counterexample

Guo P2 seed 1 types `hermite_divided_difference` on the 5-branch triple sum —
**not** DD-OK; compile/verify UNKNOWN. Naming Hermite is not G3.

Wrong-sign DEV: never DD-OK (good). Some ZERO on the true substitutions \(f(x),f(y)\)
while the flipped quotient is NONZERO.

## 20. Publication decision

**E.** See `PUBLICATION_DECISION.md`. No paper directory.

## 21. Exact commits / tags / artifacts

| thing | SHA / path |
|---|---|
| P1 freeze | `3fea222` |
| V2 contracts | `45b2b4d` |
| Phase 5 + scoring | `45f1e46` |
| P1 runs | `research/grounded_proposer/runs/` (unmutated) |
| P2 runs | `research/representation_invention/llm/runs/` |
| Phase 5 | `RESULTS_PHASE5.md` |
| DEV table | `RESULTS_DEV.md` |
| Baselines | `RESULTS_BASELINES.json` |
| Bench | `ssc-representation-bench-v0.1` |
| Freeze | `final/FREEZE_MANIFEST.json` |

Frozen authorities not mutated: B9 `4237f6b`, LGG `efc0924`, Beyond-LGG
`3214a5a`, SOL `0a2905b`, Track B `d20c1a2`.

## 22. HUMAN_REQUIRED remainder

None for the mathematical controls. A physicist is **not** required to decide
ZERO/NONZERO. Opening D6/I remains blocked until a certified DD or master
exists on a scientific expression (Guo-scale still UNKNOWN under generic V).
