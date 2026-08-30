# Thermal machine packages

Six source-backed `RPSCasePackageV1` candidates derived only from thermal
dossiers 09, 10, 11, and 13. They are not benchmark partitions.

- Two fixed scientific instances are `PACKAGE_READY` because every required
  obligation has a recorded exact `ZERO` verdict.
- Four symbolic families are `PROOF_REQUIRED`; their required identity is
  `UNKNOWN` and has not been promoted.
- Thermal 12 (Integral), 14 (Hurwitz zeta/factorial), 15 (theta), and 16
  (Gamma) remain packaging gaps under the frozen parser and were not
  represented by fake undefined-function semantics.

Validate without network access:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python \
  -m research.representation_program_search.packages.thermal.validate --check
```

`proposer_view.json` contains only opaque source-member references and the
assumption-contract reference. Evaluator programs, depths, roles, obligation
verdicts, and package status remain outside that projection.
