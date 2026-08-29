# Thermal / many-body candidate dossiers (C2)

Dossiers only. No DEV admission. Guo is not a case here.

| case_id | ladder | rejected | source |
|---|---|---|---|
| `thermal-01-fermi-im-digamma` | R5 | no | DLMF 5.4.17 |
| `thermal-02-bose-im-digamma` | R5 | no | DLMF 5.4.16 |
| `thermal-03-digamma-reflection` | R6 | no | DLMF 5.5.4 |
| `thermal-04-coth-matsubara` | R5 | no | DLMF 4.36.3 |
| `thermal-05-trigamma-double-pole` | R5 | no | DLMF 5.15.1 |
| `thermal-06-fermi-dirac-polylog` | R1 | no | DLMF 25.12.14–16 |
| `thermal-07-green-spectral-hilbert` | R6 | no | Wikipedia many-body Green |
| `thermal-08-matsubara-newton-dd-underspecified` | R2 | **yes** PROBLEM_UNDERSPECIFIED | Wikipedia Matsubara table |

Each case is a `CandidateDossier` JSON plus a markdown note. Analytic-domain predicates that a verifier would need are labeled DECLARED / DERIVED / NOT_DECLARED from the cited source only. Pole-exclusion is never imported from Guo.
