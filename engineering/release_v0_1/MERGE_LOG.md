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

Frozen scientific evidence changed by integrations: **none**.
