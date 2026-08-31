# Research Preview v0.1 Status

CURRENT_PHASE: `CLEAN_ROOM_REPLAY`

BLOCKERS:

- Clean-room replay at product HEAD `bd6f0a1` is in progress.
- Final three-reviewer gate (physicist UX, reproducibility, safety/claims)
  waits on that replay.
- Historical full suite is not fully green; see `FULL_SUITE_RESULT.md` for the
  frozen-research-only triage. That result is disclosed and is not being
  rewritten.

ACTIVE_WORKTREES:

- `work/eng-repro-head` (current HEAD clean-room replay)
- `work/eng-review-physicist` / `work/eng-review-repro` / `work/eng-review-safety`
  (after replay)

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
- `3de1a90` — reviewer-blocker remediation (Demo B, snapshot hashes, reports)
- `f9692c1` / `bd6f0a1` — reject unsafe `real: false` workspace semantics

RELEASE_CRITICAL_TESTS: `PASS` (17 tests at `bd6f0a1`)

ALPHA_READINESS: `PENDING_CLEAN_ROOM_AND_REVIEW`

NEXT_AUTO_ACTION: `Complete clean-room replay at bd6f0a1, then launch three independent reviewers.`
