# Verdict — source assumption audit

Hop authority unchanged:

```
G0016 → G0013 = UNKNOWN LEVEL_B
```

Close: **TRULY ADDITIONAL**.

The verifier did not fail. The frozen problem does not contain enough
analytic-domain hypothesis to certify a pole-free neighborhood.

## 1. What does the frozen Guo source declare?

| source | domain content |
|---|---|
| Wolfram header | Authority Guo App. A/B; “exact finite Gamma; no small-Gamma expansion”; index coincidences as removable limits |
| `symbols.json` | `beta`, `gamma`, `mu`, … : `real=true`, **`nonzero=false`**, no `positive` |
| `load_guo_item` | same reals; **`required_assumptions` is missing** (`None`) |
| Wolfram ingest | default real; nonzero only if listed (empty) |
| V5 freeze | hop texts and degeneration; no positivity |

Declared, and only this: symbols are **real** (and bound indices `n,m,ell` are real). `epsilon` is an undefined function, not a real-valued symbol.

Not declared: `beta>0`, `gamma>0`, `gamma≠0`, `epsilon` real, `z0 ∉ Z_≤0`.

“Exact finite Gamma” is a **formula-selection** note (keep finite-Γ DC, do not expand small Γ). It is not the inequality `gamma>0`.

`1/gamma^2` in some branches is not a domain declaration. The generic branch also contains \((\varepsilon(m)-\varepsilon(n))^{-3}\); that locus is exactly what confluence takes a limit through.

This is **not DECLARED** and not an ingestion leak: `nonzero=false` is written on purpose.

## 2. Can those assumptions prove the 14 `z0` avoid polygamma poles?

**No.** Four unique affine germs, all of the form

```
z0 = 1/2 + βγ/(2π) ± i β(μ − ε(•))/(2π)
```

Under frozen `real=True` only, `ask` cannot prove `Re(z0)>0` or `Im(z0)≠0`.

**Pole witness** (allowed by frozen reals):

```
β=1, γ=−π, μ=0, ε(n)=0  ⇒  z0 = 0 ∈ Z_≤0
```

So pole exclusion is not **DERIVED**.

## 3. What is the minimal extra assumption, and what is it in the model?

**Minimal sufficient set that would make pole exclusion DERIVED:**

```
beta > 0,  gamma > 0,  epsilon(·) real-valued
```

Then `Re(z0) = 1/2 + βγ/(2π) > 1/2` for all 14 atoms, hence
`z0 ∉ {0,−1,−2,…}` even when `Im=0`.

Weaker but sufficient: `βγ > −π` and `ε` real (`Re>0`). Direct
`z0 ∉ Z_≤0` also suffices and is strictly weaker.

**Status in the original model / paper:**

- \(\beta=1/T>0\) and broadening \(\Gamma=\gamma>0\) with real mode
  energies \(\varepsilon_n\) are a **physical regime**, not a definition
  of the algebraic DC formula in the frozen Wolfram artifact.
- The PRB closed-form materials are **not** in this engine repository
  (gold ban). They cannot be used to backfill inequalities.
- Adding those inequalities would be a **human change of the frozen
  problem definition**, after which remainder certificates could be
  re-applied (assumption-derivation gain, not a verifier-rule change).

Until that change is explicit:

```
remainder = ASSUMPTION_REQUIRED
hop      = UNKNOWN LEVEL_B
D2       = LOCKED
```

Close letter: **TRULY ADDITIONAL**. Publication still **E**.
No Remainder V2. No D2. No LEVEL C promotion.
