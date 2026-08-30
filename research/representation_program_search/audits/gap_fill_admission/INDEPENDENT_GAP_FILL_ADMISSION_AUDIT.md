# Independent gap-fill package admission audit

Policy: `RPS_GAP_FILL_INDEPENDENT_ADMISSION_AUDIT_V1`.

This audit is read-only with respect to the scientific packages. Exact ZERO receipts are accepted as algebraic evidence and are not relabeled; admission remains a separate gate.

## Verdict

- Admission-ready packages: **0/2**.
- `gf-cr3bp-2017-eq28`: **NOT_ADMISSION_READY**; independent depth **R2**.
- `gf-vdw-2013-eq1`: **REJECT_R6_DEV_ADMISSION**; independent depth **R1_DERIVATIVE_RESPONSE_GRAPH**, not R6.

| package | exact receipts | M1 | parser | independent depth | admission blockers |
|---|---:|---|---|---|---|
| `gf-cr3bp-2017-eq28` | 4/4 ZERO | VALID_CANDIDATE_PACKAGE | PASS | `R2` | `PUBLIC_NAMESPACE_MISMATCH`, `SOURCE_BYTES_UNBOUND`, `ASSUMPTION_SOURCE_GAP`, `NONOPAQUE_PUBLIC_CASE_ID` |
| `gf-vdw-2013-eq1` | 8/8 ZERO | VALID_CANDIDATE_PACKAGE | PASS | `R1_DERIVATIVE_RESPONSE_GRAPH` | `PUBLIC_NAMESPACE_MISMATCH`, `SOURCE_BYTES_UNBOUND`, `ASSUMPTION_SOURCE_GAP`, `NONOPAQUE_PUBLIC_CASE_ID`, `DEPTH_DOWNGRADED` |

## Mechanical findings

Both strict manifests are complete, both programs load through M1 with no schema deltas, every machine expression parses under the package's exact namespace, and all 12 required obligations retain exact `ZERO` evidence. `G_NO_HERMITE` compiles both programs. CR3BP fails `G_PRIMITIVE` on the named `NEWTON_DD` operator; VDW compiles under `G_PRIMITIVE`.

The actual public search loader does not access either `symbols.json`: both catalogs omit `symbols_path`/`symbols_sha256`, so every public symbol is inferred with `real:false, nonzero:false`. That namespace disagrees with both packages' exact real-domain verifier namespaces and blocks admission.

Each package hash-binds its normalized, package-relative dossier, but neither dossier records the bytes hash of any retrieved source. This audit independently recorded exact retrieval URLs, locators, byte counts, and SHA-256 values in `reviews.json`; that independent check does not retroactively repair package provenance.

## CR3BP assessment

The primary paper genuinely contains the reciprocal-square-root divided-difference rule and four coordinate-wise factorized instances. The program is a valid operational R2 representation: one shared latent, four two-node structures, and exact reconstruction. It is not primitive-grammar evidence because `NEWTON_DD` is required by name.

Admission still fails: the public namespace drifts, retrieved source bytes are unbound, the proposer-visible case id is not opaque, and P002/P003 are not fully supported at their claimed locators. In particular, Eq. (28) belongs to the following damped-oscillator section; the CR3BP result is Eq. (27) and its preceding displayed identities.

## Van der Waals assessment

The source set is authentic and the 8/8 algebraic reconstructions are exact. It does not clear R6. G0001 already exposes the Helmholtz master, the remaining members form a familiar derivative/response graph, and the one-use reciprocal latent is a wrapper around G0006. The independent classification is `R1_DERIVATIVE_RESPONSE_GRAPH`.

Admission also fails the public-namespace, source-byte, nonopaque-id, and assumption-source gates. Exact provenance is incomplete for the bulk-modulus/compressibility lowerings: G0006/G0007 omit C003, and C002's normalized formula does not contain the G0008 enthalpy relation.

## Duplicate and leakage boundary

The gold-free automated audit found no exact/renamed identity, sealed-Guo, trivial-CSE, first-order-LGG-only, grammar-syntax, or hidden-role blocker across the historical/current corpus. Manual review agrees that neither source identity is a renamed prior task. This does not erase the nonopaque public ids or the CR3BP named-operator giveaway.

## Scope boundary

No DEV or TEST manifest was created or changed. No parser, verifier, grammar, search policy, scientific package, or Guo artifact was modified.
