# Engineering Closure and Paper Handoff

## GitHub release URL

https://github.com/DarrenWongKaWa/symbolic-compactification/releases/tag/derivation-audit-v0.2.1-alpha

Pre-release title: **Derivation Audit Alpha 0.2.1**. Marked `PRE-RELEASE`.
Generic product notes only. No unpublished manuscript information. No claim
that entire papers are proven.

## v0.2.1 tag / SHA

| Item | Value |
|---|---|
| Tag | `derivation-audit-v0.2.1-alpha` |
| Peel | `783ec64c0bb4ffd0b4b6ad33f33ead96dba49087` |
| Branch | `engineering/derivation-audit-v0.2.1` |
| Package | `0.2.1-alpha` (PEP 440 `0.2.1a0`) |
| Engine | `0.3.0` |
| Protocol | `0.2.1` |

Historical tag `derivation-audit-v0.2.0-alpha` still peels to `aaf1199`.
**Not moved.** `origin/main` remains at `aaf1199` (v0.2.0). This handoff
does not fast-forward `main`.

## Evidence branch / SHA

| Item | Value |
|---|---|
| Branch | `engineering/real-paper-validation-arxiv-2511-16422` |
| SHA | `69ad474a43ebea55cb2e524934d982e518db026b` |
| Workspace | `examples/real_papers/arxiv_2511_16422/` |

Evidence, not a product tag. Approved public metrics: 25 selected paper
steps; 19 machine `ZERO` (13 `DIRECT_EXACT` + 6 `SUBSTITUTION_EXACT`);
2 BZ periodic IBP `RULE_CERTIFICATE`; 1 asymptotic `UNKNOWN`; 0 `NONZERO`.

## Engineering freeze status

**CLOSED.** Recorded in repository-root `ENGINEERING_V0_2_CLOSED.md` on
branch `paper/derivation-audit-method`.

No automatic v0.2.2, theorem-rule catalogue, verifier expansion, benchmark
expansion, or second-paper engineering campaign is authorized. Future
engineering requires real external use + a concrete generic product gap +
explicit human authorization.

## Public privacy audit

Product tree at `783ec64`:

| Check | Result |
|---|---|
| `HEAD == 783ec64` | PASS |
| `derivation-audit-v0.2.0-alpha` → `aaf1199` | PASS |
| `examples/real_papers/` | absent |
| `manuscripts/` | absent |
| `.private_validation/` | absent |
| v0.2.1 patch files | generic adapter, tests, docs only |
| Unpublished formulas/paths/hashes added in v0.2.1 | none |
| Historical public Guo benchmark files already on `v0.2.0`/`main` | unchanged; not this patch |

Paper workspace contains only public Guo et al. (arXiv:2511.16422v2)
discussion. Unpublished local scientific manuscripts are not cited,
described, counted, or reproduced.

## Methods-paper directory

`paper/derivation-audit-method/` on branch `paper/derivation-audit-method`
(cut from product SHA `783ec64`). Writing and analysis only; does not
modify product semantics.

Working title: **Machine-Auditable Derivation Verification for Theoretical Physics**.

Central question: how can AI-assisted symbolic derivations be made
machine-auditable without granting the AI authority to certify its own
claims?

## Frozen paper claims

MAY: equation-level machine-auditable verification; fail-closed
adjudication; source-grounded provenance; local exact vs theorem-mediated
certificates; reproducible reviewer packages; public real-paper validation.

MUST NOT: full formal proof of a manuscript; physical-conclusion
verification; autonomous discovery; general theorem proving; complete
integrals/limits/asymptotics; robust representation invention.

## Available figures / tables

Planned from existing evidence (not newly computed science):

- Figure 1 architecture
- Figure 2 certificate taxonomy
- Figure 3 public Guo derivation graph
- Figure 4 fail-closed asymptotic remainder
- Table 1 status / certificate semantics
- Table 2 field-validation summary
- Table 3 adversarial integrity attacks
- Table 4 capability boundary (SUPPORTED / PARTIAL / UNSUPPORTED)

## First-draft status

Complete section-by-section first draft: `manuscript/draft-v0.md`
(§1–12 + appendices). Not a submission PDF. Figures are specified, not
yet journal-rendered. No new experiment was run to produce the draft.
