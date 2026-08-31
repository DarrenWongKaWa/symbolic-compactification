# Derivation Audit 0.2.1-alpha

**Patch on `derivation-audit-v0.2.0-alpha`. The v0.2 tag is not moved.**

Additive generic adapter exposed by public real-paper field validation.
Product model unchanged: typed derivation graph, fail-closed exact residuals,
generated reviewer tables.

- Branch: `engineering/derivation-audit-v0.2.1`
- Package: `0.2.1-alpha` (PEP 440 `0.2.1a0`)
- Engine (ZERO/NONZERO/UNKNOWN unchanged): `0.3.0`
- Protocol: `0.2.1`

## What this patch adds

```text
ZERO  ≠  CERTIFIED_BY_RULE
```

| Status | Meaning |
|---|---|
| `ZERO` | Engine simplified an executable residual to exact zero |
| `CERTIFIED_BY_RULE` | Local child ZERO + declared theorem/domain. Not an engine integral ZERO |

New edge type: `BZ_PERIODIC_INTEGRATION_BY_PARTS`  
New declared rule: `BZ_TORUS_PERIODICITY` on `BRILLOUIN_ZONE_TORUS`  
Missing periodicity: `ASSUMPTION_REQUIRED`

See [docs/RULE_CERTIFICATES.md](../../docs/RULE_CERTIFICATES.md).

Rule growth is **field-driven**. This is the first rule because a published
PRL supplement used BZ IBP and v0.2 could only say `NOT_LOWERED`. Do not
grow a theorem-prover catalogue speculatively.

## What this patch does not include

The Guo et al. public real-paper workspace is **validation evidence**, not
this product commit:

`engineering/real-paper-validation-arxiv-2511-16422`

`examples/real_papers/arxiv_2511_16422/`

## What did not change

- v0.2.0-alpha tag
- engine ZERO/NONZERO/UNKNOWN semantics
- demos A/B/C
- Mode A v0.1
