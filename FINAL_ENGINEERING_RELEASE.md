# Final Engineering Release — symbolic-compactification v0.1

Decision: **`RESEARCH_PREVIEW_ALPHA`**

This is an engineering release of a bounded researcher-workspace tool. It is
not a scientific verdict, not a claim that AI discovers physics, and not a
claim that the system reliably invents mathematical representations.

## Product scope

**Context-grounded symbolic hypothesis generation with fail-closed
verification.** Mode A (the researcher supplies the hypothesis) is the
supported workflow. Mode B (propose then verify) remains experimental and is
not a workspace CLI command in this preview.

Supported:

- ingest a small workspace of expressions, notes, assumptions, references, and
  a hypothesis
- ground the hypothesis to named source files
- compile explicit equivalence obligations
- adjudicate `ZERO` / `NONZERO` / `UNKNOWN` (plus parse/compile/assumption
  gates)
- write a provenance-rich report under `workspace/runs/<run_id>/`

Not supported / unestablished:

- robust representation invention
- autonomous theoretical physics
- universal scientific simplification
- general exact-limit certification
- treating notes, papers, or proposer text as proof

## Supported workflow

```text
researcher workspace
    → inspect expressions, assumptions, notes, and references
    → register a symbolic hypothesis
    → compile its explicit proof obligations
    → ZERO / NONZERO / UNKNOWN
    → provenance-rich report under runs/<run_id>/
```

## Install command

CPython 3.12, from a checkout of this tag:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/symbolic-compactification --version
```

Distribution identity: `0.1.0-alpha` (PEP 440 `0.1.0a0`). Engine and agent
protocol remain `0.3.0`. Direct dependencies: PyYAML 6.x and SymPy 1.x.
Core verification requires no API key.

## Three demos

All three are Mode A and live under
`engineering/release_v0_1/demos/`. Copy them before running.

| demo | result | meaning |
|---|---|---|
| A `demo_a_zero` | `ZERO` | exact algebraic factorization |
| B `demo_b_grounded_newton_dd` | `ZERO` | one fixed, denominator-safe Newton divided-difference instance of frozen C9H4/M9H1; not discovery and not the full family |
| C `demo_c_unknown` | `UNKNOWN` | intentional special-function proof gap; not success and not promotable |

```bash
symbolic-compactification inspect COPY
symbolic-compactification verify COPY
symbolic-compactification report COPY
```

## Semantics

- `ZERO`: exact certification under declared engine semantics and assumptions.
- `NONZERO`: the claimed identity was refuted on the verification route.
- `UNKNOWN`: the engine cannot decide. Not likely true, likely false, partial
  success, or permission to promote scientific state.
- `PARSE_FAILURE` / `COMPILE_FAILURE` / `ASSUMPTION_REQUIRED`: no scientific
  relation was checked.

The v0.1 machine-applied assumption surface is `real: true`, optional
`nonzero`, and declared functions. `real: false` is rejected fail-closed on
the researcher workspace.

## Limitations

See [engineering/release_v0_1/LIMITATIONS.md](engineering/release_v0_1/LIMITATIONS.md)
and [CAPABILITY_BOUNDARY.md](CAPABILITY_BOUNDARY.md). Coverage is incomplete.
`UNKNOWN` is common on hard expressions. Finite Laurent coefficients without
remainder control never certify an exact limit. Context-conditioned
representation invention remains unestablished.

## Known unsupported cases

- positivity, inequalities, excluded poles, parameter identities, boundaries,
  symmetries, and limit order (not machine-enforceable)
- general matrix/operator, IBP, continued-fraction, and Lehmann-map evaluation
- PDF/literature RAG (reference ingestion is lightweight)
- workspace `propose` (not shipped)
- legacy `symbols.json` / session CLI is compatibility-only; it is not the
  alpha workspace contract
- historical full pytest suite is not green (`2049 passed, 24 failed`,
  frozen-research-only; disclosed in
  `engineering/release_v0_1/FULL_SUITE_RESULT.md`)

## Exact tag / commit

- Product (packaged source) commit:
  `bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0`
- Tag intent: `research-preview-v0.1.0-alpha`
- Branch: `engineering/research-preview-alpha-v0.1`
- Tested platform: CPython 3.12.13, macOS 26.4 arm64

## Clean-room status

PASS at product SHA `bd6f0a1`. Ordinary and wheel installs, 17
release-critical tests, demos `ZERO`/`ZERO`/`UNKNOWN`, provenance, source
immutability, secret-canary scan, and report-integrity attacks are recorded in
[engineering/release_v0_1/CLEAN_ROOM_HEAD_REPLAY.md](engineering/release_v0_1/CLEAN_ROOM_HEAD_REPLAY.md).

Independent final reviews:

- Physicist UX: `ALPHA_READY`
- Software/reproducibility: `ALPHA_READY`
- Safety/claim-boundary: `ALPHA_READY`

Public update path: push this release branch, push tag
`research-preview-v0.1.0-alpha`, and publish these notes. Do **not** merge to
`main` as a substitute for that path, and do **not** label this a stable
v1.0.
