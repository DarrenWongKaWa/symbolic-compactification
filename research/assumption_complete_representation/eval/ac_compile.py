"""Compile H to exact obligations. Fail-closed. Not a new baseline."""
from __future__ import annotations

import re
from typing import Any, Optional

from research.llm_abstraction.constructor import (
    parse_flex,
    symbolic_core,
    _verify_pair,
)

_EQ = re.compile(r"(==|=)")


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


def _first_dd(F, var_name: str, x: str, y: str, symbols, functions):
    if F is None:
        return None
    Fx = parse_flex(x, symbols, functions)
    Fy = parse_flex(y, symbols, functions)
    if Fx is None or Fy is None:
        return None
    import sympy
    var = None
    for s in F.free_symbols:
        if s.name == var_name:
            var = s
            break
    if var is None:
        frees = [s for s in F.free_symbols if s.name not in {"pi", "E", "I"}]
        var = frees[0] if len(frees) == 1 else None
    if var is None:
        return None
    try:
        return (F.xreplace({var: Fx}) - F.xreplace({var: Fy})) / (Fx - Fy)
    except Exception:
        return None


def compile_and_verify(hyp: dict, pack: dict) -> dict[str, Any]:
    symbols = pack.get("symbols") or []
    functions = pack.get("functions") or []
    cmap = catalog_map(pack)
    if hyp.get("parse_status") != "OK":
        return {
            "constructable": False,
            "certified": False,
            "compile_status": "C_FAIL",
            "n_zero": 0, "n_nonzero": 0, "n_unknown": 0,
            "obligations": [],
            "note": hyp.get("parse_error") or "parse_failure",
        }
    F = parse_F(hyp.get("latent_object") or "", symbols, functions)
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
        lhs_e = parse_flex(symbolic_core(lhs), symbols, functions)
        rhs_e = parse_flex(symbolic_core(rhs), symbols, functions)
        if lhs_e is None or rhs_e is None:
            obligations.append({
                "text": ob, "verdict": "UNKNOWN", "note": "unparseable_obligation",
            })
            continue
        v = _verify_pair(str(lhs_e), rhs_e, symbols, functions)
        obligations.append({"text": ob, "verdict": v, "note": "parsed_eq"})

    # Catalog pair from reconstruction "Gxxxx = Gyyyy" or residual vs 0.
    recon = hyp.get("reconstruction_rule") or ""
    for gid, text in cmap.items():
        if gid in recon or gid in (hyp.get("latent_object") or ""):
            pass

    # If F parses and two node names exist, try first difference quotient
    # against catalog members that look like quotients. Evaluation of the
    # claim, not a new baseline operator family.
    nodes = [str(n) for n in (hyp.get("nodes") or []) if n]
    var_name = None
    vs = hyp.get("variables") or []
    if vs:
        v0 = vs[0]
        var_name = v0.get("name") if isinstance(v0, dict) else str(v0)
    hidden_nodes = []
    if F is not None and len(nodes) >= 2 and var_name:
        dd = _first_dd(F, var_name, nodes[0], nodes[1], symbols, functions)
        if dd is not None:
            for mmap in hyp.get("member_maps") or []:
                mt = member_text(mmap, cmap)
                if mt and "/" in mt:
                    v = _verify_pair(mt, dd, symbols, functions)
                    obligations.append({
                        "text": f"first_dd[{nodes[0]},{nodes[1]}] vs {mmap.get('source_node_id')}",
                        "verdict": v,
                        "note": "compiled_first_dd",
                    })

    # Direct residual of current expression (never counts as representation
    # discovery; recorded separately).
    current = pack.get("current") or ""
    if current:
        cur_e = parse_flex(current, symbols, functions)
        if cur_e is not None:
            try:
                import sympy
                from research.llm_abstraction.constructor import _equal
                zero = _equal(cur_e, sympy.Integer(0))
                v = "ZERO" if zero else "UNKNOWN"
            except Exception:
                v = "UNKNOWN"
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
    # C_OK if we obtained at least one machine-checkable (non-prose) obligation
    # other than the B0 residual dump.
    real = [o for o in obligations if o.get("note") != "b0_style_residual_not_discovery"
            and o.get("note") != "prose_obligation"]
    compile_status = "C_OK" if real else "C_FAIL"
    certified = compile_status == "C_OK" and n_zero > 0 and n_nz == 0 and n_unk == 0
    return {
        "constructable": bool(constructable),
        "certified": bool(certified),
        "compile_status": compile_status,
        "F_parsed": F is not None,
        "F_srepr": str(F) if F is not None else "",
        "n_zero": n_zero,
        "n_nonzero": n_nz,
        "n_unknown": n_unk,
        "obligations": obligations,
        "note": "",
    }
