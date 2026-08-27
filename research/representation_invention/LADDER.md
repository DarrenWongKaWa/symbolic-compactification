# Representation ladder (frozen)

R-level is an **evaluation** label. It is not shown to the proposer as a
target menu beyond the allowed `representation_type` strings.

Do not assume Guo reaches every level.

| level | name | operational test |
|---|---|---|
| R0 | Local confluence | `limit(generic, var → point) == degenerate` on grounded members |
| R1 | Newton first DD | explicit `F[x,y] = (F(x)-F(y))/(x-y)` equals a grounded member |
| R2 | Repeated-node DD | `F[x,x] = F'(x)` and/or `F[x,x,y]` with stated multiplicities |
| R3 | Higher Hermite DD | multiple repeated nodes / higher degeneracy, explicit formula |
| R4 | Piecewise→DD | several Piecewise branches reconstructed as one DD family |
| R5 | Special-function DD | same as R1–R4 with special F (e.g. polygamma) |
| R6 | Master object | ≥2 distinct grounded members from one F via nontrivial operators |
| R7 | Sector compactification | a scientific sector via a small master set |
| R8 | Generator / basis | geometric or symmetry-adapted representation |

## Guo DEV boundaries (evaluation only)

| G | meaning |
|---|---|
| G0 | grounded local relation |
| G1 | multiple local confluence relations (P1 already) |
| G2 | explicit Newton DD |
| G3 | explicit Hermite / repeated-node DD |
| G4 | one master explains multiple branch families |
| G5 | small master library across sectors |
| G6 | geometric / invariant generators |

P1 at `3fea222` is G1, not G2.

Human L4–L7 labels are **not** proposer targets.
