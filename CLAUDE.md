# CLAUDE.md

Same product contract as `AGENTS.md`. Read that file plus
`docs/paper-audit.md` before auditing a paper.

**Product.** symbolic-compactification takes a scientist's paper or
derivation, builds auditable evidence layers, and emits reviewer-facing
HTML and Markdown. You may propose. The engine certifies only exact
`ZERO`.

**Flagship.** `examples/guo-evidence-ledger/output/index.html`
(Markdown twin: `output/REPORT.md`).

**Happy path.**

```bash
pip install -e ".[dev]"
symbolic-compactification audit init DIR
# manuscript → DIR/manuscript/ ; edges → DIR/edges/
symbolic-compactification audit inventory DIR
symbolic-compactification audit verify DIR
symbolic-compactification audit report DIR
```

**Invariants.** No invented adjacency edges. No `0*` as Exact. No
frozen-RESULTS rewrite. `UNKNOWN` never promotes. Presentation is not a
certificate.

**Tests.** `make test`. Do not weaken tests.

Claim-map V2 (arXiv:2604.04520): `examples/2604.04520/` — `audit.json`
to `v2/audit.html` and `v2/audit.md`. Keep V1. Do not stamp Exact from
remainders or Rice–Mele numerics.
