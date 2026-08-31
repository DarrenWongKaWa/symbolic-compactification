# Research Preview Alpha — symbolic-compactification 0.1.0-alpha

**Context-grounded symbolic hypothesis generation with fail-closed verification.**

Research Preview Alpha — experimental proposer, verified hypothesis checking.

This is **not** a stable v1.0 release and is **not** merged to `main`.

- Tag: `research-preview-v0.1.0-alpha`
- Branch: `engineering/research-preview-alpha-v0.1`
- Product (packaged source) commit: `bd6f0a1ecb766526be3eb5cc596eeb337e4b69d0`

## What is supported

Mode A — the researcher supplies a hypothesis; the tool grounds it, compiles
proof obligations, and returns `ZERO` / `NONZERO` / `UNKNOWN` with provenance.

```text
init → inspect → verify → report
```

Reliable parts: exact adjudication in covered domains, grounding, provenance,
structured observations, reproducible runs.

The proposer is experimental and never promotes scientific state. The
verifier is the only judge.

## What this is not

- not an autonomous theoretical physicist
- not “AI discovers physics”
- not a guaranteed scientific simplifier
- not a general formal proof system
- not a claim that representation invention is established

## Release gates

| Gate | Result |
|---|---|
| Clean install (CPython 3.12) | PASS |
| Release-critical tests | 17/17 PASS |
| Clean-room replay | PASS |
| Demos | ZERO / ZERO / UNKNOWN |
| Reviewer A (physicist UX) | ALPHA_READY |
| Reviewer B (reproducibility) | ALPHA_READY |
| Reviewer C (safety/claims) | ALPHA_READY |

## Full-suite disclosure

The historical full test suite is **not** fully green:

```text
2049 passed, 24 failed
```

Those 24 failures are frozen historical authority drift, one optional client,
and cache enumeration. They were disclosed and were not rewritten to make
the suite green.

## Install

```bash
git clone --branch research-preview-v0.1.0-alpha \
  https://github.com/DarrenWongKaWa/symbolic-compactification.git
cd symbolic-compactification
python3.12 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/symbolic-compactification --version
```

Read `LIMITATIONS.md` before using a result in scientific work.
