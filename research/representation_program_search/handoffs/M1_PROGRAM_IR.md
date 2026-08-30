# M1 handoff — typed Program IR / constructor

Implementation commit: `8d481d9f81660e8a2398020472fd2ce6ab010410`

Base observed in the isolated worktree before M1 changes: `0508065`.

## Delivered

- immutable typed records for exact source members, latent objects, first-class
  node multiplicities, operators, outputs/intermediates, member
  reconstructions, assumptions, and proof obligations;
- deterministic compact sorted-key JSON and SHA-256 program identity;
- alpha-normalization of bound latent parameters to `z0`, `z1`, ... in bind
  order while preserving source member ids, paths, hashes, node/value
  expressions, and raw source bytes exactly;
- strict JSON construction with unknown-field and alias rejection;
- exact source path/hash/parser validation with complete assigned/unexplained
  accounting;
- executable constructors for all frozen `RepresentationGrammarV1` operators;
- hard `G_FULL`, `G_NO_HERMITE`, and `G_PRIMITIVE` ablation validation;
- structurally distinct Newton and Hermite node rules, including confluent
  derivative/factorial construction for grouped repeated nodes;
- exact dependency-closure checks for member reconstruction;
- obligation compilation that emits current text/hash and candidate expression
  with status `COMPILED`, never a proof verdict;
- IR-level independent `VALUE`-self tautology detection;
- a read-only `RPSCasePackageV1` loader with whole-manifest validation;
- focused unit tests covering deterministic identity, alpha equivalence,
  source integrity, every operator, repeated-node typing, ablations,
  assumptions, aliases, missing links, tautologies, R2/R3 compilation, and
  legacy package compatibility.

Implementation lives only under:

- `research/representation_program_search/program_ir/`
- `tests/test_rps_program_ir.py`

No parser, verifier, frozen contract, package, or historical artifact was
changed.

## Compiler/verifier boundary

The constructor never calls `simplify()`, `equals()`, numeric comparison, or
the verifier. It performs typed exact expression construction and returns
`COMPILE_FAILURE` on every exceptional path. `COMPILED` is not `ZERO` and is
not PROGRAM_SUCCESS.

The R2 Newton and R3 Hermite unit fixtures submit the emitted obligations to
the repository verifier as an independent test assertion; both receive exact
`ZERO`. That verifier call is in the test, not hidden in compiler execution.

## Thermal package compatibility audit

All six current thermal packages load with their artifact manifests and member
hashes intact. The loader injects only exact facts from package-owned files:
source references from `source_catalog.json`, assumption statuses from
`assumptions.json`, and obligation/member links from
`reference/obligations.json`.

Every thermal reference program currently reports these executable-schema
deltas:

1. source records are outside the legacy `program.json`;
2. assumption statuses are outside the legacy `program.json`;
3. operator outputs are missing;
4. assignment outputs are missing;
5. obligation-to-output links are missing;
6. its pre-M1 program id is not the M1 alpha-normalized hash after exact
   package facts are attached.

M1 does not infer any missing link from list position, “last operator,” or a
reconstruction filename. Consequently each thermal program fails closed at
`OPERATOR_OUTPUT_MISSING:OP0`. This is a precise compatibility result, not a
refutation of its already-recorded scientific obligations.

## Tests

Focused integration:

```text
32 passed in 1.54s
```

Command:

```bash
.venv/bin/python -m pytest -q \
  tests/test_rps_program_ir.py \
  tests/test_rps_contracts.py \
  tests/test_rps_thermal_packages.py
```

Full repository:

```text
1717 passed in 205.71s (0:03:25)
```

`git diff --check` and Python bytecode compilation also passed.

## Deliberate limits

- The compiler stays inside the frozen parser dialect. Native matrix/tensor
  syntax that cannot be represented by an exact scalar/component lowering is
  still a `PACKAGING_GAP`; M1 does not extend the parser.
- Hermite repeated labels must be contiguously grouped. A sequence such as
  `NODES[x,y,x]` fails closed instead of invoking a limit or reordering nodes.
- `RECURRENCE` has two explicit structural forms (`FORWARD_DIFFERENCE` and
  `SHIFTED_VALUE`). Scientific correction terms must be explicit downstream
  `LINEAR_COMBINATION` inputs; they are never guessed.
- Basis operators compile explicit scalar/component-lowered basis terms. They
  do not infer a metric, dual basis, normalization, or symmetry assumption.
- This work implements M1 only. Search, scoring, verifier adjudication, package
  repair, partition choice, and experimental results remain coordinator-owned.
