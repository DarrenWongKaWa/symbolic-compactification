# E10 HEAD clean-room handoff

## Verdict

`ALPHA_READY`

Exact tested commit:
`bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0`.

## Completed gates

- separate detached clean checkout: PASS
- fresh CPython 3.12.13 ordinary non-editable install: PASS
- fresh wheel build/install and outside-checkout execution: PASS
- installed import origins, `pip check`, and both console entry points: PASS
- release-critical group: `17 passed in 9.36s`
- CLI demos: `ZERO`, `ZERO`, `UNKNOWN` with verify exits 0, 0, and 3
- corrected Demo B fixed obligation: exact `ZERO`
- exact embedded build commit, dependency versions, and recomputed input
  hashes: PASS
- CLI and Python API source immutability: PASS
- environment secret-canary scans: PASS, zero matches
- genuine-`UNKNOWN` report symlink attack: rejected as
  `RUN_REPORT_INVALID`, exit 4, no attacker content
- forged regular report attack: rejected as `RUN_REPORT_MISMATCH`, exit 4,
  no attacker content
- one-snapshot parse/hash binding for project, assumptions, and hypothesis
  metadata: PASS (inside the 17-test gate)
- checkout cleanliness and `git diff --check`: PASS

No production code or frozen scientific evidence was changed in this lane.
The only committed outputs are this handoff and
`CLEAN_ROOM_HEAD_REPLAY.md`.

## Boundaries

- The full historical suite was not rerun under the one-full-suite policy.
  Its disclosed integration result remains `2049 passed, 24 failed`; it must
  not be reported as green.
- This verdict covers the bounded Mode A Research Preview workflow on the
  tested Python 3.12/macOS arm64 host. It is not a cross-platform matrix.
- It is an engineering reproducibility verdict, not a scientific result.
- No release tag existed during this replay. The coordinator owns the final
  decision and tag.
- The prior clean-room replay at `3de1a90` is stale relative to this HEAD
  and was not reused.

## Evidence

See `engineering/release_v0_1/CLEAN_ROOM_HEAD_REPLAY.md` for exact commands,
artifact hashes, performance measurements, and adversarial results.
