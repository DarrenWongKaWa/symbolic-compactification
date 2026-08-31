# R4 Privacy / Security Review — derivation-audit v0.2

## Verdict

**ALPHA_READY**

Privacy gate: **PASS**. Security (privacy slice): **PASS**.

This is an engineering privacy/export decision for the public v0.2 branch. It
is not a scientific verdict. Unpublished local sources were not opened and
are not release evidence.

## Reviewed revision

| Item | Value |
|---|---|
| Branch | `engineering/derivation-audit-v0.2` |
| HEAD | `ff40d0ec6a8655c32d84ae7b3d901fe76e1c9935` |
| v0.1 tag | `research-preview-v0.1.0-alpha` (`c27378fe154e133cde1f913d0b9200a44353aec5`) |
| Clean-room record | `engineering/derivation_audit_v0_2/CLEAN_ROOM_REPLAY.md` (`CLEAN_ROOM_PASS`) |
| Review worktree | clean at review time; this file is the only intended commit on `work/da-r4-review` |

Scope: public checkout vs the v0.1 tag, plus the derivation-audit privacy
firewall, packaging, public demos, private-offline helpers, and free-form
redaction. Unpublished papers, host-absolute personal paths, and denylist
payloads are out of scope and must not appear in this report.

## Blocking findings

None.

## Checklist

| Check | Result |
|---|---|
| No repository-root `manuscripts/` directory | **PASS** |
| `.gitignore` contains `.private_validation/` | **PASS** (added on this branch) |
| `tests/test_audit_privacy.py` uses synthetic tokens only | **PASS** |
| Public demos A/B/C are textbook algebra, not near-clones | **PASS** |
| `SSC_PRIVATE_OFFLINE` refuses network/proposer | **PASS** (library + tests; audit CLI is unconditionally local) |
| Wheel / sdist exclude `.private_validation` and `manuscripts/` | **PASS** (`private_hits []`) |
| Secret redaction still used on free-form strings | **PASS** |
| `git diff c27378f...HEAD` adds no unpublished manuscript paths | **PASS** |

## Evidence

### 1. No `manuscripts/` tree; private validation is gitignored

- `manuscripts/` does not exist in the worktree and is not in `git ls-files`.
- `.private_validation/` does not exist in this checkout and is not tracked.
- `.gitignore` gained an explicit rule:

  ```
  # Local unpublished validation (never commit; never package)
  .private_validation/
  ```

- The denylist path `.private_validation/private_denylist.txt` is the same
  gitignored tree. Public CI with a missing file loads an empty denylist.

### 2. v0.2 delta vs `c27378f` does not add unpublished manuscript paths

`git diff --name-status c27378f...HEAD` adds 89 paths, all under `docs/`,
`engineering/`, `src/`, `tests/`, plus `.gitignore`, `README.md`, and
`pyproject.toml`. No path named `manuscripts/` or `.private_validation/` is
added, modified, or deleted.

The only new TeX files are the three synthetic demo workspace sources:

- `engineering/derivation_audit_v0_2/demos/A/manuscript/source.tex`
- `engineering/derivation_audit_v0_2/demos/B/manuscript/source.tex`
- `engineering/derivation_audit_v0_2/demos/C/manuscript/source.tex`

`manuscript/source.tex` is the frozen audit-workspace layout (`audit.yaml`
`manuscript_source`), not a repository papers directory. Commit history
between the tag and HEAD has no deleted unpublished-paper paths.

### 3. Privacy tests are synthetic-only

`tests/test_audit_privacy.py` documents the contract in its module docstring:
synthetic denylist tokens only; no manuscript text. Observed tokens:

- `SYNTHETIC_DENYLIST_TOKEN_ALPHA`
- `SYNTHETIC_DENYLIST_TOKEN_BETA`

`tests/test_audit_package.py` redaction fixture uses
`sk-proj-synthetic0123456789`, labelled synthetic. No live credential
literals were found in the v0.2 audit sources.

Release-critical privacy assertions in
`tests/test_derivation_audit_release_critical.py` check gitignore, private
relpaths, empty public denylist, and the private-offline error codes.

Targeted run (39 passed): privacy, public-demo static inventory, package
private-copy firewall, reproduce-script offline constraints, v0.1 secret
redaction, and the release-critical private-offline/gitignore test.

### 4. Public demos are independent textbook constructions

Demos A/B/C declare `synthetic: true` and state they are not derived from
unpublished sources. Mathematics:

| Demo | Content | Expected machine statuses |
|---|---|---|
| A | Freshman identities `(x+1)**2` vs `x**2+2*x+1`, and `2*(x+1)` vs `2*x+2` | two `ALGEBRAIC_EQUIVALENCE` → `ZERO` |
| B | `K(m,n)=m+n`, the `2x2` projector `[[0,0],[0,1]]`, local pair `A(m,n)+A(n,m)=2S` | typed `ZERO` plus `DEFINITION` / `RECORDED` |
| C | Toy Laurent `F(g)=a/g+b*g` | two coefficient `ZERO`; parent `ASYMPTOTIC_CLAIM` `UNKNOWN` |

Static tests refuse `.private_validation/` and `private_denylist.txt` inside
demo trees. Unpublished sources were not opened for comparison; the public
objects are elementary identities with generic labels (`eq:binomial-left`,
`eq:projector`, `eq:F`, …) and no specialized research kernels, private
equation numbers, or nicknames.

### 5. Private-offline and always-on local-only verification

`src/symbolic_compactification/audit/privacy.py` freeze constants:

- `SSC_PRIVATE_OFFLINE`
- `.private_validation/`
- refused prefixes `http://`, `https://`, `ftp://`

With the env var set to `1`, `refuse_network_if_private_offline` raises
`PRIVATE_OFFLINE_NETWORK_REFUSED` and `refuse_proposer_if_private_offline`
raises `PRIVATE_OFFLINE_PROPOSER_DISABLED`. Tests lock that behavior.

The audit command surface (`audit init|inventory|inspect|verify|table|report|package`)
has no proposer and no HTTP client. Stronger always-on controls apply even
when the env var is unset:

- `contained_relpath` requires workspace-relative `/` paths; rejects `..`,
  absolute paths, backslashes, and symlinks.
- Reviewer-package export always drops network-shaped prefixes and
  `.private_validation/` (including when that tree is planted in a workspace).
- Optional HTML report is self-contained: CSP `connect-src 'none'`,
  `img-src 'none'`, no beacons.
- `reproduce.sh` contains no `http://`, `https://`, `curl`, or `pip install`.

### 6. Wheel / sdist: `private_hits []`

Independent Python 3.12 rebuild of HEAD (artifacts under a throwaway temp
directory, not committed):

| Artifact | Members | `private_hits` |
|---|---|---|
| `symbolic_compactification-0.1.0a0-py3-none-any.whl` | 56 | `[]` |
| `symbolic_compactification-0.1.0a0.tar.gz` | 251 | `[]` |

The wheel contains only `symbolic_compactification/` and dist-info. The sdist
contains package sources, `setup.py` / `pyproject.toml` / `README.md`, and
`tests/*.py`. Neither distribution contains `.private_validation/`,
`manuscripts/`, demo workspace trees, or `engineering/`. This matches the
clean-room packaging note.

`build_reviewer_package` skips `.private_validation` even if present, and
does not follow symlinks out of the workspace.

### 7. Secret redaction on free-form public strings

v0.1 `security.redact_text` / `redact_public_data` remain the public-output
boundary. Derivation-audit uses them on:

- CLI JSON (`redact_public_data`) and human path/name fields (`redact_text`)
- evidence warnings and provenance warning lists (redact, then bound to 2048)
- run-id credential-shape rejection
- reviewer-package JSON (`redact_public_data`) and copied text
  (`redact_text`), including obligation residuals when they are free-form
  strings

`test_free_form_strings_are_redacted` plants a synthetic token-shaped value
in a claim/residual and asserts the packaged copies contain `[REDACTED]`
and not the secret. Certified algebraic residuals are still exact inside the
verifier; redaction is a public-export filter, not DLP of researcher sources.

## Residual risks (non-blocking)

These do not fail the privacy gate for this alpha. They must not be “closed”
by shipping unpublished material or by treating denylist absence as a skip
of researcher obligations.

1. **Env-gated helpers are not called from audit CLI.** Production
   verification is already local-only (no network client, no audit proposer).
   A future experimental proposer **must** call
   `refuse_proposer_if_private_offline` before any external prompt. Until
   then, `SSC_PRIVATE_OFFLINE=1` is a freeze API plus tests, not a CLI no-op
   that re-enables network.

2. **Denylist scan is a release process, not an `audit package` side effect.**
   `scan_paths` is tested and skips the private-validation tree so the
   denylist cannot self-match. Public CI has no denylist file (empty ⇒ no
   hits). Humans remain responsible for not committing private sources.

3. **Local `reports/TABLE_*.md` and `REPORT.md` do not re-redact scientific
   cells.** Exact residuals must stay exact. Public export (CLI JSON and
   reviewer package) re-applies redaction. Do not put credentials in
   expressions, claims, or notes.

4. **HTML is a local convenience view** (escaped, CSP-locked, not part of
   the reviewer-package file list). Treat it as workspace-local, not a
   distribution artifact.

5. **Redaction is defence in depth**, not a general DLP system. The primary
   control remains: private sources stay off this branch, off git history,
   and out of reviewer packages.

## Gate mapping

| Release gate | This review |
|---|---|
| PRIVACY | PASS |
| SECURITY (secret/export slice) | PASS |
| PUBLIC_DEMOS (privacy of fixtures) | PASS |
| REVIEWER_PACKAGE (no private tree, no network replay) | PASS |

Allowed non-blocking limitations in `RELEASE_GATE.md` (manual PDF inventory,
`NOT_LOWERED`, remainder certification, complex assumptions, experimental
proposer, manual transcription) are unchanged and were not expanded.

## Conclusion

The public derivation-audit v0.2 branch does not contain a `manuscripts/`
directory, does not track `.private_validation/`, packages no private members
(`private_hits []`), uses synthetic privacy-test tokens, ships only textbook
public demos, keeps verification local, and still redacts credential-shaped
free-form strings on public CLI/package output. **ALPHA_READY.**
