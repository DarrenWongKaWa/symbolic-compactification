# Evaluation stages (frozen before LLM)

Operational object:

```
H = (R, {A_i}, {O_i}, F)
```

Required fields: representation_type, grounded member IDs, roles, F
(if applicable), variables, nodes/multiplicities, operators, instance
maps, reconstruction, assumptions, proof obligations.

“this resembles a divided difference” is **TYPE_ONLY**, not success.

## Stages

| stage | question |
|---|---|
| D | correct representation family proposed? |
| G | source members correctly identified? |
| C | compile to exact proof obligations? |
| V | ZERO / NONZERO / UNKNOWN |
| Q | quality class below |

## Quality classes

OPERATIONAL_CORRECT, SHALLOW_REPACKAGING, TAUTOLOGICAL,
UNNECESSARY_STRUCTURE, WRONG_MEMBER, WRONG_OPERATOR,
WRONG_REPRESENTATION, TYPE_ONLY, COMPILE_FAILURE,
VERIFIER_UNKNOWN, PROBLEM_UNDERSPECIFIED.

A frozen B9 type-name without F/members/reconstruction is TYPE_ONLY.

## Depth

PROPOSED_DEPTH vs CERTIFIED_DEPTH. Never report R6 as achieved if only
an R2 relation verifies.

## AI_UNIQUE_SUCCESS

All of: strongest frozen symbolic baseline lacks the operational
representation; LLM proposes it; grounded; complete assumptions;
compile; required obligations ZERO; no leak; non-tautological; not a
rename. Candidate vs confirmed counted separately.

Guo is not in this experiment.
