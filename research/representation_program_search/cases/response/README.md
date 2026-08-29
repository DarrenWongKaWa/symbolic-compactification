# C3 — perturbation / response candidate dossiers

Owner: C3 (`cases/response/`).
Parent contracts: `5321eaa`.
Schema: `research/assumption_complete_representation/schema.py` (`CandidateDossier`).

Dossiers only. Not admitted to DEV/TEST. No search implementation.
Guo is sealed: every row has `is_guo=false`. No `Phi_Gamma`, no Hermite-on-Guo.

## Scope

Publicly documented **perturbative kernels**, **response coefficients**, **resolvent expansions**, and **degenerate denominators**, with analytic domains **written in the source** (not folklore `iε`).

Historical AC response identities are forbidden as headline cases (see `../../HISTORICAL_DIAGNOSTIC.md`): `ac-r01`–`ac-r08`, Lindhard, Lehmann, Lippmann–Schwinger as previously packaged, Kato simple eigenvalue, Sokhotski–Plemelj as previously packaged, Guo.

## Layout

```
cases/response/
  README.md
  index.json
  rps-r-*.json
```

## Counts

- candidates: 8
- rejected: 0
- `is_guo`: all false

| case_id | domain | ladder | latent structure | source |
|---|---|---|---|---|
| `rps-r-birman-schwinger-kernel` | perturbation | `R6_master_object` | compact free-resolvent kernel `K_λ`; bound states ↔ eigenvalue 1 | [Birman–Schwinger](https://en.wikipedia.org/wiki/Birman%E2%80%93Schwinger_principle); Birman 1961; Schwinger PNAS 1961 |
| `rps-r-krein-spectral-shift` | perturbation | `R6_master_object` | `ln Det(I+V R_0(z))` Cauchy master of `ξ`; Im `z` ≠ 0 | Yafaev [arXiv:math/0701301](https://arxiv.org/abs/math/0701301) Thm 2.1; Krein 1953 |
| `rps-r-feshbach-optical-heff` | perturbation | `R6_master_object` | Schur complement `(E-QHQ)^{-1}`; magnetic pole `B-B_0` | [Feshbach resonance](https://en.wikipedia.org/wiki/Feshbach_resonance); Feshbach Ann. Phys. 1958/1962 |
| `rps-r-faddeeva-plasma-z` | response | `R5_special_function` | Fried–Conte `Z` / Faddeeva `w`; integral for Im `z` > 0 | [Faddeeva function](https://en.wikipedia.org/wiki/Faddeeva_function); Fried–Conte 1961 |
| `rps-r-schrieffer-wolff-denom` | perturbation | `R2_newton_dd` | `S_{ij}=V_{ij}/(d_i-d_j)`; written `|V|≪|d_i-d_j|` | [Schrieffer–Wolff](https://en.wikipedia.org/wiki/Schrieffer%E2%80%93Wolff_transformation); PR 149 (1966) |
| `rps-r-fano-beutler-profile` | response | `R4_piecewise_unification` | `q`-family `(ε+q)^2/(ε^2+1)`; `E_res` in the continuum | [Fano resonance](https://en.wikipedia.org/wiki/Fano_resonance); Fano PR 124 (1961) |
| `rps-r-lorentz-causal-poles` | response | `R4_piecewise_unification` | Lorentz denominator; poles in Im `ω` < 0 if `γ>0` | [Lorentz oscillator](https://en.wikipedia.org/wiki/Lorentz_oscillator_model); [arXiv:2008.05546](https://arxiv.org/abs/2008.05546) |
| `rps-r-weyl-titchmarsh-m` | green | `R6_master_object` | Herglotz `M(z)` on `C\R`; Green from Wronskian of Weyl solutions | Clark–Gesztesy [arXiv:math/9905070](https://arxiv.org/abs/math/9905070) Thm 2.8 |

## Assumption policy

Labels are `DECLARED` | `DERIVED` | `NOT_DECLARED` only.
Physical folklore (`T>0`, `m>0`, `η>0` beyond a written inversion `ε↓0`) is not inserted.
Analytic domains are copied from the cited theorem/page, not from contour folklore.

## Distinct from historical AC response

- Not Hilbert first resolvent identity (`ac-r01` / `mp-resolvent-dd-01`).
- Not Sokhotski–Plemelj `1/z` (`ac-r02`).
- Not outgoing Helmholtz Green (`ac-r03`).
- Not Lindhard occupation DD (`ac-r04`).
- Not Lehmann spectral `G(z)` (`ac-r05`).
- Not Matsubara pole family (`ac-r06`).
- Not Lippmann–Schwinger `1/(E-H_0±iε)` (`ac-r07`).
- Not underspecified Kubo frequency (`ac-r08`).
- Not Kato simple-eigenvalue reduced resolvent (`mp-kato-simple-ev-01`).

Do not run admission. Do not add these to DEV.
