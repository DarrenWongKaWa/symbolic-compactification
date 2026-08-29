# Reproducibility — Track V5

No LLM. Python 3.12 `.venv`. Do not commit `.env`.

## Frozen inputs

```
.venv/bin/python -m pytest tests/test_cl_freeze.py tests/test_cl_schema.py -q
```

`research/coefficient_laurent/FROZEN_INPUTS_V5.json` sha256:

`3d6a5bf2ba327b8b8b3f91609f185494ade3b0eeec303175ab7df98c014d16fc`

- `n_hops` = 18
- `no_llm_calls` = true, `no_new_hypotheses` = true
- `primary_hop` = `guo-p2-s0-i3:G0016->G0013`
- `method_version` = `v5-coeff-laurent-1`
- `parent_track_v4` = `248d247`

Parent authorities: V4 close `248d247`, V5 freeze `7102e8a`,
V3 soundness `d2752f9`, V2 close `fe53ebc`.

Unsound L-A close: `fb3b929` (remainder hardcoded ZERO).
Reviews: `a51f768` … `e27d2d3`. Remainder fail-close retracts hop
ZERO; case **L-D**. Tag `coefficient-space-laurent-v1` still points
at the first L-D close `ba2a0ce` (not moved).

## Package tests

```
.venv/bin/python -m pytest tests/test_cl_atoms.py tests/test_cl_basis.py \
  tests/test_cl_c0.py tests/test_cl_cache.py tests/test_cl_cache_audit.py \
  tests/test_cl_engine.py tests/test_cl_falsifier.py tests/test_cl_freeze.py \
  tests/test_cl_generic.py tests/test_cl_grouping.py tests/test_cl_numeric.py \
  tests/test_cl_pg_series.py tests/test_cl_poles.py tests/test_cl_rational.py \
  tests/test_cl_remainder.py tests/test_cl_schema.py tests/test_cl_sparse.py -q
```

Replay after remainder fail-close: **167 passed in 1.85 s** (`test_cl_engine.py` added).

## Generic / adversarial suite

```
PYTHONPATH=. .venv/bin/python research/coefficient_laurent/eval/generic_suite.py
PYTHONPATH=. .venv/bin/python -c "from research.coefficient_laurent.falsifier import run_cases; r=run_cases(); print(r.get('n_false_zero', r))"
```

false hop ZERO must be 0.

## Guo V5 rescore

```
PYTHONPATH=. .venv/bin/python research/coefficient_laurent/eval/guo_v5_rescore.py
```

Per-edge process budget: 40 s (`EDGE_SECONDS`). Timeout is UNKNOWN,
never ZERO. Ell-hops are expected to timeout; **do not raise the
budget after seeing sibling ZERO**.

Committed artifacts (do not rewrite to change a verdict):

- `GUO_V5_RESCORE.json` / `.csv` / `.md`
- hops ZERO=0 NONZERO=0 UNKNOWN=18 case **L-D**
- 6 m→n: LEVEL_B UNKNOWN, neg=ZERO, c0=ZERO, rem=UNKNOWN
- FAMILY_ZERO=0 FAMILY_UNKNOWN=7 `d2_unlocked=false`

Live replay of the six former m→n hops (not the 12 ell-hops):
`sparse_laurent_limit` on G0016→G0013 returned LEVEL_B UNKNOWN in
2.18 s, `max_intermediate_ops=1696`, `used_full_together=False`,
c0=ZERO, rem=UNKNOWN (CPython 3.12.13, SymPy 1.14.0).

## Versions

- method `v5-coeff-laurent-1`
- cache keys: source/target **full text** SHA256, degeneration,
  target value, assumptions hash, method version, atom-decomposition
  hash (`research/coefficient_laurent/cache.py`)
- C0 matcher: per-polygamma grouping; per-atom `together` of a coeff
  pair only; `used_full_together` always False
