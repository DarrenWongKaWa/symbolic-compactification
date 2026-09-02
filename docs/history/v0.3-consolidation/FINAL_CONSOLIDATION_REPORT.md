# Final consolidation report — v0.3.0-alpha

Unified Research Preview. Not a stable v1.0.

## Identities

| Identity | Value |
|---|---|
| Release | `v0.3.0-alpha` |
| Package | `0.3.0-alpha` (PEP 440 `0.3.0a0`) |
| Engine | `0.3.0` (unchanged `ZERO` / `NONZERO` / `UNKNOWN`) |
| Agent protocol | `0.3.0` (unchanged) |
| Base SHA | `af022cab90366385685c57aac9500a891db1be24` (`origin/main` before merge) |
| Consolidation HEAD | `b04dd7e2872c7b4a274490e13ea20ad839985473` |
| Merge SHA | `f1d225e46eec3aac17381fb2f7618fa830a8ec79` (PR #4, merge commit, not squash) |
| Release tag peel | `f1d225e46eec3aac17381fb2f7618fa830a8ec79` |
| Release URL | https://github.com/DarrenWongKaWa/symbolic-compactification/releases/tag/v0.3.0-alpha |

Flagship precondition: `GUO_FULL_PAPER_AUDIT_FLAGSHIP_V1` completed with
`FULL_PAPER_AUDIT_DEMONSTRATED` (`archive/guo-full-paper-audit-flagship-v1`
`d92f3ec`).

## Branches

| | Count | Refs |
|---|---:|---|
| Pre-clean remote | 10 | `main`, `paper/derivation-audit-method`, six engineering/experiment lineages, `engineering/v0.3-consolidation`, flagship experiment |
| Post-clean remote | 2 | `main` (`f1d225e`), `paper/derivation-audit-method` (`ed9af5a`) |

`paper/derivation-audit-method` is kept temporarily: it still holds unique
manuscript work not on `main`.

## Archive tags created

Verified on origin before any branch deletion. Old release tags were not
moved.

| Tag | Original branch | Peel |
|---|---|---|
| `archive/derivation-audit-v0.2` | `engineering/derivation-audit-v0.2` | `aaf1199` |
| `archive/derivation-audit-v0.2.1` | `engineering/derivation-audit-v0.2.1` | `3c8c689` |
| `archive/guo-selected-edge-validation-v1` | `engineering/real-paper-validation-arxiv-2511-16422` | `69ad474` |
| `archive/forward-proposer-replay-v1` | `experiment/forward-proposer-replay-v1` | `b9b6972` |
| `archive/approximation-authority-v1` | `experiment/approximation-authority-v1` | `5477cf2` |
| `archive/prd-cross-paper-stress-v1` | `experiment/prd-theory-derivation-audit-v1` | `4f12401` |
| `archive/guo-full-paper-audit-flagship-v1` | `experiment/guo-full-paper-audit-flagship-v1` | `d92f3ec` |

Unmoved: `derivation-audit-v0.2.0-alpha` (`aaf1199`),
`derivation-audit-v0.2.1-alpha` (`783ec64`).

## Obsolete branches deleted

After tag + prerelease + archive-tag verification:

- `engineering/derivation-audit-v0.2`
- `engineering/derivation-audit-v0.2.1`
- `engineering/real-paper-validation-arxiv-2511-16422`
- `experiment/forward-proposer-replay-v1`
- `experiment/approximation-authority-v1`
- `experiment/prd-theory-derivation-audit-v1`
- `experiment/guo-full-paper-audit-flagship-v1`
- `engineering/v0.3-consolidation`

Private local `engineering/research-preview-alpha-v0.1` was never pushed.

## Root items removed or moved from current `main`

Deleted from current tree (recoverable from tags/history):

- `benchmark/`, `benchmark_v0.2/`, `benchmark_structure/`, `benchmark_abstraction/`
- `research/`, `engineering/`, `release/`, `reviews/`, `roles/`, `workspace/`
- `CAPABILITIES.json`, `FINAL_DERIVATION_AUDIT_RELEASE.md`, `FINAL_ENGINEERING_RELEASE.md`
- `REPERTOIRE_V2.md`, `REPRODUCIBILITY.md`, `REPRODUCIBILITY_STRUCTURE_DISCOVERY.md`

Moved into product docs:

- `CAPABILITY_BOUNDARY.md` → `docs/history/capability-boundary.md`
- `NEGATIVE_RESULTS.md` → `docs/history/negative-results.md`
- `SCIENTIFIC_EXPERIMENTS_CLOSED.md` → `docs/history/scientific-experiments-closed.md`

Added at root: `LICENSE` (MIT).

Current root: `README.md`, `LICENSE`, `pyproject.toml`, `Makefile`,
`AGENTS.md`, `setup.py`, `src/`, `tests/`, `docs/`, `examples/`, `scripts/`,
`consolidation/`, `.github/`, `.grok/`, `.gitignore`.

## Benchmark files removed from current `main`

| Tree | Deleted paths |
|---|---:|
| `benchmark/` | 134 |
| `benchmark_structure/` | 37 |
| `benchmark_abstraction/` | 37 |
| `benchmark_v0.2/` | 16 |

Pointer: `docs/history/benchmark-history.md`. The corpora still exist in
git history and `research-preview-v0.1.0-alpha`. This is not a claim that
they never existed.

## Tests retained

51 product test modules plus `tests/fixtures/` (audit demos A/B/C, basic,
medium, long). Research-only suites (`test_rps_*`, `test_ac_*`, `test_sv_*`,
representation/structure-discovery/abstraction, …) were removed from `main`
and remain in archive tags.

Full product pytest on the clean-room clone: **566 passed, 1 skipped**.
Release-critical markers: **40 passed, 1 skipped**.

## Docs consolidated

User docs: `getting-started`, `forward-derivation`, `paper-audit`,
`semantics`, `limitations`, `architecture`, `research-evidence`, plus
`edge-types`, `rule-certificates`, `threat-model`, and `docs/history/`.

One skill contract: `.grok/skills/symbolic-compactification/SKILL.md`
(Grok adapter) with harness-neutral `AGENTS.md`.

## Examples consolidated

- `examples/forward/exact-step` — accepted `ZERO`
- `examples/forward/refused-step` — refused `NONZERO`
- `examples/audit/minimal` — `STRUCTURAL` + `ZERO` + `UNKNOWN`
- `examples/flagship/guo/` — RESULTS.md, REPRODUCE.md, frozen manifests

## Flagship demo path

[`examples/flagship/guo/RESULTS.md`](../examples/flagship/guo/RESULTS.md)

Printed equation numbers; GitHub-rendered mathematics; 189/189 coverage;
source-grounded relations only.

## Clean-room status

`CLEAN_ROOM_PASS` — see `CLEAN_ROOM_REPORT.md`.

Install succeeded. Forward exact `ZERO`. Forward refused `NONZERO` / no
promotion. Minimal audit `DEFINITION` 1, `ZERO` 2, `UNKNOWN` 1. Guo
`RESULTS.md` byte-identical after deterministic replay. Engine `0.3.0`.
API key required: **false**.

## New-visitor review

All ten questions pass after branch deletion. See `PHYSICIST_REVIEW.md`.

## CI note after the tag

GitHub `release-gate` on Python 3.12 passed every product step on
`f1d225e` (tests, firewall, CLI, forward demos, minimal audit, Guo
inventory). Python 3.10 failed at **test collection** because
`tests/test_packaging_contract.py` imported `tomllib` (stdlib in 3.11+).
That is a test-import issue, not an engine or demo failure. It is patched
on `main` after the tag. The `v0.3.0-alpha` tag was **not moved**.

## Remaining active branches

1. `main`
2. `paper/derivation-audit-method` (temporary manuscript work)
