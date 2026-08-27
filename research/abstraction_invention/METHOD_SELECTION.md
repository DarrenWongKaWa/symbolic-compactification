# Method selection (after v0.2 DEV, before TEST freeze)

Chosen **one primary** extra mechanism: **operator-aware relation graph
(B5) plus canonicalization control (B3/B4) and LGG quality filter (B2).**

Not HO-pattern AU. Not DreamCoder. Not a new residual rule.

## Why

DEV v0.2:

- **F2 distributivity:** expand-canon makes `F(x*(y+z))` and `F(x*y+x*z)`
  identical. Raw LGG is the wrong tree. This is CASE A for T2: not invention.
- **F3 derivative:** relation graph finds `d/dz` polygamma; LGG only holes
  the order.
- **F3 permutation:** `T(i,j)` vs `T(j,i)` is a permutation edge; zip-LGG
  can emit `T(theta,theta)`.
- **F1:** score ranks the Guo polygamma family above `I*mu*theta0` without
  gold. Shallow keep-filter is imperfect.

## Targets

F1 ranking, F2 canon, F3/F4 operator edges.

## Already solved in literature

AC-canon, Plotkin LGG, sympy.diff. We assemble them under frozen B9/LGG
baselines.

## Experimental remainder

F5–F8 (confluence as representation change, generators, libraries).

## Falsification

If TEST F2 positives are not recovered by B3, or F3 permutation/derivative
positives have no graph edge, the selection is wrong.

LLM remains BLOCKED — cannot choose CASE D.
