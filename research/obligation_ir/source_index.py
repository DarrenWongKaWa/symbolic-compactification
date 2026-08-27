"""Full-expression source inventory for Track B. Does not change SOL node cap."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import sympy
from sympy.core.function import AppliedUndef

from symbolic_compactification import parse_expression
from symbolic_compactification.models import AdapterError


@dataclass
class SourceNode:
    gid: str
    kind: str
    text: str
    srepr: str
    ops: int
    cond: str = ""
    h_factors: tuple[str, ...] = ()
    parent_gid: str = ""
    sol_node_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["h_factors"] = list(self.h_factors)
        return d


def _ops(e: sympy.Expr) -> int:
    try:
        return int(sympy.count_ops(e))
    except Exception:
        return 0


def _h_factors(expr: sympy.Expr) -> tuple[str, ...]:
    hs = []
    for sub in sympy.preorder_traversal(expr):
        if isinstance(sub, AppliedUndef) and type(sub).__name__ in {"h1", "h2"}:
            hs.append(str(sub))
    return tuple(sorted(set(hs)))


def _cond_key(cond: sympy.Expr) -> str:
    if cond is True or cond == sympy.true:
        return "True"
    return sympy.srepr(cond)


class SourceIndex:
    def __init__(self, nodes: list[SourceNode], *, root_text: str = ""):
        self.nodes = nodes
        self.root_text = root_text
        self.by_gid = {n.gid: n for n in nodes}
        self.by_srepr = {}
        for n in nodes:
            self.by_srepr.setdefault(n.srepr, []).append(n)
        self.by_text = {}
        for n in nodes:
            self.by_text.setdefault(n.text, []).append(n)

    def to_dict(self) -> dict[str, Any]:
        return {"n": len(self.nodes), "nodes": [n.to_dict() for n in self.nodes]}


def build_index(
    expression: str,
    symbols: list,
    functions: Optional[list] = None,
    *,
    sol_nodes: Optional[list[dict]] = None,
) -> SourceIndex:
    expr = parse_expression(expression, symbols, functions=functions or None)
    nodes: list[SourceNode] = []
    n = 0

    def add(kind: str, e: sympy.Expr, *, cond: str = "", parent: str = "",
            h: tuple[str, ...] = ()) -> SourceNode:
        nonlocal n
        n += 1
        gid = f"G{n:04d}"
        node = SourceNode(
            gid=gid,
            kind=kind,
            text=str(e),
            srepr=sympy.srepr(e),
            ops=_ops(e),
            cond=cond,
            h_factors=h or _h_factors(e),
            parent_gid=parent,
        )
        nodes.append(node)
        return node

    add("root", expr)
    terms = list(sympy.Add.make_args(expr))
    for t in terms:
        hs = _h_factors(t)
        if isinstance(t, sympy.Sum):
            snode = add("sum", t, h=hs)
            summand = t.args[0] if t.args else t
            if isinstance(summand, sympy.Piecewise):
                pnode = add("piecewise", summand, parent=snode.gid, h=hs)
                for arg in summand.args:
                    bexpr, bcond = arg
                    add(
                        "piecewise_branch",
                        bexpr,
                        cond=_cond_key(bcond),
                        parent=pnode.gid,
                        h=hs,
                    )
            else:
                add("summand", summand, parent=snode.gid, h=hs)
        elif isinstance(t, sympy.Piecewise):
            pnode = add("piecewise", t, h=hs)
            for arg in t.args:
                bexpr, bcond = arg
                add(
                    "piecewise_branch",
                    bexpr,
                    cond=_cond_key(bcond),
                    parent=pnode.gid,
                    h=hs,
                )
        else:
            add("term", t, h=hs)

    seen_pg = set()
    for sub in sympy.preorder_traversal(expr):
        if getattr(sub, "func", None) is sympy.polygamma:
            key = sympy.srepr(sub)
            if key in seen_pg:
                continue
            seen_pg.add(key)
            add("polygamma", sub)

    if sol_nodes:
        by_s = {n.srepr: n for n in nodes}
        by_id = {}
        for sn in sol_nodes:
            sr = sn.get("srepr")
            nid = sn.get("node_id") or ""
            if sr and sr in by_s and not by_s[sr].sol_node_id:
                by_s[sr].sol_node_id = nid
            tx = sn.get("text")
            if tx:
                hits = [n for n in nodes if n.text == tx and not n.sol_node_id]
                if len(hits) == 1:
                    hits[0].sol_node_id = nid
            if nid:
                by_id[nid] = sn
        have_ids = {n.sol_node_id for n in nodes if n.sol_node_id}
        for sn in sol_nodes:
            nid = sn.get("node_id") or ""
            if not nid or nid in have_ids:
                continue
            n += 1
            gid = f"G{n:04d}"
            nodes.append(SourceNode(
                gid=gid,
                kind="sol_node",
                text=str(sn.get("text") or ""),
                srepr=str(sn.get("srepr") or ""),
                ops=int(sn.get("ops") or 0),
                sol_node_id=nid,
            ))
    return SourceIndex(nodes, root_text=str(expr))
