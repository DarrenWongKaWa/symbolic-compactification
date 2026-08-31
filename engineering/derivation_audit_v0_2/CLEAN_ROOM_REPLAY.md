# Clean-room replay — derivation audit v0.2

Commit: `c85a70361b3017fc42fbab6e7876e8578ec2f187`
Python: 3.12.13
Environment: fresh venv, `pip install` of a detached checkout of
`engineering/derivation-audit-v0.2`. No unpublished sources present.

## Results

| Gate | Result |
|---|---|
| `pytest -m derivation_audit_release_critical` | 11 passed |
| `pytest -m release_critical` (v0.1) | 17 passed |
| Public Demo A verify/table/package/`reproduce.sh` | PASS (2 ZERO) |
| Public Demo B verify/table/package/`reproduce.sh` | PASS (3 ZERO + DEFINITION + RECORDED) |
| Public Demo C verify/table/package/`reproduce.sh` | PASS (2 ZERO coefficients; ASYMPTOTIC_CLAIM UNKNOWN) |
| Wheel / sdist | built; no `.private_validation/` or `manuscripts/` members |
| Source immutability | PASS (release-critical) |

## Verdict

`CLEAN_ROOM_PASS`

Private unpublished material was not used. Optional local private acceptance
is skipped: the unpublished workspace is not in the public audit.yaml layout,
and converting it would copy non-exportable sources.
