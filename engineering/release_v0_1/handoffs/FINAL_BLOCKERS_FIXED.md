# Final E11 blockers fixed

## Scope

This lane fixes exactly the two blockers reported by the post-fix external-user
retest. It does not change scientific semantics, frozen research evidence,
engine version `0.3.0`, agent protocol version `0.3.0`, or package version.

## 1. Installed source revision

- Setuptools now generates `symbolic_compactification/_build_info.py` only in
  the build directory.
- Ordinary non-editable installs and wheel installs retain the exact source
  checkout `HEAD` even when the CLI runs outside that checkout.
- Runtime provenance prefers that immutable built identity and retains live
  Git as the editable/source-checkout fallback.
- Valid resolved identities are exactly 40 lowercase hex characters, with an
  optional `-dirty` marker. `unknown` remains the fail-closed fallback when no
  source identity exists and cannot satisfy the release provenance gate.
- Dirty means Git reported a tracked change or non-ignored untracked file at
  build/runtime identity capture.

The packaging regression runs both `pip install --target <dir> .` and a built
wheel install, invokes the workspace CLI from outside the repository, and
checks the persisted `provenance.json` commit.

## 2. Root README

The packaged long description is now the v0.1 researcher-workspace entrypoint.
It states the closed scientific boundary, makes Mode A canonical, documents
the fail-closed result contract and claim limits, links all release docs, and
moves the legacy file/session CLI and APIs to a compatibility section. The
obsolete Publication E status is no longer presented as current.

## Verification

- Focused packaging and release-critical rerun: `19 passed`.
- Packaging, release-critical, provenance, research API, and report/CLI set:
  `60 passed` after the README line-wrap assertion was corrected.
- A separate fresh CPython 3.12 ordinary-install and wheel-install replay is
  recorded by the coordinator after the final clean commit.

No scientific or frozen research artifact was edited.
