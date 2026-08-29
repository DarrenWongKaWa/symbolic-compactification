# C4 — tensor / invariant candidate dossiers

Owner: C4 (`cases/tensor/`).
Contracts: `5321eaa`. Dossiers only. Not admitted to DEV/TEST.

Fresh published invariant-tensor, Young-adjacent, and irrep-reconstruction
identities with **explicit index domains**. JSON records are `CandidateDossier`
objects (same fields as the AC `schema.py` contract).

Guo is sealed. No Guo case, no search code.

## Forbidden as headline cases (see `../../HISTORICAL_DIAGNOSTIC.md`)

Do not resubmit renamed or symbol-permuted copies of:

`ac-t-eps-delta`, `ac-t-young-s3`, `ac-t-clebsch-half`, `ac-t-ricci-weyl`,
`ac-t-weyl-su2-char`, `ac-t-iso4-projectors`, `ac-t-pauli-completeness`,
`ac-t-rej-index-rename`.

Near-duplicates (same identity, renamed indices, 3D ε–δ specializations of
the 3D Levi-Civita product, S_3 Young on V^{⊗3}, 1/2⊗1/2 CG, 4D Ricci–Weyl
S+E+W, SU(2) Weyl character, SO(3) volumetric/deviatoric rank-4, Pauli Fierz)
are HISTORICAL_DIAGNOSTIC, never headline.

## Layout

```
cases/tensor/
  README.md
  index.json
  rps-t-*.json
```

## Counts

- candidates: 8
- rejected: 0
- `is_guo`: all false

| case_id | ladder | index domain | source |
|---|---|---|---|
| `rps-t-su3-gellmann-fierz` | R8 | color {1,2,3}, adjoint {1..8} | Wikipedia Gell-Mann Fierz; Haber 2021 eq. (6) |
| `rps-t-su3-d-contractions` | R8 | adjoint {1..8} | Macfarlane–Sudbery–Weisz 1968; Haber (26)–(27), (75)–(76) |
| `rps-t-su3-octet-projectors` | R8 | adjoint {1..8} | Wikipedia 8⊗8 CG; Macfarlane 1968; Haber N=3 |
| `rps-t-riemann-young-22` | R8 | {1..n}^4, n≥2 | Fiedler math/0212278; Fulling–King–Wybourne–Cummins 1992 |
| `rps-t-barnes-rivers-dn` | R8 | Lorentz {0..4}, d=5 | Barnes JMP 1965; Buchbinder–Shapiro n-dim 1/(d−1) |
| `rps-t-stf-son-rank3` | R8 | Cartesian {1..5}, n=5 | Toth–Turyshev arXiv:2109.11743; Thorne 1980 |
| `rps-t-weyl-selfdual-4d` | R8 | Euclidean {1..4} | Wikipedia Weyl C±; Singer–Thorpe 1969; AHS 1978 |
| `rps-t-dirac-gamma-completeness` | R8 | spinor {1..4}, μ∈{0..3} | Wikipedia Fierz / γ-matrices; Itzykson–Zuber A-2 |

Do not run admission. Do not add these to DEV. Do not implement search here.
