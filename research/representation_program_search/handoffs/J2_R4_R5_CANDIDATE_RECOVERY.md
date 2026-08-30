# J2 R4/R5 strict candidate-recovery handoff

Branch: `work/rps-dev-recovery`

Implementation commit: the commit containing this handoff (reported to the
coordinator separately).

## Delivered

- a hash/byte/locator-bound source ledger for the two strongest explicitly
  real-domain scientific leads;
- four retained `init-session` + main-proposer + exact-step diagnostic runs;
- a deterministic negative-boundary audit in machine and Markdown form;
- historical held-out identity checks against Newton, Hermite-two, and
  piecewise-DD tasks;
- focused regression tests asserting zero retained candidates and a missing
  R4/R5 slot.

## Scientific disposition

No candidate package was created. Real-domain scientific formulas are
available, but no honest R4/R5 case remains under all frozen rules:

1. The Hiai--Petz logarithmic-mean kernel is parser-feasible, but the source
   itself supplies its divided-difference representation. It is a direct
   instantiation of already-inspected held-out Newton/piecewise-DD identities,
   not a fresh representation-search case.
2. The Bouchard et al. SPD coefficient becomes the historical Hermite-two
   template for `F(z)=z*log(z)` only after the positive-domain logarithm
   identity is applied. Positivity cannot be encoded in the frozen namespace;
   the exact verifier returns `NONZERO` on the broader real domain, with the
   recorded exact counterexample `x=1/2`, `y=-2`, residual value `4*I*pi/25`.
   It is also an old-TEST structural variant.
3. The parser's only non-elementary admitted family is `polygamma`; its
   symbolic recurrence remains recorded `UNKNOWN`. Other genuinely fresh R5
   objects are outside the frozen parser, while fixed values or named VALUE
   families do not meet the requested depth.

The distinction is deliberate: this is a package-eligibility/mining boundary,
not a claim that positive-real matrix kernels or special-function science do
not exist.

## Method boundary

`load_public_case()` and M1 compile are explicitly `NOT_APPLICABLE` because no
identity survived to candidate status. No dummy proposer view, package,
ablation, DEV/TEST manifest, grammar change, parser change, verifier change, or
shared manifest was created. ZERO diagnostics establish only old-template
mappings and are never promoted.

## Verification

```text
5 passed in 0.12s
```

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m pytest -q tests/test_rps_r4_r5_candidate_recovery.py
```

Audit refresh/check:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m research.representation_program_search.audits.r4_r5_candidate_recovery.audit \
  --check
```

Expected audit status: `VALID_NEGATIVE_BOUNDARY`; candidate count `0`; R4/R5
slot `MISSING`.
