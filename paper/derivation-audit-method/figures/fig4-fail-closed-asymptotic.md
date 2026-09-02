# Figure 4 — Soundness: remainder stays UNKNOWN

**Type.** Experimental soundness panel.
**Paradigm.** Before/after of an encoding cheat that the system refuses.

**Caption (draft).** Finite coefficient checks may return engine ZERO while the enclosing remainder claim stays UNKNOWN. The audit layer refuses to rewrite \(F(\Gamma)=A/\Gamma+O(\Gamma)\) as the exact residual \(F-A/\Gamma=0\) in order to manufacture a green row. Left: Demo C, which ships with the product tag. Right: Guo Eq. (D-57). Non-green output is soundness evidence, not a failed paper.

## Layout

Two columns.

Left — Demo C:

```text
Laurent / coefficient children  →  TABLE_VERIFIED (ZERO)
enclosing ASYMPTOTIC_CLAIM     →  TABLE_UNCERTIFIED (UNKNOWN)
```

Right — Guo (D-57):

```text
Γ expansion typed ASYMPTOTIC_CLAIM
remainder O(Γ) is not a local residual
status UNKNOWN
```

A rejected encoding in a grey ghost box:

```text
do not emit:  F − A/Γ = 0   ⇒   fake ZERO
```

## Tool

PowerPoint or draw.io. Not a 3D funnel of “partial success”.
