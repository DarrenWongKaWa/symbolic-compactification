# Third-party registry — Structural Observation Layer v1

No vendored copies. Prefer PyPI, then CLI, then container.

| backend | repo | version/commit | license | install | interface | capability | limitations |
|---|---|---|---|---|---|---|---|
| SymPy | github.com/sympy/sympy | 1.14.0 (dep `sympy>=1.12,<2`) | BSD-3-Clause | pip/uv | Python API | AST, CSE, poles, Piecewise, diff | `simplify()` not treated as truth |
| MatchPy | github.com/HPAC/matchpy | 0.5.5 | MIT | extra `observations` | Python API | AC/associative matching | last upstream 2024; one-to-one Pattern API |
| egglog-python | github.com/egraphs-good/egglog-python | installed wheel | MIT | extra `egraph` | Python API | named commute theory pack | Python ≥3.11; heavy extras; not a dump of all rewrites |
| egg / egglog core | github.com/egraphs-good/egg, egglog | via egglog-python | MIT | not linked directly | — | e-graphs | accessed only through egglog-python |
| frozen LGG | this repo `prototype/antiunify.py` | SHA `efc0924` | project license | in-tree wrap | Python import | LGG_FAMILY | optional if research/ not present |
| Cadabra2 | github.com/kpeeters/cadabra2 | — | GPL-3 | external `cadabra2` | subprocess | tensor/index (planned) | **UNAVAILABLE** here; GPL kept out-of-process |
| FORM | github.com/form-dev/form | — | GPL (COPYING) | external `form` | subprocess | large-expr inventory | **UNAVAILABLE** here; GPL out-of-process |
| Metatheory.jl | github.com/JuliaSymbolics/Metatheory.jl | — | MIT | Julia | not implemented | overlap with egglog | deferred; not mandatory |

FUTURE_ABSTRACTION_BACKEND (not preprocessing): DreamCoder/Stitch/babble; LLM proposers.
