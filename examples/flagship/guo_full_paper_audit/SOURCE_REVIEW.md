# Independent source review

Reviewers read `source_anchors/main.tex` after the first relation freeze. They were forbidden from assigning ZERO.

## Numbering

Route A (TeX counters) and Route B (arXiv HTML `ltx_tag_equation` / `ltx_tag_equationgroup`) both give 189 printed numbers, 1-8 then A-9 through G-189, no gaps. Appendix D begins at (D-57). No numbering discrepancy.

## Relation corrections (before rerun)

Added because the independent read found source support that the first freeze omitted:

- Eq. (A-9) as a standalone definition
- Eq. (A-17) -> Eqs. (A-19), (A-20) divided-difference definitions
- Eqs. (B-21), (B-22) $O(A^3)$ expansions
- Eq. (C-28) polygamma-argument definition
- Eqs. (D-58), (D-80) as presented $K$-formulae
- Eq. (E-129) off-diagonal second-derivative identity
- Eq. (F-169) -> Eq. (F-170) Berry-connection rewrite

No adjacency pair was added without prose.

## Transcription / harness corrections (not residual retuning)

- Identifier harvest for Mode A `assumptions.yaml` now scans frozen tokens. The first pass missed `e12` (scientific-notation parse) and several `g_{ab}` symbols, which failed closed as PARSE_FAILURE.
- Eq. (D-105) residual compares the Feynman-Hellmann / $\epsilon_{21}=-\epsilon_{12}$ members. The last paper equality $A_{12}^a A_{21}^b+A_{21}^a A_{12}^b=2g_{ab}$ is the declared metric convention, not an independent ZERO.
- Injected `sign` / `times_two` controls are skipped when the right-hand side is identically 0, because those mutations of 0 remain 0. `plus_one` is kept.

No residual was rewritten after a NONZERO to manufacture ZERO.
