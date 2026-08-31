# Research Preview v0.1 Merge Log

Integration base: `284997c5310fe74c228a0485cd0edc4ebdfcd79d`

Frozen scientific evidence is read-only for this engineering program. Each
integration is reviewed for scope, checked for whitespace, and followed by
targeted tests before the next dependent lane starts.

| lane | source commit | integrated commit | scope | verification |
|---|---|---|---|---|
| E1 install/packaging | `8a7c4b1` | `984783b` | Python 3.12 packaging and YAML dependency | E1: 36 passed; coordinator packaging/workspace/provenance set included below |
| E2 workspace UX | `05e1edd` | `9a6975e` | strict read-only workspace loader/initializer | E2: 71 passed; coordinator foundation set: 30 workspace/provenance/packaging passed |
| E5 provenance | `2a2fd7a` | `0e59200` | deterministic secret-safe run records | E5: 59 passed; coordinator adjacent parser/namespace/provenance: 69 passed |

Coordinator integrated foundation result: **99 targeted tests passed**.

No path under the frozen scientific research evidence was modified by these
three integrations.

| lane | source commit | integrated commit | scope | verification |
|---|---|---|---|---|
| E4 Python API | `2d1aff2` | `5fc1909` | fail-closed workspace verification/reporting | 35 focused passed |
| E6 security | `2dd7e87` | `ede6bd9` | production redaction and secret audit | 70 lane tests; 38 coordinator security/API tests passed |
| E8 docs | `09cbb0f` | `1dbd28d` | physicist-oriented user contract | documentation checks and 38 foundation tests passed |
| E3 CLI | `35cc78b` | `bfe0a46` | init/inspect/verify/report with legacy compatibility | 72 affected and 48 compatibility tests passed |
| E9 demos | `8618a42` | `6227c1e` | exactly three immutable workspaces | ZERO/ZERO/UNKNOWN; 25 lane tests passed |
| E7 fail-closed | `04c00d5` | `6c4230a` | public statuses and release-critical marker | 12/12 current release-critical tests pass |
| E11 user simulation | `98f26ae`, `c4c89a0` | `578368c`, `707fc29` | fresh-install external UX rejection/retest | blockers recorded, never hidden |
| alpha blocker fix | `4b25910` | `590bc1c` | version, deps, reports, diagnostics | 62 focused and 12 release-critical passed |
| final blocker fix | `f106469` | `73169db` | wheel source revision and root README | 60 focused; source/wheel installed provenance passed |
| integration evidence | n/a | `eb02da4` | full-suite disclosure and gate evidence | recorded; 24 historical failures triaged as non-release |
| first clean-room | `c7dcbb9` | `21a512f` | ordinary-install replay at `eb02da4` | 12 release-critical; demos ZERO/ZERO/UNKNOWN |
| E11 final user retest | user-final | `aca1864` | first-time researcher Mode A retest | `ALPHA_READY` for UX lane at `eb02da4` |
| reviewer A (first) | `d91accb` | `5742e73` | physicist UX rejection | Demo B domain + assumption-schema blockers |
| reviewer B (first) | `80c7cbd` | `7fc1985` | software/reproducibility | `ALPHA_READY` |
| reviewer C (first) | `18f1072` | `26a6234` | safety/claim rejection | report symlink + double-read hash |
| reviewer-blocker fix | `99f04c7` | `3de1a90` | Demo B specialization, snapshot hashes, report integrity | 16 release-critical; 88 affected |
| final clean-room | `02dd318` | `4956008` | ordinary+wheel replay at `3de1a90` | 16 release-critical; demos ZERO/ZERO/UNKNOWN |
| physicist re-review | `b4c9faf` | `9379453` | UX rejection of `real: false` | documented contract not enforced |
| complex-namespace gate | parse-failure WT | `f9692c1` | reject `real: false` fail-closed | release-critical regression added |
| report contract align | parse-failure WT | `bd6f0a1` | report/docs/test wording for that gate | 17 release-critical; 96 affected at HEAD |

Frozen scientific evidence changed by integrations: **none**.

Coordinator note (takeover after prior-session crash): product HEAD `bd6f0a1`
was verified locally before the current clean-room replay. Targeted result:
`17 passed` (`pytest -q -m release_critical tests`) and `96 passed` on the
workspace/API/provenance/security/demo/packaging set. `git diff 284997c --
research/` is empty.

| lane | source commit | integrated commit | scope | verification |
|---|---|---|---|---|
| HEAD clean-room | `8681003` | `4168672` | ordinary+wheel replay at `bd6f0a1` | 17 release-critical; demos ZERO/ZERO/UNKNOWN |
| final reviewer A | `d887b86` | `d887b86` | physicist UX | `ALPHA_READY` |
| final reviewer B | `98bb150` | `98bb150` | software/reproducibility | `ALPHA_READY` |
| final reviewer C | `a7a333a` | `a7a333a` | safety/claims | `ALPHA_READY` |

Coordinator decision: **`RESEARCH_PREVIEW_ALPHA`**. Product SHA remains
`bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0`. Frozen scientific evidence
changed by this program: **none**.
