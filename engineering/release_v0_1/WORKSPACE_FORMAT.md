# Researcher Workspace Format v0.1

The workspace is a plain directory of researcher-owned source files plus a
tool-owned `runs/` directory. It has no database and no benchmark schema.

```text
workspace/
├── project.yaml
├── expressions/
│   ├── current.txt
│   └── candidate.txt
├── notes/
│   └── research_notes.md
├── assumptions/
│   └── assumptions.yaml
├── references/
│   └── README.md
├── hypotheses/
│   └── hypothesis.json
└── runs/
```

All declared paths are workspace-relative, use `/`, and remain inside their
named category. Absolute paths, `..`, backslash paths, and symlink escapes are
rejected. Metadata files are UTF-8 and have bounded size.

## `project.yaml`

Only the following fields are accepted:

```yaml
project_name: "thermal-response-check"
objective: "Test whether the proposed response kernel equals the current expression."
expression_entrypoint: expressions/current.txt
assumptions_file: assumptions/assumptions.yaml
optional_notes:
  - notes/research_notes.md
optional_references:
  - references/README.md
```

`project_name`, `objective`, `expression_entrypoint`, and `assumptions_file`
are required. Notes and references may be omitted. Unknown fields, duplicate
paths, YAML anchors, and YAML aliases are rejected rather than guessed.

## Expressions

Each member is a plain-text expression accepted by the strict parser. The
file's exact bytes own its SHA-256 identity. Supported content is limited by
the parser whitelist and resource bounds; arbitrary Python is never accepted.

`project.expression_entrypoint` names the current expression and must also be
a member of the hypothesis. Other member names are declared in
`hypotheses/hypothesis.json`.

The loader reads expression files directly. It does not rewrite whitespace,
replace symbols, expand sums, or overwrite a source with a normalized form.
If a normalized or lowered form is needed, it belongs in the run output as a
separate generated artifact.

## `assumptions/assumptions.yaml`

Declare every symbol used by the expressions and any allowed undefined
functions:

```yaml
symbols:
  - name: x
    real: true
    nonzero: false
  - name: m
    real: true
    nonzero: true
functions:
  - K
```

String symbol shorthand is accepted by the underlying namespace normalizer,
but explicit objects are preferred in external workspaces because they make
domain choices visible. Assumptions are never inferred from notation, notes,
references, or common physical practice.

Do not use `real: false` as an informal synonym for an unconstrained complex
symbol until the documented namespace-contract defect is resolved. Affected
claims fail closed; see [LIMITATIONS.md](LIMITATIONS.md).

## `hypotheses/hypothesis.json`

The stable schema is version 1:

```json
{
  "schema_version": 1,
  "hypothesis_type": "equivalence",
  "members": [
    "expressions/current.txt",
    "expressions/candidate.txt"
  ],
  "latent_object": null,
  "operators": [],
  "instance_maps": {},
  "reconstruction_rule": "current is exactly equivalent to candidate",
  "assumptions_used": ["x", "m"],
  "proof_obligations": [
    {
      "obligation_id": "equivalence-1",
      "relation": "equivalent",
      "left": "expressions/current.txt",
      "right": "expressions/candidate.txt"
    }
  ]
}
```

Fields have these meanings:

- `hypothesis_type`: the claimed structural relation; v0.1 release-critical
  support is exact equivalence.
- `members`: exact workspace-relative expression sources used by the claim.
- `latent_object`: optional human-readable latent object; it is not proof.
- `operators`: optional named structural operations; names do not certify
  their mathematical validity.
- `instance_maps`: explicit mappings from members to parameters/instances.
- `reconstruction_rule`: readable statement of how members are reconstructed.
- `assumptions_used`: every declared symbol name. Omission is rejected rather
  than repaired silently.
- `proof_obligations`: exact member-to-member relations for compilation.

A simple equivalence form may contain only `hypothesis_type`, two `members`,
and `assumptions_used`. When `proof_obligations` is omitted, the loader
deterministically constructs one `equivalent(left, right)` obligation. It does
not invent assumptions, member roles, operators, or reconstruction meaning.

JSON duplicate keys, unknown fields, missing members, undeclared assumptions,
duplicate obligation identifiers, and obligation references outside `members`
are rejected. A syntactically valid but unsupported relation is preserved long
enough to return `COMPILE_FAILURE`; it is not silently reinterpreted.

## Notes and references

Notes are UTF-8 context files. References may be paths, citation lists,
manually curated excerpts, or lightweight metadata stored under
`references/`. The preview does not implement full PDF ingestion or
literature retrieval.

Context files can ground a researcher-visible report. They cannot create
assumptions or serve as verifier proof by themselves.

## `runs/<run_id>/`

This is the only default write area after initialization. Each verification
attempt receives a new, non-overwriting run directory containing generated
results, `provenance.json`, and a human-readable report when requested.

Run provenance records the timestamp, tool and dependency versions, git
commit, exact input/expression/hypothesis/assumption hashes, verifier route,
result, runtime, and warnings. It never records `.env` content, API keys, auth
headers, or an unrelated process-environment inventory.

## Immutability contract

`inspect`, `verify`, and `report` do not modify expressions, assumptions,
notes, references, hypotheses, or `project.yaml`. `init` refuses an existing
target rather than merging into or replacing it. Researchers should still
keep their workspace in ordinary version control or backups; immutability is
a tool behavior, not a backup service.
