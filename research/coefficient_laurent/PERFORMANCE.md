# Track V5 performance audit

No LLM. No ell-hop retune. Numbers below are either committed
artifacts or a live replay of the already-certified primary hop
and the generic suite. Timeout / size-guard is UNKNOWN, not ZERO.

Replay host: CPython 3.12.13, SymPy 1.14.0, `fb3b929`.
Command:

```
PYTHONPATH=. .venv/bin/python  # sparse_laurent_limit on G0016→G0013
.venv/bin/python -m pytest tests/test_cl_*.py -q
```

## Methods compared (same frozen primary hop)

| method | G0016→G0013 | ops / time | hop verdict |
|---|---|---|---|
| Whole-kernel `together()` (V4) | `together_ops=27327` | size-guard; never cancelled as a blob | UNKNOWN |
| Whole-kernel `series` / `limit` | historical 30–90 s process timeout | not used in V5 | UNKNOWN |
| V4 atom-series then `together` of the sum | 14 atoms; together still explodes on generic→diagonal | `GUO_HOP_RESCORE` provenance `laurent` | UNKNOWN |
| V5 sparse Laurent + per-polygamma C0 | `max_intermediate_ops=1696`; C0 tree `ops:990` | live `sparse_laurent_limit` **2.18 s** after remainder fail-close | LEVEL_B UNKNOWN (c0=ZERO, rem=UNKNOWN) |

Sibling ell-hops G0016→G0014 / G0016→G0015 were not re-timed.
Committed rescore: UNKNOWN, `EDGE_SECONDS=40`, `proof_level=LEVEL_A`,
neg/c0/remainder/max_ops all null.

## V4 baselines on the same family (not re-run)

`research/polygamma_confluence/GUO_HOP_RESCORE.json`, family
`guo-p2-s0-i3`:

| hop | V4 verdict | together_ops | note |
|---|---|---:|---|
| G0013→G0012 | ZERO | 1592 | diagonal→triple; atom-series `t0` |
| G0014→G0012 | ZERO | 2796 | diagonal→triple |
| G0015→G0012 | ZERO | 3845 | diagonal→triple |
| G0016→G0013 | UNKNOWN | 27327 | generic→diagonal; V5 target |
| G0016→G0014 | UNKNOWN | — | timeout |
| G0016→G0015 | UNKNOWN | — | timeout |

## Generic suite

`false_ZERO = 0`, 4 rows, live 0.0002 s (schema compose only).
Does not exercise Guo kernels.

## Caps (frozen; not retuned after sibling outcomes)

| cap | value | role |
|---|---:|---|
| `engine.NTERMS` | 3 | per-atom `series(t,0,NTERMS)` |
| `engine.PMIN` | −6 | sparse window start |
| `engine.PMAX` | 0 | through `t^0` |
| `engine.CANCEL_OPS_CAP` | 400 | blob cancel cannot ZERO a 1317-op C0−G0013 |
| `c0.OPS_CAP` | 800 | full-pair expand/cancel size-guard |
| `c0.PAIR_TOGETHER_CAP` | 4000 | per-atom rational `together` only |
| `c0.CANCEL_OPS_CAP` | 80 | per-atom cancel |
| `eval.EDGE_SECONDS` | 40 | process budget; timeout → UNKNOWN |

## What this table is not

It is not a reason to raise ell-hop budgets. It is not FAMILY
V_GAIN. Numeric probes are not in this table (`numeric/` cannot
mint ZERO).
