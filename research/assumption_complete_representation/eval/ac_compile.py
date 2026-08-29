"""Compile H to exact obligations. Fail-closed. Not a new baseline.

COMPILER_V1.1: expand catalog IDs and F(arg) applications in
proof-obligation strings. The frozen schema asks for
``G0001 - F(lam) = 0``; leaving those tokens unexpanded was a
software bug (all operational hypotheses scored UNKNOWN). Rescore
the same raw outputs; label COMPILER_GAIN. Do not re-query the API
to hide the failure.
"""
from __future__ import annotations

import re
from typing import Any, Optional

import sympy

from research.llm_abstraction.constructor import (
    _equal,
    parse_flex,
    symbolic_core,
    _verify_pair,
)

COMPILER_VERSION = "ac-compile-v1.1"

_GID = re.compile(r"\bG\d{4}\b")
_HEAD_VAR = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*="
)


def catalog_map(pack: dict) -> dict[str, str]:
    return {
        e["source_node_id"]: e["text"]
        for e in (pack.get("catalog") or [])
        if e.get("source_node_id") and e.get("text")
    }


def member_text(mmap: Any, cmap: dict[str, str]) -> str:
    if not isinstance(mmap, dict):
        return ""
    gid = str(mmap.get("source_node_id") or mmap.get("member") or "")
    if mmap.get("text"):
        return str(mmap["text"])
    return cmap.get(gid, "")


def _split_eq(text: str) -> Optional[tuple[str, str]]:
    raw = (text or "").strip()
    if not raw:
        return None
    depth = 0
    for i, c in enumerate(raw):
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth = max(0, depth - 1)
        elif depth == 0 and raw[i:i + 2] == "==":
            return raw[:i].strip(), raw[i + 2:].strip()
        elif depth == 0 and c == "=" and raw[i:i + 2] != "==":
            return raw[:i].strip(), raw[i + 1:].strip()
    return None


def parse_F(text: str, symbols: list, functions: list):
    core = symbolic_core(text or "")
    if not core:
        return None
    return parse_flex(core, symbols, functions)


def latent_head_var(text: str) -> tuple[str, str]:
    m = _HEAD_VAR.match(text or "")
    if m:
        return m.group(1), m.group(2)
    return "F", "t"


def _matching_paren(s: str, open_i: int) -> Optional[int]:
    depth = 0
    for j in range(open_i, len(s)):
        if s[j] == "(":
            depth += 1
        elif s[j] == ")":
            depth -= 1
            if depth == 0:
                return j
    return None


def expand_catalog_ids(text: str, cmap: dict[str, str]) -> str:
    def repl(m: re.Match) -> str:
        gid = m.group(0)
        src = cmap.get(gid)
        if not src:
            return gid
        return f"({src})"
    return _GID.sub(repl, text)


def expand_head_calls(
    text: str,
    head: str,
    F_expr,
    var_name: str,
    symbols: list,
    functions: list,
    cmap: dict[str, str],
) -> str:
    if F_expr is None or not head:
        return text
    var = None
    for s in F_expr.free_symbols:
        if s.name == var_name:
            var = s
            break
    if var is None:
        frees = [s for s in F_expr.free_symbols if s.name not in {"pi", "E", "I"}]
        if len(frees) == 1:
            var = frees[0]
    if var is None:
        return text
    pat = re.compile(rf"\b{re.escape(head)}\s*\(")
    guard = 0
    while guard < 32:
        guard += 1
        m = pat.search(text)
        if not m:
            return text
        open_i = text.find("(", m.start())
        close = _matching_paren(text, open_i)
        if close is None:
            return text
        arg = text[open_i + 1:close]
        arg_exp = expand_catalog_ids(arg, cmap)
        arg_e = parse_flex(symbolic_core(arg_exp), symbols, functions)
        if arg_e is None:
            return text
        try:
            inst = F_expr.xreplace({var: arg_e})
        except Exception:
            return text
        repl = "(" + sympy.sstr(inst) + ")"
        text = text[:m.start()] + repl + text[close + 1:]
    return text


def expand_obligation(
    text: str,
    pack: dict,
    F_expr,
    head: str,
    var_name: str,
) -> str:
    cmap = catalog_map(pack)
    symbols = pack.get("symbols") or []
    functions = pack.get("functions") or []
    t = expand_catalog_ids(text, cmap)
    t = expand_head_calls(t, head, F_expr, var_name, symbols, functions, cmap)
    return t


def _verify_exprs(a, b, symbols, functions) -> str:
    if a is None or b is None:
        return "UNKNOWN"
    if _equal(a, b):
        return "ZERO"
    try:
        if _equal(a - b, sympy.Integer(0)):
            return "ZERO"
    except Exception:
        pass
    return _verify_pair(str(a), b, symbols, functions)


def compile_and_verify(hyp: dict, pack: dict) -> dict[str, Any]:
    symbols = pack.get("symbols") or []
    functions = pack.get("functions") or []
    cmap = catalog_map(pack)
    if hyp.get("parse_status") != "OK":
        return {
            "constructable": False,
            "certified": False,
            "compile_status": "C_FAIL",
            "compiler_version": COMPILER_VERSION,
            "n_zero": 0, "n_nonzero": 0, "n_unknown": 0,
            "obligations": [],
            "note": hyp.get("parse_error") or "parse_failure",
        }
    latent = hyp.get("latent_object") or ""
    head, var_name = latent_head_var(latent)
    vs = hyp.get("variables") or []
    if vs:
        v0 = vs[0]
        var_name = v0.get("name") if isinstance(v0, dict) else str(v0) or var_name
    F = parse_F(latent, symbols, functions)
    obligations: list[dict] = []

    for ob in hyp.get("proof_obligations") or []:
        if not isinstance(ob, str):
            continue
        pair = _split_eq(ob)
        if pair is None:
            obligations.append({
                "text": ob, "verdict": "UNKNOWN", "note": "prose_obligation",
            })
            continue
        lhs, rhs = pair
        lhs_x = expand_obligation(lhs, pack, F, head, var_name)
        rhs_x = expand_obligation(rhs, pack, F, head, var_name)
        lhs_e = parse_flex(symbolic_core(lhs_x), symbols, functions)
        rhs_e = parse_flex(symbolic_core(rhs_x), symbols, functions)
        if lhs_e is None or rhs_e is None:
            obligations.append({
                "text": ob,
                "expanded": f"{lhs_x} = {rhs_x}",
                "verdict": "UNKNOWN",
                "note": "unparseable_obligation",
            })
            continue
        v = _verify_exprs(lhs_e, rhs_e, symbols, functions)
        obligations.append({
            "text": ob,
            "expanded": f"{lhs_x} = {rhs_x}",
            "verdict": v,
            "note": "parsed_eq",
        })

    current = pack.get("current") or ""
    if current:
        cur_e = parse_flex(current, symbols, functions)
        if cur_e is not None:
            zero = _equal(cur_e, sympy.Integer(0))
            v = "ZERO" if zero else "UNKNOWN"
            obligations.append({
                "text": "current_residual_vs_0",
                "verdict": v,
                "note": "b0_style_residual_not_discovery",
            })

    n_zero = sum(1 for o in obligations if o["verdict"] == "ZERO"
                 and o.get("note") != "b0_style_residual_not_discovery")
    n_nz = sum(1 for o in obligations if o["verdict"] == "NONZERO")
    n_unk = sum(1 for o in obligations if o["verdict"] == "UNKNOWN"
                and o.get("note") != "b0_style_residual_not_discovery")
    constructable = F is not None or n_zero > 0 or any(
        o.get("note") == "parsed_eq" for o in obligations
    )
    real = [o for o in obligations if o.get("note") not in {
        "b0_style_residual_not_discovery", "prose_obligation",
    }]
    compile_status = "C_OK" if real else "C_FAIL"
    certified = compile_status == "C_OK" and n_zero > 0 and n_nz == 0 and n_unk == 0
    return {
        "constructable": bool(constructable),
        "certified": bool(certified),
        "compile_status": compile_status,
        "compiler_version": COMPILER_VERSION,
        "F_parsed": F is not None,
        "F_srepr": str(F) if F is not None else "",
        "n_zero": n_zero,
        "n_nonzero": n_nz,
        "n_unknown": n_unk,
        "obligations": obligations,
        "note": "",
    }
