# ac-r03-helmholtz-outgoing-green

**Title.** 3D outgoing Helmholtz Green function selected by the Sommerfeld radiation condition

- domain: `green`
- proposed_ladder: `R5_special_function`
- rejected: `False`
- is_guo: `False`
- status: dossier only; not admitted to DEV

## Expression sketch

R = sqrt((x - x0)**2 + (y - y0)**2 + (z - z0)**2); u_plus = exp(I*k*R)/(4*pi*R); u_minus = exp(-I*k*R)/(4*pi*R); general combination u = c*u_plus + (1 - c)*u_minus. Only u_plus satisfies Sommerfeld: limit(|x|->oo, |x|**((n-1)/2)*(diff(u, |x|) - I*k*u)) = 0 for time-harmonic convention exp(-I*omega*t), n = 3, k > 0.

## Latent structure

Two specializations of the spherical-wave master exp(s*k*R)/(4*pi*R) with s = +/- I. Sommerfeld radiation (outgoing vs incoming) selects one member of the family. The singularity at R = 0 is the source point, not a CSE of the denominator.

## Public source

Wikipedia, Sommerfeld radiation condition (https://en.wikipedia.org/wiki/Sommerfeld_radiation_condition); Sommerfeld, Partial Differential Equations in Physics (1949).

## ScientificAssumptionContract

### Symbol assumptions

- `k`: `{'real': True, 'positive': True}`
- `n`: `{'integer': True}`
- `x`: `{'real_vector': True, 'dimension': 'n'}`
- `x0`: `{'real_vector': True, 'dimension': 'n'}`
- `c`: `{'complex': True}`

### Function domains

- `u`: radiating solution of Helmholtz on R^n, n in {2, 3}
- `f`: given compactly supported source

### Branch conventions

- |x - x0| is the Euclidean distance (nonnegative square root).
- Outgoing spherical wave is exp(+i k R) for the exp(-i omega t) convention.

### Predicates (DECLARED / DERIVED / NOT_DECLARED)

#### nonzero_conditions

- **DECLARED.** Classical pointwise formula is written with |x - x0| in the denominator (R != 0)
  - source: Wikipedia Sommerfeld radiation condition: u_pm(x) = exp(+/- i k |x-x0|)/(4*pi*|x-x0|)

#### positivity_conditions

- **DECLARED.** Wave number k > 0
  - source: Wikipedia Sommerfeld radiation condition: 'k > 0 is a constant, called the wave number'

#### analytic_domains

- **DECLARED.** Inhomogeneous Helmholtz (nabla^2 + k^2) u = -f in R^n for n = 2, 3, with f of compact support
  - source: Wikipedia Sommerfeld radiation condition, Formulation
- **DECLARED.** Radiating solutions satisfy the Sommerfeld radiation condition uniformly in direction x/|x|
  - source: Wikipedia Sommerfeld radiation condition: lim_{|x|->oo} |x|^{(n-1)/2} (d/d|x| - i k) u(x) = 0
- **DECLARED.** Time-harmonic convention is exp(-i omega t); the opposite convention replaces -i by +i in Sommerfeld
  - source: Wikipedia Sommerfeld radiation condition, Formulation, last paragraph
- **DECLARED.** Of the family u = c u_+ + (1-c) u_-, only u_+ is radiating for the stated Sommerfeld sign
  - source: Wikipedia Sommerfeld radiation condition: 'Of all these solutions, only u_+ satisfies the Sommerfeld radiation condition'

#### limit_domains

- **DECLARED.** |x| -> infinity uniformly in all directions, with the Sommerfeld operator (d/d|x| - i k)
  - source: Wikipedia Sommerfeld radiation condition: limit as |x| -> oo uniformly in direction

#### derived_conditions

- (none)

### Source provenance

- https://en.wikipedia.org/wiki/Sommerfeld_radiation_condition
- Sommerfeld, A., Partial Differential Equations in Physics, Academic Press, 1949
- Jackson, J. D., Classical Electrodynamics, outgoing Helmholtz Green function G_k = exp(i k |x-x'|)/(4*pi*|x-x'|)

## Why not CSE / LGG

CSE shares |x-x0| in the two spherical waves. LGG antiunifies exp(+/- i k R)/R as a first-order template with a sign hole. The scientific representation is radiation selection of one member of a two-point family, not a common subexpression.

## Proposer leak risk

Do not plant sealed-control gold names. 'Sommerfeld', 'outgoing', and 'Hankel' should not appear as gold target wording in a later proposer view.

## Notes

Normalization follows the cited Sommerfeld Wikipedia page (no overall minus). Jackson's (nabla^2 + k^2) G = -delta uses G = exp(i k R)/(4*pi*R). Limiting absorption Im k > 0 is not used: it is not written on the cited page and is not inserted. Real k > 0 plus Sommerfeld is the declared uniqueness condition. Not the sealed G3 control.
