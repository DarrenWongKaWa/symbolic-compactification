# Thermal / special-function candidate dossiers (C2)

RPS v1 miners. Dossiers only; not admitted DEV/TEST. Guo is not a case.
Parent contracts: `5321eaa`. Own directory only.

AC thermal-01–thermal-08 are HISTORICAL_DIAGNOSTIC. These eight identities
are new published equations with written domains. They are not the
Fermi/Bose Im-digamma pair (DLMF 5.4.16–5.4.17), not trigamma series
5.15.1, not coth Matsubara 4.36.3, and not polylog Fermi-Dirac 25.12.14–16.

| case_id | ladder | rejected | source |
|---|---|---|---|
| `thermal-09-digamma-recurrence` | R2 | no | DLMF 5.5.2 |
| `thermal-10-polygamma-recurrence` | R3 | no | DLMF 5.15.5 |
| `thermal-11-gauss-multiplication-psi` | R7 | no | DLMF 5.5.9 |
| `thermal-12-bose-kernel-integral` | R5 | no | DLMF 5.9.12 |
| `thermal-13-alternating-fermi-series` | R5 | no | DLMF 5.7.7 |
| `thermal-14-hurwitz-polygamma` | R6 | no | DLMF 25.11.12 |
| `thermal-15-theta-modular-heat` | R8 | no | DLMF 20.7.32 |
| `thermal-16-gamma-cosh-modulus` | R5 | no | DLMF 5.4.4 |

Each case is a `CandidateDossier` JSON. Analytic-domain predicates a
verifier would need are labeled DECLARED / DERIVED from the cited source
only. Pole/cut exclusion is never imported from Guo. Physical folklore
(T>0) is not inserted unless the source writes it (here: Re z>0, Re a>0,
Im tau>0, y real).
