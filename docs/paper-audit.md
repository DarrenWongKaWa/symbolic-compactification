# Paper audit

A paper audit is a typed check of author-claimed derivations, not a
score of the paper. Public audit demos under `examples/audit/` and
`tests/fixtures/audit_demos/` are synthetic. They are not unpublished
manuscripts.

1. Inventory numbered equations (printed numbers, not TeX labels).
2. Record only source-supported relations. Adjacent numbering is not a
   derivation.
3. Lower what the frozen engine can check.
4. Emit a human-readable table. `ZERO` is generated, never authored.

```bash
cp -R examples/audit/minimal /tmp/ssc-audit
symbolic-compactification audit verify /tmp/ssc-audit
symbolic-compactification audit table /tmp/ssc-audit
```

For a reviewer-facing export, run:

```bash
symbolic-compactification audit package /tmp/ssc-audit
```

Open `reviewer-verification-package/REVIEWER_SUMMARY.html` first. It is a
pre-generated, offline overview of evidence counts, provenance, and the
unresolved queue for readers who do not run the replay. The matching
`REVIEWER_SUMMARY.md` is the plain-text version. These files are generated
from machine records and do not create or upgrade verification statuses.

That toy workspace contains:

- a definition (`STRUCTURAL`)
- two exact Laurent-coefficient identities (`ZERO`)
- an enclosing `O(g)` remainder (`UNKNOWN`)

Finite coefficient `ZERO` is not a remainder proof.

## Many-body papers: step cards in a reviewer package

For a many-body paper, the fastest route is to draft step cards straight
from the LaTeX source and put them into an audit as `STEP_CARD` edges:

```bash
symbolic-compactification manybody draft manuscript/source.tex --out cards/
# fill cards/conventions.yaml once; set each card's check
# list the cards in edges/edges.yaml as STEP_CARD edges
symbolic-compactification audit verify .
symbolic-compactification audit package .
```

`tests/fixtures/audit_demos/S` is a complete synthetic example with one
planted error. In the reviewer summary, each step card shows:
- the claim as written, rendered from the manuscript's LaTeX (MathML, so
  no script and no network);
- where it comes from: the paper title, file, line, equation number and
  `\label`;
- the claim as the tool read it, what the tool computed, and a
  counterexample with a diagnosis when the step fails.

A formula that cannot be read as printed, for example one with an
unbalanced bracket, is not decided. A card may declare a bracket-only
`erratum`: the tool checks that only bracket characters differ, and the
page shows the printed and corrected forms side by side with the verdict
after correction. The conventions table lists the notation and
definitions, the only hand-written link, so a reviewer checks it once.
[`case-study-jwm.md`](case-study-jwm.md) runs this on a classic Keldysh
paper.

Equation numbers are counted from the order of numbered displays in the
source. Appendices are numbered A1, B2, and so on. Check them against the
typeset paper before you cite them.

## Historical paper cases

Paper-specific ledgers are not part of the default skill or CI path.
They live under [`research-cases/`](../research-cases/README.md).

## Semantics

`ZERO` is never `CERTIFIED_BY_RULE`. Brillouin-zone integration by parts
is a local Leibniz `ZERO` plus a declared torus rule. See
[semantics.md](semantics.md) and [edge-types.md](edge-types.md).

Only obligations returning exact ZERO may appear as machine-verified.
