# Owner: V5 — special-function localization

Polygamma-local identities already in SymPy. Do not invent masters.

`classify_identity(expr_or_pair)` → `supported` | `unsupported` | `UNKNOWN`.

Admitted:

- `d/dz polygamma(n, z) = polygamma(n + 1, z)`
- Newton first DD of `polygamma(0, ·)` vs `(psi(x) - psi(y))/(x - y)`

No Φ_Γ, no L4–L7. Guo-scale confluence is not classified as `supported`.
