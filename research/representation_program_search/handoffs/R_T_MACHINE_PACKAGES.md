# R/T machine-package handoff

## Outcome

The bounded response/tensor packaging audit produced three `PACKAGE_READY`
artifacts. Only the Feshbach package is an operational fixed scientific
instance. The two tensor packages are deliberately labeled
`FINITE_INDEX_DIAGNOSTIC`; neither is evidence for a symbolic-dimension R8
success.

| Package | Audited target depth | Frozen lowering scope | Exact retained run | Result |
| --- | --- | --- | --- | --- |
| `rps-r-feshbach-optical-heff` | R6 | `FIXED_SCIENTIFIC_INSTANCE` | `20260830T111715Z-48b9b3` | 1 proposal, 1 verifier call, 1 ZERO |
| `rps-t-barnes-rivers-dn` | R8 | `FINITE_INDEX_DIAGNOSTIC` | `20260830T111715Z-e0ff63` | 1 proposal, 1 verifier call, 1 ZERO |
| `rps-t-stf-son-rank3` | R8 | `FINITE_INDEX_DIAGNOSTIC` | `20260830T111715Z-fc8d84` | 1 proposal, 1 verifier call, 1 ZERO |

All runs record `MAIN_AGENT_ONLY`, retain both the HYPOTHESIS proposal step and
the certified verification step, and end in a complete final certified form.
Each aggregate obligation uses independent tag indeterminates, so exact ZERO
certifies every displayed reconstruction/check in its declared fixed scope.

## Package contents and leakage boundary

Every package conforms to `RPSCasePackageV1` and contains immutable member
texts, symbol declarations, a SHA-256 source catalog, a complete assumption
contract, a source manifest with equation-level locators, an evaluator-only
reference program and obligation description, and the retained verifier run.
`package.json` content-addresses every artifact except itself.

`proposer_view.json` contains exactly two top-level fields: `assumptions` and
`source_catalog`. It does not expose audited depth, a gold/reference program,
operator names or sequences, source roles, obligations, or verdicts.

## Scientific bounds

- The Feshbach package specializes the exact P/Q block-elimination equation to
  one scalar P channel and one scalar Q channel. It reconstructs the closed
  kernel, self energy, effective Hamiltonian, effective equation, and Schur
  form from a reused resolvent kernel. It does not claim continuum, scattering,
  Hermiticity, or symbolic operator verification.
- The Barnes--Rivers replay checks eight basis-channel values and two
  completeness components at `d=5` in a fixed Euclidean signature. It does not
  prove idempotence, orthogonality, completeness for every index, or the
  symbolic-`d` algebra.
- The STF replay reconstructs ten components and checks two vanishing trace
  slices at `n=5`. It does not prove the symbolic-`n` projector or all 35
  independent rank-3 components.

The primary equation evidence is Feshbach's P-space effective equation
(Rev. Mod. Phys. 36, p. 1077, after Eq. 4), the n-dimensional Barnes--Rivers
formulas and completeness relation in Shapiro Eqs. 67--69 and 76
(arXiv:2210.12319), and the rank-3 trace subtraction in Toth--Turyshev
Eqs. 14--16 (arXiv:2109.11743). Retrieval URLs, exact PDF hashes, equation
transcriptions, and crosschecks are recorded in each `source_manifest.json`.

## Non-packaged dossier dispositions

`PACKAGING_GAPS.json` covers all 16 fresh response/tensor dossiers:

- `PACKAGE_READY`: 3;
- `PACKAGING_GAP`: 5;
- `PROBLEM_UNDERSPECIFIED`: 1;
- `REJECT_DEPTH`: 2;
- `REJECT_SCOPE`: 1;
- `DUPLICATE_REVIEW`: 4.

The important hard gaps are special-function/analytic-continuation semantics,
operator determinant/ODE Green-function semantics, and invariant tensor
contractions. Fixed scalarization of the SU(3) cases would collapse the target
to a supplied arithmetic table, so it was preserved as `PACKAGING_GAP` rather
than forced through the parser. Guo and historical or near-duplicate identities
were not packaged.

## Validation

`tests/test_representation_response_tensor_packages.py` checks the frozen
lowering enum, complete artifact hashes, member catalog hashes and parser
admission, proposer-view leakage, canonical program IDs, retained session
summaries, ZERO/CERTIFIED/PROVEN terminal steps, source locators, complete
assumption labels, finite-index nonclaims, and full dossier-disposition
coverage.

Targeted result: `5 passed`.
