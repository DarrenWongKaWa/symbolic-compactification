# Final Reviewer B — Software and Reproducibility

## Verdict

`ALPHA_READY`

No software/reproducibility blocker was found for the bounded Research Preview
v0.1 workflow. This verdict applies to Mode A (researcher-supplied hypothesis),
the documented Python 3.12 environment, and the exact fail-closed workspace
surface. It does not endorse the closed scientific research paths or optional
LLM transport.

## Independent review posture

- Review branch: `work/eng-review-repro`
- Reviewed head: `aca18646617c151d0914e739105ee1acf46d8d78`
- Independent clean root: `/private/tmp/ssc-review-b.4PjhXi`
- Checkout: detached, `git clone --no-local --no-checkout`
- Runtime: CPython 3.12
- Production and frozen research files: read-only
- Review output: this report only

The recorded clean-room replay targeted
`eb02da4ee06f9d8d523b82a526dbdb317050588c`. The only subsequent changes
through the reviewed head are four evidence documents: the clean-room report,
its handoff, the final external-user retest, and its handoff. No package,
workspace, test, dependency, demo, or scientific file changed after the
recorded replay. I nevertheless rebuilt and exercised the current head
independently.

## Installation and package identity

A fresh ordinary, non-editable installation from the detached current-head
checkout passed:

- installed distribution: `symbolic-compactification 0.1.0a0`;
- user-facing identity: `0.1.0-alpha`;
- engine/protocol identities: `0.3.0` / `0.3.0`;
- import origin: the fresh environment's `site-packages`, not the checkout;
- dependencies: PyYAML 6.0.3 and SymPy 1.14.0;
- `pip check`: PASS;
- `symbolic-compactification` and `ssc` entry points: PASS.

I then built a wheel from the still-clean checkout, installed it in a second
new Python 3.12 environment, and ran it outside the checkout. The artifact was
`symbolic_compactification-0.1.0a0-py3-none-any.whl`, 127,769 bytes, with this
build-instance SHA-256:

`be60540324666a8528fee7d98932536269bc27b6e6e0b645cd6f813eb739b2e6`

The wheel-installed CLI created and verified a fresh workspace as `ZERO`. Its
provenance recorded the exact reviewed commit
`aca18646617c151d0914e739105ee1acf46d8d78`, package/engine/protocol versions,
the two direct dependency versions, verifier route, and all required source
hashes. The wheel hash is correctly documented as build-instance evidence,
not as a byte-reproducible published artifact.

## Release and focused tests

Independent current-head results:

```text
python -m pytest -q -m release_critical
12 passed in 8.08s

python -m pytest -q \
  tests/test_packaging_contract.py tests/test_workspace.py \
  tests/test_research_api.py tests/test_run_provenance.py \
  tests/test_release_security.py tests/test_release_demos.py
66 passed in 27.73s
```

The explicit release group covers clean parse, workspace initialization, CLI
smoke behavior, `ZERO`, `NONZERO`, `UNKNOWN`, parse/compile/assumption gates,
provenance, deterministic hashes, source immutability, secret redaction,
report generation, and the retracted finite-Laurent/remainder regression.

## CLI, Python API, and demos

All three committed demo workspaces were copied outside the checkout and run
through the non-editable installed CLI using `inspect`, `verify`, and `report`:

| demo | result | verify exit | source bytes after run |
|---|---|---:|---|
| A — exact factorization | `ZERO` | 0 | identical |
| B — grounded Newton divided differences | `ZERO` (4/4 obligations) | 0 | identical |
| C — intentional polygamma proof gap | `UNKNOWN` | 3 | identical |

Generated files appeared only under each copied workspace's `runs/` tree.
Demo C stated that `UNKNOWN` is not success and cannot promote scientific
state. Demo B's compact CLI prints an unsimplified residual even beside a
`ZERO` verdict; the persisted evidence retains the exact simplified-zero
result. This is potentially verbose but not a correctness or reproducibility
blocker.

The installed wheel's public Python workflow also passed outside the checkout:

```python
workspace = load_workspace("wheel-workspace")
run = verify_hypothesis(workspace)
report = generate_report(workspace, run)
```

It returned `ZERO` and produced a provenance-rich `REPORT.md`.

## Provenance, hashes, and immutability

For two independent runs over the same initialized workspace, these stable
fields compared byte-for-byte equal after canonical JSON sorting:

- input hashes;
- expression hashes;
- hypothesis hash;
- assumptions hash;
- source commit;
- package version;
- dependency versions;
- result.

Run identifiers, timestamps, runtimes, and resulting whole-artifact hashes are
intentionally instance-specific. This distinction is documented and avoids a
false deterministic-artifact claim.

The detached source checkout remained clean after installation, testing,
wheel construction, and external execution. The three copied demos retained
identical composite SHA-256 manifests for every non-`runs/` file before and
after `inspect`, `verify`, and `report`.

## Independent triage of the 24 full-suite failures

I reran the five implicated historical groups and reproduced the recorded
result exactly:

```text
24 failed, 35 passed in 2.41s
```

The failures decompose exactly as recorded:

1. One RPS closure-manifest assertion detects later root-registry hash drift.
   It predates this engineering branch and concerns frozen closure evidence.
2. Nineteen RPS SOL replay/search assertions fail closed because the frozen
   SOL authority pins the pre-alpha SHA-256 of
   `src/symbolic_compactification/models.py`; the release-only version change
   correctly yields `SOL_AUTHORITY_SOURCE_DRIFT` before SOL execution.
3. One research-only LLM transport test imports the optional `openai` client,
   which is not an alpha runtime dependency.
4. Three frozen matrix-package tests enumerate a generated `__pycache__/`
   directory as if it were a case package.

These failures are real and must continue to be disclosed; the repository's
historical full suite is not green. They do not import or exercise the
researcher workspace release path, and none contradicts the 12-test release
gate or the 66 focused package/workspace/API/security/demo tests. Updating the
frozen SOL authority or closure hashes merely to turn the suite green would
violate the engineering-only research lock. Treating the missing optional LLM
client as a core dependency would also enlarge the alpha attack and install
surface without supporting Mode A.

## Version and tag posture

The source, metadata, runtime, and CLI identities agree on `0.1.0-alpha`
(PEP 440 `0.1.0a0`). No `research-preview-v0.1.0-alpha` tag exists yet. That is
the correct pre-decision posture: the program forbids tagging before the
clean-room and three-reviewer gates. If the coordinator's final gate also
passes, the release package, final engineering report, status ledger, exact
release commit, and tag should be created together and checked for internal
identity consistency.

## Non-blocking boundaries

- The alpha support contract is Python 3.12 on the tested macOS arm64 host;
  the broader `requires-python >=3.10` metadata is not independently validated
  here and must not be described as a tested platform matrix.
- Wheels built at different times are not asserted to be byte-identical.
- The historical full suite remains red and must be reported as such.
- Cross-platform installation, optional observation extras, experimental LLM
  proposal, and scientific representation discovery are outside this verdict.
- `engineering/release_v0_1/STATUS.md` still describes clean-room replay as
  pending. The coordinator must update that ledger when recording the final
  decision; it is not evidence against the completed replay itself.

## Blockers

None for the bounded Research Preview Alpha release gate.

## Recommendation

`ALPHA_READY`

Proceed only if the other two independent reviewers concur and the
coordinator's final requirement-by-requirement gate preserves the disclosed
full-suite failures, tested-platform boundary, exact release commit, and
fail-closed claim language.
