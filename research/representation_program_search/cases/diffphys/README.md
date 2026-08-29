# Differentiable physics / SciML candidate dossiers (C5)

Dossiers only. No search code. No DEV admission. Guo is not a case here.

Historical AC SciML identities are **forbidden** as headline cases
(`../HISTORICAL_DIAGNOSTIC.md`): sciml-phi-hermite, vanloan, daleckii,
adjoint-linear, ou-mehler, deq-ift, tweedie, lyapunov-kronecker.

| case_id | ladder | topic | source |
|---|---|---|---|
| `rps-dp-relton-second-frechet` | R6 | 4n block-exp of mixed second Frechet of exp; not 2n Van Loan/Mathias | Higham–Relton, SIMAX 35 (2014) Thm 3.5 |
| `rps-dp-skaflestad-wright-phisq` | R5 | phi double-angle recurrence; not `phi_k = exp[0^{(k)}, z]` | Skaflestad–Wright, Appl. Numer. Math. 59 (2009); EXPINT |
| `rps-dp-dexpinv-bernoulli` | R6 | dexpinv Bernoulli–ad series / Magnus; inverse of L_exp, not the Duhamel block | Iserles–Munthe-Kaas–Nørsett–Zanna, Acta Numer. 9 (2000) |
| `rps-dp-liouville-jacobi-cnf` | R6 | det Φ = exp ∫ tr A; Jacobi; CNF instantaneous CoV | Hartman; Higham Thm 1.13(c); Chen et al. 2018; FFJORD |
| `rps-dp-rodrigues-so3-dexp` | R4 | Rodrigues + Gallego–Yezzi dR + left Jacobian; θ=0 unification | Gallego–Yezzi, JMIV 51 (2015); Murray–Li–Sastry |
| `rps-dp-stm-sensitivity-kernel` | R6 | two-time STM: composition, mixed partials, forward sensitivity kernel | Rugh Ch. 9; Hairer–Nørsett–Wanner I.14 |
| `rps-dp-cossin-oscillator-prop` | R4 | oscillator propagator as exp(t companion); ω=0 sinc confluence | Higham Ch. 12; Hairer–Lubich–Wanner XIII |

Each case is a `CandidateDossier` JSON. Analytic-domain predicates a
verifier would need are labeled DECLARED or DERIVED from the cited
source only. No Guo. No parser extension. Not admitted here.
