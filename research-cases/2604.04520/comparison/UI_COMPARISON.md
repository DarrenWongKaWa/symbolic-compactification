# UI comparison — Anan V3.1 before vs after

Presentation only. `examples/2604.04520/evidence/audit.json` is unchanged
(sha256 `1c966908877c818741e228c7d904bc7a85a9ab90d8200262b48a173cd6b49dc8`).
No status was rewritten. Guo is visual grammar, not an Anan data template.

The scientific skill still decides **what** to show. This pass only
changes **how** the reviewer HTML shows it.

Target user: a theoretical physicist refereeing a derivation-heavy paper.
Primary question: **what does the physicist still need to judge?**

## Visible layers (unchanged contract)

1. Summary
2. Coloured equation map A–E
3. Compact claims C1–C5
4. Central derivation (4) → C → D → (5)
5. Reviewer queue

Equation records (93) and the full ledger stay in drawers.

## What changed

| Surface | Before | After |
|---|---|---|
| First screen | Completeness + metrics grid + stack + map | Completeness + **Need your judgment** strip + stack + map |
| Metrics grid | Duplicated the completeness counts | Removed (one fact, one home) |
| Jump to obligations | Scroll to queue | Strip lists O1, O5, O6, O7, O2, O8, O9, O3 |
| Central certified/structural edges | `E-D-longitudinal` fully visible | `✓ 1 machine-discharged step` behind Show |
| Unresolved load-bearing | Visible | Still visible (not hidden) |
| Reviewer queue | Cards, weak border | Inspect-orange frame; **Source** on each card |
| Accept warning | “it never changes…” | “it does not change a machine status to Exact.” Once, at queue start |
| Disclaimer | One sentence in the banner | Unchanged, still once |
| Math | MathJax `\(`/`\)` only; unsalvageable cues dropped | Same MathJax; escaped `<pre class="tex-fallback">` if typesetting fails |
| `audit.json` statuses | C2 `GAP`, 1 Exact-if-A, 13 unresolved | Identical |

File bytes grew (84 501 → 115 479) because every typeset formula now carries a
hidden fallback. Visible copy is not a 93-row table; it is the five layers
plus the judgment strip.

## One-minute physicist questions

| # | Question | Where the page answers it |
|---|---|---|
| Q1 | What do I still need to judge? | First-screen strip → `#queue`. Eight obligations, not 93 equations. |
| Q2 | What is the central derivation? | `#graph`: (4) → C-1 → C-2 → D-1 → D-2 / D-4 / D-8 → (5). Inspect edges open. |
| Q3 | What are the paper’s claims? | `#claims` C1–C5, compact, with path and blockers. |
| Q4 | Where is Eq. (5)? | Map chip `(5)` → `#claim-C2`. |
| Q5 | What is actually certified? | Colour stack 0 Exact / 1 Exact-if-A / 3 blue / 13 inspect / 0 red. Banner: local certification is not a paper-level certificate. |

## Independent UI review (no scientific redesign)

Pass as a referee report, not a dashboard.

- Hierarchy is correct: orange obligations louder than green/blue bookkeeping.
- Accept remains UI-only. It does not paint Exact.
- Map still occupies first-screen height (93 chips). That is required by
  the HTML contract, not a regression.
- Numerical support stays on C5 / O9. No standalone “Numerical evidence”
  heading.
- Math fallback is present in the document. Live MathJax in a browser was
  not exercised in this pass (no browser driver in the worktree run).
- Duplicate completeness metrics are gone.

No certification status, inventory row, or derivation edge was edited to
make the page look greener.
