# Track V4 — polygamma local confluence

Parent: Track V3 close `d2752f9` (CASE I-D). No LLM. Track D2 locked
until a frozen family is FAMILY_ZERO or FAMILY_NONZERO.

## Central question

Can a *generic* per-atom series of polygamma rational terms, plus Laurent
`t^0` comparison, certify the 327-op diagonal→triple hops that timed out
as whole-kernel series — without Guo-specific identities?

## Method

```
spectator mul-args peel (no degeneration-dependent S)
    → reconstruct K = pref * Sum_i T_i   (each T_i one polygamma)
    → T_i.series(t, 0, n) independently
    → together(pref(t) * sum cores)
    → Laurent coeffs of t^{<0} must vanish
    → t^0 vs target: expand==0 or cancel==0
```

`t` is the one-parameter degeneration (`var - point`).

Forbidden: Guo closed forms, Φ_Γ / L4–L7, converting timeout to ZERO,
numeric agreement, majority FAMILY_ZERO, joint-limit auto-promotion.

## Outcomes

- **J-A** a frozen 5-branch family FAMILY_ZERO → D2 may unlock
- **J-B** FAMILY_NONZERO → D2 may unlock as correction
- **J-C** diagonal hops ZERO, generic hops UNKNOWN → D2 locked
- **J-D** even atom-series UNKNOWN/timeout → D2 locked
