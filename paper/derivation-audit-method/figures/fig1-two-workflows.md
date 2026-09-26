# Figure 1 — One typed evidence graph, two workflows

Skill: `figure-designer` (HKUSTDial/Supervisor-Skills).
This is the paper's conceptual overview and the running example of the two
scientific tasks. It is a hybrid of Motivated Example (Paradigm B, side by
side) and Solution Overview (shared centre layer). It is **not** a pipeline
bar chart and **not** a performance teaser.

Old `fig1-architecture.md` (untyped list vs typed Guo fragment) is superseded
as Figure 1. That Guo fragment moves to Figure 4.

---

### 1. Figure type

- Type: motivated-example (with solution-overview centre)
- Reason: reviewers must see in 30 seconds that the product is one graph
  used in two directions, not "a paper-checking tool."

### 2. Paradigm recommendation

- Paradigm: Existing-vs-Ours layout adapted to **two modes of the same method**
- Why: the contribution is a structural change (shared evidence object),
  not a score on one input.
- Alternatives rejected:
  - Running-example-plus-failure-case alone: would re-centre Guo and revert
    to audit-only storytelling.
  - Performance teaser: no leaderboard metric exists.

### 3. Layout sketch

- Canvas: landscape, ~180 mm × 90 mm (two-column width, not a large canvas
  with tiny fonts).
- LEFT panel (Forward Mode), top-to-bottom:
  1. `E_t` + papers / notes / assumptions / objective
  2. candidate proposals `{H_i}` (dashed box; label **untrusted**)
  3. typed grounding → obligation
  4. fail-closed verifier
  5. `ZERO` / `NONZERO` / `UNKNOWN`
  6. only admissible candidates → `E_{t+1}`
  7. loop arrow back to step 1
- RIGHT panel (Retrospective Audit), top-to-bottom:
  1. published path `E_1 → … → E_N`
  2. equation inventory (labels, not algebra)
  3. typed existing edges
  4. parallel verification
  5. generated reviewer tables
- CENTRE band (shared):
  - title: **Typed evidence graph**
  - edge: \(\gamma=(e_{\mathrm{from}},e_{\mathrm{to}},\tau,\rho,A)\)
  - two axes: claim semantics \(\tau\) ≠ certificate provenance \(c\)
  - authority: proposal ≠ verification
- Arrows from both panels into the centre band and back out.
- Colour: left = ColorBrewer Set2 teal; right = ColorBrewer Set2 orange;
  centre = grey band. Dual-encode with left/right labels, not colour alone.

### 4. Labelling

- Element names: Forward derivation; Retrospective audit; Typed evidence
  graph; Untrusted proposals; Fail-closed verifier; Generated tables.
- No "Module A/B/C" placeholders.
- Critical highlight: dashed "untrusted" on proposals; solid "authority" on
  verifier; a small lock on `TABLE_VERIFIED`.
- Font: ≥ 9 pt after scaling; serif to match the paper.
- Palette: ColorBrewer qualitative (Set2), colour-blind safe.

### 5. Tool suggestion

- Primary: draw.io / diagrams.net, export SVG + PDF.
- Alternative: PowerPoint → PDF.
- Not Matplotlib.

### 6. Universal rule audit (spec)

- [ ] Vector format: specified PDF/SVG (user must verify after drawing)
- [ ] Font size ≥ 8 pt: specified 9 pt (user must verify after scaling)
- [ ] Colour-blind safe: Set2 + text labels
- [ ] Self-contained caption: first sentence is the finding
- [ ] Honest axis range: n/a
- [ ] No chartjunk: no 3D, no shadows, no decorative AI art

Caption (finding first):

> Figure 1. Constructing a derivation and auditing a manuscript are opposite
> operations on one typed evidence graph. Left: untrusted candidates may
> advance `E_t` only after fail-closed verification. Right: an existing path
> is inventoried, typed, and verified in parallel; reviewer tables are
> generated from integrity-bound records. Centre: the same edge object
> \(\gamma=(e_{\mathrm{from}},e_{\mathrm{to}},\tau,\rho,A)\) and the same
> authority split.

### 7. Integrity gate

- Gate 1 paradigm matches type: pass (hybrid documented)
- Gate 2 layout drawable from sketch: pass
- Gate 3 real names: pass
- Gate 4 tool matches complexity: pass
- Gate 5 vision rules: user-verify after drawing
- Gate 6 running example matches Introduction: **user-verify**
- Gate 7 n/a (not a results chart)

### 8. Severity

- 0 CRITICAL. Action: draw vector SVG/PDF; do not ship this markdown as the figure.
