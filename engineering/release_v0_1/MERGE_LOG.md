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
