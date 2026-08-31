# Research Preview v0.1 Status

CURRENT_PHASE: `CLEAN_ROOM_AND_RELEASE_REVIEW`

BLOCKERS:

- Clean-room replay and final three-reviewer gate not yet complete.
- Historical full suite is not fully green; see `FULL_SUITE_RESULT.md` for the
  frozen-research-only triage.

ACTIVE_WORKTREES:

- `work/eng-repro` (next)
- `work/eng-release-review` (after replay)

MERGED_SHAS:

- `984783b` — packaging/install
- `9a6975e` — researcher workspace
- `0e59200` — provenance/run records
- `5fc1909` — Python API
- `ede6bd9` — security boundary
- `1dbd28d` — user documentation
- `bfe0a46` — workspace CLI
- `6227c1e` — immutable demos
- `6c4230a` — fail-closed semantics/release-critical group
- `590bc1c` — first external-user blocker fixes
- `73169db` — installed provenance and root README

RELEASE_CRITICAL_TESTS: `PASS` (12 tests)

ALPHA_READINESS: `PENDING_CLEAN_ROOM_AND_REVIEW`

NEXT_AUTO_ACTION: `Run clean-room install/tests/demos/provenance/secret replay.`
