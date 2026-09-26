# Software authority lock — v0.3.0-alpha

Manuscript constitution (wins on conflict):
`manuscript/PAPER_AUTHORITY_LOCK.md`.
Claim wording: `manuscript/CLAIM_EVIDENCE_MATRIX.md`.

Paper closure uses **one** public software authority:

| Item | Value |
|---|---|
| Release | `v0.3.0-alpha` Unified Research Preview |
| URL | https://github.com/DarrenWongKaWa/symbolic-compactification/releases/tag/v0.3.0-alpha |
| Peel | `f1d225e46eec3aac17381fb2f7618fa830a8ec79` |
| Package | `0.3.0-alpha` (PEP 440 `0.3.0a0`) |
| Engine | `0.3.0` (unchanged exact-adjudication semantics) |
| Protocol | `0.3.0` |
| Current `main` | may contain post-tag hygiene (`a10e4b5` tomllib test import). **Do not cite `main` as the paper's software identity.** |

Do not chase development branches. Do not open `v0.3.1-alpha` for CI test-import hygiene.

Historical product tags remain recoverable and **unmoved**:

- `derivation-audit-v0.2.0-alpha` → `aaf1199`
- `derivation-audit-v0.2.1-alpha` → `783ec64`

They are lineage, not the paper's software authority.

## Product surface the paper may name

Two workflows, one kernel:

1. **Forward derivation** — candidate → verify → promote only on engine `ZERO`
2. **Paper audit** — inventory → source-grounded relations → verify → `RESULTS.md`

Public names: Forward and Audit. Historical "Mode A" / "Mode B" appear only as
lineage, never as the user model.

Core verification needs no model service and no API key.
Proposal authority ≠ verification authority.
`ZERO` ≠ `CERTIFIED_BY_RULE`.
`UNKNOWN` never promotes.

## Evidence the paper may use (archive tags)

| Role | Tag | Peel | What it supports |
|---|---|---|---|
| Depth | `archive/guo-full-paper-audit-flagship-v1` | `d92f3ec` | Guo 189/189 inventory; 146 relations; flagship `RESULTS.md` |
| Breadth | `archive/prd-cross-paper-stress-v1` | `4f12401` | Five public papers, 41 edges, false promotion 0/30 |
| Forward replay | `archive/forward-proposer-replay-v1` | `b9b6972` | Heterogeneous proposers into frozen verifier |
| Selected-edge precursor | `archive/guo-selected-edge-validation-v1` | `69ad474` | Earlier 26-edge public table; not the flagship UX |
| Approximation study | `archive/approximation-authority-v1` | `5477cf2` | RQ4 candidate only; overlay not in the v0.3 product schema |

Public flagship entry in the product tree:
`examples/flagship/guo/RESULTS.md` on tag `v0.3.0-alpha`.

## Frozen flagship counts (Guo et al., PRL 136, 206303; arXiv:2511.16422v2)

From committed `RESULTS.md` (byte-identical under clean-room replay):

- numbered equations inventoried: 189/189
- derivation relations in the public table: 146
- executable numbered relations: 53 (plus 1 local Leibniz helper)
- `EXACT_ZERO`: 32
- `ZERO_UNDER_SUBSTITUTION`: 21
- `CERTIFIED_BY_RULE`: 11
- `UNKNOWN_REMAINDER`: 17
- `STRUCTURAL`: 47
- `UNSUPPORTED`: 18
- `NONZERO`: 0
- false promotion on injected controls: 0/155

This is **not** "189 formulae proved." Inventory coverage and certified
residuals are different numbers.

## Frozen breadth counts (five-paper sample)

From `archive/prd-cross-paper-stress-v1` `RESULTS.md`:

- papers: 5
- equation edges: 41
- `EXACT_ZERO`: 10
- `ZERO_UNDER_SUBSTITUTION`: 10
- `CERTIFIED_BY_RULE`: 1
- `UNKNOWN` / `UNKNOWN_REMAINDER`: 7
- `STRUCTURAL`: 8
- `PARSE_FAILURE` / `COMPILE_FAILURE`: 3
- `NONZERO`: 0
- false promotion on injected invalids: 0/30

Statuses `CERTIFIED_UNDER_DECLARED_APPROXIMATION` and
`UNDECLARED_APPROXIMATION_REQUIRED` appear in that experiment tree. They are
**not** v0.3.0-alpha product statuses. Cite them only as experimental
diagnostics. Do not imply the released schema ships those overlays.

## Frozen forward-replay counts

From `archive/forward-proposer-replay-v1`:

- injected invalids refused: 0/36 false promotion
- gold recovered hidden targets as expressions: 8/8
- gold promotion-eligible versus current: 6/8
- gplearn-raw TargetRecovery: 0/8
- verdict: `FORWARD_WORKFLOW_DEMONSTRATED_WITH_CAVEATS`

## Paper MUST NOT

- treat `main` HEAD as the frozen software
- treat selected-edge 25/26 as the flagship public result
- claim complete-paper proof or physical-conclusion verification
- productize approximation overlays
- reopen representation-invention campaigns
- cite unpublished local manuscripts
- start `v0.3.1-alpha` for test-import hygiene
