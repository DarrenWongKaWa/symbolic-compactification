# Owner: Subagent F — Adversarial falsifier

Attack only. Do not improve the method, compiler, or prompts.

Ten claims live in `cases.py` and `fixtures/*.json`. Local sympy / structural
checkers in `checkers.py` must not return ZERO on any of them. If
`research.representation_invention.obligations` later exposes compile/verify,
`obligations_probe.py` calls it and still forbids ZERO.

False ZERO count must stay 0. Do not weaken a checker to make an attack
"fail" (including always-NONZERO gates: `true_newton_dd_control` must remain
ZERO).
