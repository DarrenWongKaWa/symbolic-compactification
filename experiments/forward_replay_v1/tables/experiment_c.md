# Experiment C — MS-01 promote/refuse session

Rollout: FR-01 → FR-02 → FR-03.
These are three public Guo algebraic kernels, **not** paper-adjacent
states of one expression. The session tests the loop, not manuscript
adjacency.

| Family | Accepted steps | Notes |
|---|---|---|
| gold_control | 3/3 | Pipeline control; not proposer success |
| llm_masked first candidate | 3/3 | Algebraic regroup / prefactor / C12 |
| cas_sympy first candidate | 3/3 | Stay-put equivalent rewrites |
| poison: FR-01 sign_flip then gold | refuse then accept | Refused invalid did not poison later gold of the original state |

`poison_refused_then_gold_ok: true` in `metrics/experiment_c.json`.
