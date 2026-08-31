# Derivation-audit v0.2 — R1 Theoretical Physicist UX

## Verdict

`BLOCKED`

A theorist who copies the public demos and runs `audit table` / `audit report`
**can** read an honest reviewer table: `ZERO` is not `DEFINITION`, is not
`SPLIT`, and is not an uncertified remainder. The generated artifacts do not
claim that AI proved a paper.

The first-run CLI does not preserve that honesty. `audit verify` reports
`AUDIT_VERIFIED` with exit 0 for an empty graph, a `NONZERO` residual, and
Demo C's `ASYMPTOTIC_CLAIM` `UNKNOWN`. `audit inventory` rewrites the
researcher-owned equation registry the docs promise is immutable. Inventory
labels cannot be used as `edge_id`. Bare `ssc verify` is Mode A and pollutes
the audit `runs/` tree.

Until those four engineering defects are fixed, a working physicist can
reasonably believe the tool just verified the derivation when it did not.

Reviewed: public code/docs/demos only, commit `ff40d0e` on
`engineering/derivation-audit-v0.2` (at/after `c85a703`). No unpublished
sources. Fresh CPython 3.12 install of this worktree; commands run in
`/tmp/ssc-da-r1-ux` copies.

## Question

Can a theorist create an audit, register equations, declare typed edges, run
verify, and read a reviewer table that distinguishes `ZERO` from
`DEFINITION` / `SPLIT` / `UNKNOWN` / asymptotic remainder without thinking
AI proved the paper?

**Tables/docs: yes. End-to-end CLI as shipped: not yet.**

## Scope and evidence

Read, then executed:

- First-screen `README.md`; `docs/DERIVATION_AUDIT.md`,
  `docs/AUDIT_QUICKSTART.md`, `docs/STATUS_SEMANTICS.md`,
  `docs/EDGE_TYPES.md`, `docs/REVIEWER_PACKAGE.md`,
  `docs/DERIVATION_AUDIT_LIMITATIONS.md`
- `engineering/derivation_audit_v0_2/PUBLIC_DEMOS.md` and demos A/B/C
- `src/symbolic_compactification/audit/schema.py` (status + table rules)
- CLI: `ssc audit init|inventory|inspect|verify|table|report|package`
- Fresh venv: `python3.12 -m pip install /private/tmp/ssc-da-v02`

Walked:

1. `audit init` skeleton → inventory → inspect → verify empty edges
2. Copied demos A/B/C (no committed `runs/`) through verify/table/report/package
3. Inventory on curated Demo A
4. Theorist-authored `lhs`/`rhs` without a residual file
5. `SPLIT_PARENT` + child; `NONZERO` residual; illegal `eq:` `edge_id`
6. Bare `ssc verify` on an audit workspace

## Engineering blockers

### 1. `audit verify` reports `AUDIT_VERIFIED` / exit 0 with no per-edge statuses

`cmd_audit_verify` always prints `status: AUDIT_VERIFIED` and returns 0.
JSON is `{status, run_id, records, workspace, run_directory}` only.

Observed on the installed CLI:

| Workspace | Scientific content | CLI |
|---|---|---|
| empty `edges: []` | 0 records | `AUDIT_VERIFIED`, `records: 0`, exit 0 |
| Demo C | 2 coefficient `ZERO` + remainder `UNKNOWN` | `AUDIT_VERIFIED`, `records: 3`, exit 0 |
| residual `(x+1)**2 - (x**2 + 1)` | `NONZERO` | `AUDIT_VERIFIED`, `records: 1`, exit 0 |

Mode A `ssc verify` prints `result: ZERO|NONZERO|UNKNOWN|…` and uses the
documented exit codes (0/2/3/4). The module docstring still says
`Exit codes: 0 = ZERO, 2 = NONZERO, 3 = UNKNOWN`. Audit verify violates
that contract.

A physicist who runs the command named `verify` and stops — or who never
opens `TABLE_*.md` — will read “verified”. That is the “tool proved the
paper” failure mode, even though the tables themselves are careful.

Required engineering (no new science):

- Pipeline token ≠ scientific verdict (e.g. `AUDIT_RUN_RECORDED`).
- Stdout and `--json` must include per-edge `status`/`result`/`edge_type`
  and table-bucket counts (`ZERO`, `NONZERO`, `UNKNOWN`, `DEFINITION`,
  `SPLIT` / `CERTIFIED_BY_CHILDREN`, `NOT_LOWERED`, …).
- Print `next: symbolic-compactification audit table <dir>`.
- Honor the existing exit-code contract, or document a distinct audit
  convention and stop claiming 0 means `ZERO`.

### 2. `audit inventory` rewrites researcher-owned `equations/equations.yaml`

Docs:

- `docs/AUDIT_QUICKSTART.md`: inventory writes sidecars under `reports/`
  only.
- `docs/DERIVATION_AUDIT.md`: researcher-owned sources are never rewritten.
- `docs/THREAT_MODEL.md`: commands write only `runs/` and `reports/`.

Code (`inventory_equations(..., write=True)` from `audit inventory`)
merges into `equations/equations.yaml`.

Quickstart order is: curate `equations.yaml`, then inventory. Running
inventory on public Demo A (curated `equation_id` + `native_expression` +
`body`) overwrote bodies with LaTeX including `\label{…}` and trailing
periods, and injected a second identifier:

```text
- id: eq:binomial-left          # inventory
  equation_id: eq.binomial-left # curated demo / edges source_from
  curated: true
  native_expression: expressions/binomial_lhs.txt
  body: '\label{eq:binomial-left}\n\n    (x+1)^{2}'
```

Edges still verified because they bind residual files, not equation
bodies. The registered catalog the theorist just curated is no longer
stable, and the documented immutability contract is false.

Required engineering: write `reports/inventory.json` only by default.
If a manifest merge remains, it must be opt-in, must not clobber
`curated: true` bodies/`native_expression`, and docs/threat model must
match the code.

### 3. Inventory labels cannot be declared as `edge_id`; init has no legal example

Init's only `next` line is `audit inventory`. Inventory ids are LaTeX
labels such as `eq:placeholder`. Edge ids must match
`[A-Za-z0-9][A-Za-z0-9._-]{0,127}` (`schema._ID_RE`). Colon is illegal.

```text
error: EDGE_ID_INVALID
source: …/edges/edges.yaml
```

No charset hint, no mapping from inventory `id`/`label` to `edge_id`.
Init `edges/edges.yaml` is `edges: []` with no commented legal edge.
Demos already work around this (`edge_id: A.binomial-expand`,
`source_from: eq.binomial-left` vs label `eq:binomial-left`).

The naive path “inventory registered `eq:foo`; declare that edge” dies
before verify. Grounding also does not check `source_from`/`source_to`
against the equation manifest unless the string looks like a file path,
so equation registration is not what the verifier binds — that is fine
if documented, but the id split is not.

Required engineering: one id alphabet; or accept `eq:` labels as edge
ids; fail with the allowed pattern; drop a commented legal edge +
residual into the init skeleton; after inventory, print that edges and
native-text `expressions/*.txt` are still required.

### 4. Bare `ssc verify` / `ssc inspect` are Mode A and write into the audit `runs/` tree

`ssc --help` lists Mode A `verify` first (“verify a workspace hypothesis”)
and `audit` last. README's first screen correctly leads with
`ssc audit …`.

On Demo C, `ssc verify <audit-dir>` (no `audit` subcommand):

- `result: PARSE_FAILURE`, `error_code: SOURCE_FILE_MISSING`,
  `source: project.yaml`
- Wrote `runs/<id>/{REPORT.md,provenance.json,result.json}` into the
  **audit** workspace

`latest_audit_run_id` skips directories without `machine_records.json`,
so `audit table` still picked a real audit run. The physicist still sees
a failed “verify” and a junk run next to real evidence.

Required engineering: if `audit.yaml` is present, Mode A `init` /
`inspect` / `verify` / `report` must refuse with
`use: symbolic-compactification audit verify <dir>` and must not write
`runs/`.

## Checks that passed

| Area | Assessment | Evidence |
|---|---|---|
| Create audit | PASS | `audit init` creates the advertised tree and refuses to overwrite. |
| Typed edges | PASS once authored | Frozen catalogue; unknown type `INTEGRATION_BY_PARTS` fail-closes `UNKNOWN_EDGE_TYPE`. `lhs`/`rhs` without a residual file lowered to `ZERO` for `ALGEBRAIC_EQUIVALENCE`. |
| Reviewer tables | PASS | Inclusion is `schema.may_appear_in_verified_table` / `table_bucket` only. Preambles state Markdown cannot create `ZERO`. |
| `ZERO` vs `DEFINITION` | PASS | Demo B: three local identities in `TABLE_VERIFIED`; `B.define-K` is `DEFINITION` in `TABLE_STRUCTURAL`; `B.worksheet` is `RECORDED`. |
| `ZERO` vs remainder | PASS | Demo C: two `LAURENT_COEFFICIENT` `ZERO` rows; `C.asymptotic-O` is `ASYMPTOTIC_CLAIM` / `UNKNOWN` in `TABLE_UNCERTIFIED`, not rewritten as `F-a/g=0`. |
| `SPLIT` display | PASS (not in demos) | Hand-authored `SPLIT_PARENT` with a `ZERO` child rendered `SPLIT — all children certified` in `TABLE_STRUCTURAL`, never as `ZERO`. |
| `NONZERO` wording | PASS | Table title `POTENTIAL DERIVATION MISMATCHES`; “check transcription, assumptions, conventions, and the derivation step.” Not “the paper is wrong.” |
| Claim boundary | PASS in docs/artifacts | README, limitations, reports, and package README use the approved machine claim + caveat. Forbidden phrases (`AI proves your paper`, …) are absent from generated tables/reports/packages. |
| Package | PASS | `audit package` exports four tables, residuals, `reproduce.sh`, replay sources. Demo C package still shows remainder `UNKNOWN`. |
| Inspect honesty | PASS | `counts are not scientific evidence`. |
| Assumptions surface | PASS as disclosure | Quickstart and limitations state only `real: true`, optional `nonzero`, named functions. Alpha does not pretend to encode positivity, poles, or limit order. |

Public demos A/B/C match `PUBLIC_DEMOS.md` once `audit table` is run.

## Non-blocking observations

- Public demos never exercise `SPLIT_PARENT`. Tables and docs do; add a
  tiny split to Demo B if you want the public path to show that row.
- Demo B `DEFINITION` still fills the column **Executable residual** with
  `(K(m, n) ) - (m + n )` even though the edge is not executable. Rename
  the column or leave it blank for non-executable rows.
- `docs/PUBLIC_DEMOS.md` says Demo A has “several” algebraic edges;
  the committed demo has two.
- `audit package --dest` overwrites an existing directory (`exist_ok=True`)
  despite `REVIEWER_PACKAGE.md` (“do not overwrite”).
- Init placeholder `1 = 1` plus empty edges makes `init → inventory →
  verify` look successful (blocker 1) without any scientific graph.

## Conclusion

The reviewer-table contract is the right product: generated, typed, and
fail-closed. Demo C in particular teaches the remainder lesson a theorist
needs.

The CLI still sells a single `AUDIT_VERIFIED` bit, inventory mutates the
equation registry, and the first-run id/command split fights the documented
workflow. Those are engineering fixes. They are release-critical for a
tool whose defining promise is that it will not let anyone think the
paper was proved.

`BLOCKED`
