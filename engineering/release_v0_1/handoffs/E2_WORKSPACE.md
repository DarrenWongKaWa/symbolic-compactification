# E2 — Workspace UX handoff

## Scope

Implemented the minimal external researcher workspace in
`symbolic_compactification.workspace`. This slice does not implement CLI
parsing, verification orchestration, reporting, provenance records, or a
proposer.

## Public foundation

- `initialize_workspace(path)` creates a new workspace and refuses every
  existing target, including an empty directory. It never overwrites a user
  file.
- `load_workspace(path)` validates and reads a workspace without writing to
  it. It returns a typed `ResearchWorkspace` snapshot.
- `WorkspaceError` includes a stable `.code`, an actionable `.detail`, and an
  optional `.path` for CLI/API error mapping.
- `WorkspaceProject`, `WorkspaceHypothesis`, `HypothesisObligation`, and
  `WorkspaceSource` expose normalized, typed metadata.

The public names are exported from `symbolic_compactification.__init__`.

## Format

```text
workspace/
├── project.yaml
├── expressions/
│   ├── current.txt
│   └── candidate.txt
├── notes/research_notes.md
├── assumptions/assumptions.yaml
├── references/README.md
├── hypotheses/hypothesis.json
└── runs/
```

`project.yaml` accepts only `project_name`, `objective`,
`expression_entrypoint`, `assumptions_file`, `optional_notes`, and
`optional_references`. Required paths are relative and category-scoped.

`assumptions.yaml` accepts `symbols` plus optional `functions`, and delegates
namespace validation to the existing engine normalizers.

`hypothesis.json` uses schema version 1 and accepts only:

- `hypothesis_type`
- `members`
- `latent_object`
- `operators`
- `instance_maps`
- `reconstruction_rule`
- `assumptions_used`
- `proof_obligations`

The required simple form is `hypothesis_type`, `members`, and
`assumptions_used`. When that form declares `equivalence` with exactly two
members and omits `proof_obligations`, the loader deterministically constructs
one `equivalent(left, right)` obligation and marks
`normalized_simple_form=True`. It does not infer assumptions or repair member
references.

## Safety decisions

- YAML is parsed with `yaml.safe_load`; anchors and aliases are rejected.
- Metadata shapes and keys are strict; JSON duplicate keys are rejected.
- Absolute paths, `..`, non-portable backslashes, category escapes, and
  symlink escapes are rejected.
- Expressions are parsed by the existing strict parser after assumptions are
  normalized.
- `assumptions_used` must name every declared symbol, preventing the verifier
  from silently using an assumption that the hypothesis record omits.
- Every loaded source carries a SHA-256 over its exact bytes.
- Notes and references remain context. They are never translated into
  assumptions.
- Source files are opened read-only. No load path writes or normalizes in
  place. Generated run output remains the responsibility of the run layer.

## Integration notes

- Runtime import requires PyYAML. E1 owns the package dependency change, so
  this commit intentionally does not edit `pyproject.toml`.
- E3 can map `WorkspaceError.code` to concise CLI statuses and reserve
  tracebacks for `--debug`.
- E4 can compile the normalized `HypothesisObligation` records. Unknown
  relation names are syntactically retained so the compiler can return
  `COMPILE_FAILURE` instead of the loader misclassifying them as parse errors.
- E5 can reuse the exact source hashes already present on the workspace
  snapshot.

## Tests

Focused tests cover initialization, no-overwrite behavior, source-file
immutability, simple-form normalization, strict keys, YAML alias rejection,
duplicate JSON keys, expression parse failure, traversal, symlink escape, and
undeclared assumption references.

Command:

```bash
PYTHONPATH=src python3 -m pytest -q tests/test_workspace.py
```
