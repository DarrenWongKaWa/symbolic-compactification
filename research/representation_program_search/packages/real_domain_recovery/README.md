# Real-Domain DEV Candidate Recovery

This collection contains two newly mined, real-domain packages that are ready
only for independent review. It does not create or modify a DEV/TEST manifest,
and it performs no admission.

- `rps-real-c3j9`: fixed real-SPD second-order matrix-log response components,
  sourced to Rubensson (2024). The full program uses repeated-node structure;
  both no-Hermite and primitive programs construct the same obligations from
  `VALUE`, `DERIVATIVE`, `SUBSTITUTE`, and `LINEAR_COMBINATION`.
- `rps-real-c8q2`: three real nonzero radial special-function kernels, sourced
  to exact NIST DLMF artifacts. One latent scalar kernel generates the first
  two orders by differentiation and the third by an order relation. Its R5
  depth remains explicitly subject to independent downgrade review.

Every program variant has its own main-proposer HYPOTHESIS record followed by
an exact verifier step. All required obligations are ZERO. ZERO proves only
the compiled scalar reconstruction under the recorded contract; it does not
admit a package or settle scientific depth.

Run the fail-closed validator from repository root:

```bash
PYTHONPATH=. python -m \
  research.representation_program_search.packages.real_domain_recovery.validate
```

`RECOVERY_GAPS.json` records why R2 and R6 remain missing.
