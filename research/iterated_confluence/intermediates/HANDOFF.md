# HANDOFF — Track V3 Subagent V3-G (intermediate expression builder)

Parent: `dcfb90cac087a47241aced2dc0c3b851f1a12e21`
Branch: `work/v3-intermediate-builder`
Owned: `research/iterated_confluence/intermediates/**`, `tests/test_ic_intermediates.py`

Did not edit `schema.py`, `FROZEN_INPUTS_V3.json`, `freeze_v3.py`, or
historical run JSON. No LLM. No interpolated kernels. No gold names.

## What was implemented

`build_intermediate(parent_expr, variable, target_value, parent_id, symbols=None)`
under `research/iterated_confluence/intermediates/`.

```python
from research.iterated_confluence.intermediates import (
    build_intermediate,
    IntermediateBuild,
)

built = build_intermediate(parent, variable, target_value, parent_id, symbols)
# built.record            schema.IntermediateExpression
# built.expr              set only if reconstruction_ok
# built.reconstruction_ok True iff parent.xreplace({var: val}) is finite
#                         and equals the constructed expr
```

- Construction is raw `xreplace` only.
- `Eq` in `variable` / `target_value` / `condition` is Eq imposition.
- Vanishing denominator or non-finite image → `reconstruction_ok False`,
  `expr is None` (limit edges are not intermediates).
- Frozen 5-branch families: source `G####` members already occupy the
  3-index equality lattice, so no intermediate is required. Coverage is
  membership only; `constructed_intermediates` is always `[]`.

## Tests

`tests/test_ic_intermediates.py`

- exact sub `(x+y).subs(y, 0) == x`, `reconstruction_ok True`
- unevaluated `(x-y)/(x-y)` at `y=x` is not rewritten to `1`
- `(x**2-y**2)/(x-y)` at `y=x` is not an intermediate
- no interpolate / invent API
- source-ban on gold names
- six frozen 5-member families need no intermediate

Command: `.venv/bin/python -m pytest tests/test_ic_intermediates.py -q`

## Remaining risks

- SymPy evaluates `(x-y)/(x-y)` to `1` at construction; the builder can
  only refuse a ratio the caller actually passed.
- `.subs` is a reconstruction check after a finite `xreplace`; it is not
  used to construct. Disagreement refuses.
- Lattice completeness is index-set membership, not a confluence ZERO.

## COMMIT SHA

Parent `dcfb90cac087a47241aced2dc0c3b851f1a12e21`.
Branch `work/v3-intermediate-builder`.
Message: `Add exact intermediate expressions with reconstruction provenance.`
