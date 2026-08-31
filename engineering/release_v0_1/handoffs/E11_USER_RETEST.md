# E11 — External-user post-fix retest handoff

## Verdict

`INTERNAL_ONLY` at
`590bc1c5da7bc36ed36c23510f6b2ca9422e62f9`.

## What passed

- Fresh CPython 3.12.13 virtual environment and non-editable `pip install .`
- Correct `0.1.0-alpha` external identity on both installed CLIs
- Correct PyYAML 6.0.3 and SymPy 1.14.0 provenance
- Complete human report with hypothesis, grounding, hashes, dependencies,
  warnings, and artifact inventory
- Safe, located, actionable parse and compile diagnostics
- Real workspace `ASSUMPTION_REQUIRED` path
- Installed CLI `ZERO`, `NONZERO`, and committed Demo C `UNKNOWN`
- Documented installed Python API workflow
- Source-byte immutability for success, refutation, proof gap, all ingestion
  gates, report regeneration, and refused reinitialization
- Environment and malformed-source secret canaries absent from all generated
  run artifacts

All five blockers from the original E11 simulation are fixed.

## Remaining blockers

1. Non-editable installed runs record `git_commit: "unknown"`, not the
   originating commit required by the release provenance contract.
2. The root README used as the packaged long description still describes an
   obsolete scientific-era status and legacy workflow rather than the closed
   research boundary and v0.1 researcher workspace.

Commands, run ids, exit codes, timings, evidence, and the full post-fix audit
are in `engineering/release_v0_1/EXTERNAL_USER_RETEST.md`.

No production code or frozen scientific evidence was changed in this lane.
