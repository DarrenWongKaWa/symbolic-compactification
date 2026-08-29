# ac-r02-sokhotski-plemelj-boundary

**Title.** Sokhotski-Plemelj retarded and advanced boundary values of 1/z

- domain: `response`
- proposed_ladder: `R4_piecewise_unification`
- rejected: `False`
- is_guo: `False`
- status: dossier only; not admitted to DEV

## Expression sketch

limit(1/(x + I*epsilon), epsilon -> 0+) = P(1/x) - I*pi*DiracDelta(x); limit(1/(x - I*epsilon), epsilon -> 0+) = P(1/x) + I*pi*DiracDelta(x); limit(1/(x - I*epsilon) - 1/(x + I*epsilon), epsilon -> 0+) = 2*I*pi*DiracDelta(x). Integral form: f continuous on R, a < 0 < b, limit(Integral(f(x)/(x +/- I*epsilon), (x, a, b)), epsilon -> 0+) = -/+ I*pi*f(0) + P*Integral(f(x)/x, (x, a, b)).

## Latent structure

Retarded and advanced distributional boundary values of the meromorphic master F(z)=1/z. Upper vs lower half-plane approaches unify as a piecewise/principal-value plus delta decomposition (R4) of one Cauchy kernel (R6).

## Public source

Wikipedia, Sokhotski-Plemelj theorem, real-line version (https://en.wikipedia.org/wiki/Sokhotski%E2%80%93Plemelj_theorem).

## ScientificAssumptionContract

### Symbol assumptions

- `x`: `{'real': True}`
- `epsilon`: `{'real': True}`
- `a`: `{'real': True}`
- `b`: `{'real': True}`

### Function domains

- `f`: complex-valued and continuous on the real line (real-line version)
- `phi`: analytic on the smooth closed simple curve C (plane version)

### Branch conventions

- P denotes Cauchy principal value.
- Upper-half-plane boundary value of 1/z corresponds to 1/(x + i0+); lower to 1/(x - i0+).

### Predicates (DECLARED / DERIVED / NOT_DECLARED)

#### nonzero_conditions

- (none)

#### positivity_conditions

- **DECLARED.** The approximating imaginary part tends to zero from above: epsilon -> 0+
  - source: Wikipedia Sokhotski-Plemelj theorem, Version for the real line: lim_{epsilon -> 0+} 1/(x +/- i epsilon)
- **DECLARED.** Integration limits satisfy a < 0 < b
  - source: Wikipedia Sokhotski-Plemelj theorem: 'a and b be real constants with a < 0 < b'

#### analytic_domains

- **DECLARED.** The Cauchy integral phi(z) = (1/(2*pi*I))*Integral(phi(zeta)/(zeta - z), C) is not evaluated for z on C; it defines analytic functions phi_i inside C and phi_e outside C
  - source: Wikipedia Sokhotski-Plemelj theorem, Statement of the theorem
- **DECLARED.** Real-line formulae are distributional/integral identities; the real-line version makes no use of analyticity of f
  - source: Wikipedia Sokhotski-Plemelj theorem: 'Note that this version makes no use of analyticity.'

#### limit_domains

- **DECLARED.** epsilon -> 0+ in the distributional sense against continuous f on [a, b]
  - source: Wikipedia Sokhotski-Plemelj theorem, real-line integral equalities
- **DECLARED.** Interior and exterior limits w -> z with z on C of phi_i and phi_e
  - source: Wikipedia Sokhotski-Plemelj theorem, plane version: lim_{w -> z} phi_i(w) and phi_e(w)

#### derived_conditions

- (none)

### Source provenance

- https://en.wikipedia.org/wiki/Sokhotski%E2%80%93Plemelj_theorem
- Sochocki, J. (1868); Plemelj, J. (1908), Riemann-Hilbert problem

## Why not CSE / LGG

CSE can share the 1/(x +/- i epsilon) kernel across retarded and advanced copies. LGG first-order antiunification does not reconstruct the principal-value plus delta decomposition or the interior/exterior Cauchy boundary values of a single 1/z master.

## Proposer leak risk

Do not plant sealed-control gold names. 'Sokhotski-Plemelj' and 'i0+' are source names; strip from proposer view if used as gold. Do not present the P + delta formula as a hidden target wording.

## Notes

Physics application on the same page writes the time-integral representation of 1/(E - i epsilon) with epsilon -> 0+. SymPy-writable as 1/(x + I*epsilon) before the distributional limit. Not the sealed G3 control.
