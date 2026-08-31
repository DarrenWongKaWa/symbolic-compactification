# Final Reviewer Blockers Fixed

Date: 2026-08-31

Branch: `work/eng-review-blockers`

Scope: engineering-only remediation of the final physicist-UX and
safety/claim-boundary findings. No scientific evaluator, experiment, benchmark,
or frozen research evidence was changed.

## Fixes

1. `project.yaml`, the declared assumptions YAML, and
   `hypotheses/hypothesis.json` are each read into one immutable byte snapshot.
   Parsing, size checks, workspace summaries, and SHA-256 provenance now derive
   from exactly those bytes. Deterministic mutation regressions cover all three
   old double-read boundaries.
2. Persisted run artifacts are opened through a bounded, no-follow,
   regular-file boundary. Symlinks, nonregular files, out-of-run paths,
   oversized files, and artifacts that change during a read fail closed.
   Existing `REPORT.md` content is returned only when it byte-matches a fresh
   render from validated `result.json` and `provenance.json`; forged reports and
   report symlinks return stable codes without exposing their content.
3. Demo B is now one fixed, source-grounded, denominator-safe specialization
   of the already-frozen `C9H4/M9H1` Newton divided-difference identity:
   `alpha=1/3`, `x1_old=0`, `x1_new=1`, `x2_hold=1`, with fixed nodes `10/9`
   and `25/9`. Its one obligation is `ZERO`; the demo explicitly states that it
   is verification of frozen evidence, not discovery or generic-family
   certification.
4. Public workflow documentation, the capability boundary, and generated
   reports now state the exact v0.1 assumption surface: `real: true`/optional
   `nonzero`
   flags and declared functions only. Positivity, general inequalities,
   excluded poles, parameter identities, boundary conditions, symmetries, and
   limit order are not machine-enforceable, so hypotheses depending on them are
   outside supported alpha certification. `ASSUMPTION_REQUIRED` is documented
   as declaration-consistency checking for `assumptions_used`, not discovery of
   mathematically necessary assumptions.

## Verification

- Release-critical marker: `16 passed in 13.30s`.
- Combined affected suite (`release_critical`, workspace, research API/CLI,
  security, demos): `88 passed in 53.06s`.
- Coordinator split replay: workspace/API `32 passed`; CLI/security/demos
  `40 passed`.
- `git diff --check`: clean.
- Python compilation check: clean.
- Frozen research diff: empty.

## Remaining blockers

No blocker from the four remediated reviewer findings remains in the bounded
tests. Final clean-room replay and independent release re-review remain
coordinator gates; this handoff does not itself issue an alpha decision or tag.
