# Where the agents stopped vs the PRB closed form

Date: 2026-08-21. Engine commit for the live runs: `a0560a6`; this note
landed in `3795a86`+. This is an experiment comparison, **not** a certified
compact form and **not** a substitute for
`FINAL_EXACT_CLOSED_FORM.md` in the scientific-line / PRB materials.

Target closed form (authoritative human result):

- scientific-line: `sources/compact_tensor/FINAL_EXACT_CLOSED_FORM.md`
- same frozen raw DC source SHA-256 as `examples/long/Guo_Sigma_abc_dc_exact.txt`:
  `63742cc4e6bf401dd48e258ecb86676b0d7570cc075cae38b91dc188652afc44`

Live A/B setup: [2026-08-21-skill-vs-blank.md](2026-08-21-skill-vs-blank.md).

---

## The ladder (PRB Form I → Form II)

A run only “reaches the PRB answer” if it has **all** of these, certified.

| Step | What the frozen closed form has | Why it matters |
|---|---|---|
| L0 | Ingest the Guo raw DC artifact without mutating bytes | starting object |
| L1 | Keep `Sum` / `Piecewise` / indexed `h1,h2,epsilon` as structure | no eager expansion |
| L2 | Fold four raw sums into **two** sums (2-index + 3-index) by linearity | shared kernels |
| L3 | Name two kernels \(K_2\) (pair) and \(K_3\) (triple) multiplying vertex weights | same skeleton as Form I |
| L4 | One thermal master \(\Phi_\Gamma\) (and reflected \(\Phi_\Gamma^\sharp\)) from \(\psi_0(z_\pm)\) | not a pile of polygamma rationals |
| L5 | Confluent kernels \(\mathfrak M_\Gamma=[w^2]\mathcal R_{1,\Gamma}\), \(\mathfrak T_\Gamma=[w^2]\mathcal R_{2,\Gamma}\) using Hermite divided differences \(H_1,H_2\) | **no `Piecewise`**: coincidences are the same analytic object |
| L6 | Geometric vertices \(\mathcal P^{a(bc)}_{nm}\), \(\mathcal L^{a(bc)}_{nm\ell}\) | \(h_1,h_2\) become covariant generators |
| L7 | Form II: nine frozen geometric generators \(\mathcal G_\alpha\) and coefficients \(F_{\alpha,\Gamma}\) | the boxed PRB answer |

Form I is L3+L4+L5+L6. Form II is L7. Dropping `Piecewise` without L4–L5 is
**not** Form I: it is an uncertified confluence slogan on the raw polygamma
branches.

---

## Detailed progress table

| Agent | Reached | Stopped at | Missing vs PRB | Proof used | Match to PRB answer? |
|---|---|---|---|---|---|
| **PRB closed form** | L7 | — | — | frozen scientific-line certificates, not this engine | **the target** |
| **Skill-1** | L0–L2 (ZERO), then `collect_common_factor` (ZERO; ops 3932→~1986) | 2 sums, still 2 `Piecewise` / 7 branches | L3 names only implicit; L4–L7 entirely absent | this engine `step` ZERO | **no**; first millimetres of the skeleton |
| **Skill-2** | L0–L2 (ZERO), same rewrite as Skill-1 | same as Skill-1 | same | `step` ZERO | **no**; same place |
| **Skill-3** | L0–L1 (inspect + `init-session --proposer-mode main`) | no candidate | L2–L7 | no `step` | **no** |
| **Blank-1** | L0, L2, L3 in Wolfram (`K2`,`K3`, `zP`/`zM`, still `Piecewise`) | collected polygamma rationals; kept coincidence branches | L4 master \(\Phi\); L5 \(H_1,H_2\) / \([w^2]\); L6–L7 | Wolfram `Together`/`Simplify` + 30-digit spots | **no**; closer *narrative* than Skill, different object |
| **Blank-2** | L0, L2, L3; **claimed** L5-style “drop every Piecewise” | \(P,Q=\psi(z_\pm)\) derivative kernels, not \(\mathfrak M,\mathfrak T\) | L4 as \(\Phi_\Gamma\); L5 generating functions; L6–L7; Kubo 3-point (self-reported missing) | `Simplify` / `Series` / `PossibleZeroQ` | **no**; slogan nearest to “one kernel, no Piecewise”, algebra is not Form I |
| **Blank-3** | L0, L2, L3; confluence as limits of generic \(K_2,K_3\) | rational polygamma \(K_2,K_3\) | L4–L7 | local SymPy coefficient cancellation | **no**; would not publish without a verifier |

Engine check of Blank-2’s “drop default `Piecewise` branch only” against the
Skill-1 certified 2-sum current: **UNKNOWN** (`TIME_BUDGET_EXCEEDED`). Not
promoted. So even the *weak* confluence rewrite is not a ZERO identity in
this verifier.

---

## Gap list (what nobody produced)

1. **Thermal master.** Nobody wrote \(\Phi_\Gamma(e)=\tfrac12+\frac{i}{\pi}\psi_0(z_+(e))\) and \(\Phi_\Gamma^\sharp=1-\Phi_\Gamma(2\mu-e)\) as the *only* thermal input.
2. **Generating functions.** Nobody defined \(\mathcal R_{1,\Gamma}(w;x,y)\) / \(\mathcal R_{2,\Gamma}(w;x,y,z)\) or extracted \(\mathfrak M=[w^2]\mathcal R_1\), \(\mathfrak T=[w^2]\mathcal R_2\).
3. **Hermite divided differences.** Nobody introduced \(H_1[f;u,v]\), \(H_2[f;u,v,r]\) as the confluence mechanism. Blank agents cancelled Laurent tails of the *raw* polygamma kernels instead.
4. **No-Piecewise theorem.** PRB: coincidences are Hermite limits of one object. Agents: either kept `Piecewise` (Skill, Blank-1) or deleted it by CAS/`Series` (Blank-2/3) without a ZERO residual here.
5. **Geometry.** Nobody replaced indexed \(h_1,h_2\) by \(\mathcal P,\mathcal L\) or the nine \(\mathcal G_\alpha\).
6. **Form II stratification.** The C3-indexed sums (\(n\), \(n\neq m\), triple-distinct, \(n=\ell\), etc.) with \(C_H,L_{2,\Re},P_{\Re},\ldots\) did not appear.

---

## How far is “closer”?

```text
raw Guo Piecewise
    → L2 two sums          Skill-1/2 CERTIFIED; Blank all reached
    → L3 named K2/K3       Blank only (uncertified)
    → L5 no Piecewise      Blank-2/3 claimed; engine UNKNOWN on a crude drop
    → L4+L5 𝔐, 𝔗          nobody
    → L6 𝒫, ℒ             nobody
    → L7 nine generators   PRB only
```

Skill arm: **correct, shallow.** Stops at certified linearity + common-factor
folding. Does not invent the closed form.

Blank arm: **directionally nearer to Form I’s two-kernel / confluence
story**, still a **different formula** (compressed Guo polygamma, not the
frozen master + divided-difference kernels), and **not** engine-certified.

**None of the six agents output the PRB final answer.**
