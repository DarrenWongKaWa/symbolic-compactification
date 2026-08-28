# Reproducibility — Track V3

No LLM. Python 3.12 `.venv`. Do not commit `.env`.

## Frozen inputs

```
.venv/bin/python -m pytest tests/test_ic_freeze.py tests/test_ic_schema.py -q
```

`FROZEN_INPUTS_V3.json` sha256:

`e1fc6df85b0d293f3251ec87c1827409f402c01752a73251be8899f5b00c41db`

Parent authorities: Track V `38d6d4a`, V2 freeze `4dee916`, V2 close `fe53ebc`.

## Package tests

```
.venv/bin/python -m pytest tests/test_ic_*.py -q
```

## Generic / adversarial suite

```
PYTHONPATH=. .venv/bin/python research/iterated_confluence/eval/generic_suite.py
PYTHONPATH=. .venv/bin/python -c "from research.iterated_confluence.falsifier import run_cases; print(run_cases()['n_false_family_zero'])"
```

## Local-complexity gate

```
PYTHONPATH=. .venv/bin/python research/iterated_confluence/eval/local_complexity.py
```

## Guo iterated rescore

```
PYTHONPATH=. .venv/bin/python research/iterated_confluence/eval/guo_iterated_rescore.py
```

Per-edge process budget: 25 s (`EDGE_SECONDS`). Timeout is UNKNOWN, never ZERO.

## Router / series / freeze versions

- Track V `check_limit` LIMIT_OPS_CAP=80 for `sympy.limit`; series has no ops cap (wall-clock budgeted in rescore).
- Spectator: mul-args AppliedUndef peel then Track V split; expanding splits rejected.
- Path independence: required only when two or more paths share start and end.
