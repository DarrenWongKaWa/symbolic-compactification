# E10 — Clean-room reproducibility handoff

## Verdict

`ALPHA_READY` for the E10 lane at
`eb02da4ee06f9d8d523b82a526dbdb317050588c`.

## Evidence delivered

- New detached clean clone of the exact requested commit
- Fresh CPython 3.12.13 non-editable install from the checkout
- `pip check`: PASS
- Both installed CLI entry points: PASS
- Release-critical gate: 12 passed in 8.15 seconds
- Installed-CLI demos: `ZERO`, `ZERO`, `UNKNOWN`
- Verify exit codes: 0, 0, 3
- `inspect` and `report` exit codes: all 0
- All required provenance fields present
- Exact bare 40-hex source revision in normal-install and wheel-install runs
- Every recorded input/expression/hypothesis/assumptions hash rederived from
  source bytes
- Source byte manifests identical before and after all demo commands
- Synthetic secret-canary scans: PASS
- Human reports generated for all three demos
- Direct clean-checkout wheel build and isolated outside-checkout CLI run: PASS
- Wheel SHA-256:
  `c111dcc047c9667afb510fcddc2d56c3453772ff49b75ddfce24371a4aff7c84`

The full commands, outcomes, hashes, timings, maximum RSS measurements, and
scope boundaries are in `engineering/release_v0_1/CLEAN_ROOM_REPLAY.md`.

## Blockers

None in the clean-room lane. The coordinator's final readiness audit and
three-reviewer release gate remain outside E10's decision authority.

## Change scope

Only this handoff and `CLEAN_ROOM_REPLAY.md` were added. No production code,
test, demo input, user source, or frozen scientific evidence was changed.
