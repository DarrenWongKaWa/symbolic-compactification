# ac-r07-lippmann-schwinger-iepsilon

**Title.** Lippmann-Schwinger perturbative resolvent with causal plus/minus i epsilon

- domain: `perturbation`
- proposed_ladder: `R6_master_object`
- rejected: `False`
- is_guo: `False`
- status: dossier only; not admitted to DEV

## Expression sketch

Naive: psi = phi + 1/(E - H0) * V * psi  (singular because E is an eigenvalue of H0). Causal regularization: psi_pm = phi + 1/(E - H0 +/- I*epsilon) * V * psi_pm. Spectral form: psi_pm = phi + Integral(|phi_beta> / (E - E_beta +/- I*epsilon) * <phi_beta|V|psi_pm>, beta). T-matrix form: psi_alpha_pm = phi_alpha + Integral(T_beta_alpha_pm * |phi_beta> / (E_alpha - E_beta +/- I*epsilon), beta).

## Latent structure

Perturbative energy denominators are evaluations of the free resolvent G0(zeta) = 1/(zeta - H0) at zeta = E +/- i epsilon. In (+) and out (-) are two members of that master resolvent family. The unregularized pole E = E_beta is declared singular; i epsilon is the causal (limiting-absorption) regularization, not a CSE of 1/(E - E_beta).

## Public source

Wikipedia, Lippmann-Schwinger equation (https://en.wikipedia.org/wiki/Lippmann%E2%80%93Schwinger_equation); Lippmann and Schwinger, Phys. Rev. 79, 469 (1950), doi:10.1103/PhysRev.79.469.

## ScientificAssumptionContract

### Symbol assumptions

- `E`: `{'real': True, 'notes': 'eigenvalue of H0 as written'}`
- `epsilon`: `{'notes': 'appears as +/- i epsilon in the resolvent; positivity inequality not extra-inserted'}`
- `H0`: `{'type': 'free Hamiltonian with known eigenvectors'}`
- `V`: `{'type': 'interaction / scattering potential'}`

### Function domains

- `G0_pm`: free resolvent 1/(E - H0 +/- i epsilon)
- `phi`: eigenfunction of H0: H0|phi> = E|phi>
- `psi_pm`: in (+) / out (-) Lippmann-Schwinger states

### Branch conventions

- Plus i epsilon vs minus i epsilon labels in vs out states as written: psi^(+/-) = phi + 1/(E - H0 +/- i epsilon) V psi^(+/-).
- +i epsilon in the Lippmann-Schwinger kernel is the outgoing/causal choice in the page's opening formula.

### Predicates (DECLARED / DERIVED / NOT_DECLARED)

#### nonzero_conditions

- **DECLARED.** E - H0 is singular because E is an eigenvalue of H0; the naive resolvent 1/(E - H0) is not used
  - source: Wikipedia Lippmann-Schwinger equation, Derivation: 'However E - H0 is singular since E is an eigenvalue of H0'

#### positivity_conditions

- (none)

#### analytic_domains

- **DECLARED.** The singularity is eliminated in two ways by making the denominator slightly complex: E - H0 +/- i epsilon
  - source: Wikipedia Lippmann-Schwinger equation, Derivation
- **DECLARED.** i epsilon is required for causality, ensuring scattered waves consist only of outgoing waves; made rigorous by the limiting absorption principle
  - source: Wikipedia Lippmann-Schwinger equation, opening definition paragraph
- **DECLARED.** psi^(+) is the in state (matches free data in the infinite past); psi^(-) is the out state (infinite future). Energy-contour for wavepackets: late-time contour closed in the lower half-plane; early-time in the upper half-plane
  - source: Wikipedia Lippmann-Schwinger equation, Interpretation as in and out states / A contour integral

#### limit_domains

- **DECLARED.** Wave-packet identification psi^{-}=phi at t -> +oo and psi^{+}=phi at t -> -oo uses contours closed according to exp(-i E t)
  - source: Wikipedia Lippmann-Schwinger equation, A contour integral

#### derived_conditions

- (none)

### Source provenance

- https://en.wikipedia.org/wiki/Lippmann%E2%80%93Schwinger_equation
- Lippmann, B. A. and Schwinger, J., Phys. Rev. 79, 469 (1950), doi:10.1103/PhysRev.79.469

## Why not CSE / LGG

CSE shares the energy denominator across partial waves. LGG antiunifies two Born terms. The scientific object is a causal resolvent master with declared in/out half-planes and a declared singularity of the unregularized 1/(E-H0).

## Proposer leak risk

Do not plant sealed-control gold names. 'Limiting absorption' and 'T-matrix' should not be planted as gold names. Do not import sealed-control i0+ folklore.

## Notes

epsilon > 0 is not inserted as a standalone inequality; the source writes +/- i epsilon and 'slightly complex' plus limiting absorption. Not the sealed G3 control. Scalar model 1/(E - E_beta + I*epsilon) is SymPy-writable.
