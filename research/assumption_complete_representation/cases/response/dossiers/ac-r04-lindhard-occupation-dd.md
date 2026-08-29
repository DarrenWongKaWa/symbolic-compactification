# ac-r04-lindhard-occupation-dd

**Title.** Lindhard density-response kernel as Fermi-Dirac Newton divided difference

- domain: `response`
- proposed_ladder: `R2_newton_dd`
- rejected: `False`
- is_guo: `False`
- status: dossier only; not admitted to DEV

## Expression sketch

chi(q, omega) = Sum((f(E(k + q)) - f(E(k))) / (hbar*(omega + I*delta) + E(k + q) - E(k)), k); E(k) = hbar**2 * k**2 / (2*m); f = Fermi-Dirac in thermodynamic equilibrium; delta is a positive infinitesimal. Static: chi(q, 0) = Sum((f(E(k+q)) - f(E(k))) / (E(k+q) - E(k)), k). Long wavelength: f(E(k+q)) - f(E(k)) ~ q · nabla_k f, E(k+q) - E(k) ~ hbar**2 * k·q / m. T = 0: f(k) = Heaviside(kF - |k|).

## Latent structure

The occupation numerator over the energy denominator is the first Newton divided difference of f along the pair (E(k), E(k+q)), evaluated in a retarded i delta prescription. The q -> 0 (repeated-node) stratum replaces the quotient by nabla_k f, i.e. a derivative of the same master occupation. Piecewise generic vs long-wavelength unification, not CSE of the two Fermi factors.

## Public source

Wikipedia, Lindhard theory (https://en.wikipedia.org/wiki/Lindhard_theory); Lindhard, Mat.-Fys. Medd. Dan. Vid. Selsk. 28, 8 (1954).

## ScientificAssumptionContract

### Symbol assumptions

- `hbar`: `{'real': True, 'notes': 'appears as written in the kernel'}`
- `omega`: `{'real': True, 'notes': 'frequency argument of chi; i delta is written separately'}`
- `delta`: `{'real': True, 'positive': True, 'infinitesimal': True}`
- `m`: `{'real': True, 'notes': 'electron mass as written in E_k = hbar^2 k^2 / 2m; positivity not added'}`
- `kF`: `{'real': True, 'notes': 'Fermi wave vector in the T = 0 section'}`

### Function domains

- `f`: Fermi-Dirac distribution for electrons in thermodynamic equilibrium; at T = 0, Heaviside(kF - |k|)
- `E`: kinetic energy E(k) = hbar**2 * k**2 / (2*m)
- `chi`: Lindhard density-response function of (q, omega)

### Real-valued functions

`E`

### Branch conventions

- Candidate expression is the k-sum kernel, not the T = 0 closed form F(x) with log|...|. That closed form uses absolute values (real restriction); a complex log branch is not taken from the source.

### Predicates (DECLARED / DERIVED / NOT_DECLARED)

#### nonzero_conditions

- **DECLARED.** Generic summand denominator hbar*(omega + i delta) + E(k+q) - E(k); static omega + i delta -> 0 leaves E(k+q) - E(k)
  - source: Wikipedia Lindhard theory, Lindhard function and Static limit

#### positivity_conditions

- **DECLARED.** delta is a positive infinitesimal constant
  - source: Wikipedia Lindhard theory: 'delta is a positive infinitesimal constant'

#### analytic_domains

- **DECLARED.** Retarded frequency argument is written as omega + i delta with delta a positive infinitesimal
  - source: Wikipedia Lindhard theory: chi(q, omega) has hbar (omega + i delta) in the denominator
- **DECLARED.** At T = 0, f_k = Theta(kF - |k|); the sum is then evaluated 'in the continuous limit using analytic continuation'
  - source: Wikipedia Lindhard theory, Zero temperature functions

#### limit_domains

- **DECLARED.** Long-wavelength limit q -> 0 with f_{k+q} - f_k ~ q · nabla_k f_k and E_{k+q} - E_k ~ hbar^2 k·q / m, then delta -> 0
  - source: Wikipedia Lindhard theory, Long wavelength limit / Derivation in 3D
- **DECLARED.** Static limit written as omega + i delta -> 0
  - source: Wikipedia Lindhard theory, Static limit: 'Consider the static limit (omega + i delta -> 0)'

#### derived_conditions

- **DERIVED.** In the q -> 0 static stratum the occupation quotient becomes a derivative of f (repeated energy node)
  - source: Declared Taylor replacements f_{k+q}-f_k ~ q·nabla_k f and E_{k+q}-E_k ~ hbar^2 k·q / m

### Source provenance

- https://en.wikipedia.org/wiki/Lindhard_theory
- Lindhard, J., On the properties of a gas of charged particles, Kgl. Danske Videnskab. Selskab, Mat.-Fys. Medd. 28, no. 8 (1954)

## Why not CSE / LGG

CSE sees two Fermi factors and a shared energy denominator. LGG would antiunify chi at two momenta. The latent object is the Newton quotient of f at the pair of band energies, with a declared retarded i delta and a declared derivative stratum at q -> 0.

## Proposer leak risk

Do not plant sealed-control gold names, or 'divided difference of the Fermi function' as proposer gold. 'Lindhard function' is a public name and should be stripped from proposer view if used as a target.

## Notes

T > 0 is not written as an inequality on the general kernel and is not inserted. m > 0 is not inserted. Do not use the T = 0 log-abs closed form as the expression to certify in C: its complex branch is not declared. Candidate is the sum kernel. Not the sealed G3 control. Finite-T polygamma masters are left to C2; this is a response bubble.
