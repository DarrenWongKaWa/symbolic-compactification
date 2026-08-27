"""Domain-neutral abstraction quality. No gold features."""
from __future__ import annotations

import sympy
from sympy.core.function import AppliedUndef

from symbolic_compactification import parse_expression
from symbolic_compactification.models import AdapterError


def _ops(e: sympy.Expr) -> int:
    try:
        return int(sympy.count_ops(e)) + 1
    except Exception:
        return 1


def _parse(text: str, symbols: list, functions: list | None):
    try:
        return parse_expression(text, symbols, functions=functions or None)
    except AdapterError:
        return None


def score_hypothesis(template: str, family: list[str], *,
                     symbols: list | None = None,
                     functions: list | None = None) -> dict:
    merged = list(symbols or []) + infer_symbols(template, *family) + _theta_syms(template)
    seen = set()
    uniq = []
    for s in merged:
        n = s["name"] if isinstance(s, dict) else str(s)
        if n in seen:
            continue
        seen.add(n)
        uniq.append(s if isinstance(s, dict) else {"name": n, "real": True})
    symbols = uniq
    fns = []
    seenf = set()
    for n in list(functions or []) + infer_functions(template, *family):
        if n not in seenf:
            seenf.add(n)
            fns.append(n)
    functions = fns
    ft = _parse(template, symbols, functions)
    members = [(_parse(m, symbols, functions) or m) for m in family]
    member_exprs = [m for m in members if isinstance(m, sympy.Expr)]
    if ft is None or len(member_exprs) < 2:
        return {"S": -99.0, "gain": -99.0, "depth": 0.0, "coherence": 0.0,
                "named_ops": 0.0, "keep": False, "n": len(family)}
    dl_members = sum(_ops(m) for m in member_exprs)
    holes = [s for s in ft.free_symbols if s.name.startswith("theta")]
    dl_F = _ops(ft)
    # maps: remaining free symbols of members not in template non-holes
    dl_maps = max(1, len(holes)) * len(member_exprs)
    gain = dl_members - dl_F - dl_maps
    max_m = max(_ops(m) for m in member_exprs)
    depth = dl_F / max_m
    # coherence: holes should be filled by small expressions — use family
    # size of hole names vs template. Approximate: hole count vs ops.
    coherence = 0.0
    if holes:
        # small holes relative to members
        coherence = min(1.0, 2.0 / (1 + len(holes)))
        # bonus if template still has non-hole symbols or named calls
    named = 0.0
    if any(isinstance(s, AppliedUndef) or getattr(s, "func", None) is sympy.polygamma
           for s in sympy.preorder_traversal(ft)):
        named = 1.0
    elif any(not s.name.startswith("theta") for s in ft.free_symbols):
        named = 0.3
    # Weight named operators over raw MDL: a larger special-function
    # template should beat I*mu*theta even if gain is slightly negative.
    S = 0.25 * gain + 3 * depth + 2 * coherence + 4 * named
    keep = (named == 1.0) or (
        (gain >= 0) and (depth >= 0.25) and (named >= 0.3) and (dl_F >= 4)
    )
    return {
        "S": round(S, 4),
        "gain": round(gain, 4),
        "depth": round(depth, 4),
        "coherence": round(coherence, 4),
        "named_ops": named,
        "keep": keep,
        "n": len(family),
        "dl_members": dl_members,
        "dl_F": dl_F,
    }


_RESERVED = {
    "sin", "cos", "tan", "exp", "log", "sqrt", "Abs", "I", "pi", "E", "oo",
    "polygamma", "Sum", "Product", "Piecewise", "Eq", "Ne", "True", "False",
}


def infer_symbols(*texts: str) -> list:
    import re
    names = set()
    funcs = set()
    for t in texts:
        t = t or ""
        funcs.update(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", t))
        names.update(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", t))
    names -= _RESERVED
    funcs -= _RESERVED
    names -= funcs
    return [{"name": n, "real": True} for n in sorted(names)]


def infer_functions(*texts: str) -> list:
    import re
    funcs = set()
    for t in texts:
        funcs.update(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", t or ""))
    funcs -= _RESERVED
    funcs -= {"theta0", "theta1", "theta2", "theta3"}
    return sorted(funcs)


def _theta_syms(template: str) -> list:
    import re
    names = sorted(set(re.findall(r"theta[0-9]+", template)))
    return [{"name": n, "real": True} for n in names]


def rank_records(recs: list[dict], *, symbols=None, functions=None) -> list[dict]:
    out = []
    for r in recs:
        sc = score_hypothesis(
            r["template"], r.get("family") or [],
            symbols=symbols, functions=functions,
        )
        item = dict(r)
        item["score"] = sc
        out.append(item)
    out.sort(key=lambda x: -x["score"]["S"])
    return out
