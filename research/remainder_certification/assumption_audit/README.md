# R10 — assumption-leak auditor

Branch: `work/r-assumption-audit`
Parent: `adbfd9f` (RemainderCertificate IR freeze)
Owned: `assumption_audit/`, `tests/test_rc_assumption_audit.py`
Did not edit: `schema.py`, `ASSUMPTION_POLICY.md`, sibling R packages, V5 engine.

No LLM. Not Track V6. Track D2 stays **LOCKED**.
Do not revive the retracted `fb3b929` LEVEL_C ZERO.

## Job

Static scan of `research/remainder_certification/**/*.py` for silent
class-C/D insertions (positive beta, nonzero gamma, extra `real` on
mu, energy-difference genericity, polygamma-pole avoidance, “generic
parameters”, Cauchy `M` finiteness, real-only paths, small-`t` without
a disk). Comments count. Class A declarations on a certificate are
not leaks.

`research/coefficient_laurent/engine.py` is scanned only for the
retracted energy-domain ZERO shortcut. If that file is absent, the
suite still passes on `schema.py` + `ASSUMPTION_POLICY.md`.

Any finding:

- remainder verdict cannot stay `CERTIFIED` (`ASSUMPTION_REQUIRED`)
- hop remainder slot `ZERO` is rewritten to `UNKNOWN`
- hop ZERO promotion is forbidden

Remainder `CERTIFIED` is still not hop ZERO. Composition stays
`research.coefficient_laurent.schema.compose_hop_verdict`.

## API

```python
from research.remainder_certification.assumption_audit import (
    audit_certificate,
    apply_assumption_gate,
    scan_all,
    scan_text,
)

scan_all()                       # production tree + engine if present
audit_certificate(cert)          # never upgrades
apply_assumption_gate("ZERO", leaks=leaks)   # -> UNKNOWN if hidden
```

## Tests

```
PYTHONPATH=. python -m pytest tests/test_rc_assumption_audit.py -q
```

Attack snippets live in the test module, not in remainder Python.
