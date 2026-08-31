# symbolic-compactification Research Preview v0.1

Status: engineering release candidate. `RESEARCH_PREVIEW_ALPHA` is granted
only after the integrated release gates pass.

symbolic-compactification is a research harness for proposing, grounding, and
checking symbolic scientific structures. Its reliable core is
context-grounded symbolic hypothesis generation with fail-closed verification:
a researcher supplies expressions, assumptions, context, and a hypothesis;
the verifier returns `ZERO`, `NONZERO`, or `UNKNOWN` and records provenance.

The tool is designed to remain useful when no AI proposer is present. The
release-critical workflow is **Mode A: verify my hypothesis**. **Mode B:
propose then verify** is experimental and never bypasses the same verifier.

## Start here

- [QUICKSTART.md](QUICKSTART.md) gives one CLI workflow and one Python API
  workflow.
- [WORKSPACE_FORMAT.md](WORKSPACE_FORMAT.md) defines the researcher-owned
  workspace.
- [SEMANTICS.md](SEMANTICS.md) defines every user-visible result.
- [LIMITATIONS.md](LIMITATIONS.md) states the capability and claim boundary.
- [INSTALLATION.md](INSTALLATION.md) gives Python 3.12 installation and wheel
  checks.
- `EXAMPLE_WORKSPACE/` is the minimal workspace produced by `init`.

## Canonical workflow

```text
researcher workspace
    -> inspect expressions, assumptions, notes, and references
    -> register a symbolic hypothesis
    -> compile its explicit proof obligations
    -> adjudicate each obligation: ZERO / NONZERO / UNKNOWN
    -> write a provenance-rich report under workspace/runs/<run_id>/
```

`ZERO` is the only result that certifies the submitted equality under the
declared engine semantics and assumptions. `UNKNOWN` is a valid fail-closed
result, not partial approval. User-owned expressions, notes, references,
assumptions, and hypotheses are read-only; generated files belong under
`runs/`.

## Scope

Supported for the preview:

- strict ingestion of a small, human-readable workspace;
- exact equivalence checks in the documented parser/verifier coverage;
- explicit `real: true`/optional-nonzero symbol flags, declared functions, and source-member
  grounding;
- hashes and bounded run provenance;
- reports that distinguish proof, refutation, and proof gaps.

Experimental or outside the preview contract:

- AI-generated hypotheses;
- general mathematical representation invention;
- arbitrary matrix, tensor, limit, and special-function certification;
- automatic extraction of scientific meaning from papers.

The alpha assumptions schema does not represent positivity, general
inequalities, excluded poles, parameter identities, boundary conditions,
symmetries, or limit order. Any claim that depends on one of those predicates
is outside supported alpha certification, even if the predicate appears in a
note or reference.

This is not an autonomous theoretical physicist, a universal simplifier, or a
general formal proof system. See [LIMITATIONS.md](LIMITATIONS.md) before using a
result in scientific work.

## Compatibility

The workspace commands extend the existing CLI. The file-oriented
`inspect`/`verify` forms and the session commands `init-session`, `step`,
`summary`, and `finalize` remain compatibility surfaces. Existing observation
commands remain separate from certification.

## Release-gate note

These documents state the v0.1 external interface. The coordinator must verify
the integrated `init`, workspace-path `inspect`, workspace-path `verify`,
`report`, and Python API examples before declaring the alpha ready. Successful
installation alone is not evidence of scientific readiness.
