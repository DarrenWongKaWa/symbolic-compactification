# External proposer landscape

Deep-research brief (frozen before adapters):

- RQ1: Which public systems generate *symbolic candidates* that can be adapted
  to a next-state transformation of an existing analytic expression?
- RQ2: Which of those systems are actually installable and runnable here?
- RQ3: Which native problem class is symbolic regression (fit f(x) to data)
  versus derivation transformation (rewrite E_t to E_{t+1})?

This is an implementation-availability audit, not a survey paper.

## Classification

| System | Paper | Repo | License | Native I/O | Class |
|---|---|---|---|---|---|
| ERRLESS | OpenReview/ICLR 2026 anonymous PDF; arXiv:2608.09617 cited in the campaign brief | **No public implementation found** in this session (PDF only; Bayesian SR via max-ent RL on expression ASTs; evaluated on AI Feynman / SRBench) | unknown | data → posterior over expressions | PAPER_ONLY_OR_NOT_REPRODUCIBLE |
| PySR | Cranmer, arXiv:2305.01582 | https://github.com/MilesCranmer/PySR Apache-2.0; `pip install pysr` | Apache-2.0 | (X, y) → sympy expression | RUNNABLE_BUT_TASK_MISMATCH (also **blocked here**: no Julia binary) |
| AI Feynman | Udrescu & Tegmark, Sci. Adv. 2020 | https://github.com/SJ001/AI-Feynman | MIT-ish (check repo) | (X, y) physics-motivated SR | RUNNABLE_BUT_TASK_MISMATCH (data-fit, not rewrite; heavy deps) |
| gplearn | Stephens; scikit-learn GP | https://github.com/trevorstephens/gplearn BSD-3; `pip install gplearn` 0.4.3 | BSD-3-Clause | (X, y) → symbolic program | RUNNABLE_AND_RELEVANT as a *third-party SR candidate source* on sampled evaluations of E_t, with explicit task-mismatch caveat |
| FunSearch | Romera-Paredes et al., Nature 2024 | no turnkey installer for arbitrary physics expressions | — | evolve code in a sandbox with an evaluator | PAPER_ONLY_OR_NOT_REPRODUCIBLE for this campaign |
| GPT-f / Lean copilots | Polu 2020; Song 2024 | Lean-specific | — | tactics in a kernel | NOT_APPLICABLE (wrong object) |
| Generic LLM | this session / recorded agent | n/a | — | masked text → candidate expressions | RUNNABLE_AND_RELEVANT |
| SymPy CAS rewrites | Meurer et al. 2017 | bundled with the frozen product | BSD | expr → factor/collect/expand/simplify | RUNNABLE_AND_RELEVANT (deterministic rule/CAS family) |

## Task-class distinction

Guo forward tasks are **derivation transformations**: E_t is already an analytic
expression; E_{t+1} is a regrouping, prefactor simplification, or substitution
of a declared identity.

Symbolic regression infers f from numerical samples. That can be *adapted*
to algebraic equivalence by sampling E_t(x) and asking the SR tool to
rediscover an equivalent formula. It cannot honestly express
substitution-conditioned steps unless the identity is already compiled into
the samples. We do **not** rewrite Guo tasks as Feynman-style data-fit
problems.

ERRLESS is therefore related work, not an adapter target.

## Decision

Third-party symbolic tool actually executed: **gplearn 0.4.3**
(Python-only GP symbolic regressor; see `INSTALL_THIRD_PARTY.md`).
Raw TargetRecovery@1 on the frozen tasks: 0/8. PySR would be preferred if
Julia were present; its absence was rechecked (`which julia` empty;
`import pysr` missing) and not faked. AI Feynman was not installed: it is
the same native class as gplearn, which already satisfied the mandatory
real-implementation requirement.

CAS family: **SymPy** already in the frozen engine environment.

LLM family: recorded masked-context generation (no target files in the
proposer prompt).
