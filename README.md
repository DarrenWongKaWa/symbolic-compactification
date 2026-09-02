# symbolic-compactification

**Verified symbolic reasoning for theoretical physics.**

An agent-assisted scientific derivation-audit system.

Give it a paper or a derivation. It builds auditable evidence layers and
emits reviewer-facing **HTML** and **Markdown**. A model may propose. Only
the deterministic engine may certify, and only on exact `ZERO`.

This is not a CAS, not a theorem prover, and not an autonomous physicist.

Package `0.3.1-alpha`. Engine `0.3.0` (same `ZERO` / `NONZERO` / `UNKNOWN`
meanings as `v0.3.0-alpha`). Research preview, not a stable v1.0.

## What goes in

A scientific source with numbered equations (TeX or an audit workspace),
plus source-grounded derivation relations. Adjacent equation numbers are
not a derivation.

## What comes out

- **HTML evidence ledger** — first-screen colour bar, Must-review Sign
  queue, appendix map, obligation table.
- **Markdown report** — the same frozen statuses as the HTML.
- **Machine records** — `RESULTS.md` / audit `runs/` that the HTML may
  only *present*, never rewrite.

## Flagship

Guo et al., Phys. Rev. Lett. 136, 206303 (arXiv:2511.16422v2).

Open the reviewer HTML:

[`examples/guo-evidence-ledger/output/index.html`](examples/guo-evidence-ledger/output/index.html)

Same science as Markdown:

[`examples/guo-evidence-ledger/output/REPORT.md`](examples/guo-evidence-ledger/output/REPORT.md)

How to read the layers: [`examples/guo-evidence-ledger/README.md`](examples/guo-evidence-ledger/README.md).

## Install

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/symbolic-compactification --version
```

Core verification needs no model service and no API key.

## Paper audit

Numbered equations only. Record source-grounded relations, then:

## One happy path

**New paper (agent or human):**

```bash
symbolic-compactification audit init my-audit
# copy the manuscript into my-audit/manuscript/
symbolic-compactification audit inventory my-audit
# record source-grounded edges under my-audit/edges/
symbolic-compactification audit verify my-audit
symbolic-compactification audit report my-audit
```

That writes `my-audit/reports/REPORT.md` and `my-audit/reports/report.html`.

**Inspect the flagship (no re-audit required):**

```bash
open examples/guo-evidence-ledger/output/index.html
```

**Forward derivation** (candidate must be exact `ZERO`; promote only on `ZERO`):

```bash
cp -R examples/forward/exact-step /tmp/ssc-exact
symbolic-compactification verify /tmp/ssc-exact
```

Minimal agent prompt:

> Audit this scientific paper using symbolic-compactification. Follow
> AGENTS.md and docs/paper-audit.md. Produce the reviewer-facing HTML
> report and the corresponding Markdown report, with evidence
> traceability. Do not invent edges. Do not treat 0* as Exact.

## Machine-certified vs human review

| Status | Who decides |
|---|---|
| `EXACT_ZERO` / `ZERO` | Machine. Local residual is 0. Not a paper pass. |
| `ZERO_UNDER_SUBSTITUTION` | Machine checked 0 **after** written substitution A. Does not prove A. |
| `CERTIFIED_BY_RULE` | Local identity + declared rule. Not engine `ZERO`. |
| `STRUCTURAL` | Definition / bookkeeping. No equality to check. |
| remainders, limits, special functions | Uncertified. Human scientific review. |
| claimed cancel / vanishing | Orange Sign queue. Human must decide. |
| `UNSUPPORTED` algebra | Not compiled. Not a pass. |
| `NONZERO` | Machine residual is not 0. |

`UNKNOWN` never promotes. Workspace `0*` is **invalid historical overlay**
and is excluded from reviewer output.

## Docs

- [Getting started](docs/getting-started.md)
- [Paper audit](docs/paper-audit.md)
- [Architecture](docs/architecture.md)
- [Semantics](docs/semantics.md)
- [Limitations](docs/limitations.md)
- [Forward derivation](docs/forward-derivation.md)

## License

MIT. Historical research campaigns live under [`docs/history/`](docs/history/)
and archive tags, not on the product path.
