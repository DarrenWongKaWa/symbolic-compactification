# HANDOFF — Track V3-E (path composition)

Parent: `dcfb90cac087a47241aced2dc0c3b851f1a12e21`
Branch: `work/v3-path-composition`

Commit message: `Add path composition: PATH_ZERO is not FAMILY_ZERO.`

## Owned

- `research/iterated_confluence/compose/**`
- `tests/test_ic_compose.py`

Did not edit `schema.py`, `PROTOCOL.md`, `FROZEN_INPUTS_V3.json`,
`freeze_v3.py`, `STATUS.md`, `OWNERS.md`, historical run JSON, or frozen
V2/V files. No LLM. No Guo gold names.

## What was implemented

Path composition under `research/iterated_confluence/compose/`. The rule
is imported, not reimplemented:

```python
from research.iterated_confluence.schema import compose_path_verdict
```

`compose_path` / `compose_paths` only package step verdicts into
`PathCertificate.path_verdict`. They do not emit a family verdict.

Public API (`from research.iterated_confluence.compose import ...`):

| symbol | role |
|---|---|
| `compose_path` | `list[PathStep] \| list[str]` → `PathCertificate` with `path_verdict` |
| `compose_paths` | fill `path_verdict` on each `PathCertificate` from its steps |

`PATH_ZERO` iff every required step is ZERO. Any step NONZERO ⇒
`PATH_NONZERO`. Otherwise `PATH_UNKNOWN`. Empty path is `PATH_UNKNOWN`,
not `PATH_ZERO`.

PATH_ZERO of one path with `require_path_independence=True` and no
consistency is FAMILY_UNKNOWN via `schema.compose_family_verdict` (called
only from tests).

## Tests

`tests/test_ic_compose.py`

Command: `.venv/bin/python -m pytest tests/test_ic_compose.py -q`

## Remaining risks

- Step adjacency (source/target chain) is not checked here; that is
  V3-B paths / V3-D edges.
- Path consistency / order independence is V3-F, not this package.
- Step verdicts are taken as given; this package does not re-verify
  local edges.
- A single PATH_ZERO path is never a family certificate.

## COMMIT SHA

Parent `dcfb90cac087a47241aced2dc0c3b851f1a12e21`.
Branch `work/v3-path-composition`.
Message: `Add path composition: PATH_ZERO is not FAMILY_ZERO.`
