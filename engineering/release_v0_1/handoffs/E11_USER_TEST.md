# E11 — External-user simulation handoff

## Verdict

`INTERNAL_ONLY` at integrated commit
`6227c1e5b0291fb1915ce83a007b8ba6aa247bd0`.

## Completed replay

- Fresh CPython 3.12.13 environment and non-editable `pip install .`
- Both installed CLI entrypoints and the documented Python API snippet
- Researcher workspace initialization and manual Mode A input editing
- `inspect -> verify -> report` with a researcher-authored `ZERO`
- Intentional `NONZERO` with exact counterexample
- Committed Demo C via CLI with first-class `UNKNOWN`
- Source SHA-256 snapshots before/after all primary workflows
- Repeated-init no-overwrite check
- Environment secret-canary scan
- Default parse- and compile-failure UX probes

Functional outcomes were correct, fail-closed, and source-immutable. Exact
commands, timings, outputs, interpretation, and friction are recorded in
`engineering/release_v0_1/EXTERNAL_USER_SIMULATION.md`.

## Release blockers

1. External package/CLI identity remains `0.3.0`, not the requested
   `0.1.0-alpha`, and packaging retains the old summary.
2. Provenance records SymPy only and omits the direct PyYAML dependency.
3. The human report omits assumptions, detailed grounding/hypothesis context,
   member hashes, dependency versions, warnings, and artifact inventory
   promised by the quickstart.
4. Default parse/compile errors do not identify the offending source or
   obligation safely enough for a new user to correct them.
5. `ASSUMPTION_REQUIRED` is documented as active but has no external
   researcher-workspace API/CLI emission path.

No code fix was attempted in this lane, and no scientific semantics or frozen
research evidence was changed.
