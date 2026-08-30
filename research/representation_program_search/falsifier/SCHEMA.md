# RPSFalsifierSuiteV1 schema

`suite.json` is the root manifest. It binds every evaluator artifact by
SHA-256 and lists exactly six traps plus one positive control. `suite.json`
does not hash itself.

Each trap contains:

- `trap.json`: expected stage, failure class, source/candidate bindings, and
  retained session paths where verification is allowed;
- `symbols.json` and `assumptions.json`: the exact parser namespace and
  declaration provenance;
- `members/*.txt`: source-member bytes;
- `evaluator/program.json`: an evaluator-only program in
  `RepresentationProgramAdapterV1`;
- `evaluator/actions.json`: legal grammar actions, except the one deliberately
  ill-typed Hermite action;
- `evaluator/candidates/*.txt`: executable reconstructions or exact byte
  witnesses;
- `verification/runs/...`: engine-owned evidence for executable identities.

`RepresentationProgramAdapterV1` uses the frozen V1 latent forms, operators,
and actions. It is intentionally a narrow fixture format, not a competing
Program IR. Required top-level fields are `grammar_version`, `latent_objects`,
`node_structures`, `operators`, `member_assignments`, `reconstruction`, and
`assumptions_used`. `program_id` is the canonical SHA-256 of the remaining
JSON after recursively sorting object keys.

The M1 integration seam is one-way:

```text
fixture JSON -> M1 loader/compiler -> actual failure/result
                                 compare -> frozen expected outcome
```

No trap or evaluator-only dominance witness may be exposed to a search
proposer. The suite is not a source of search actions, target labels, or gold
programs.

Fixture failure classes are versioned independently from M1's detailed error
strings. `adapter.py` freezes the mapping
`HERMITE_NODE_MULTIPLICITY -> HERMITE_REPEATED_NODE_REQUIRED`; M1 may append a
node id after a colon (for example,
`HERMITE_REPEATED_NODE_REQUIRED:nodes_001`). Integration compares the prefix,
not string identity.
