# E11 final external-user handoff

Verdict: `ALPHA_READY`

Integration head tested:
`eb02da4ee06f9d8d523b82a526dbdb317050588c`.

## Scope

- Fresh CPython 3.12.13 virtual environment.
- Ordinary `pip install .`, not editable.
- Installed CLI and Python API run outside all checkouts.
- Root README/quickstart Mode A workflow.
- `ZERO`, `NONZERO`, `UNKNOWN`, `PARSE_FAILURE`, `COMPILE_FAILURE`, and
  `ASSUMPTION_REQUIRED`.
- Committed Demo C.
- Exact installed-build provenance, dependency inventory, report content,
  source immutability, overwrite refusal, and secret-canary scans.

## Evidence summary

- Install and `pip check`: PASS.
- Release identity: `0.1.0-alpha` / PEP 440 `0.1.0a0`; engine/protocol remain
  separately identified as `0.3.0`.
- Wheel SHA-256:
  `63a89f8394776e209a9364795d40021305029cdfeb42c8fb3143e15443b163f8`.
- All seven installed runs record exact commit
  `eb02da4ee06f9d8d523b82a526dbdb317050588c`, plus PyYAML 6.0.3 and SymPy
  1.14.0.
- Mode A and installed Python API: `ZERO`.
- Intentional mutation: `NONZERO`, residual `-1`, exact counterexample
  `x = -2` with value `-1`.
- Committed Demo C: `UNKNOWN`, exit 3, explicit no-promotion semantics.
- Parse/compile/assumption gates: actionable source, stable code, bounded hint,
  exit 4, persisted report, no default traceback.
- All researcher-source before/after hashes match outside `runs/`.
- Repeated `init` refuses overwrite with `WORKSPACE_ALREADY_EXISTS`.
- Environment and malformed-source canaries are absent from every generated
  run artifact.
- Installed package long description is the current root research-preview
  README.

No release blocker was found. Two terminology details remain non-blocking:
the low-level inspect parse code differs from the public result name, and
bound `Sum`/`Product` counters are not explained in compact inspect output.

Full evidence:
`engineering/release_v0_1/EXTERNAL_USER_FINAL_RETEST.md`.

Only these two report files were changed in this worktree; production code and
frozen evidence remained read-only.
