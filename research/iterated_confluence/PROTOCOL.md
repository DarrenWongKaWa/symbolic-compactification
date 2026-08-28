# Track V3 — iterated one-parameter confluence

No new LLM calls. Frozen V2 Guo 5-branch / Hermite families only
(`FROZEN_INPUTS_V3.json`, n=7). Track D2 stays locked until a frozen
family is `FAMILY_ZERO` or `FAMILY_NONZERO`.

## Central question

Can a multi-parameter / five-branch confluent family be reduced into a
sequence of exact one-parameter confluence steps whose local symbolic
complexity is comparable to the already-certified two-member Guo cases,
and can those local certificates be composed into `FAMILY_ZERO` or
`FAMILY_NONZERO` without Guo-specific identities?

## Causal separation

`verifier gain ≠ compiler gain ≠ grounding gain ≠ discovery gain`

This track is **V only**. Frozen hypotheses. No proposer. No SOL change.
No historical run rewrite.

## Safety rule

Do **not** assume iterated limit = joint limit unless that equality is
itself certified. Distinguish:

- `PATH_ZERO` — every step on one declared path is ZERO
- `FAMILY_ZERO` — all required paths PATH_ZERO, reconstruction ZERO,
  and path consistency `CONSISTENT_ZERO` when the claim needs order
  independence

An order-dependent family must never be `FAMILY_ZERO`.

## Already certified (do not re-prove as novelty)

Two-member Guo local confluence after spectator factoring:

```
h1 * h2 * K_generic  →  h1 * h2 * K_diag
lim K_generic = K_diag   (series / local confluence)
```

ZERO on frozen P2 pairs G0004/G0005 and G0008/G0009 (Track V `38d6d4a`).
Those same pairwise edges are ZERO inside `guo-p2-s2-i4` (Track V2
`fe53ebc`) but that 4-member family remains FAMILY_UNKNOWN.

## Allowed methods

Exact substitution, cancel/together, spectator split with reconstruction
`E - reconstructed(E) == 0`, series around one degeneration parameter,
derivative reduction, local special-function identities, typed DD
recurrence already frozen in Track V/V2. Fallback UNKNOWN.

Forbidden: Guo-specific identity table, gold leakage (`Phi_Gamma`,
L4–L7, PRB masters), converting timeout/size-guard to ZERO, numeric
agreement as exact, majority FAMILY_ZERO, anonymous algebraic
interpolation of intermediate branches.

## Outcome classes

- **I-A** frozen five-branch family FAMILY_ZERO → D2 may unlock
- **I-B** frozen family FAMILY_NONZERO → D2 may unlock as correction
- **I-C** local edges ZERO, path consistency UNKNOWN → D2 locked
- **I-D** local edge UNKNOWN → D2 locked
- **I-E** decomposition invalid under source semantics → D2 locked
