# Verification scopes

A ZERO residual is encoded-expression equality under declared symbols.
It is not automatically:

- a correct translation of the paper source
- a domain certificate
- a licence to swap summation order, commute operators, or drop boundary terms
- a proof of an `O(·)` remainder
- an improvement of compactness

| Relation | What the engine may certify |
|---|---|
| Pointwise identity | Residual zero on the same variables, domain, and assumptions |
| Sum identity | Not automatic; index range, relabelling, and multiplicity stay obligations |
| Integral identity | Not automatic; boundary terms stay obligations |
| Coefficient identity | That coefficient only, never the remainder |
| New definition | Unfolded residual may be ZERO; cyclic or wrapping names are not an improvement |

Do not silently add assumptions (`x ≥ 0`) to manufacture ZERO for `√(x²)=x`.
Do not treat `AB` as `BA` without a declared commutative type.
