# HANDOFF — Track V3 Subagent V3-H (local complexity optimizer)

Parent: `dcfb90cac087a47241aced2dc0c3b851f1a12e21`
Branch: `work/v3-complexity`

## Owned

- `research/iterated_confluence/complexity/**`
- `tests/test_ic_complexity.py`

Did not edit `schema.py`, `freeze_v3.py`, `FROZEN_INPUTS_V3.json`, frozen
run JSON, or other V3 owner directories. No LLM. No identity tables.

## What was implemented

`reduce_kernel(expr)` searches for a lower-`count_ops` form using only
named algebraic rewrites (`cancel`, `together`, `factor`, `collect`) plus
exact child substitution. Each applied step is appended to `trace`.
Common-subexpression names are recorded as `let t = ...` lines and are
not secretly substituted.

Certification (fail closed):

- `original == reduced`, or `cancel(original - reduced) == 0`
- protected shape preserved: Piecewise branch conditions, Sum/Product
  limits, Integral/Limit heads
- uncertified proposals return the original with `equivalent=False`
- a different `expr_reduced` is returned only when `equivalent=True`

Piecewise is never a global `cancel`/`factor` target. Branches are
reduced independently and rebuilt with `evaluate=False`, so equal branch
values do not collapse the family.

This module reports ops before/after. It does not emit ZERO / NONZERO /
FAMILY_ZERO.

## Tests

`tests/test_ic_complexity.py`

Command: `.venv/bin/python -m pytest tests/test_ic_complexity.py -q`
Result: **12 passed**

- cancel `(x-y)*(x+y)/(x-y)` → `x+y`, `equivalent=True`, fewer ops
- monkeypatched uncertified rewrite rejected (`equivalent=False`, original)
- Piecewise not collapsed
- source-ban: no gold special-function names, no identity table, no CAS-global simplifier
- different `expr_reduced` implies `equivalent=True`

## Remaining risks

- `cancel` certifies rational-function identity, including cancellation
  of a common linear factor that is a hole on the variety `x = y`. That
  is the same local residual the verifier already uses; it is not a
  domain certificate.
- `factor` / `collect` are skipped above 80 ops so large kernels fail
  closed rather than hang. `cancel` / `together` still run on those
  forms when they stay algebraic and unprotected.
- Rebuilding a special-function head around a cancelled argument is
  kept only when `cancel` of the outer difference is 0. Argument-only
  kernels should be passed in separately.
- CSE `let` lines document repeated subexpressions; a later verifier
  must not treat them as a binding environment for `expr_reduced`.
- This optimizer does not decide confluence or family verdicts.

## COMMIT SHA

Parent `dcfb90cac087a47241aced2dc0c3b851f1a12e21`.
Branch `work/v3-complexity`.
Message: `Add certified local-kernel complexity reduction for V3.`
