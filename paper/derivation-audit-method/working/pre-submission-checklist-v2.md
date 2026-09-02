# Pre-submission checklist v2

Do **not** run `pre-submission-reviewer` until the items below are frozen.
This pass produced a restructured manuscript and specifications, not a
camera-ready submission.

## Blockers (must be true before that skill)

- [ ] Target venue selected by the author (`working/venue-v2.md` recommends
      CPC, second SciPost Physics Codebases).
- [ ] Vector figures exist (SVG/PDF) for Figures 1–4 from
      `figures/fig1-two-workflows.md`, `fig2-two-axis.md`,
      `fig3-forward-mode.md`, `fig4-guo-audit.md`. Markdown specs are not
      figures.
- [ ] Page layout exists (LaTeX for CPC or the chosen venue class).
- [ ] Reference list is final after an independent citation pass on the
      frozen PDF, not only on this markdown.
- [ ] Author confirms Guo accounting: 25 paper steps; 18 paper-level ZERO
      (12 DIRECT + 6 SUBST); 19 complete-run ZERO with Leibniz helper.
- [ ] Author confirms Forward Mode wording: implemented workflow +
      experimental proposer, not autonomous discovery.
- [ ] Author confirms unpublished private manuscripts remain excluded.

## Recommended later pass (when blockers clear)

1. `figure-designer` audit against the drawn SVGs (vision rules).
2. Independent citation verification (Rung 1 sub-agent) on the LaTeX
   reference list.
3. `pre-submission-reviewer` on the compiled PDF: macro logic, writing,
   grammar, LaTeX, figure quality.
4. Optional second `paper-polish` after reviewer comments, not before
   figures exist.

## Not blockers for the present draft-v2 markdown

- Engineering freeze (already closed).
- New experiments (forbidden).
- Venue submission (forbidden in this task).
