# R3 — Software and reproducibility (derivation-audit v0.2)

## Verdict

`ALPHA_READY`

No software/reproducibility blocker was found for the bounded derivation-audit
v0.2 research-preview surface: exclusive `audit init`, source-immutable
`audit verify`, exclusive run directories, offline `reproduce.sh` replay of
the public demos, still-working v0.1 Mode A `init`/`verify`, both advertised
pytest gates, and the generated `reviewer-verification-package/` layout.

This verdict does not relabel the historical full suite as green, does not
claim byte-identical wheels, and does not endorse closed scientific research
paths. Package identity remains `0.1.0-alpha`.

## Independent review posture

- Review lane: R3 (software and reproducibility only)
- Reviewed integration HEAD:
  `ff40d0ec6a8655c32d84ae7b3d901fe76e1c9935`
  (`engineering/derivation-audit-v0.2`)
- Product commit (last packaged-source change):
  `c85a70361b3017fc42fbab6e7876e8578ec2f187`
  (`src/`, `tests/`, `pyproject.toml`, and `setup.py` are identical between
  `c85a703` and this HEAD; the intervening commit is
  `engineering/derivation_audit_v0_2/CLEAN_ROOM_REPLAY.md` only)
- Independent clone: `/private/tmp/ssc-da-r3-repro` and identity clone
  `/private/tmp/ssc-da-r3-id` (detached, `git clone --no-local --no-checkout`
  of `ff40d0e`)
- Runtime: CPython 3.12.13, pip 26.2.1
- Host: macOS 26.4 (Darwin 25.4.0), arm64
- Production, frozen research, and demo sources: not edited
- Review output: this report only
- Unpublished manuscripts: not present, not read

The recorded clean-room replay targeted `c85a703`. It was treated as a claim
to challenge, not as proof. I rebuilt and exercised `ff40d0e` independently.

## Installation and package identity

A fresh ordinary, non-editable installation from a detached `ff40d0e`
checkout, with the venv **outside** the clone so untracked env files cannot
mark the source dirty, passed:

```bash
python3.12 -m venv /private/tmp/ssc-da-r3-env
/private/tmp/ssc-da-r3-env/bin/python -m pip install -U pip
/private/tmp/ssc-da-r3-env/bin/python -m pip install /private/tmp/ssc-da-r3-id
/private/tmp/ssc-da-r3-env/bin/python -m pip check
/private/tmp/ssc-da-r3-env/bin/symbolic-compactification --version
```

Results:

- installed distribution: `symbolic-compactification 0.1.0a0`
- user-facing identity: `0.1.0-alpha`
- engine / protocol: `0.3.0` / `0.3.0`
- derivation-audit protocol: `0.2.0`
- CLI `--version`:
  `symbolic-compactification 0.1.0-alpha (PEP 440 0.1.0a0; engine 0.3.0, protocol 0.3.0)`
- import origin: `/private/tmp/ssc-da-r3-env/lib/python3.12/site-packages/symbolic_compactification/__init__.py`
  (not the checkout)
- embedded source identity: `ff40d0ec6a8655c32d84ae7b3d901fe76e1c9935`
  (`SOURCE_GIT_DIRTY = False`)
- direct runtime dependencies: PyYAML 6.0.3 and SymPy 1.14.0
- `pip check`: `No broken requirements found.`
- console entry points `symbolic-compactification` and `ssc`: PASS

A first install with `env-normal/` *inside* the clone correctly recorded
`SOURCE_GIT_DIRTY = True` / `git_commit …-dirty`. Clean and dirty identities
are therefore distinct. The identity-authoritative install used an external
venv.

A wheel and sdist built from the detached checkout contained no
`.private_validation/` or `manuscripts/` members. Wheel:
`symbolic_compactification-0.1.0a0-py3-none-any.whl` (184,936 bytes). Sdist:
`symbolic_compactification-0.1.0a0.tar.gz` (464,354 bytes, 251 members).
Wheels built at different times are not asserted to be byte-identical.

## Required checks

### 1. `audit init` never overwrites — PASS

`initialize_audit_workspace` refuses any path that exists or is a symlink
(`WORKSPACE_ALREADY_EXISTS`). Scaffold files use `write_new`, which refuses
to replace an existing file.

Independent CLI:

| target | second `audit init` | exit |
|---|---|---:|
| freshly initialized workspace | `WORKSPACE_ALREADY_EXISTS` | 4 |
| existing empty directory | `WORKSPACE_ALREADY_EXISTS` | 4 |

v0.1 `init` on an existing Mode A workspace likewise exits 4 with
`WORKSPACE_ALREADY_EXISTS`.

### 2. `verify` never mutates sources — PASS

`verify_audit` snapshots researcher-owned trees, writes only under
`runs/<run_id>/`, and re-hashes sources before return (`SOURCE_MUTATED` if
bytes change). Public demos A/B/C were copied outside the checkout. SHA-256
manifests of every non-`runs/` / non-`reports/` / non-package file were
identical before and after `audit verify`, `table`, `report`, and `package`.

Generated files appeared only under each copy's `runs/<run_id>/`,
`reports/`, and (on `package`) `reviewer-verification-package/`.

### 3. Runs are exclusive / never overwritten — PASS

`write_exclusive_audit_run` creates `runs/<run_id>/` with `mkdir(exist_ok=False)`
staging and refuses a pre-existing id (`RUN_ALREADY_EXISTS`).

On copied Demo A:

- first verify wrote `20260831T212818Z-0f6c11c1`
- second verify wrote a **new** id `20260831T212827Z-d3091018`
- first `machine_records.json` bytes were unchanged
- `verify_audit(..., run_id=<existing>)` raised `RUN_ALREADY_EXISTS`

### 4. `reproduce.sh` works offline — PASS

Exported packages contain an executable `#!/bin/sh` script with no
`http://`, `https://`, `curl`, or `pip install`. It re-runs
`audit verify` then `audit table` on bundled `replay/` and requires a
**local** install.

Copied packages were replayed with
`PATH=<venv>/bin:$PATH`, `http_proxy`/`https_proxy=http://127.0.0.1:1`,
and `PIP_NO_INDEX=1`:

| package | `reproduce.sh` | statuses | replay sources |
|---|---|---|---|
| Demo A | exit 0 | 2 `ZERO` | unchanged |
| Demo B | exit 0 | 3 `ZERO` + `DEFINITION` + `RECORDED` | unchanged |
| Demo C | exit 0 | 2 coefficient `ZERO`; `ASYMPTOTIC_CLAIM` `UNKNOWN` | unchanged |

Without the venv on `PATH`, the script fails closed on this host
(`python3` is system 3.9.6: `ModuleNotFoundError: No module named
'symbolic_compactification'`). That is the documented local-install
requirement, not a network fetch.

### 5. v0.1 CLI `init` / `verify` still works — PASS

Installed CLI on a fresh Mode A workspace:

```text
symbolic-compactification init <dir> --json  → WORKSPACE_INITIALIZED, exit 0
symbolic-compactification verify <dir> --json → result ZERO, exit 0
```

`pytest -m derivation_audit_release_critical` includes
`test_v0_1_workspace_verify_still_zero`. `pytest -m release_critical`
remains the v0.1 17-test gate and is green at this HEAD.

### 6. Pytest gates — PASS

Independent current-head results from the non-editable environment, run
inside the detached checkout:

```text
python -m pytest -q -m derivation_audit_release_critical
...........                                                              [100%]
11 passed in 12.35s

python -m pytest -q -m release_critical
.................                                                        [100%]
17 passed in 16.53s
```

This matches `CLEAN_ROOM_REPLAY.md` (`11` / `17`). Collection policy in
`tests/conftest.py` owns those exact modules
(`test_derivation_audit_release_critical.py` and
`test_release_critical.py`). Other files that happen to carry the same
marker are not part of the advertised commands.

### 7. Reviewer-verification-package layout — PASS

Default export path is `<workspace>/reviewer-verification-package/`.
Demo A contained:

```text
README.md
TABLE_VERIFIED.md
TABLE_STRUCTURAL.md
TABLE_UNCERTIFIED.md
TABLE_NONZERO.md
assumptions.yaml
MANIFEST.json
reproduce.sh
obligations/<edge_id>.json
obligations/<edge_id>.residual.txt
obligations/<edge_id>.artifact.txt
machine_results/machine_records.json
machine_results/provenance.json
machine_results/verification_table.json
machine_results/verification_table.csv
replay/audit.yaml
replay/assumptions/assumptions.yaml
replay/equations/equations.yaml
replay/edges/edges.yaml
replay/expressions/*.txt
replay/manuscript/source.tex
```

`MANIFEST.json` records `package_schema: DerivationAuditReviewerPackageV1`,
`schema: DerivationAuditV1`, engine `0.3.0`, the run id, and SHA-256 of
every packaged file except itself. `reproduce.sh` is executable.
`.private_validation/` is not copied.

`TABLE_VERIFIED.md` is generated text: “Markdown cannot create ZERO or
VERIFIED status.” Demo A listed exactly the two algebraic `ZERO` rows.

Committed demo trees ship inputs plus empty `runs/` and `reports/`
`.gitkeep` files only. No recorded runs are in git.

## Public demos (independent copies)

| demo | verify | records | tables | source snapshot |
|---|---:|---:|---|---|
| A — freshman algebra | 0 | 2 | 2 `ZERO` | unchanged |
| B — typed structural | 0 | 5 | 3 `ZERO` + `DEFINITION` + `RECORDED` | unchanged |
| C — coefficient vs remainder | 0 | 3 | 2 `ZERO` + `UNKNOWN` remainder | unchanged |

Clean-identity provenance on an empty initialized workspace recorded
`git_commit=ff40d0ec6a8655c32d84ae7b3d901fe76e1c9935` (no `-dirty`),
`package_version=0.1.0a0`, `engine_version=0.3.0`,
`verifier_route=python_sympy_exact_v1`, PyYAML 6.0.3, SymPy 1.14.0.

## Non-blocking documentation / packaging notes

These do **not** withhold `ALPHA_READY`. They are contract-text defects
around generated artifacts, not evidence-overwrite bugs.

1. **`audit inventory` rewrites `equations/equations.yaml`.**
   `docs/AUDIT_QUICKSTART.md` says inventory writes `reports/` only and
   does not rewrite researcher sources. The implementation merges into
   the equation manifest (`write=True` from the CLI) while leaving the
   manuscript bytes unchanged. Curated ids are preserved in tests. This
   is not `audit verify`, and verify's source snapshot was unchanged.

2. **`audit package --dest` overwrites an existing directory.**
   `docs/REVIEWER_PACKAGE.md` says “`--dest` must be a new path; exports
   do not overwrite existing destinations.” `_prepare_dest` uses
   `mkdir(..., exist_ok=True)` and then rewrites package files. Re-export
   to the default `reviewer-verification-package/` also overwrites that
   generated tree. Researcher sources and `runs/<run_id>/` are not the
   destination. Fail-closed exclusive dest would match the docs.

3. **Package does not copy `REPORT.md`; `reproduce.sh` does not run
   `audit report`.** The user doc lists `REPORT.md` among package
   contents and describes replay of “table/report generation from the
   recorded run.” The generated package README and tests require tables
   + `replay/` + `reproduce.sh`, which **re-verifies** then regenerates
   tables. That is a stronger scientific replay than copying a report.
   Align the user doc.

4. **Default package path is not `reports/`.** The same user doc says
   generated files live under `reports/` unless `--dest` is given. The
   default dest is `reviewer-verification-package/` at the workspace
   root.

5. **Stale packaging-contract README phrase.**
   `tests/test_packaging_contract.py::test_packaged_readme_is_the_research_preview_entrypoint`
   still asserts the exact v0.1 sentence “Scientific experimentation is
   closed”. Current README says “Scientific experimentation remains
   closed.” The advertised `pytest -m release_critical` command does
   **not** collect that module (conftest owns `test_release_critical.py`
   only) and is green. I ran the file as extra focused coverage: 1
   failed, 89 passed among the extra audit/workspace files. Not part of
   the v0.2 gate.

6. **No `tests/test_audit_backward_compat.py`.** The interface contract
   named that file for E16. Backward compatibility is covered by
   `test_v0_1_workspace_verify_still_zero` inside the v0.2 release-critical
   module and by the independent Mode A CLI run above.

## Blockers

None for the bounded derivation-audit v0.2 alpha reproducibility gate.

## Recommendation

`ALPHA_READY`

Proceed only if the other independent reviewers concur and the
coordinator's requirement-by-requirement gate preserves: exclusive init,
source-immutable verify, exclusive runs, offline local-install
`reproduce.sh`, v0.1 Mode A `init`/`verify`, the 11+17 pytest gates, and
the fail-closed claim language. The documentation mismatches in
non-blocking notes 1–4 should be fixed as text, not by expanding
scientific scope.
