# R4/R5 strict candidate-recovery boundary

Policy: `RPS_R4_R5_CANDIDATE_RECOVERY_V1`.

## Verdict

No strict M1 DEV candidate was created. The R4/R5 slot remains `MISSING`.
This is a negative mining/package result, not evidence that the underlying
scientific formulas do not exist.

| lead | scientific domain | scientific formula available | package disposition |
|---|---|---:|---|
| `SCREEN-A` | x,y are positive real spectral values | yes | rejected: `OLD_TEST_VARIANT:test-a-newton-first`; `OLD_TEST_VARIANT:test-b-piecewise-dd`; `SOURCE_EXPOSES_DIVIDED_DIFFERENCE_TARGET`; `NOT_GENUINELY_FRESH` |
| `SCREEN-B` | positive real eigenvalues of real SPD matrices | yes | rejected: `OLD_TEST_VARIANT:test-a-hermite-two`; `FROZEN_NAMESPACE_CANNOT_ENFORCE_POSITIVITY`; `SOURCE_TO_PROGRAM_LOWERING_NONZERO_ON_FROZEN_REAL_DOMAIN`; `NOT_GENUINELY_FRESH` |

## Scientific availability versus package eligibility

Hiai--Petz supplies an exact positive-real logarithmic-mean kernel and
explicitly defines its distinct/coalesced divided-difference form. That
same explicitness makes the proposed program a direct instantiation of
the already-inspected Newton/piecewise-DD held-out identities. It is not
a fresh representation-search case.

Bouchard et al. supplies a piecewise coefficient on real SPD spectra.
After the positive-domain identity `log(x/y)=log(x)-log(y)`, its distinct
coefficient is exactly the historical Hermite-two template for
`F(z)=z*log(z)`, and its diagonal coefficient is the confluent stratum.
The frozen symbol namespace cannot declare positivity. The exact verifier
therefore correctly finds a counterexample on its broader real domain
instead of certifying that source-to-program lowering.

## Frozen R5 boundary

The parser admits elementary functions and `polygamma`; it does not admit
the broader special-function objects needed by the fresh R5 leads. The
recorded symbolic polygamma recurrence remains `UNKNOWN`. A fixed value or
a member that simply names `polygamma` would be a diagnostic/VALUE family,
not the requested representation change.

## Recorded diagnostics

| id | verdict | purpose |
|---|---|---|
| `D001` | `ZERO` | Parser-feasible first divided-difference lowering; rejected as a direct old-TEST instantiation. |
| `D002` | `NONZERO` | The source declares positive eigenvalues, but positivity is unavailable in the frozen namespace; the required log quotient lowering is refuted on the broader real probe domain. |
| `D003` | `UNKNOWN` | The only admitted non-elementary family does not certify its symbolic recurrence under the frozen verifier. |
| `D004` | `ZERO` | After an external positive-domain log lowering, the proposed structure is exactly the historical Hermite-two template instantiated with F(z)=z*log(z); this diagnostic is not source-member certification. |

All four diagnostics retain `init-session`, main-proposer hypothesis, and
exact step records. ZERO is used only to establish the parser-feasible
old-template mappings; it is not promoted to a case result. NONZERO and
UNKNOWN remain fail-closed.

## Package and method boundary

`load_public_case()` and M1 compilation are `NOT_APPLICABLE`: there is no
retained candidate to load or compile. No public view, package, DEV/TEST
manifest, grammar change, parser change, verifier change, or ablation
artifact was created. Creating dummy artifacts for a rejected identity
would weaken rather than test the frozen method contract.

Machine report: `MINING_BOUNDARY.json`.
Source retrieval ledger: `source_ledger.json`.
