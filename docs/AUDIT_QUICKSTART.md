# Derivation-audit quickstart

v0.2 derivation-audit alpha in development on
`engineering/derivation-audit-v0.2`. No model and no API key are required.

Mode A (`symbolic-compactification init`) remains supported; this page is the
**audit** workspace only.

## 1. Install from a checkout

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/symbolic-compactification --version
```

`ssc` is equivalent. See [engineering/release_v0_1/INSTALLATION.md](../engineering/release_v0_1/INSTALLATION.md).

## 2. Create an audit workspace

The path must not already exist. Initialization never overwrites.

```bash
symbolic-compactification audit init my-paper-audit
```

## 3. Supply sources (manual transcription)

Replace the placeholder manuscript. Inventory reads labels only; it does
**not** translate LaTeX into algebra. Put every machine-parsable member and
residual in `expressions/` as native text accepted by the strict parser.

Edit:

- `manuscript/source.tex` (or the path in `audit.yaml`)
- `equations/equations.yaml` — curated equation ids / labels after inventory
- `edges/edges.yaml` — typed edges (`edge_id`, `edge_type`, optional
  `source_from` / `source_to`, optional lhs/rhs/residual, `children` for
  splits)
- `expressions/*.txt` — explicit residuals and members
- `assumptions/assumptions.yaml` — every symbol and allowed undefined function

```yaml
symbols:
  - name: x
    real: true
    nonzero: false
functions: []
```

Do not declare `real: false`. The alpha cannot encode positivity, general
inequalities, excluded poles, parameter identities, boundaries, symmetries,
or limit order.

Choose `edge_type` from the [frozen catalogue](EDGE_TYPES.md). Do not encode
an asymptotic remainder as `ALGEBRAIC_EQUIVALENCE`.

## 4. Inventory and inspect

```bash
symbolic-compactification audit inventory my-paper-audit
symbolic-compactification audit inspect my-paper-audit
```

`inventory` writes tool-owned sidecars under `reports/` only. `inspect`
prints hashes and config; its counts are not scientific evidence. Neither
command rewrites researcher sources.

## 5. Verify, table, report, package

```bash
symbolic-compactification audit verify my-paper-audit
symbolic-compactification audit table my-paper-audit
symbolic-compactification audit report my-paper-audit
symbolic-compactification audit package my-paper-audit
```

`verify` creates `runs/<run_id>/` and does not reuse a previous snapshot
silently. `table` / `report` / `package` read a recorded run (`--run` to
select; latest by default).

Read `reports/TABLE_VERIFIED.md` as the machine-verified set. Read
`TABLE_STRUCTURAL.md`, `TABLE_NONZERO.md`, and `TABLE_UNCERTIFIED.md` for
everything else. Narrative in `REPORT.md` cannot add a verified row.

## 6. Read the result

| Status | Meaning |
|---|---|
| `ZERO` | Exact residual vanished under the recorded route and assumptions. |
| `NONZERO` | Exact evidence refutes the encoded residual. |
| `UNKNOWN` | Undecided. Nothing is certified. |
| `NOT_LOWERED` | No executable residual for this edge type / encoding. |
| `DEFINITION` / `RECORDED` / `SPLIT` | Structural tracking, not proof. |

Only obligations returning exact `ZERO` are listed as machine-verified. See
[STATUS_SEMANTICS.md](STATUS_SEMANTICS.md).

## Mode A (still supported)

Hypothesis-level equivalence without a derivation graph:

```bash
symbolic-compactification init my-symbolic-project
symbolic-compactification inspect my-symbolic-project
symbolic-compactification verify my-symbolic-project
symbolic-compactification report my-symbolic-project
```

[engineering/release_v0_1/QUICKSTART.md](../engineering/release_v0_1/QUICKSTART.md)
