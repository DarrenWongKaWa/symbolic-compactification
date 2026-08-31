# symbolic-compactification Research Preview v0.1

**Context-grounded symbolic hypothesis generation with fail-closed
verification.**

Research Preview Alpha — experimental proposer, verified hypothesis checking.

Status: **`RESEARCH_PREVIEW_ALPHA`** (`0.1.0-alpha`). This is **not** a stable
v1.0 release. Scientific experimentation remains closed.

This package is the external researcher-facing slice of the v0.1 preview. The
reliable core is verified hypothesis checking. The proposer is experimental.

Install and run from a full repository checkout of tag
`research-preview-v0.1.0-alpha`. This directory is documentation and an
example workspace; it is not a second copy of the Python package.

## Start here

- [QUICKSTART.md](QUICKSTART.md) — one CLI workflow and one Python API workflow
- [INSTALLATION.md](INSTALLATION.md) — Python 3.12 install and wheel checks
- [WORKSPACE_FORMAT.md](WORKSPACE_FORMAT.md) — researcher-owned files
- [SEMANTICS.md](SEMANTICS.md) — `ZERO` / `NONZERO` / `UNKNOWN` and gates
- [LIMITATIONS.md](LIMITATIONS.md) — claim boundary; read before scientific use
- [REPRODUCIBILITY.md](REPRODUCIBILITY.md) — clean-room commands and results
- [CHANGELOG.md](CHANGELOG.md) — 0.1.0-alpha notes
- `EXAMPLE_WORKSPACE/` — the tree created by `symbolic-compactification init`

## Canonical workflow

```text
researcher workspace
    → inspect expressions, assumptions, notes, and references
    → register a symbolic hypothesis
    → compile its explicit proof obligations
    → adjudicate ZERO / NONZERO / UNKNOWN
    → write a provenance-rich report under workspace/runs/<run_id>/
```

Mode A (verify my hypothesis) is the supported workflow. Mode B (propose then
verify) is experimental and is not a workspace CLI command in this preview.

`ZERO` is the only result that certifies the submitted equality under the
declared engine semantics and assumptions. `UNKNOWN` is a valid fail-closed
result, not partial approval.

This is not an autonomous theoretical physicist, a universal simplifier, or a
system that discovers physics.
