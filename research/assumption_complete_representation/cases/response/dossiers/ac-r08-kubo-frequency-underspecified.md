# ac-r08-kubo-frequency-underspecified

**Title.** Kubo linear-response commutator (frequency-domain analyticity not declared)

- domain: `response`
- proposed_ladder: `R6_master_object`
- rejected: `True` (`PROBLEM_UNDERSPECIFIED`)
- is_guo: `False`
- status: dossier only; not admitted to DEV

## Expression sketch

Time-domain Kubo (Wikipedia, general formula): <A(t)> = <A>_0 - (I/hbar)*Integral(<[A(t), V(t')]>_0, (t', t0, t)); H(t) = H0 + V(t)*Heaviside(t - t0); equilibrium trace uses rho_0 = exp(-beta*H0), beta = 1/k_B T. Desired but not on this page: retarded chi(omega + i0+) or a half-plane analyticity statement.

## Latent structure

Causal commutator kernel in time. A representation-discovery target in this line would be the retarded frequency kernel / spectral representation / i0+ boundary value of that commutator. Those analytic-domain hypotheses are not written on the cited Kubo page.

## Public source

Wikipedia, Kubo formula, General Kubo formula (https://en.wikipedia.org/wiki/Kubo_formula); Kubo, J. Phys. Soc. Jpn. 12, 570 (1957), doi:10.1143/JPSJ.12.570.

## ScientificAssumptionContract

### Symbol assumptions

- `t`: `{'real': True}`
- `t0`: `{'real': True}`
- `beta`: `{'real': True, 'notes': 'beta = 1/k_B T as written in the equilibrium trace; T>0 not inserted'}`
- `hbar`: `{'real': True}`

### Function domains

- `A`: observable whose equilibrium expectation is Tr[rho_0 A]/Z_0
- `V`: hermitian perturbation defined for all t

### Predicates (DECLARED / DERIVED / NOT_DECLARED)

#### nonzero_conditions

- (none)

#### positivity_conditions

- **DECLARED.** The perturbation is switched on after t0 via Heaviside theta(t - t0)
  - source: Wikipedia Kubo formula: H(t) = H0 + V(t) theta(t - t0)

#### analytic_domains

- **NOT_DECLARED.** Retarded frequency-domain response analytic in Im omega > 0
  - source: Wikipedia Kubo formula (general Kubo formula section) does not state a half-plane analyticity condition on chi(omega)
- **NOT_DECLARED.** i0+ (or omega + i eta, eta -> 0+) prescription for the Fourier transform of the causal commutator
  - source: Wikipedia Kubo formula general formula remains an integral over t' in [t0, t]; no Sokhotski/i0+ identity is declared there

#### limit_domains

- **NOT_DECLARED.** Fourier transform of the causal commutator to a retarded chi(omega)
  - source: Not stated in the Wikipedia general Kubo formula section used as the source

#### derived_conditions

- (none)

### Source provenance

- https://en.wikipedia.org/wiki/Kubo_formula
- Kubo, R., Statistical-Mechanical Theory of Irreversible Processes. I, J. Phys. Soc. Jpn. 12, 570-586 (1957), doi:10.1143/JPSJ.12.570

## Why not CSE / LGG

Even as a time-domain identity the structure is a causal commutator kernel, not CSE. The case is recorded because a verifier for a retarded frequency representation would need analytic-domain data the source does not declare.

## Proposer leak risk

Do not plant sealed-control gold names. Do not insert i0+, eta>0, or T>0 to rescue the frequency-domain reading of this page.

## Notes

Rejected as PROBLEM_UNDERSPECIFIED for the frequency-domain representation task: analytic-domain predicates a verifier needs are NOT_DECLARED. Time-domain causality and the equilibrium beta-trace ARE declared and must not be confused with i0+. T>0 is not inserted. Not the sealed G3 control. Do not backfill from Mahan/AGD.
