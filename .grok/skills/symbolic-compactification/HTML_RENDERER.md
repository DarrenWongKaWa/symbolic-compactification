---
name: html-renderer
description: >
  Emit a self-contained evidence-ledger HTML page from frozen RESULTS
  from frozen RESULTS. Presentation is not a certificate. Never emit 0*.
---

# HTML_RENDERER

Emit one self-contained HTML page. Presentation is not a certificate.
Statuses are copied from frozen RESULTS. JavaScript must not infer ZERO.

## First screen

1. Kicker: `Evidence ledger`
2. Completeness band: `AUDIT_INCOMPLETE` until the Sign queue is empty
   **and** `missing_declared_moves` is certified. Local Sign does not
   clear the banner while completeness is uncertified.
3. Three cells: inventoried / extracted / executable. Do not hero `NONZERO`.
4. Stacked colour bar (click a colour to filter the table):
   - dark green — `EXACT_ZERO`
   - light green — `ZERO_UNDER_SUBSTITUTION`
   - one blue band — cite + def (tooltip splits the two counts)
   - one orange band — remainder + unsupported (tooltip: sign, gap, look/remainder)
   - dark red — `NONZERO` (keep a sliver even when the count is 0)
5. Legend:
   - Green = checked 0 (dark direct, light after A)
   - Blue = definition or cited rule
   - Orange = reviewer looks
   - Dark red = local residual ≠ 0
   - Green is not a paper pass.
   Do not write “proved zero” or “refuted”.
6. Sign table, default open. **You** = Sign / Signed button only.
   Status column on those rows is empty (orange bar on the row is enough).
7. Main-text ← appendix correspondence if present.
8. **Appendix map (first screen, never a closed `<details>`).**
   If the paper has appendix (or sectioned) numbered equations, emit a
   visible `<section id="map-sec">` of coloured equation chips with the
   paper’s section letters (Guo: A–G), with → frozen edge and ⋯
   consecutive numbers only.
   DOM: inside `<header>`, after Must review / correspondence, **before**
   the Judged line and **before** `<main id="main">`.
   Reference: `examples/guo-evidence-ledger/presentation/index.src.html` `#map-sec`.
   Forbidden: `<details id="map-sec">`. Do not put the map after
   `<main>`. Do not hide it behind a summary click.
   If the TeX has no `\appendix`, omit the map. Do not invent A–G.
9. Judged line (counts of `0` / `0 if A` / `cite`).
10. Optional `<details id="encode-sec">` for uncompiled algebra (gap,
    still UNSUPPORTED). Then the full obligation table. Default filter =
    Sign queue.

The engineering layer’s job is to emit this HTML. Do not emit `0*`.
That overlay is invalid history (`docs/history/invalid-0star-lineage/`).

Skeleton (header, first screen):

```html
<section id="map-sec">
  <h2>Appendix map A–…</h2>
  <p>Click a numbered box for the formula. → frozen edge; ⋯ consecutive numbers only. This map is on the first screen.</p>
  <div class="lanes" id="derivation-map" data-static="true">
    <!-- one .lane per appendix letter; .eq-node coloured from frozen RESULTS -->
  </div>
</section>
```

## Fail closed

After writing HTML, run `python3 verify_first_screen.py PATH.html`.
It fails if `id="map-sec"` is a `<details>`, sits after `id="main"`,
or is missing when the page inventories appendix equations.
It also fails if the page contains `0*` or `ws-zero`.

## Chips and Sign

Chip + hue + You: `CLASSIFIER.md`.

Every chip, filter pill, bar segment, and Sign button has `title` and a
visible tooltip on hover / focus.

| Chip / control | Tooltip |
|---|---|
| `0` | Machine checked left−right = 0. Local residual only, not a paper pass. |
| `0 if A` | Machine checked 0 after the substitution in column A?. Does not prove A. |
| `cite` | Author invoked a named rule. Local identity + declared rule, not a CAS integral. |
| `def` | Definition or bookkeeping. No equality to check. |
| `remainder` | Finite terms do not prove the O(·) or the limit. |
| `look` | Not compiled. Special function, named identity, or similar. Do not treat as algebra 0. |
| `gap` | Local algebra was not in the frozen table. Not a pass. |
| `≠0` | Submitted residual is not 0. |
| Sign | Record that you accept this cancel. Does not change frozen RESULTS. |
| Signed | Local sign-off. Click again to undo. Parent stays orange. |

Sign state is UI-only `localStorage` keyed by `paper-id` + `rel-id`.
It must not change frozen RESULTS, turn a row green, or clear
`AUDIT_INCOMPLETE` while `missing_declared_moves` is uncertified.

## No-JS floor

Band, three cells, colour bar, Sign rows, **appendix map**, and the full
table remain in the HTML. Filters and Sign persistence require JS.

## Colour tokens

`--ok` `#2d6a4f`, `--cite` `#2e5a88`, `--inspect` `#b86a12`, `--wrong` `#9b2c2c`.
