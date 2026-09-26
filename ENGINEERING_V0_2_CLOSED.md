# Derivation Audit v0.2 engineering is CLOSED.

```text
Derivation Audit v0.2 engineering is CLOSED.
```

This file records an engineering freeze after public publication of
`derivation-audit-v0.2.1-alpha`. It does not change product semantics.

## Frozen lineage

```text
v0.2.0-alpha
    → real-paper validation
    → v0.2.1-alpha
```

| Object | Role | SHA / ref |
|---|---|---|
| `derivation-audit-v0.2.0-alpha` | Historical product tag. **Do not move.** | `aaf1199` |
| `engineering/real-paper-validation-arxiv-2511-16422` | Public real-paper **evidence**, not a product tag | `69ad474` |
| `engineering/derivation-audit-v0.2.1` | Generic product patch | `783ec64` |
| `derivation-audit-v0.2.1-alpha` | Product tag on the generic patch | `783ec64` |

GitHub pre-release:

https://github.com/DarrenWongKaWa/symbolic-compactification/releases/tag/derivation-audit-v0.2.1-alpha

## Frozen product principles

1. `ZERO ≠ CERTIFIED_BY_RULE`
2. Certificate class describes provenance, not mathematical truth ranking
3. Rule growth is field-driven
4. Proposal authority ≠ verification authority
5. The verified table is generated, not authored
6. `UNKNOWN` must never be promoted for narrative convenience

## What is not authorized

No automatic:

- v0.2.2
- new theorem rule catalogue
- verifier expansion
- benchmark expansion
- second-paper engineering campaign

is authorized.

Do not add `TRACE_CYCLICITY`, `STOKES`, `HERMITICITY`, `COMPLETENESS`, or
similar rules speculatively.

Do not open a new scientific-discovery campaign.

Do not retag `derivation-audit-v0.2.0-alpha`.

Do not treat the real-paper evidence branch as product source.

Unpublished local scientific manuscripts remain excluded from public
provenance.

## What would be required to reopen engineering

Future engineering changes require **all** of:

```text
real external use
+ concrete generic product gap
+ explicit human authorization
```

A missing presentation artifact for the methods paper must be created from
**existing** evidence. It is not a license to generate new scientific
capability.

## Next program

The next deliverable is not more product code.

It is a methods manuscript in `paper/derivation-audit-method/` explaining
why an AI may propose a derivation, but only explicit source-grounded
machine evidence may certify it.
