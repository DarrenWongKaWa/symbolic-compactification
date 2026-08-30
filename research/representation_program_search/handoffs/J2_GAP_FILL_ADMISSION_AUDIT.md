# Handoff - independent gap-fill admission audit

## Scope

Read-only audit of package commit `8bab08d94efaedc4ab65b5b71a6d1252bf91c01e`.
No scientific package, shared manifest, DEV/TEST partition, parser, verifier,
grammar, search method, or Guo artifact was changed.

## Explicit package verdicts

- `gf-cr3bp-2017-eq28`: **NOT_ADMISSION_READY**. The exact program and 4/4
  ZERO receipts support independent depth R2. It remains blocked by the actual
  public-loader namespace mismatch, absent retrieved-source byte hashes,
  nonopaque public id, and incomplete source support for P002/P003. Its source
  locator is also misnamed: the CR3BP representation is around Eq. (27), while
  Eq. (28) is the following damped-oscillator case.
- `gf-vdw-2013-eq1`: **REJECT_R6_DEV_ADMISSION**. The 8/8 ZERO receipts and M1
  graph are internally exact, but the source catalog directly exposes the
  Helmholtz master as G0001. The rest is a familiar derivative/response graph;
  the one-use reciprocal latent is only a wrapper. Independent depth is
  `R1_DERIVATIVE_RESPONSE_GRAPH`, not R6. It also fails the same public-loader,
  source-byte, id-opacity, and assumption-source gates, with incomplete exact
  claim links for G0006/G0007/G0008.

Admission-ready count remains **0/2**. The R2 and R6 DEV slots remain missing
unless a future independent review receives repaired packages; this audit does
not authorize repair or admission.

## Evidence retained

- M1 and strict manifest checks pass for both packages.
- All 12 required receipts remain exact ZERO; no prior failure was relabeled.
- All member/candidate expressions parse under each package's exact namespace.
- Actual `load_public_case()` loads both views but infers every symbol as
  `real:false, nonzero:false`, because neither catalog binds `symbols.json`.
- `G_NO_HERMITE` compiles both; CR3BP fails `G_PRIMITIVE` on named
  `NEWTON_DD`; VDW compiles under `G_PRIMITIVE`.
- Primary/authoritative source authenticity was independently checked and exact
  retrieval hashes are recorded in `audits/gap_fill_admission/reviews.json`.
- Gold-free duplicate/leakage screening and manual identity review found no
  exact or renamed prior scientific case. This does not repair nonopaque public
  package ids or the named-operator giveaway.

## Reproduction

```bash
PYTHONPATH=. uv run --with pytest pytest -q \
  tests/test_rps_gap_fill_candidates.py \
  tests/test_rps_gap_fill_admission_audit.py

PYTHONPATH=. uv run python -m \
  research.representation_program_search.audits.gap_fill_admission.audit \
  --check
```

See `audits/gap_fill_admission/INDEPENDENT_GAP_FILL_ADMISSION_AUDIT.md` and
its JSON companion for the complete findings.
