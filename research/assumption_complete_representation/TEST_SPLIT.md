# TEST / CHALLENGE freeze

After DEV_METHOD_SELECTION (GENERAL_FINAL=P0). Prompts not retuned.
Guo excluded.

## Headline TEST (n=10)

mp-kato-simple-ev-01, mp-parlett-schur-01,
sciml-tweedie-gauss-01, sciml-ou-mehler-01, sciml-deq-ift-01,
sciml-adjoint-linear-01,
ac-t-weyl-su2-char, ac-t-ricci-weyl, ac-t-clebsch-half, ac-t-iso4-projectors.

## CORE_COMPARABLE (held-out LLM vs baseline)

sciml-tweedie-gauss-01, sciml-ou-mehler-01, sciml-deq-ift-01,
ac-t-weyl-su2-char.

The other six headline tasks are PACKAGING_GAP.

## DUPLICATE_CONTROL (not headline)

thermal-02-bose-im-digamma, mp-mathias-block-01, thermal-04-coth-matsubara.

## CHALLENGE

ac-r02-sokhotski-plemelj-boundary, mp-opitz-dd-01,
sciml-lyapunov-kronecker-01, thermal-06-fermi-dirac-polylog,
ac-t-pauli-completeness.

P4 is not run on TEST CORE (no unlabeled DD/Hermite family in CORE).
AI_UNIQUE only on CORE_COMPARABLE.
