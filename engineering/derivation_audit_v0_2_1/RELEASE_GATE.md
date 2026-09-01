# Release gate — 0.2.1-alpha

Product SHA intended for tag `derivation-audit-v0.2.1-alpha`.
Do **not** move `derivation-audit-v0.2.0-alpha`.

| Gate | Result |
|---|---|
| Identity `0.2.1-alpha` / PEP 440 `0.2.1a0` / engine `0.3.0` | PASS |
| `pytest -m release_critical` | 17/17 PASS |
| `pytest -m derivation_audit_release_critical` | 14/14 PASS |
| `tests/test_audit_bz_ibp.py` | 5/5 PASS |
| Public demos A/B/C inspect+verify+table | PASS (A: 2 ZERO; B: 3 ZERO + structural; C: 2 ZERO + remainder UNKNOWN) |
| Privacy: no `manuscripts/`, no `.private_validation/` | PASS |
| Guo workspace absent from this product tree | PASS |
| v0.2.0-alpha tag unmoved | PASS |

No new rule types beyond `BZ_TORUS_PERIODICITY`.
