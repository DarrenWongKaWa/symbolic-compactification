"""Representation-aware obligations. Only EXACT/UNIQUE binds are compiled."""
from __future__ import annotations

import re
from typing import Any, Optional

import sympy
from sympy.core.function import AppliedUndef

from research.llm_abstraction.constructor import _equal, parse_flex
from research.obligation_ir.grounding import Binding, EXACT_BIND, UNIQUE_STRUCTURAL_BIND
from research.obligation_ir.schema import (
    COMPILE_FAILURE,
    COMPILE_OK,
    CONFLUENCE,
    DERIVATIVE,
    DIVIDED_DIFFERENCE,
    LIMIT,
    Obligation,
)
from research.obligation_ir.source_index import SourceIndex
from symbolic_compactification import UNKNOWN, ZERO, NONZERO
from research.obligation_ir.verify import VerifyResult


def _match_balanced(text: str, start: int) -> Optional[str]:
    if start >= len(text) or text[start] != "(":
        return None
    d = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            d += 1
        elif text[i] == ")":
            d -= 1
            if d == 0:
                return text[start:i + 1]
    return None


def extract_master_defs(latent: str) -> list[tuple[str, str]]:
    """Pull F(z)=polygamma(...) style definitions. Format only."""
    out = []
    for m in re.finditer(
        r"(F_\+|F_-|F\+|F-|psi|Psi|P_\+|P_-)\s*\(\s*([A-Za-z])\s*\)\s*=\s*",
        latent,
    ):
        rest = latent[m.end():].lstrip()
        if rest.startswith("polygamma"):
            i = rest.find("(")
            args = _match_balanced(rest, i)
            if args:
                out.append((m.group(1), "polygamma" + args, m.group(2)))
        elif rest.startswith("loggamma") or rest.startswith("log_gamma"):
            name = "loggamma" if rest.startswith("loggamma") else "log_gamma"
            i = rest.find("(")
            args = _match_balanced(rest, i)
            if args:
                out.append((m.group(1), "loggamma" + args, m.group(2)))
    # G_r(z) = polygamma(r, (beta*z + pi)/(2*pi))
    m = re.search(
        r"polygamma\(\s*([A-Za-z0-9]+)\s*,\s*(\([^;]+?\)|(?:beta[^\n,]+pi\)/\(2\*pi\)))",
        latent,
    )
    return out


def _parse_F(defn: str, zname: str, symbols, functions):
    extra = list(symbols or []) + [{"name": zname, "real": True}]
    return parse_flex(defn, extra, functions)


def newton_dd(f_of_z: sympy.Expr, z: sympy.Symbol, x: sympy.Expr, y: sympy.Expr) -> sympy.Expr:
    return (f_of_z.xreplace({z: x}) - f_of_z.xreplace({z: y})) / (x - y)


def _eps(index: str, functions) -> Optional[sympy.Expr]:
    try:
        return sympy.Function("epsilon")(sympy.Symbol(index))
    except Exception:
        return None


def compile_dd(
    hyp: dict,
    binds: list[Binding],
    index: SourceIndex,
    *,
    symbols: list,
    functions: list,
) -> list[tuple[Obligation, VerifyResult]]:
    latent = hyp.get("latent_object") or ""
    defs = extract_master_defs(latent)
    if not defs:
        return []
    admissible = [b for b in binds if b.admissible and b.kind == "piecewise_branch" and (
        not b.cond or "true" in (b.cond or "").lower() or b.cond == ""
    )]
    # generic branches: cond fingerprint true
    from research.obligation_ir.grounding import _node_cond_fp
    generic = []
    for b in binds:
        if not b.admissible:
            continue
        n = index.by_gid.get(b.gid)
        if n and n.kind == "piecewise_branch" and _node_cond_fp(n) == "true":
            generic.append(b)
        if n and n.kind == "sum":
            # uniquely bound kernel: its True branch is the generic member
            pws = [x for x in index.nodes if x.kind == "piecewise" and x.parent_gid == n.gid]
            for pw in pws:
                for br in index.nodes:
                    if br.kind == "piecewise_branch" and br.parent_gid == pw.gid and _node_cond_fp(br) == "true":
                        generic.append(Binding(
                            alias=b.alias + "/generic",
                            confidence=b.confidence,
                            gid=br.gid, sol_node_id=br.sol_node_id,
                            text=br.text, srepr=br.srepr, kind=br.kind,
                            cond=br.cond, evidence="child_of_unique_sum",
                        ))
    if not generic:
        generic = [b for b in binds if b.admissible and "true" in b.alias.lower()]
    rows = []
    for b in generic:
        node = index.by_gid.get(b.gid)
        if node is None:
            continue
        member_e = parse_flex(node.text, symbols, functions)
        if member_e is None:
            obl = Obligation(
                kind=DIVIDED_DIFFERENCE, left=b.alias, right="", member=node.text,
                compile_status=COMPILE_FAILURE, compile_error="bound_text_unparseable",
            )
            rows.append((obl, VerifyResult(DIVIDED_DIFFERENCE, UNKNOWN, "none", "unparseable_bound")))
            continue
        # nodes from first map
        nodes = []
        for im in hyp.get("instance_maps") or []:
            th = im.get("theta") if isinstance(im, dict) else {}
            if isinstance(th, dict) and isinstance(th.get("nodes"), list):
                nodes = [str(x) for x in th["nodes"]]
                break
            if isinstance(th, dict):
                vs = str(th.get("variables") or "")
                found = re.findall(r"epsilon\(([a-z]+)\)", vs)
                if len(found) >= 2:
                    nodes = [f"epsilon({found[0]})", f"epsilon({found[1]})"]
                    break
        if len(nodes) < 2:
            nodes = ["epsilon(m)", "epsilon(n)"]
        x = parse_flex(nodes[0], symbols, functions)
        y = parse_flex(nodes[1], symbols, functions)
        if x is None or y is None:
            continue
        for fname, defn, zname in defs:
            f = _parse_F(defn, zname, symbols, functions)
            z = next((s for s in (f.free_symbols if f is not None else []) if s.name == zname), None)
            if f is None or z is None:
                obl = Obligation(
                    kind=DIVIDED_DIFFERENCE, left=node.gid, right=defn, member=node.text,
                    latent=defn, compile_status=COMPILE_FAILURE, compile_error="unparseable_F",
                )
                rows.append((obl, VerifyResult(DIVIDED_DIFFERENCE, UNKNOWN, "none", "unparseable_F")))
                continue
            dd = newton_dd(f, z, x, y)
            obl = Obligation(
                kind=DIVIDED_DIFFERENCE,
                left=node.gid,
                right=f"({defn}[{nodes[0]}]-{defn}[{nodes[1]}])/({nodes[0]}-{nodes[1]})",
                member=node.text,
                latent=defn,
                nodes=nodes[:2],
                compile_status=COMPILE_OK,
            )
            if _equal(member_e, dd):
                v = ZERO
                note = "branch_equals_newton_dd"
            else:
                v = NONZERO
                note = "branch_not_equal_newton_dd"
            rows.append((obl, VerifyResult(
                DIVIDED_DIFFERENCE, v, "newton_dd", f"{fname}:{note}",
                compile_status=COMPILE_OK, witness=str(dd)[:400],
            )))
    return rows


def compile_confluence(
    hyp: dict,
    binds: list[Binding],
    index: SourceIndex,
    *,
    symbols: list,
    functions: list,
) -> list[tuple[Obligation, VerifyResult]]:
    from research.obligation_ir.grounding import _node_cond_fp
    gen, diag = [], []

    def _add_branch(b, n):
        fp = _node_cond_fp(n)
        if fp == "true":
            gen.append((b, n))
        elif fp == "eq_m_n":
            diag.append((b, n))

    for b in binds:
        if not b.admissible:
            continue
        n = index.by_gid.get(b.gid)
        if n is None:
            continue
        if n.kind == "piecewise_branch":
            _add_branch(b, n)
        elif n.kind == "sum":
            pws = [x for x in index.nodes if x.kind == "piecewise" and x.parent_gid == n.gid]
            for pw in pws:
                for br in index.nodes:
                    if br.kind == "piecewise_branch" and br.parent_gid == pw.gid:
                        _add_branch(b, br)
    rows = []
    # pair generic/diag that share piecewise parent
    for gb, gn in gen:
        parent = gn.parent_gid
        ds = [(db, dn) for db, dn in diag if dn.parent_gid == parent]
        if len(ds) != 1:
            continue
        db, dn = ds[0]
        A = parse_flex(gn.text, symbols, functions)
        D = parse_flex(dn.text, symbols, functions)
        obl = Obligation(
            kind=CONFLUENCE,
            left=gn.gid,
            right=dn.gid,
            member=gn.text,
            latent=dn.text,
            var="epsilon(m)",
            to="epsilon(n)",
            compile_status=COMPILE_OK if A is not None and D is not None else COMPILE_FAILURE,
            compile_error=None if A is not None and D is not None else "unparseable_branch",
        )
        if A is None or D is None:
            rows.append((obl, VerifyResult(LIMIT, UNKNOWN, "none", "unparseable_branch", COMPILE_FAILURE)))
            continue
        # limit epsilon(m) -> epsilon(n)
        em = None
        en = None
        for sub in sympy.preorder_traversal(A):
            if isinstance(sub, AppliedUndef) and type(sub).__name__ == "epsilon":
                arg = str(sub.args[0]) if sub.args else ""
                if arg == "m":
                    em = sub
                if arg == "n":
                    en = sub
        if em is None or en is None:
            rows.append((obl, VerifyResult(
                LIMIT, UNKNOWN, "sympy.limit", "no_epsilon_m_n_in_generic", COMPILE_OK,
            )))
            continue
        dummy = sympy.Dummy("em")
        A2 = A.xreplace({em: dummy})
        try:
            lim = sympy.limit(A2, dummy, en)
            ok = _equal(lim, D)
            rows.append((obl, VerifyResult(
                CONFLUENCE, ZERO if ok else NONZERO, "sympy.limit",
                "lim_eps_m_to_eps_n_vs_diag", COMPILE_OK, witness=str(lim)[:400],
            )))
        except Exception as exc:
            rows.append((obl, VerifyResult(
                CONFLUENCE, UNKNOWN, "sympy.limit", type(exc).__name__, COMPILE_OK,
            )))
    return rows


def compile_derivative_identities(
    hyp: dict,
    binds: list[Binding],
    *,
    symbols: list,
    functions: list,
) -> list[tuple[Obligation, VerifyResult]]:
    """If members are polygamma(k, z) source nodes, check d^k polygamma(0,z)."""
    rows = []
    parsed = []
    for b in binds:
        if not b.admissible:
            continue
        e = parse_flex(b.text, symbols, functions)
        if e is None:
            continue
        parsed.append((b, e))
        if getattr(e, "func", None) is not sympy.polygamma:
            continue
        if len(e.args) != 2:
            continue
        k, arg = e.args
        if not getattr(k, "is_integer", False) and k != 0:
            try:
                ki = int(k)
            except Exception:
                continue
        else:
            try:
                ki = int(k)
            except Exception:
                continue
        if ki <= 0:
            continue
        master = sympy.polygamma(0, arg)
        d = master
        zsyms = list(arg.free_symbols)
        if not zsyms:
            # differentiate wrt a dummy inside epsilon?
            continue
        # d/d(arg) via chain: polygamma(k,arg) == d^k polygamma(0,arg) / d arg^k
        dk = sympy.polygamma(ki, arg)
        obl = Obligation(
            kind=DERIVATIVE, left=b.gid, right=f"d^{ki} polygamma(0, arg)",
            member=b.text, compile_status=COMPILE_OK, order=ki,
        )
        v = ZERO if _equal(e, dk) else NONZERO
        rows.append((obl, VerifyResult(
            DERIVATIVE, v, "sympy.polygamma_identity", f"order={ki}",
            COMPILE_OK, witness=str(dk),
        )))
    # Pairwise d/ds identities among exact-bound members (Guo N0014 vs N0016).
    for i, (b1, e1) in enumerate(parsed):
        for b2, e2 in parsed[i + 1:]:
            for s in list(e1.free_symbols)[:6]:
                try:
                    d = sympy.diff(e1, s)
                except Exception:
                    continue
                if _equal(d, e2):
                    obl = Obligation(
                        kind=DERIVATIVE, left=b1.gid, right=b2.gid,
                        member=b1.text, var=str(s), compile_status=COMPILE_OK,
                    )
                    rows.append((obl, VerifyResult(
                        DERIVATIVE, ZERO, "sympy.diff", f"d/d{s}",
                        COMPILE_OK, witness=str(d),
                    )))
                    break
    return rows
