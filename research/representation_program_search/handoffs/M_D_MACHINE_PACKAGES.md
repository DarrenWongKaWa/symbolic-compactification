# M/D handoff — fixed matrix and differentiable-physics packages

Owner: replacement case packager M/D

Branch: `work/rps-package-matrix-dp`

## Delivered and corrected disposition

Four fresh `RPSCasePackageV1` artifacts live under
`packages/matrix_diffphys/`. They form no benchmark partition and make no
symbolic-matrix-dimension claim.

| package | depth | status | source dossier | required verdicts |
|---|---:|---|---|---:|
| `mx-sqrt-newton-fixed-r2` | R2 | `PACKAGE_READY` | `mx-polar-psd-sqrt-01` | 1 ZERO |
| `mx-sqrt-hermite-fixed-r3` | R3 | `PACKAGE_READY` | `mx-polar-psd-sqrt-01` | 1 ZERO |
| `dp-oscillator-confluent-fixed-r4` | R4 | `PROOF_REQUIRED` | `rps-dp-cossin-oscillator-prop` | 4 ZERO, 1 UNKNOWN |
| `mx-abba-exp-fixed-r6` | R6 | `PACKAGE_READY` | `mx-ab-ba-functional-01` | 4 ZERO |

All four package manifests use the frozen lowering enum
`FIXED_SCIENTIFIC_INSTANCE`. Scientific detail remains evaluator-side in each
`source_manifest.json`, including the explicit denial of a symbolic matrix
dimension proof.

## R4 proof gap and restricted replay

The source claim declares complex `w`. Its exponential/Piecewise
reconstruction remains required UNKNOWN in session
`20260830T111540Z-8f5972` (`PROOF_REQUIRED`), so the package is not ready.
No new domain assumption was authorized.

The later real-`w` replay `20260830T111904Z-6a347e` is retained only as
`INELIGIBLE_RESTRICTED_REPLAY`. Its ZERO verdict is counted in
`attempt_verdict_counts`, not in required certification evidence. It cannot
promote or certify the complex-domain source claim.

The remaining R4 member reconstructions are exact ZERO:

- composition: `20260830T111540Z-e8bce0`
- exponential cosine form: `20260830T113039Z-eed90a`
- trigonometric normalization: `20260830T113039Z-b632ee`
- zero-frequency scalar reconstruction: `20260830T113039Z-0aa2db`

## Reconstruction coverage

The validator now requires every program member assignment to satisfy exactly
one of these evidence paths:

1. its reconstruction plus the canonical newline is byte-identical to the
   immutable source member and is tagged `BYTE_IDENTICAL_EXACT`; or
2. a required obligation starts from that exact source member and its
   candidate bytes equal the recorded reconstruction.

R6 therefore adds required ZERO sessions for the two previously uncovered
entries:

- G0003: `20260830T113039Z-b633e0`
- G0004: `20260830T113039Z-e89ee2`

R3 now contains an explicit node object for `[x,x]`; every `HERMITE_DD`
operator references a node-object ID rather than an inline list.

## Proposer firewall

Proposer-visible assumptions now contain only predicates and domain/branch
facts needed to define the source claim. Exact representation derivations,
operator roles, site-multiplicity explanations, and closed target formulas
remain evaluator-side in source manifests and reference programs.

Proposer case IDs are opaque (`MDF0001` through `MDF0004`). The validator and
tests scan both keys and values, rejecting named `NEWTON`/`HERMITE`,
recurrence, multiplicity/repeated-node, confluent/coincident-site, and target-
form cues.

## Source and duplicate discipline

- Square-root formulas are tied to Higham (1986), equation (1.1) and the
  Fréchet derivative below (1.2), plus de Boor (2005), the distinct/coincident
  recurrence immediately before equation (31).
- Oscillator formulas are tied to Higham and Kandolf (2017), equations
  (1.1), (1.2b), and (1.3).
- AB/BA reconstruction is tied to Higham (2008), Theorem 1.35, equation
  (1.31).

No Historical Diagnostic identity or Guo case is used. The R4
Piecewise-shell similarity received explicit manual review; the scientific
members and identities are distinct.

## Validation

`packages/matrix_diffphys/validate.py` fails closed on schema drift, a
non-enum lowering scope, artifact or source-dossier hash mismatch, incomplete
assumptions, proposer key/value leakage, noncanonical program IDs, inline
Hermite node lists, uncovered member reconstructions, session mismatch,
status/verdict inconsistency, missing equation locators, and
symbolic-dimension overclaims.

Observed results:

```text
PYTHONPATH=. python3 -m \
  research.representation_program_search.packages.matrix_diffphys.validate
status: VALID; three PACKAGE_READY; one PROOF_REQUIRED
required totals: 10 ZERO, 1 UNKNOWN, 0 NONZERO

PYTHONPATH=. python3 -m pytest -q \
  tests/test_rps_matrix_diffphys_packages.py \
  tests/test_rps_leakage_audit.py \
  tests/test_rps_assumption_audit.py \
  tests/test_rps_contracts.py
30 passed in 27.34s
```

## Scientific limits

- R2 and R3 are scalar spectral coefficients derived from a fixed positive
  diagonal 2 by 2 square-root setting.
- R4 is a fixed 2 by 2 scalar-frequency oscillator flow. Its complex-domain
  source claim has a verifier proof gap and is not package-ready.
- R6 is a fixed diagonal 2 by 2 AB/BA exponential construction, not
  arbitrary-dimensional AB/BA functional calculus.
- These are admissible package candidates only. No DEV/TEST/CHALLENGE choice
  was made.
