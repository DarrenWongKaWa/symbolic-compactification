# Pre-registered contributions

These contributions are frozen for draft-v0. Do not inflate them.

## C1 — Typed derivation graph

A theoretical derivation is represented as typed edges rather than treating
every neighboring pair of equations as lhs–rhs equality.

## C2 — Fail-closed adjudication

Exact executable obligations return `ZERO`, `NONZERO`, or `UNKNOWN`, with
no narrative promotion of `UNKNOWN`.

## C3 — Evidence provenance

Machine records bind source, expression, assumptions, obligation, verifier,
and result through immutable hashes / provenance.

## C4 — Generated verification tables

A verified table cannot be authored by an LLM. It is generated only from
integrity-valid machine records.

## C5 — Rule certificates

Some derivation steps combine a local engine certificate with a declared
mathematical theorem / domain. These receive `CERTIFIED_BY_RULE`, not fake
engine `ZERO`.

```text
ZERO ≠ CERTIFIED_BY_RULE
```

## C6 — Explicit epistemic typing

Distinguish:

- `DIRECT_EXACT`
- `SUBSTITUTION_EXACT`
- `RULE_CERTIFICATE`
- `STRUCTURAL`
- `ASYMPTOTIC` / `UNKNOWN`

These labels describe provenance, not mathematical-truth ranking.

## C7 — Real-paper field validation

Demonstrate the frozen pipeline on a published theoretical-physics
derivation without modifying the verifier core (engine `0.3.0`
`ZERO`/`NONZERO`/`UNKNOWN` semantics). A missing Brillouin-zone
integration-by-parts adapter was a generic product gap, not a new
scientific algorithm, and is recorded as the v0.2.1 patch.
