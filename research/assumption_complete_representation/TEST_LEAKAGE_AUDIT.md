# TEST leakage audit (structure only; TEST not frozen)

LLM DEV results were **not** used.

## DEV near-duplicates (kept)

- RESOLVENT_CLUSTER: mp-resolvent-dd-01 ≈ ac-r01 (opposite resolvent convention)
- DALECKII_KREIN_CLUSTER: mp-daleckii-krein-01 ≈ sciml-daleckii-krein-01

No additional DEV near-duplicates.

## HOLD vs DEV

Do **not** headline (renamed / same master as DEV):

- thermal-02-bose-im-digamma ≈ thermal-01 (DLMF 5.4.16 vs 5.4.17)
- mp-mathias-block-01 ≈ sciml-vanloan-blockexp-01
- thermal-04-coth-matsubara: same Matsubara/coth family as DEV thermal kernels

Headline TEST candidates (structurally new, assumption-complete):

- sciml-tweedie-gauss-01 (R6, parseable)
- sciml-ou-mehler-01 (R6)
- ac-t-weyl-su2-char (R8)
- mp-parlett-schur-01 (R4; no R4 in DEV)
- mp-kato-simple-ev-01 (R2 perturbation, not Hilbert identity)
- sciml-deq-ift-01, sciml-adjoint-linear-01
- tensor: ac-t-ricci-weyl, ac-t-clebsch-half, ac-t-iso4-projectors, ac-t-pauli-completeness

CHALLENGE: ac-r02 (R4 boundary values; A4 GAP, disqualifies=false),
mp-opitz-dd-01, sciml-lyapunov-kronecker-01, thermal-06-fermi-dirac-polylog.

Guo is excluded. Prompts are not retuned from this graph.
This file does **not** freeze TEST.
