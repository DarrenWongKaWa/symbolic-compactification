# ac-r01-resolvent-hilbert-identity

**Title.** Hilbert first resolvent identity as Newton divided difference of the Green's operator

- domain: `green`
- proposed_ladder: `R2_newton_dd`
- rejected: `False`
- is_guo: `False`
- status: dossier only; not admitted to DEV

## Expression sketch

Convention (Wikipedia): R(z, A) = (A - z*I)**(-1). Identity on the resolvent set: R(z, A) - R(w, A) - (z - w)*R(z, A)*R(w, A) = 0. Newton quotient: (R(z, A) - R(w, A))/(z - w) = R(z, A)*R(w, A). Scalar check (A -> a): ((1/(a - z) - 1/(a - w))/(z - w) - 1/((a - z)*(a - w))). Confluent node: diff(R(z, A), z) = R(z, A)**2.

## Latent structure

First Newton divided difference of the resolvent (Green's operator) in the spectral parameter equals the product of resolvents. The repeated-node/Hermite case is the holomorphic derivative on the resolvent set. Same master object R(·, A) for generic and coincident spectral parameters.

## Public source

Wikipedia, Resolvent formalism, section Resolvent identity (https://en.wikipedia.org/wiki/Resolvent_formalism); Dunford-Schwartz Vol. I Lemma 6 p. 568; Kato, Perturbation Theory for Linear Operators (1980).

## ScientificAssumptionContract

### Symbol assumptions

- `z`: `{'complex': True}`
- `w`: `{'complex': True}`
- `a`: `{'complex': True, 'notes': 'scalar model of a spectral value of A'}`
- `A`: `{'type': 'closed operator / Banach-space operator'}`

### Function domains

- `R`: holomorphic on the resolvent set rho(A) = {zeta : (A - zeta I) invertible}

### Branch conventions

- Wikipedia defines R(z; A) = (A - z I)**(-1). Dunford-Schwartz (cited there) use (z I - A)**(-1), which flips the sign of Hilbert's identity. Keep one convention.

### Predicates (DECLARED / DERIVED / NOT_DECLARED)

#### nonzero_conditions

- **DECLARED.** (A - z I) is invertible, i.e. z belongs to rho(A)
  - source: Wikipedia Resolvent formalism, Resolvent identity: 'For all z, w in rho(A)'
- **DECLARED.** (A - w I) is invertible, i.e. w belongs to rho(A)
  - source: Wikipedia Resolvent formalism, Resolvent identity: 'For all z, w in rho(A)'

#### positivity_conditions

- (none)

#### analytic_domains

- **DECLARED.** z and w lie in the resolvent set rho(A); the first resolvent identity holds there
  - source: Wikipedia Resolvent formalism: 'For all z, w in rho(A), the first resolvent identity (also called Hilbert's identity) holds'
- **DECLARED.** The resolvent is an analytic (holomorphic-calculus) function of z off the spectrum
  - source: Wikipedia Resolvent formalism: resolvent 'captures the spectral properties of an operator in the analytic structure of the functional'; holomorphic functional calculus

#### limit_domains

- **DERIVED.** The z -> w limit of the Newton quotient is taken with z, w in rho(A) and equals the z-derivative of R
  - source: Holomorphy of R on rho(A) (declared) implies the difference quotient has a holomorphic continuation through z = w

#### derived_conditions

- **DERIVED.** On rho(A), dR/dz = R(z, A)**2 in the Wikipedia (A - z I)**(-1) convention
  - source: Divide Hilbert's identity by (z - w) and take z -> w using holomorphy on rho(A)

### Source provenance

- https://en.wikipedia.org/wiki/Resolvent_formalism
- Dunford, N. and Schwartz, J. T., Linear Operators, Part I General Theory, Wiley-Interscience, 1988, Lemma 6, p. 568
- Kato, T., Perturbation Theory for Linear Operators, 2nd ed., Springer, 1980, ISBN 0-387-07558-5
- Fredholm, E. I., Acta Mathematica 27 (1903) 365-390, doi:10.1007/bf02421317

## Why not CSE / LGG

CSE can share the product R(z)R(w) but does not identify the difference quotient as the first divided difference of a meromorphic master. First-order LGG antiunifies R(z)-R(w) as a binary template without nodes, reconstruction, or the confluent derivative at repeated spectral parameters.

## Proposer leak risk

Do not plant sealed-control gold names or 'divided difference' as a target label in proposer-visible text. Hilbert/resolvent identity is the public source name and may be stripped later. Keep Dunford vs Wikipedia sign convention out of the gold channel.

## Notes

Scalar specialization is SymPy-writable. Operator identity is the scientific object. Not the sealed G3 control. No beta/gamma positivity is used or inserted. Confluent member is R3_hermite_dd on the same F = R(·, A).
