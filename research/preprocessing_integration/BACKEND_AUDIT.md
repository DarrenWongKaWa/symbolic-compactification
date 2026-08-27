# Backend audit

Date: 2026-08-27. Infrastructure line; not a scientific paper result.

| backend | capability | maintained? | language | license | integration |
|---|---|---|---|---|---|
| SymPy | CAS / AST / CSE / diff | yes | Python | BSD-3 | required dependency |
| MatchPy | AC matching | low (PyPI 0.5.5, 2021/patches 2024) | Python | MIT | optional extra |
| egglog-python | e-graphs | yes | Python/Rust | MIT | optional extra |
| Cadabra2 | tensors / indices | yes | C++/Python | GPL-3 | optional CLI |
| FORM | huge expressions | yes | C | GPL | optional CLI |
| Metatheory.jl | eqsat | yes | Julia | MIT | not in v1 (overlap egglog) |

GPL programs are **not** linked into the Python package. They are probed
via `shutil.which` and subprocess only.

Wolfram Mathematica is **not** in the open-source core (existing Wolfram
*text* adapter is translation only).
