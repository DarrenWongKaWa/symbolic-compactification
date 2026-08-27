"""Instantiate LLM hypotheses on parsed expressions. Fail-closed.

Does not modify frozen obligations.py. String substitution of single
letters into prose is forbidden; witnesses are SymPy identities only.
"""
from __future__ import annotations

import re
from typing import Any, Optional

import sympy
from sympy.core.function import AppliedUndef

from research.llm_abstraction.schema import LLMStructureHypothesis, OK
from symbolic_compactification import (
    NONZERO,
    UNKNOWN,
    ZERO,
    parse_expression,
    verify_equivalent,
)
from symbolic_compactification.budgets import BudgetExceeded, run_with_budget
from symbolic_compactification.models import AdapterError
from symbolic_compactification.parser import get_parse_policy

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_ALIASES = (
    (re.compile(r"\blog_gamma\b"), "loggamma"),
    (re.compile(r"\bLogGamma\b"), "loggamma"),
)
_SKIP_THETA_KEYS = {"order", "n", "n_diff", "times", "k"}  # only skipped for *diff repeat*, not always
_DIFF_REPEAT_KEYS = {"order", "n_diff", "times"}


_MAP_META = {"member", "O", "operator_on_template", "theta", "map", "note"}


def _theta(imap: Any) -> dict[str, str]:
    if not isinstance(imap, dict):
        return {}
    t = imap.get("theta") or imap.get("map") or {}
    if isinstance(t, dict) and t:
        return {str(k): str(v) for k, v in t.items()}
    return {
        str(k): str(v) for k, v in imap.items()
        if k not in _MAP_META and isinstance(v, (str, int, float))
    }


def _member(imap: Any, fallback: str = "") -> str:
    if isinstance(imap, dict):
        return str(imap.get("member") or fallback)
    return fallback


def _op_name(imap: Any, operators: list, member: str) -> str:
    if isinstance(imap, dict) and imap.get("O"):
        return str(imap.get("O")).lower()
    for op in operators or []:
        if isinstance(op, dict) and str(op.get("member")) == member:
            return str(op.get("O") or "identity").lower()
        if isinstance(op, str):
            return op.lower()
    if isinstance(imap, dict):
        return str(imap.get("operator_on_template") or "identity").lower()
    return "identity"


def _depth0_cut(text: str, seps: str) -> str:
    depth = 0
    out = []
    i = 0
    while i < len(text):
        c = text[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth = max(0, depth - 1)
        elif depth == 0 and c in seps:
            rest = text[i + 1:].lstrip()
            if not rest:
                break
            if rest[:1].islower() or rest.lower().startswith(
                ("a ", "an ", "the ", "with ", "where ", "which ", "viewed ")
            ):
                break
        out.append(c)
        i += 1
    return "".join(out).strip().rstrip(",")


def symbolic_core(text: str) -> str:
    """Format-only: take assignment RHS and drop trailing English."""
    t = (text or "").strip().strip("`")
    for pat, repl in _ALIASES:
        t = pat.sub(repl, t)
    if "=" in t:
        depth = 0
        last = t.rfind("=")
        # last depth-0 equals
        last = None
        depth = 0
        for i, c in enumerate(t):
            if c in "([{":
                depth += 1
            elif c in ")]}":
                depth = max(0, depth - 1)
            elif c == "=" and depth == 0:
                last = i
        if last is not None:
            t = t[last + 1:].strip()
    return _depth0_cut(t, ",.;")


def _policy_names() -> set[str]:
    pol = get_parse_policy()
    return set(pol["allowed_functions"]) | {"pi", "E", "I", "oo", "True", "False",
                                            "Sum", "Product", "Piecewise", "Eq",
                                            "Ne", "Lt", "Le", "Gt", "Ge", "And",
                                            "Or", "Not"}


_EXTRA_HEADS = {
    "loggamma": sympy.loggamma,
    "gamma": sympy.gamma,
    "digamma": sympy.digamma,
}


def parse_flex(text: str, symbols: list, functions: Optional[list]) -> Optional[sympy.Expr]:
    core = symbolic_core(text)
    if not core:
        return None
    hm = re.match(r"^(loggamma|gamma|digamma)\((.*)\)$", core)
    if hm:
        inner = parse_flex(hm.group(2), symbols, functions)
        if inner is not None:
            try:
                return _EXTRA_HEADS[hm.group(1)](inner)
            except Exception:
                return None
    declared_s = list(symbols or [])
    declared_f = list(functions or [])
    have_s = {s["name"] if isinstance(s, dict) else str(s) for s in declared_s}
    have_f = set(declared_f)
    reserved = _policy_names()
    idents = _IDENT.findall(core)
    for ident in idents:
        if ident in have_s or ident in have_f or ident in reserved:
            continue
        if re.search(rf"\b{re.escape(ident)}\s*\(", core):
            declared_f.append(ident)
            have_f.add(ident)
        else:
            declared_s.append({"name": ident, "real": True})
            have_s.add(ident)
        if len(declared_s) > 38:
            break
    try:
        expr = parse_expression(core, declared_s, functions=declared_f or None)
    except (AdapterError, Exception):
        return None
    if isinstance(expr, tuple) or not isinstance(expr, sympy.Expr):
        return None
    return expr


def _sym_named(expr: sympy.Expr, name: str) -> Optional[sympy.Symbol]:
    for s in expr.free_symbols:
        if s.name == name:
            return s
    return None


def instantiate(expr: sympy.Expr, theta: dict[str, str], symbols, functions) -> Optional[sympy.Expr]:
    out = expr
    for k, v in theta.items():
        if k in _DIFF_REPEAT_KEYS:
            continue
        dst = parse_flex(str(v), symbols, functions)
        src = _sym_named(out, k)
        if src is not None:
            if dst is None:
                return None
            out = out.xreplace({src: dst})
            continue
        hits = [
            s for s in sympy.preorder_traversal(out)
            if isinstance(s, AppliedUndef) and type(s).__name__ == k
        ]
        if not hits:
            continue
        for s in hits:
            if dst is not None:
                out = out.xreplace({s: dst})
            elif _IDENT.fullmatch(str(v)):
                out = out.xreplace({s: sympy.Function(str(v))(*s.args)})
            else:
                return None
    return out


def _swap_applied(expr: sympy.Expr) -> sympy.Expr:
    if isinstance(expr, AppliedUndef) and len(expr.args) == 2:
        return expr.func(expr.args[1], expr.args[0])
    found = None
    for sub in sympy.preorder_traversal(expr):
        if isinstance(sub, AppliedUndef) and len(sub.args) == 2:
            found = sub
            break
    if found is None:
        return expr
    swapped = found.func(found.args[1], found.args[0])
    return expr.xreplace({found: swapped})


def _swap_two_symbols(expr: sympy.Expr, names: list[str] | None = None) -> sympy.Expr:
    if names and len(names) >= 2:
        a = _sym_named(expr, names[0])
        b = _sym_named(expr, names[1])
        if a is not None and b is not None:
            tmp = sympy.Dummy()
            return expr.xreplace({a: tmp}).xreplace({b: a, tmp: b})
    syms = [s for s in expr.free_symbols if s.name not in {"pi", "E"}]
    if len(syms) < 2:
        return expr
    a, b = list(syms)[:2]
    tmp = sympy.Dummy()
    return expr.xreplace({a: tmp}).xreplace({b: a, tmp: b})


def _diff_repeat(expr: sympy.Expr, var: sympy.Symbol, n: int) -> sympy.Expr:
    out = expr
    for _ in range(max(1, n)):
        out = sympy.diff(out, var)
    return out


def _equal(a: sympy.Expr, b: sympy.Expr) -> bool:
    if a == b:
        return True
    try:
        if sympy.expand(a - b) == 0:
            return True
    except Exception:
        pass
    try:
        if sympy.simplify(a - b) == 0:
            return True
    except Exception:
        pass
    return False


def _verify_pair(member_text: str, cand: sympy.Expr, symbols, functions) -> str:
    mem = parse_flex(member_text, symbols, functions)
    if mem is None:
        return UNKNOWN
    if _equal(mem, cand):
        return ZERO
    try:
        r = run_with_budget(
            verify_equivalent,
            (str(mem), str(cand), symbols),
            kwargs={"functions": functions or None},
            seconds=6.0,
            operation="llm_obligation",
        )
        return r.verdict
    except (BudgetExceeded, AdapterError, Exception):
        return NONZERO if mem is not None else UNKNOWN


def construct_and_verify(
    hyp: LLMStructureHypothesis,
    symbols: list,
    functions: list | None,
) -> dict[str, Any]:
    functions = functions or []
    if hyp.parse_status != OK:
        return {
            "constructable": False,
            "certified": False,
            "n_zero": 0, "n_nonzero": 0, "n_unknown": 1,
            "obligations": [],
            "note": hyp.parse_error or "parse_failure",
        }
    maps = list(hyp.instance_maps or [])
    if not maps and hyp.target_members:
        maps = [{"member": m, "theta": {}, "O": "identity"} for m in hyp.target_members]
    tmpl = parse_flex(hyp.latent_object, symbols, functions)
    results = []
    n_zero = n_nz = n_unk = 0
    for imap in maps:
        member = _member(imap)
        theta = _theta(imap)
        op = _op_name(imap, hyp.operators, member)
        if tmpl is None:
            n_unk += 1
            results.append({
                "member": member, "instantiated": symbolic_core(hyp.latent_object),
                "operator": op, "verdict": UNKNOWN, "note": "unparseable_latent",
            })
            continue
        inst = instantiate(tmpl, theta, symbols, functions)
        cands: list[tuple[str, Optional[sympy.Expr]]] = [("instantiate", inst)]
        if any(k in op for k in ("d/d", "diff", "deriv")):
            nrep = 1
            for k in _DIFF_REPEAT_KEYS:
                if k in theta:
                    try:
                        nrep = int(float(theta[k]))
                    except (TypeError, ValueError):
                        nrep = 1
            var = None
            for k in theta:
                if k in _DIFF_REPEAT_KEYS:
                    continue
                var = _sym_named(tmpl, k)
                if var is not None:
                    break
            if var is None and tmpl.free_symbols:
                var = next(iter(tmpl.free_symbols))
            if var is not None:
                try:
                    d = _diff_repeat(tmpl, var, nrep)
                    cands.append(("diff_then_instantiate", instantiate(d, theta, symbols, functions)))
                    if inst is not None:
                        v2 = _sym_named(inst, var.name)
                        if v2 is not None:
                            cands.append(("instantiate_then_diff", _diff_repeat(inst, v2, nrep)))
                except Exception:
                    pass
        if "perm" in op or op == "swap":
            keys = [k for k in theta if k not in _DIFF_REPEAT_KEYS]
            if inst is not None:
                cands.append(("permute_inst_args", _swap_applied(inst)))
                cands.append(("permute_inst_syms", _swap_two_symbols(inst, keys)))
            cands.append(("permute_tmpl_then_inst", instantiate(_swap_applied(tmpl), theta, symbols, functions)))
            cands.append(("permute_tmpl_syms", instantiate(_swap_two_symbols(tmpl, keys), theta, symbols, functions)))

        verdict = UNKNOWN
        note = "no_candidate"
        used = None
        saw_nonzero = False
        for label, cand in cands:
            if cand is None:
                continue
            v = _verify_pair(member, cand, symbols, functions)
            if v == ZERO:
                verdict = ZERO
                note = label
                used = cand
                break
            if v == NONZERO:
                saw_nonzero = True
                used = cand
                note = label
        else:
            if saw_nonzero:
                verdict = NONZERO
            else:
                verdict = UNKNOWN
        if verdict == ZERO:
            n_zero += 1
        elif verdict == NONZERO:
            n_nz += 1
        else:
            n_unk += 1
        results.append({
            "member": member,
            "instantiated": str(used) if used is not None else symbolic_core(hyp.latent_object),
            "operator": op,
            "verdict": verdict,
            "note": note,
        })
    certified = n_zero >= 1 and n_nz == 0 and n_unk == 0 and n_zero == len(results)
    return {
        "constructable": bool(results) and n_unk < len(results),
        "certified": bool(certified),
        "n_zero": n_zero,
        "n_nonzero": n_nz,
        "n_unknown": n_unk,
        "obligations": results,
        "hypothesis_type": hyp.hypothesis_type,
        "d_level": hyp.d_level,
        "latent_object": hyp.latent_object,
        "core": symbolic_core(hyp.latent_object),
    }
