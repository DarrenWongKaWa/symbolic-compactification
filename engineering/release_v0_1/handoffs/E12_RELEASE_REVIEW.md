# E12 Release-Skeptic Handoff — Safety and Claims

Verdict: `INTERNAL_ONLY`

Reviewed integration HEAD:
`aca18646617c151d0914e739105ee1acf46d8d78`.

## Release blockers

1. `generate_report()` follows an existing `REPORT.md` symlink and trusts its
   prose. A genuine `UNKNOWN` run was made to return and print a false
   `Result: **ZERO**` plus an arbitrary canary read from outside the workspace.
   This fails `SECURITY` and `FAIL_CLOSED`.
2. Project, assumptions, and hypothesis metadata are parsed from one read and
   hashed from a second read. A deterministic assumptions race produced a
   `ZERO` run using `nonzero: false` while its recorded assumptions hash named
   bytes containing `nonzero: true`. This fails `PROVENANCE` and permits an
   assumption/provenance mismatch.

Detailed reproduction and acceptance criteria are in
`engineering/release_v0_1/reviews/REVIEW_C_SAFETY_CLAIMS.md`.

## Positive evidence retained

- release-critical: `12 passed`;
- focused workspace/API/CLI/security: `56 passed`;
- normal source immutability and environment-secret canaries: pass;
- ordinary input/run-directory escape guards: pass;
- normal `UNKNOWN` no-promotion semantics: pass;
- installed build revision/dependency provenance: pass;
- marketing/claim scan and scientific-line lock: pass.

The recorded `2049 passed, 24 failed` full-suite result is not green, but its
documented failures are outside the bounded external workflow and are not the
basis of this rejection. They must remain disclosed.

Only this handoff and the detailed reviewer report were changed. No production
code or frozen scientific evidence was edited.
