# Paper handoff after v0.3.0-alpha freeze

Canonical software lock: `SOFTWARE_AUTHORITY.md`.

## GitHub release URL

https://github.com/DarrenWongKaWa/symbolic-compactification/releases/tag/v0.3.0-alpha

Pre-release title: **symbolic-compactification v0.3.0-alpha**.
Unified Research Preview. Not a stable v1.0.

## v0.3.0-alpha tag / SHA

| Item | Value |
|---|---|
| Tag | `v0.3.0-alpha` |
| Peel | `f1d225e46eec3aac17381fb2f7618fa830a8ec79` |
| Package | `0.3.0-alpha` (PEP 440 `0.3.0a0`) |
| Engine | `0.3.0` |
| Protocol | `0.3.0` |

Historical tags `derivation-audit-v0.2.0-alpha` (`aaf1199`) and
`derivation-audit-v0.2.1-alpha` (`783ec64`) are unmoved lineage.

Post-tag `main` may contain test-import hygiene. It is not the paper's
software identity.

## Evidence tags (not live branches)

Live experiment/engineering branches were deleted after archival.
Cite archive tags, not deleted branch names, as the durable pointer.

| Evidence | Archive tag | Peel |
|---|---|---|
| Guo full-paper flagship | `archive/guo-full-paper-audit-flagship-v1` | `d92f3ec` |
| Five-paper sampled stress | `archive/prd-cross-paper-stress-v1` | `4f12401` |
| Forward proposer replay | `archive/forward-proposer-replay-v1` | `b9b6972` |
| Guo selected-edge precursor | `archive/guo-selected-edge-validation-v1` | `69ad474` |
| Approximation authority (RQ4 candidate) | `archive/approximation-authority-v1` | `5477cf2` |

## Engineering freeze status

**Product engineering CLOSED at v0.3.0-alpha.**
No automatic v0.3.1, theorem-rule catalogue, verifier expansion, or
additional full-paper audit campaign is authorized. Future engineering
requires a user-visible bug, install failure, or certificate-semantics
bug, plus explicit human authorization.

## Public privacy audit

Unpublished local scientific manuscripts are not cited, described, counted,
or reproduced. Flagship source is public Guo et al. (arXiv:2511.16422v2).

## Methods-paper directory

`paper/derivation-audit-method/` on branch `paper/derivation-audit-method`.
Writing and analysis only; does not modify product semantics.

Working title: **Verified Symbolic Reasoning for Theoretical Physics
through Typed Evidence Graphs**.

Central question: how can constructive symbolic derivation and retrospective
manuscript audit share one machine-auditable evidence contract, without
granting a proposer the authority to certify its own claims?

Evidence chain the paper now defends:

```
proposal/extraction is untrusted
  → typed scientific claim
  → deterministic evidence
  → fail-closed scientific state
```

Forward shows a candidate cannot certify itself.
Audit shows a paper relation cannot certify itself by prose.
Guo flagship shows the contract covers one 189-equation theoretical
derivation, not a handful of toy identities.
The five-paper sample shows the same statuses travel beyond one manuscript,
without claiming five complete-paper proofs.
