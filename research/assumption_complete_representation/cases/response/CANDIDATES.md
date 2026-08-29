# Response / Green candidates (C1)

Dossiers only. Not admitted. `is_guo=false` on every row.

| case_id | domain | ladder | rejected | latent structure | source |
|---|---|---|---|---|---|
| `ac-r01-resolvent-hilbert-identity` | green | `R2_newton_dd` | no | Newton DD of resolvent; confluent `R'=R^2` | [Resolvent formalism](https://en.wikipedia.org/wiki/Resolvent_formalism); Kato 1980; Dunford–Schwartz I Lemma 6 |
| `ac-r02-sokhotski-plemelj-boundary` | response | `R4_piecewise_unification` | no | UHP/LHP boundary values of `1/z`; P+δ | [Sokhotski–Plemelj](https://en.wikipedia.org/wiki/Sokhotski%E2%80%93Plemelj_theorem) |
| `ac-r03-helmholtz-outgoing-green` | green | `R5_special_function` | no | outgoing vs incoming spherical wave; Sommerfeld | [Sommerfeld radiation condition](https://en.wikipedia.org/wiki/Sommerfeld_radiation_condition) |
| `ac-r04-lindhard-occupation-dd` | response | `R2_newton_dd` | no | Fermi–Dirac Newton quotient; `q→0` derivative | [Lindhard theory](https://en.wikipedia.org/wiki/Lindhard_theory); Lindhard 1954 |
| `ac-r05-lehmann-spectral-master` | green | `R6_master_object` | no | Hilbert-transform master `G(z)` of `ρ` | [Green's function (many-body)](https://en.wikipedia.org/wiki/Green%27s_function_(many-body_theory)) |
| `ac-r06-matsubara-pole-family` | response | `R3_hermite_dd` | no | Matsubara pole order ↔ occupation DD/derivatives | [Matsubara summation](https://en.wikipedia.org/wiki/Matsubara_frequency) |
| `ac-r07-lippmann-schwinger-iepsilon` | perturbation | `R6_master_object` | no | causal free resolvent `1/(E-H0±iε)` | [Lippmann–Schwinger](https://en.wikipedia.org/wiki/Lippmann%E2%80%93Schwinger_equation); doi:10.1103/PhysRev.79.469 |
| `ac-r08-kubo-frequency-underspecified` | response | `R6_master_object` | **yes** `PROBLEM_UNDERSPECIFIED` | time-domain Kubo; frequency i0+ **not** declared | [Kubo formula](https://en.wikipedia.org/wiki/Kubo_formula); doi:10.1143/JPSJ.12.570 |

## Assumption policy

Labels are `DECLARED` | `DERIVED` | `NOT_DECLARED` only.
Physical folklore (`T>0`, `m>0`, `η>0` beyond a written `η→0+`) is not inserted.
`ac-r08` keeps the missing frequency-domain hypotheses as `NOT_DECLARED` and is
rejected; it is preserved, not deleted (`ADMISSION_GATE.md`).

## SymPy sketches

Scalar specializations intended as later engine input (not admitted here):

- `ac-r01`: `(1/(a-z)-1/(a-w))/(z-w) - 1/((a-z)*(a-w))`
- `ac-r02`: `1/(x + I*epsilon)` with `epsilon -> 0+`
- `ac-r03`: `exp(I*k*R)/(4*pi*R)` with `R=sqrt((x-x0)**2+...)`
- `ac-r04`: `(f(E1)-f(E2))/(hbar*(omega+I*delta)+E1-E2)`
- `ac-r05`: `1/(-(omega+I*eta)+xi)` and `1/(-I*omega_n+xi)`
- `ac-r06`: `1/(I*omega-xi)**n` and two-pole product
- `ac-r07`: `1/(E-E_beta+I*epsilon)`
- `ac-r08`: time-domain commutator integral (frequency form not sourced)
