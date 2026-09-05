# V1 vs V2 vs V3 — arXiv:2604.04520

V1: `../v1/` visual-ledger baseline.
V2: `../v2/` claim-ledger baseline.
V3 / V3.1: `../v3/` current canonical product, from `../evidence/audit.json`.
V3.1 is a shorter presentation of V3. Statuses are unchanged.

V3 is **not scientifically greener** than V1 or V2. Machine-certified
edges remain **1** (2×2 unitarity under \(S^\dagger S=I\)). Claim C2
(Eq. (4)→(5)) stays `GAP`.

## What V1 did well

- Colour stack: orange is huge on purpose.
- Coloured appendix chips, `→` vs `⋯`.
- Fail-closed: Green functions and \(O(\Gamma)\) remainders are not Exact.
- Serif scientific page, compact chips, left-edge table hues.

## What V2 did well

- Paper-level claims C1–C5.
- Reconstructed Eq. (4)→(5) via Appendix C then D.
- Assumptions vs transformation vs status as separate fields.
- Reviewer queue with Accept / Reject / Needs derivation; Accept does
  not stamp Exact.
- Independent Markdown with TeX, from the same `audit.json`.
- Corrected inventory 93 = 11+82 (V1 split the S-matrix).

## What V3 preserves from both

From V1: colour stack, tone key, coloured chips, `→`/`⋯`, first-screen
map, table left-edge hues, typography.

From V2: `audit.json` semantics, C1–C5, (4)→(5) graph, reviewer queue,
Markdown twin, inventory 93, no new Exact.

V3 also routes chips to a specific edge, claim, or obligation instead of
one generic `#obligation-table`.

## What was removed

- V1 **Sign** buttons (human sign-off looked like a certificate).
- V2 uncoloured locator chips and the extra tan “numerical” colour.
- Duplicate chip map in the lower page (section E is a table, not a
  second strip).

## V3.1 presentation

V3.1 does not recertify. It keeps the V1 colour grammar and the V2
claim/derivation/obligation model. Visible layers are only:

1. Summary (state, metrics, colour bar)
2. Coloured Main + A–E map
3. Compact C1–C5
4. Central Eq. (4)→(5) derivation
5. Reviewer queue

Equation records, the full relation ledger, and numerical-support detail
stay in `audit.json` and in click-to-open drawers. MathJax no longer
uses `$` delimiters, so truncated inventory cues cannot be mis-parsed.

## Why V3 is clearer

A physicist sees status colour first, then the paper’s claims, then the
load-bearing (4)→(5) chain, then what they must decide. The map no
longer pretends that consecutive numbers are derivation edges: main-text
(4) and (5) are joined by `⋯`, because the reconstructed path runs
through Appendix C and D.

## Scientific status

No status in `evidence/audit.json` was rewritten for V3.

Visual-only changes:

- Equation chips now inherit the worst reconstructed-edge hue for that
  node (so D-1 is orange because TR/shift edges sit on it, even though
  the longitudinal step itself is `STRUCTURAL`).
- Inventory lines with no reconstructed edge are orange `UNCERTIFIED`
  (V1 painted many of these `UNSUPPORTED`; same inspect hue, V2 label).
- `NUMERICAL_SUPPORT` uses orange, not a third colour.

## Files

| Role | Path |
|---|---|
| Canonical HTML | `v3/audit.html` |
| Canonical Markdown | `v3/audit.md` |
| Pointer | `index.html` → `v3/audit.html` |
| Evidence | `evidence/audit.json` |
| V1 baseline | `v1/` |
| V2 baseline | `v2/` |
