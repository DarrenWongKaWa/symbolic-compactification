# ac-r05-lehmann-spectral-master

**Title.** Lehmann Hilbert-transform master unifying Matsubara and retarded Green functions

- domain: `green`
- proposed_ladder: `R6_master_object`
- rejected: `False`
- is_guo: `False`
- status: dossier only; not admitted to DEV

## Expression sketch

rho(k, omega) spectral density; G(k, z) = Integral(rho(k, x)/(-z + x), (x, -oo, oo))/(2*pi); Matsubara: G_M(k, omega_n) = G(k, I*omega_n) = Integral(rho/(-I*omega_n + x))/(2*pi); retarded: G_R(k, omega) = G(k, omega + I*eta), eta -> 0+; advanced: G_A uses -I*eta. Free specialization on the same page: G_M(k, omega_n) = 1/(-I*omega_n + xi(k)), G_R(k, omega) = 1/(-(omega + I*eta) + xi(k)).

## Latent structure

One Hilbert-transform master G(k, z) of the spectral density. Matsubara, retarded, and advanced Green functions are evaluations of the same F at i omega_n, omega+i eta, and omega-i eta. Poles of G_R (G_A) lie in the lower (upper) half-plane. This is a master analytic object, not CSE of two denominators.

## Public source

Wikipedia, Green's function (many-body theory), sections Basic definitions, Imaginary-time ordering and beta-periodicity, Spectral representation, Hilbert transform (https://en.wikipedia.org/wiki/Green%27s_function_(many-body_theory)).

## ScientificAssumptionContract

### Symbol assumptions

- `beta`: `{'real': True, 'notes': 'inverse temperature beta = 1/k_B T as written; T>0 is not inserted'}`
- `eta`: `{'real': True}`
- `omega`: `{'real': True}`
- `zeta`: `{'integer': True, 'notes': '+1 bosons, -1 fermions as written'}`
- `tau`: `{'real': True}`

### Function domains

- `G`: Hilbert transform G(k, z) = Integral rho(k, x)/(-z + x) dx/(2*pi)
- `G_R`: retarded propagator; all poles and discontinuities in the lower half-plane
- `G_A`: advanced propagator; all poles and discontinuities in the upper half-plane
- `G_M`: thermal/Matsubara propagator; poles and discontinuities on the imaginary omega_n axis
- `rho`: spectral density from Lehmann sum over many-body eigenstates

### Real-valued functions

`rho`

### Branch conventions

- omega_n = [2 n + theta(-zeta)] * pi / beta (Matsubara frequency as written on the page).
- zeta = +1 bosons, -1 fermions.
- Source sign: denominators are (-i omega_n + xi) and (-(omega + i eta) + xi), not the (i omega_n - xi) convention.

### Predicates (DECLARED / DERIVED / NOT_DECLARED)

#### nonzero_conditions

- (none)

#### positivity_conditions

- **DECLARED.** Imaginary-time arguments of the thermal Green function lie in the interval from 0 to beta
  - source: Wikipedia Green's function (many-body theory): tau_j 'are restricted to the range from 0 to the inverse temperature beta = 1/k_B T'
- **DECLARED.** Antiperiodicity/periodicity is stated for 0 < tau < beta
  - source: Wikipedia Green's function (many-body theory): G(tau - beta) = zeta G(tau) for 0 < tau < beta

#### analytic_domains

- **DECLARED.** G_R(omega) has all poles and discontinuities in the lower half-plane; G_A in the upper half-plane
  - source: Wikipedia Green's function (many-body theory), Spectral representation
- **DECLARED.** Thermal propagator G(omega_n) has all poles and discontinuities on the imaginary omega_n axis
  - source: Wikipedia Green's function (many-body theory), Spectral representation
- **DECLARED.** Master G(k, z) is the Hilbert transform of rho; G_M = G(k, i omega_n) and G_R = G(k, omega + i eta)
  - source: Wikipedia Green's function (many-body theory), Hilbert transform
- **DECLARED.** Free two-point functions are G_M = 1/(-i omega_n + xi_k) and G_R = 1/(-(omega + i eta) + xi_k)
  - source: Wikipedia Green's function (many-body theory), Basic definitions, sign/normalization note
- **DECLARED.** rho(k, omega) = 2 Im G_R(k, omega) via Sokhotski-Weierstrass as quoted on the page
  - source: Wikipedia Green's function (many-body theory), Spectral representation, Sokhatsky-Weierstrass citation

#### limit_domains

- **DECLARED.** eta -> 0+ is implied in the retarded spectral integral
  - source: Wikipedia Green's function (many-body theory): 'the limit as eta -> 0+ is implied'

#### derived_conditions

- (none)

### Source provenance

- https://en.wikipedia.org/wiki/Green%27s_function_(many-body_theory)

## Why not CSE / LGG

CSE can share 1/(-z + xi). LGG antiunifies two specializations. The scientific representation is one Hilbert-transform master with distinct evaluation points (Matsubara vs retarded vs advanced) and declared half-plane pole locations.

## Proposer leak risk

Do not plant sealed-control gold names. 'Lehmann', 'Hilbert transform', and 'analytic continuation' should not be planted as gold target names in proposer view.

## Notes

T > 0 is not inserted; beta appears as inverse temperature and as the length of the declared tau-interval. eta > 0 is not inserted beyond the declared eta -> 0+. Not the sealed G3 control. Polygamma thermal closed forms are out of scope (C2).
