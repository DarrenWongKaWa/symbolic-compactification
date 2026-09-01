# Approximation-authority classification (v1)

Product: tag `derivation-audit-v0.2.1-alpha` peel `783ec64`.
Engine: `python_sympy_exact_v1` / `0.3.0`.
No `src/` edits. No v0.2.2. No approximate `ZERO`.

This is a **classification** campaign, not a leaderboard and not a
remainder-proof campaign.

## Research question (RQ4 candidate)

Not: can an approximation be made to return engine `ZERO`?

The question is:

> Who authorized this approximation, and after it is adopted, does the
> subsequent algebra still hold exactly?

Object:

```
source authority → approximation semantics → exact downstream verification
```

Connected to Forward RQ1:

```
proposal → identify required approximation → check authority
        → apply approximation → verify exact consequence → promote/refuse
```

## Two-stage graph

```
E0  --author-declared approximation-->  E0_tilde
    --machine-checked exact algebra-->  E1
    --exact-->  E2
```

The first arrow is not the later arrows. Engine `ZERO` is allowed only on
the exact-algebra children. A parent that packages a declared approximation
plus a child `ZERO` may be recorded, at experiment overlay level, as
`CERTIFIED_UNDER_DECLARED_APPROXIMATION`. That parent is **never** called
`ZERO`, for the same reason `CERTIFIED_BY_RULE` is never called `ZERO`.

## What is measured

Whether these four cases are **distinguished**, not an accuracy number:

1. Author declared the approximation, and downstream algebra is `ZERO`.
2. Author declared the approximation, and downstream algebra is `NONZERO`.
3. Author declared the approximation, and remainder control is `DECLARED_ONLY`
   (no remainder certificate).
4. Author declared nothing, but only a hidden approximation makes the
   equality hold.

## Frozen contrasts (not approximation)

- Exact algebraic regroup (Guo \(K_{1A}\)): provenance `NONE`, engine `ZERO`.
- Substitution identity \(e_{21}=-e_{12}\) (Guo \(T_{B,\mathrm{geo}}\)):
  still a **substitution / assumption** problem, not an approximation.
  Keep it out of the approximation parent class.

## Promotion (experiment overlay)

| Condition | Overlay | Product Mode A |
|---|---|---|
| Exact residual `ZERO`, no hidden approx | `ENGINE_ZERO` | promote |
| `AUTHOR_DECLARED` + downstream `ZERO` | `CERTIFIED_UNDER_DECLARED_APPROXIMATION` | do **not** promote the parent as `ZERO` |
| `AUTHOR_DECLARED` + downstream `NONZERO` | `REFUSED_DOWNSTREAM_NONZERO` | refuse |
| Remainder claim, no certificate | `ASYMPTOTIC_DECLARED_ONLY` | `UNKNOWN` / not lowered |
| `NONE` + hidden \(T_A\) yields `ZERO` | `UNDECLARED_APPROXIMATION_REQUIRED` | refuse naive exact claim |
| `MODEL_PROPOSED` + downstream `ZERO` | `MODEL_APPROX_NOT_AUTHORIZED` | refuse scientific promotion |

`DECLARED_ONLY` is not `REMAINDER_CERTIFIED`. Finite Laurent/coefficient
`ZERO` does not upgrade the parent (NR-004).

## Paper posture

RQ4 candidate. One Discussion sentence in the current Technique paper.
Do not add a core claim, a new product status, or a fourth evaluation RQ
in the abstract until this overlay is either promoted or split into a
follow-on method paper.
