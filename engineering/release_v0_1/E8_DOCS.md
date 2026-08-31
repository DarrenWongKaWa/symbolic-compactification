# E8 Documentation Handoff

## Scope

Engineering-only release documentation. No root README, production code,
frozen scientific evidence, experiment artifact, version, or release status
was changed.

## Added documents

- `README.md`: preview positioning, canonical workflow, scope, and navigation.
- `QUICKSTART.md`: one Mode A CLI workflow, one Python API workflow, legacy
  CLI compatibility, and experimental-proposer boundary.
- `WORKSPACE_FORMAT.md`: strict minimal workspace, schemas, path safety,
  assumptions, lightweight references, run layout, and immutability.
- `SEMANTICS.md`: `ZERO`/`NONZERO`/`UNKNOWN`, parse/compile/assumption
  statuses, composite obligations, provenance, and exit-code boundary.
- `LIMITATIONS.md`: incomplete coverage, assumptions, finite-Laurent remainder
  lesson, experimental proposer, claim boundary, source and security limits.

## Current-code checks

The documentation was cross-checked against the merged workspace, packaging,
and provenance foundations:

- `initialize_workspace()` refuses existing targets and creates the documented
  minimal layout.
- `load_workspace()` is read-only, validates strict YAML/JSON schemas and
  category-scoped paths, parses expressions through the existing strict
  parser, and exposes exact source hashes.
- simple two-member `equivalence` hypotheses normalize deterministically to
  one obligation when obligations are omitted.
- the provenance schema records the documented versions, hashes, route,
  result, runtime, and warnings; it accepts all six non-success/success
  statuses and does not inventory the environment.
- Python 3.12 packaging and both console entry points are documented by E1.

## Coordinator verification required

These statements depend on E3/E4/integration work that was not present on the
documentation baseline and must be checked or adjusted before release:

1. `symbolic-compactification init <workspace>` dispatches to
   `initialize_workspace()` without breaking `init-session`.
2. `inspect <workspace>` coexists with legacy `inspect <expression.txt>` and
   emits the documented workspace inventory/structural summary.
3. `verify <workspace>` coexists with legacy flag-based `verify`, compiles only
   supported relations, emits precise statuses, and writes every attempt under
   `runs/<run_id>/` without source mutation.
4. `report <workspace>` renders the intended run report and chooses a run
   deterministically; documentation currently follows the prompt's no-option
   canonical command.
5. Public `load_workspace`, `verify_hypothesis`, and `generate_report` imports
   accept the call sequence shown in `QUICKSTART.md`. The return example uses
   `run.result` and `report.path`; update these two field names if E4 selects a
   different typed API.
6. Workspace CLI exit-code details and `--debug` behavior match integrated
   help. `SEMANTICS.md` intentionally does not invent numeric workspace exit
   codes.
7. Each parse/compile/assumption failure attempt receives a safe provenance
   record, even if failure occurs before expression adjudication.
8. Report generation itself does not mutate researcher-owned source files.
9. Security/release agents confirm the warning-redaction and no-secret claims
   against the integrated output paths.
10. Final release status text is updated only after the readiness decision;
    no document currently claims the alpha gate passed.

## Documentation validation

Run:

```bash
git diff --check
rg -n "AI discovers physics|Autonomous theoretical physicist|Guaranteed scientific simplification|Always finds hidden structure" \
  engineering/release_v0_1/{README,QUICKSTART,WORKSPACE_FORMAT,SEMANTICS,LIMITATIONS}.md
```

The forbidden phrases appear only in explicitly negated claim-boundary text.
No URL, secret, or user file was added.

Focused implementation checks on the documentation baseline:

```text
workspace/provenance tests: 38 passed
packaging contract tests: 3 not runnable in the system Python 3.9 environment
```

The three packaging-test failures were environment/setup failures: the
distribution was not installed and the system Python's `importlib.metadata`
API is too old for the Python 3.12 packaging contract. E1 separately recorded
the clean Python 3.12 packaging pass; the coordinator-owned replay remains the
release authority.

## Blockers

No documentation-only blocker. Release use is blocked on the ten integration
checks above, especially exact CLI/API signatures and report selection.
