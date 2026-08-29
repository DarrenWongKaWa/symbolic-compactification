# R13 — alternative remainder backends

Owner: `work/r-alternatives`. Parent `adbfd9f`. Not Track V6.
No LLM. No identity tables. Track D2 **LOCKED**.

Question: is remainder better solved by an existing certified
method than by a custom symbolic bound with explicit assumptions?

## Recommendation

**CONTINUE_CUSTOM**, not **CASE R-E**.

No mature remainder backend is both sound for this class,
decidable on symbolic affine polygamma, and importable now.
Arb / python-flint are absent. `sympy.holonomic` cannot
represent polygamma. SymPy `series` `O()` is not a bound.
V5 `remainder_ok` is the correct fail-closed gate and is
insufficient for symbolic α.

Continue the custom remainder certificate. List class-A/B
hypotheses on `RemainderCertificate`. Undeclared genericity
is `ASSUMPTION_REQUIRED`, never `CERTIFIED`. Remainder
`CERTIFIED` is not hop `ZERO`.

## Files

| file | role |
|---|---|
| `MATRIX.md` | method × soundness × decidability × dependency × use-now |
| `probe.py` | import/experiment replay; never mints hop ZERO |
| `__init__.py` | `run_probe`, `RECOMMENDATION` |

```bash
PYTHONPATH=. .venv/bin/python -m research.remainder_certification.alternatives.probe
PYTHONPATH=. .venv/bin/python -m pytest tests/test_rc_alternatives.py -q
```

Do not `pip install` a backend. Do not integrate Arb, Sage,
or `ore_algebra`. Do not unlock D2.
