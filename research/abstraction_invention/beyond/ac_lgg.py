"""E-LGG for AC: canonicalize, then frozen first-order LGG.

Does not modify prototype/antiunify.py.
"""
from __future__ import annotations

import sympy

from research.abstraction_invention.beyond.canonicalize import canon_ac, canon_pipeline
from research.abstraction_invention.prototype.antiunify import lgg_pair


def lgg_after_canon(e1: sympy.Expr, e2: sympy.Expr, *, expand: bool = False):
    c1 = canon_pipeline(e1) if expand else canon_ac(e1)
    c2 = canon_pipeline(e2) if expand else canon_ac(e2)
    if c1 == c2:
        class _Exact:
            template = c1
            substitutions = {}
            n_holes = 0
            ops_kept = int(sympy.count_ops(c1))
            def useful(self):
                return False  # exact match after canon, not an invented hole
            def trivial(self):
                return True
            exact_after_canon = True
        return _Exact()
    g = lgg_pair(c1, c2)
    g.exact_after_canon = False  # type: ignore
    return g
