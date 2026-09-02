# Clean-room productize evaluation — 0.3.1-alpha

Date: 2026-09-02. Branch: `release/productize-v0.3.1-alpha`.

Isolated clones contained only the repository plus `incoming-paper/`
(synthetic manuscript `source.tex` and claimed `edges.yaml`). The prompt
was:

> Audit this scientific paper using symbolic-compactification. Produce
> the reviewer-facing HTML report and the corresponding Markdown report,
> with evidence traceability.

No development conversation was given to the agents.

## Codex

**PASS.** `codex exec` (workspace-write sandbox) read README / AGENTS.md /
docs, ran `audit init`, copied the incoming manuscript and edges, ran
`audit inventory` / `verify` / `report`.

Outputs:

- `incoming-paper-audit/reports/REPORT.md`
- `incoming-paper-audit/reports/report.html`

Engine table: DEFINITION 1, ZERO 2, UNKNOWN 1 (asymptotic remainder).
No `0*` overlay. HTML includes `#map-sec`. Statuses copied from the
recorded run, not authored.

## Claude Code

**BLOCKED.** `claude` is installed and `claude auth status` reports
logged-in OAuth, but non-interactive `claude -p` failed in this
environment (unknown default model `deepseek-v4-pro`; print mode
exited without producing a workspace). Not reported as PASS.

## Fresh-context substitute

**PASS.** A new clone followed README install + `audit init` /
`inventory` / `verify` / `report` exactly. Same HTML+Markdown pair,
same ZERO/UNKNOWN split, no `0*`.

Paths: `/tmp/ssc-cleanroom-substitute/incoming-audit/reports/`.
