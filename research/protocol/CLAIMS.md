# Frozen claims (at most three)

Freeze date: 2026-08-26
Engine commit: `73c127814af9b38db0cbeb48c4ca38b2e52c38a4`
Benchmark: `ssc-bench-v0.1`
Idea-evaluator (before data): `research/reviews/idea_evaluator_before.md`

These are **hypotheses to test**, not results. Paper drafting is forbidden
until the decision gate. Every scientific sentence in a later paper must
point to an artifact under `research/` or `docs/experiments/`.

## Research question

Can an untrusted AI agent make useful progress on difficult scientific
symbolic expressions while every accepted transformation remains exactly
auditable and semantics-preserving?

## Methodological framing (not itself a claim)

```
untrusted structural proposal
        ↓
exact fail-closed adjudication
        ↓
certified state transition
```

## C1 — Reliability of fail-closed adjudication

A fail-closed proposer–verifier–state architecture substantially reduces
**false scientific transformations** (false promotions) compared with
unconstrained LLM/CAS workflows, on the frozen test set, under matched
input, hidden-answer, and budget policies.

**Primary metrics.** False-promotion rate; NONZERO detection rate on
labeled corruptions; UNKNOWN rate (reported, never scored as success).

**Comparators.** B3 blank LLM; B4 LLM+unrestricted CAS; B5 LLM+CAS+verify
without full state/provenance; B7 full method.

**Substantial** is pre-registered in `EXPERIMENT_FREEZE.md` (not chosen
after seeing numbers).

## C2 — Certified scientific compactness

Structure-aware agentic search can reach **scientifically more compact
certified representations** than conventional CAS simplification under
matched resource budgets.

**Primary metrics.** Certified compactness vector (count_ops, n_sums,
n_piecewise_branches, repeated-kernel count) and, on Tier C, certified
ladder level. Uncertified CAS output is **not** a win for the CAS arm
and **not** a win for us.

**Comparators.** B1 SymPy conventional; B2 Mathematica if available
(else marked unavailable); B6 restricted e-graph; B7 full method.
B0 is the raw-input reference.

**Warning from existing evidence.** The 2026-08-21 Guo probe found the
skill path certified-shallow and the blank/CAS path narratively deeper
but uncertified. C2 may be false. If false, we record falsification and
do not retune the metric.

## C3 — Generalization

The protocol improves underlying models systematically across (i) at
least two substantially different proposer models and (ii) multiple
expression families, rather than overfitting to Guo \(\sigma_{abc}\) or
one proprietary model.

**Primary metrics.** Model × method table for C1 and C2 metrics on the
frozen test split; per-family breakdown (polynomial, rational, trig,
sum, piecewise, indexed, special-function, scientific).

**Comparators.** Same B3/B4/B5/B7 protocol, no test-set prompt retuning.

## Non-claims (imported from novelty_boundary.md)

Not claimed: first LLM+verifier; formal proof; CAS replacement; physics
discovery; PRB closed-form recovery; e-graph completeness.
