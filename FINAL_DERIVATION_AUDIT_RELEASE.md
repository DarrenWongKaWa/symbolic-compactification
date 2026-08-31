# Derivation Audit Alpha v0.2 — Release Record

Status: `DERIVATION_AUDIT_ALPHA_READY`

Package: `0.2.0-alpha` (PEP 440 `0.2.0a0`)
Branch: `engineering/derivation-audit-v0.2`
Tag intent: `derivation-audit-v0.2.0-alpha`
Engine (unchanged verifier semantics): `0.3.0`

This is not a stable v1.0 and is not merged to `main`. The v0.1 tag
`research-preview-v0.1.0-alpha` is not moved.

## Public scope

Machine-auditable symbolic derivation verification for theoretical and
mathematical physics, with source-grounded proof obligations and fail-closed
exact adjudication.

A researcher can: create an audit workspace, inventory equations, declare
typed edges, lower executable residuals, run the verifier, generate reviewer
tables, and export a reproduce.sh package.

Mode A (`init` / `inspect` / `verify` / `report`) remains supported.

## Privacy

Unpublished local scientific sources are not on this branch, not in the
tag, not in examples, and not in wheels/sdists. Optional private acceptance
was skipped: converting a pre-v0.2 unpublished workspace would copy
non-exportable material. Public demos are independent textbook constructions.

## Workflow

```
ssc audit init <dir>
ssc audit inventory <dir>
ssc audit inspect <dir>
ssc audit verify <dir>
ssc audit table <dir>
ssc audit report <dir>
ssc audit package <dir>
cd reviewer-verification-package && ./reproduce.sh
```

## Status semantics

Only executable engine `ZERO` with integrity PASS appears in TABLE_VERIFIED.
`NONZERO` is a potential mismatch, not a declaration that a paper is wrong.
`DEFINITION` / `RECORDED` / `SPLIT` are structural. `UNKNOWN` /
`NOT_LOWERED` / `ASYMPTOTIC_CLAIM` remain outside exact certification.
Finite coefficient ZERO is not a remainder proof.

## Anti-hallucination

LLM text cannot create verified status. The verified table is generated from
machine records. Forged markdown ZERO is dropped on regeneration. Reviewer
packages regenerate tables from the bound run rather than copying authored
markdown.

## Public demos

- A: two algebraic ZERO identities
- B: index relabeling, projector, pairwise ZERO plus DEFINITION and RECORDED
- C: two Laurent-coefficient ZERO; enclosing asymptotic remainder UNKNOWN

## Release-critical tests

`pytest -m derivation_audit_release_critical`
`pytest -m release_critical` (v0.1 gate, still 17 passed after version bump)

## Clean-room replay

See `engineering/derivation_audit_v0_2/CLEAN_ROOM_REPLAY.md` (PASS on
`c85a703`; R1/R2 blocker fixes landed after that replay and are covered by
the derivation-audit release-critical tests).

## Reviewer verdicts

| Reviewer | First verdict | After blocker fixes |
|---|---|---|
| R1 physicist UX | BLOCKED (4 UX issues) | issues addressed in `eee23f4` |
| R2 soundness | BLOCKED (package copied authored tables) | issues addressed in `eee23f4` |
| R3 reproducibility | ALPHA_READY | — |
| R4 privacy/security | ALPHA_READY | — |
| R5 skeptical editor | ALPHA_READY | — |

## Limitations (allowed)

PDF inventory is manual; some edges remain NOT_LOWERED; integral and
asymptotic remainder certification are limited; complex scientific
assumptions may be unsupported; AI edge proposal is experimental; explicit
symbolic transcription is required.

## Historical full suite

Not a v0.2 release gate. Core-only environments cannot collect the optional
observations extra. Frozen historical failures from v0.1 remain disclosed,
not rewritten.
