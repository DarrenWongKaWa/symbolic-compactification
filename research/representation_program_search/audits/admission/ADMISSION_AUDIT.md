# Representation-search admission audit

Audit version: `rps-admission-audit-v1`

Input tree SHA-256: `68ce6d78505e2bb3fe426215839bebc3a84701d4ce8f8f9b059e93d91badebe5`

Review policy SHA-256: `505a9d7127477cf0d5201ec507845cf2892c3c12a06a00f6fe5be3fc71b24a73`

This is an admission audit, not a benchmark split or scientific result. It does not edit dossiers, change the grammar/parser/verifier, or admit any case.

## Outcome

Audited 39 non-skeptic dossiers. `expression_sketch` is context only; it is never accepted as a machine expression. No dossier supplies an explicit admission package of parseable member and obligation files, and no cited source is frozen as a repository artifact with a source reference.

| status | count |
|---|---:|
| `ADMISSION_CANDIDATE` | 0 |
| `PACKAGING_GAP` | 27 |
| `PROBLEM_UNDERSPECIFIED` | 1 |
| `DUPLICATE_REVIEW` | 8 |
| `REJECT` | 3 |

`DUPLICATE_REVIEW` and `REJECT` have precedence over packaging so those problems remain visible even though the corresponding dossiers also lack machine packages. `PROBLEM_UNDERSPECIFIED` is reserved for verifier-domain assumptions, not proof gaps.

## Depth audit

| assessment | count |
|---|---:|
| `PLAUSIBLE` | 34 |
| `NEEDS_DOWNGRADE` | 3 |
| `NOT_OPERATIONAL_AT_PROPOSED_DEPTH` | 2 |

Depth is an admission plausibility judgment, never a certified representation result. A `PLAUSIBLE` R-level still requires a complete program and ZERO obligations.

## Per-case decisions

| case | cluster | primary status | proposed -> audited | parser fit | key issue |
|---|---|---|---|---|---|
| `mx-ab-ba-functional-01` | matrix | `PACKAGING_GAP` | R6_master_object -> R6 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `mx-geometric-mean-riccati-01` | matrix | `PACKAGING_GAP` | R6_master_object -> R6 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `mx-hadamard-ad-01` | matrix | `PACKAGING_GAP` | R6_master_object -> R6 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `mx-kronecker-exp-01` | matrix | `PACKAGING_GAP` | R6_master_object -> R6 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `mx-log-richter-01` | matrix | `PACKAGING_GAP` | R6_master_object -> R5 (NEEDS_DOWNGRADE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `mx-polar-psd-sqrt-01` | matrix | `PACKAGING_GAP` | R4_piecewise_unification -> R4 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `mx-rodrigues-so3-01` | matrix | `DUPLICATE_REVIEW` | R4_piecewise_unification -> R4 (PLAUSIBLE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | DUPLICATE_WITH:rps-dp-rodrigues-so3-dexp |
| `mx-sign-sqrt-block-01` | matrix | `PACKAGING_GAP` | R6_master_object -> R6 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `rps-dp-cossin-oscillator-prop` | diffphys | `PACKAGING_GAP` | R4_piecewise_unification -> R4 (PLAUSIBLE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `rps-dp-dexpinv-bernoulli` | diffphys | `PACKAGING_GAP` | R6_master_object -> R6 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `rps-dp-liouville-jacobi-cnf` | diffphys | `PACKAGING_GAP` | R6_master_object -> R6 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `rps-dp-relton-second-frechet` | diffphys | `DUPLICATE_REVIEW` | R6_master_object -> R6 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | DUPLICATE_WITH:mp-mathias-block-01 |
| `rps-dp-rodrigues-so3-dexp` | diffphys | `DUPLICATE_REVIEW` | R4_piecewise_unification -> R4 (PLAUSIBLE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | DUPLICATE_WITH:mx-rodrigues-so3-01 |
| `rps-dp-skaflestad-wright-phisq` | diffphys | `DUPLICATE_REVIEW` | R5_special_function -> R5 (PLAUSIBLE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | DUPLICATE_WITH:sciml-phi-hermite-01 |
| `rps-dp-stm-sensitivity-kernel` | diffphys | `PACKAGING_GAP` | R6_master_object -> R6 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `rps-r-birman-schwinger-kernel` | response | `PROBLEM_UNDERSPECIFIED` | R6_master_object -> R6 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | MANUAL_ASSUMPTION_GAP:The dossier says only 'regularity assumptions on V' for boundedness and compactness, without declaring a concrete potential c... |
| `rps-r-faddeeva-plasma-z` | response | `PACKAGING_GAP` | R5_special_function -> R5 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `rps-r-fano-beutler-profile` | response | `REJECT` | R4_piecewise_unification -> R1 (NOT_OPERATIONAL_AT_PROPOSED_DEPTH) | `REPRESENTABLE_AFTER_PACKAGING` | HARD_REJECT:The dossier's scientific formula is explicitly approximate, and its claimed R4 structure is only a q-parameter family plus a rescaled \... |
| `rps-r-feshbach-optical-heff` | response | `PACKAGING_GAP` | R6_master_object -> R6 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `rps-r-krein-spectral-shift` | response | `PACKAGING_GAP` | R6_master_object -> R6 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `rps-r-lorentz-causal-poles` | response | `REJECT` | R4_piecewise_unification -> R1 (NOT_OPERATIONAL_AT_PROPOSED_DEPTH) | `REPRESENTABLE_AFTER_PACKAGING` | HARD_REJECT:Thomson, Rayleigh, and resonant 'regimes' are asymptotic dominance statements, not exact Piecewise-equal branches. The proposed R4 obli... |
| `rps-r-schrieffer-wolff-denom` | response | `REJECT` | R2_newton_dd -> R2 (PLAUSIBLE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | HARD_REJECT:The displayed effective Hamiltonian is truncated at O(V^3). This experiment explicitly excludes a remainder-certification line, and an ... |
| `rps-r-weyl-titchmarsh-m` | response | `PACKAGING_GAP` | R6_master_object -> R6 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `rps-t-barnes-rivers-dn` | tensor | `PACKAGING_GAP` | R8_invariant_generator -> R8 (PLAUSIBLE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `rps-t-dirac-gamma-completeness` | tensor | `DUPLICATE_REVIEW` | R8_invariant_generator -> R8 (PLAUSIBLE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | DUPLICATE_WITH:ac-t-pauli-completeness |
| `rps-t-riemann-young-22` | tensor | `DUPLICATE_REVIEW` | R8_invariant_generator -> R8 (PLAUSIBLE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | DUPLICATE_WITH:ac-t-young-s3 |
| `rps-t-stf-son-rank3` | tensor | `PACKAGING_GAP` | R8_invariant_generator -> R8 (PLAUSIBLE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `rps-t-su3-d-contractions` | tensor | `PACKAGING_GAP` | R8_invariant_generator -> R8 (PLAUSIBLE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `rps-t-su3-gellmann-fierz` | tensor | `DUPLICATE_REVIEW` | R8_invariant_generator -> R8 (PLAUSIBLE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | DUPLICATE_WITH:ac-t-pauli-completeness |
| `rps-t-su3-octet-projectors` | tensor | `PACKAGING_GAP` | R8_invariant_generator -> R8 (PLAUSIBLE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `rps-t-weyl-selfdual-4d` | tensor | `DUPLICATE_REVIEW` | R8_invariant_generator -> R8 (PLAUSIBLE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | DUPLICATE_WITH:ac-t-ricci-weyl |
| `thermal-09-digamma-recurrence` | thermal | `PACKAGING_GAP` | R2_newton_dd -> R2 (PLAUSIBLE) | `REPRESENTABLE_AFTER_PACKAGING` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `thermal-10-polygamma-recurrence` | thermal | `PACKAGING_GAP` | R3_hermite_dd -> R3 (PLAUSIBLE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `thermal-11-gauss-multiplication-psi` | thermal | `PACKAGING_GAP` | R7_master_library -> R5 (NEEDS_DOWNGRADE) | `REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `thermal-12-bose-kernel-integral` | thermal | `PACKAGING_GAP` | R5_special_function -> R5 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `thermal-13-alternating-fermi-series` | thermal | `PACKAGING_GAP` | R5_special_function -> R5 (PLAUSIBLE) | `REPRESENTABLE_AFTER_PACKAGING` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `thermal-14-hurwitz-polygamma` | thermal | `PACKAGING_GAP` | R6_master_object -> R6 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `thermal-15-theta-modular-heat` | thermal | `PACKAGING_GAP` | R8_invariant_generator -> R7 (NEEDS_DOWNGRADE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |
| `thermal-16-gamma-cosh-modulus` | thermal | `PACKAGING_GAP` | R5_special_function -> R5 (PLAUSIBLE) | `NOT_REPRESENTABLE_UNDER_FROZEN_PARSER` | SCIENTIFIC_SOURCE_NOT_FROZEN |

## Interpretation boundaries

- A citation present in a dossier is not treated as a frozen or content-authenticated source.
- Absence of a fabrication signal is not proof that a source transcription is correct.
- Fixed-instance lowering may support a fixed-dimensional task; it must be labeled as such and cannot prove a symbolic-dimension identity.
- Declaring an unsupported special function as an undefined function can make text parse, but does not give the verifier the semantics needed to certify its identity.
- No case in this artifact is selected for DEV, TEST, or CHALLENGE.
