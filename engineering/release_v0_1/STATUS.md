# Research Preview v0.1 Status

CURRENT_PHASE: `PUBLIC_PREVIEW_PUBLISH`

BLOCKERS: none for the bounded Mode A research-preview workflow.

ACTIVE_WORKTREES:

- three final reviewers complete
- `work/eng-repro-head` complete

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
- `4168672` — HEAD clean-room replay at `bd6f0a1`
- `d887b86` — final physicist UX review
- `98bb150` — final reproducibility review
- `a7a333a` — final safety/claim review

RELEASE_CRITICAL_TESTS: `PASS` (17 tests at `bd6f0a1`)

ALPHA_READINESS: `RESEARCH_PREVIEW_ALPHA`

NEXT_AUTO_ACTION: `Public update is branch + tag + notes, not a main merge and not stable v1.0. Optional later engineering: apply the workspace real:false gate to the legacy symbols.json/session CLI.`
