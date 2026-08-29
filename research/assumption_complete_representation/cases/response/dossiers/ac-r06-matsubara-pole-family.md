# ac-r06-matsubara-pole-family

**Title.** Matsubara sums of simple and repeated Green poles as an occupation Newton/Hermite family

- domain: `response`
- proposed_ladder: `R3_hermite_dd`
- rejected: `False`
- is_guo: `False`
- status: dossier only; not admitted to DEV

## Expression sketch

S_eta = (1/beta)*Sum(g(I*omega_n), n); bosonic omega_n = 2*n*pi/beta; fermionic omega_n = (2*n + 1)*pi/beta; n integer. Table (eta = +1 bosons, -1 fermions): g = (I*omega - xi)**(-1) -> S = -eta*n_eta(xi); g = (I*omega - xi)**(-2) -> S = -eta*diff(n_eta(xi), xi) = beta*n_eta(xi)*(eta + n_eta(xi)); g = (I*omega - xi)**(-n) -> S = -eta/(n-1)! * diff(n_eta(xi), xi, n-1); g = 1/((I*omega - xi1)*(I*omega - xi2)) -> S = -eta*(n_eta(xi1) - n_eta(xi2))/(xi1 - xi2). n_F(z) = 1/(exp(beta*z) + 1); n_B(z) = 1/(exp(beta*z) - 1).

## Latent structure

Parameterized family of Matsubara pole orders (R1). Distinct poles reconstruct the first Newton divided difference of the occupation n_eta. Repeated poles reconstruct derivatives (Hermite/repeated-node DD) of the same occupation master. The two-pole and one-pole-squared rows are generic vs confluent members, not CSE.

## Public source

Wikipedia, Matsubara summation (redirect from Matsubara frequency), sections Summation formalism and Table of Matsubara frequency summations (https://en.wikipedia.org/wiki/Matsubara_frequency).

## ScientificAssumptionContract

### Symbol assumptions

- `beta`: `{'real': True, 'notes': 'period of imaginary time; beta = hbar / k_B T as written; T>0 not inserted'}`
- `n`: `{'integer': True}`
- `eta`: `{'integer': True, 'notes': 'statistical sign +1 boson / -1 fermion as written'}`
- `xi`: `{'complex': True, 'notes': 'pole location of g; reality not extra-inserted'}`
- `xi1`: `{'complex': True}`
- `xi2`: `{'complex': True}`
- `tau`: `{'real': True}`

### Function domains

- `g`: meromorphic; contour argument treats poles of g as distinct from Matsubara poles of h_eta (Fig. 1-2 on the page)
- `n_F`: Fermi-Dirac n_F(z) = (exp(beta z) + 1)**(-1)
- `n_B`: Bose-Einstein n_B(z) = (exp(beta z) - 1)**(-1)
- `h_eta`: Matsubara weighting function with simple poles at z = i omega_n

### Branch conventions

- eta = +1 bosons, eta = -1 fermions.
- Occupation n_eta is n_B for eta = +1 and n_F for eta = -1 as in the table.

### Predicates (DECLARED / DERIVED / NOT_DECLARED)

#### nonzero_conditions

- **DECLARED.** Two-pole table row is written with denominator (xi1 - xi2); the repeated-pole rows are listed separately
  - source: Wikipedia Matsubara summation, Table of Matsubara frequency summations

#### positivity_conditions

- **DECLARED.** For Green-function applications, 0 < tau < beta is used to choose the weighting function that controls left-half-plane convergence
  - source: Wikipedia Matsubara summation, Choice of Matsubara weighting function: 'g(z) = G(z) exp(-z tau), which diverges in the left half plane given 0 < tau < beta'

#### analytic_domains

- **DECLARED.** Bosonic frequencies omega_n = 2 n pi / beta and fermionic omega_n = (2 n + 1) pi / beta, n in Z, enforce periodic/antiperiodic boundary conditions on phi(tau)
  - source: Wikipedia Matsubara summation, opening definition
- **DECLARED.** The sum is replaced by a contour integral against h_eta that has simple poles at z = i omega_n; the contour is then deformed to the poles of g
  - source: Wikipedia Matsubara summation, General formalism (Fig. 1 and Fig. 2)
- **DECLARED.** h_B^{(1)} controls convergence in Re z < 0; h_B^{(2)} in Re z > 0 (and analogously for fermions)
  - source: Wikipedia Matsubara summation, Choice of Matsubara weighting function
- **DECLARED.** Summation converges if g(z = i omega) tends to 0 as z -> oo faster than z**(-1); otherwise the result may depend on the weighting-function choice (table notes)
  - source: Wikipedia Matsubara summation, opening paragraph and table footnote 1

#### limit_domains

- **DECLARED.** Zero-temperature limit is written as beta -> oo, converting the Matsubara sum into an imaginary-frequency integral
  - source: Wikipedia Matsubara summation, Zero temperature limit: 'In this limit beta -> oo'

#### derived_conditions

- **DERIVED.** The (i omega - xi)**(-2) row is the xi1 -> xi2 confluent limit of the two-pole Newton quotient of n_eta
  - source: Table lists both 1/((i omega-xi1)(i omega-xi2)) and (i omega-xi)**(-2) with S = -eta n_eta'(xi)

### Source provenance

- https://en.wikipedia.org/wiki/Matsubara_frequency
- https://en.wikipedia.org/wiki/Matsubara_summation

## Why not CSE / LGG

CSE shares (i omega - xi) factors. LGG antiunifies two rational summands. The scientific family is occupation Newton/Hermite divided differences indexed by pole multiplicity, with declared contour half-planes and 0 < tau < beta.

## Proposer leak risk

Do not plant sealed-control gold names, or 'Newton DD of n_F' as proposer gold. Table closed forms n_eta, n_eta' must not be the only hidden target wording. Leave polygamma identities unnamed (C2).

## Notes

Finite-T Green/response, not a thermal polygamma compactification. T > 0 is not inserted; 0 < tau < beta is the declared interval. Not the sealed G3 control.
