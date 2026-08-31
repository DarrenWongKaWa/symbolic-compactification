# Public derivation-audit demos

Public demos are **independent constructions**: synthetic or clearly public.
They are not near-clones of private work and must not use private equation
numbers, nicknames, or recognizable private kernels.

Intended locations (demos layer):

- `engineering/derivation_audit_v0_2/demos/A/`
- `engineering/derivation_audit_v0_2/demos/B/`
- `engineering/derivation_audit_v0_2/demos/C/`

Replay after copy to a writable workspace (never overwrite the committed
inputs). Expected machine claims follow the frozen status rules, not demo
prose.

## Demo A — algebraic equation-to-equation identities

Several `ALGEBRAIC_EQUIVALENCE` edges on elementary identities (expansion,
cancellation, rational equality) that lower to executable residuals.

**Expected:** multiple machine-verified `ZERO` rows in `TABLE_VERIFIED.md`.
Definitions, if present, stay in `TABLE_STRUCTURAL.md`.

## Demo B — typed structural steps

Typed edges that are not a single scalar rewrite:

- `INDEX_RELABELING`
- `PROJECTOR_IDENTITY`
- `PAIRWISE_REDUCTION` (local pair residual; the global sum is not one
  residual)

**Expected:** each lowered local identity that returns exact `ZERO` appears
in `TABLE_VERIFIED.md`. A parent that is only bookkeeping or a global pairing
is `RECORDED` / `NOT_LOWERED` / `SPLIT` as typed—not rewritten as one
algebraic residual.

## Demo C — coefficient `ZERO`, remainder uncertified

Finite `LAURENT_COEFFICIENT` or `SERIES_COEFFICIENT` children plus a parent
`ASYMPTOTIC_CLAIM` (global remainder) **without**
`remainder_certificate_hash`.

**Expected:**

- coefficient children may be `ZERO` and listed as machine-verified
- the parent remainder claim remains `UNKNOWN` in `TABLE_UNCERTIFIED.md`
- the parent must not appear in `TABLE_VERIFIED.md`

This is the soundness demo: finite coefficient agreement is not a remainder
proof.

## Replay sketch

```bash
symbolic-compactification audit inspect <copied-demo>
symbolic-compactification audit verify <copied-demo>
symbolic-compactification audit table <copied-demo>
symbolic-compactification audit report <copied-demo>
```

Core verification needs no API key. Optional HTML reports are non-blocking
and not required to interpret A/B/C.

Mode A v0.1 demos remain at
[engineering/release_v0_1/DEMOS.md](../engineering/release_v0_1/DEMOS.md).

A separate **public real-paper field validation** (not a synthetic demo) lives
at [`examples/real_papers/arxiv_2511_16422/`](../examples/real_papers/arxiv_2511_16422/).
It uses the same audit CLI. It does not replace A/B/C.
