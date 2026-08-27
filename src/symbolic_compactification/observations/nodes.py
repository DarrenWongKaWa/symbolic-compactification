"""Shared node inventory (SymPy-canonical when representable)."""
from __future__ import annotations

from collections import OrderedDict

import sympy
from sympy.core.function import AppliedUndef

from symbolic_compactification.models import sha256_text
from symbolic_compactification.observations.ir import ExpressionNode
from symbolic_compactification.structure import ordered_atoms

_MAX_NODES = 80


def make_nodes(expr: sympy.Expr, *, cap: int = _MAX_NODES) -> list[ExpressionNode]:
    seen: OrderedDict[str, ExpressionNode] = OrderedDict()
    n = 0
    for sub in sympy.preorder_traversal(expr):
        if not getattr(sub, "args", ()):
            continue
        key = sympy.srepr(sub)
        if key in seen:
            continue
        n += 1
        nid = f"N{n:04d}"
        fns = sorted({
            type(a).__name__
            for a in sympy.preorder_traversal(sub)
            if isinstance(a, AppliedUndef)
        })
        idx = sorted({
            str(a.args[0])
            for a in sympy.preorder_traversal(sub)
            if isinstance(a, AppliedUndef) and a.args
        })
        try:
            ops = int(sympy.count_ops(sub))
        except Exception:
            ops = 0
        seen[key] = ExpressionNode(
            node_id=nid,
            text=str(sub),
            srepr=key,
            structural_hash=sha256_text(key),
            free_symbols=sorted(s.name for s in sub.free_symbols),
            functions=fns,
            indexed_symbols=idx,
            ops=ops,
            provenance="sympy_ast",
        )
        if len(seen) >= cap:
            break
    # always include the root
    root_key = sympy.srepr(expr)
    if root_key not in seen:
        seen[root_key] = ExpressionNode(
            node_id="N0000",
            text=str(expr),
            srepr=root_key,
            structural_hash=sha256_text(root_key),
            free_symbols=sorted(s.name for s in expr.free_symbols),
            functions=sorted({
                type(a).__name__ for a in sympy.preorder_traversal(expr)
                if isinstance(a, AppliedUndef)
            }),
            ops=int(sympy.count_ops(expr)),
            provenance="sympy_ast",
        )
    return list(seen.values())


def index_by_srepr(nodes: list[ExpressionNode]) -> dict[str, str]:
    return {n.srepr: n.node_id for n in nodes}


def index_by_text(nodes: list[ExpressionNode]) -> dict[str, str]:
    return {n.text: n.node_id for n in nodes}
