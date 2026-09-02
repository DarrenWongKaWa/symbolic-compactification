# Table 2 — Guo full-paper flagship (depth)

Guo et al., *Phys. Rev. Lett.* **136**, 206303 (2026), arXiv:2511.16422v2.
Software: `v0.3.0-alpha`. Evidence: `archive/guo-full-paper-audit-flagship-v1`.
Public table: `examples/flagship/guo/RESULTS.md`.
Formative field validation, not held-out generalisation.
Not "189 equations proved."

| Quantity | Count |
|---|---|
| Numbered public equations inventoried | 189/189 |
| Derivation relations in the public table | 146 |
| Executable numbered relations | 53 |
| Local Leibniz helper (not a numbered-equation row) | 1 |
| `EXACT_ZERO` | 32 |
| `ZERO_UNDER_SUBSTITUTION` | 21 |
| `CERTIFIED_BY_RULE` (BZ periodic IBP) | 11 |
| `UNKNOWN_REMAINDER` | 17 |
| `STRUCTURAL` | 47 |
| `UNSUPPORTED` | 18 |
| `NONZERO` | 0 |
| False promotion on injected controls | 0/155 |

This is an equation-level audit and does not prove the paper or confirm
its physical conclusions.

Illustrative printed rows:

| Paper step | Class | Status |
|---|---|---|
| (D-59)→(D-60) regroup | exact algebra | `EXACT_ZERO` |
| (D-66)→(D-67) with \(\varepsilon_{21}=-\varepsilon_{12}\) | substitution | `ZERO_UNDER_SUBSTITUTION` |
| (D-114)→(D-119) BZ IBP | local Leibniz `ZERO` + torus rule | `CERTIFIED_BY_RULE` |
| (D-57) \(\Gamma\) remainder | author-declared remainder | `UNKNOWN_REMAINDER` |

The earlier selected-edge table is `archive/guo-selected-edge-validation-v1`,
a precursor, not the flagship public result.
