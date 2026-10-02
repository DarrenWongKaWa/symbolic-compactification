"""Draft step cards from a document, so that nobody retypes a formula.

    symbolic-compactification manybody draft paper.tex --out cards/

For each displayed equation (LaTeX ``equation``, ``align``, ``gather``,
``multline``, ``\\[...\\]``, ``$$...$$``; in a plain-text sheet, every line
``Claim: ...``) a card is written whose expressions are verbatim quotes:

- ``A = B = C`` becomes the steps ``A = B`` and ``B = C``;
- a trailing ``+ O(x^n)`` becomes a ``remainder`` card for ``x -> 0``;
- ``, name = expr`` clauses after the claim are proposed as definitions.

Every card includes one shared ``conventions.yaml``. The drafter lists the
tokens it could not resolve there as comments: a person or an agent fills
the notation and definitions once for the whole document, and the cards
themselves never contain hand-written expressions. A draft is a proposal:
run the cards with ``--require-source``.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import yaml

from .latex import latex_to_plain, read_macros, split_integral
# names used here, and the ones callers import from draft (kept for them)
from .prose import (_distribution_not_thermal, _dollar_math, _inline_definitions, _matsubara_names,
                    builtins_redefined, distribution_defined_in_text, log_base_stated, prose_constraints,
                    subscript_collisions,
                    special_functions_named,
                    _operator_names, _positive_symbols,
                    _realness_sensitive,
                    _stated_integers, _stated_numbers, _stated_realness, _symbol_entry,
                    prose_assignments, prose_values, stated_noncommuting)
from .relations import (_DEFINITION_LHS, _INTEGRAL, _KNOWN, _MATSUBARA, _O_TERM, _ONLY_O,
                        _SERIES, split_top_level, steps_from_latex, steps_from_sheet,
                        _tokens)

__all__ = ["draft", "split_top_level", "steps_from_latex", "steps_from_sheet",
           "stated_noncommuting", "_positive_symbols", "_stated_numbers", "_stated_realness"]


def _bare_uses(quotes, macros: dict, latex: bool) -> set[str]:
    """Names some quote uses as a plain value, not followed by '(' (S in
    'S + 1', not in 'S(w)'): a definition S(w) = ... would clash with it."""
    out: set[str] = set()
    for q in quotes:
        try:
            plain = latex_to_plain(str(q), macros) if latex else str(q)
        except (ValueError, RecursionError):
            continue
        out |= {m.group(1) for m in re.finditer(
            r"(?<![\\A-Za-z0-9_])([A-Za-z_][A-Za-z0-9_]*)(?![A-Za-z0-9_])(?!\s*\()", plain)}
    return out


def _var_name(token: str) -> str:
    return token.lstrip("\\")


def _limit_point(var: str, text: str) -> str | None:
    """'x \\to \\infty' / 'large x' -> oo, 'x \\to 0' / 'small x' -> 0, else None."""
    v = rf"\\?{re.escape(var)}"
    both = re.search(rf"{v}\s*\\(?:to|rightarrow)\s*\\pm\s*\\infty|\|\s*{v}\s*\|\s*\\(?:to|rightarrow)\s*\\infty", text)
    minus = re.search(rf"{v}\s*\\(?:to|rightarrow)\s*-\s*\\infty", text)
    infinity = re.search(rf"{v}\s*\\(?:to|rightarrow)\s*\+?\s*\\infty|large\s+\$?{v}\b", text)
    zero = re.search(rf"{v}\s*\\(?:to|rightarrow)\s*0|small\s+\$?{v}\b", text)
    if zero and (both or minus or infinity):
        return None
    if both or (minus and infinity):
        return "+-oo"
    if minus:
        return "-oo"
    if infinity and not zero:
        return "oo"
    if zero and not infinity:
        return "0"
    return None


def _remainder(card: dict, lhs: str, rhs: str, o_term, step: dict | None = None) -> None:
    """O(x^n): at x -> 0 for n > 0 and x -> oo for n < 0, unless the text
    says otherwise; the text contradicting the order leaves it for the user."""
    step = step or {}
    approx = rhs[:o_term.start()].strip()
    order_text = o_term.group(1)
    var_order = re.fullmatch(r"\s*\\?([A-Za-z]+)\s*(?:\^\s*\{?\s*(-?\d+)\s*\}?)?\s*", order_text)
    card["check"] = "remainder"
    if var_order:
        var, order = var_order.group(1), int(var_order.group(2) or 1)
        card["variable"], card["order"] = var, order
        said = _limit_point(var, step.get("sentence", "") + " " + lhs + " " + rhs)
        # no stated limit point: a negative order is a tail at infinity; a
        # positive one is checked at 0 and at infinity and decided only if they agree
        # a negative order with no stated direction: both +oo and -oo must agree,
        # unless the variable is stated positive
        point = said or (("oo" if var in step.get("positive_names", ()) else "+-oo")
                         if order < 0 else "unstated")
        if order < 0 and point == "0":
            card.update({"variable": "TODO", "hint": "negative order at 0: check the limit point"})
        card["point"] = point
        if point in ("0", "unstated"):        # one-sided only when the variable is positive
            card["direction"] = "+" if var in step.get("positive_names", ()) else "+-"
    else:
        card.update({"variable": "TODO", "order": 1, "point": "0", "direction": "+-"})
    card["source"] = {"function": lhs, "approximant": approx}


# names that are constants by convention in many-body papers (inverse
# temperature, Planck's constant); every other name before "(" is left to
# the reviewer, because a wrong guess would give a confident wrong verdict
_CONSTANTS = frozenset({"beta", "hbar"})
_LOWER_GREEK = frozenset("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu "
                         "xi rho sigma tau upsilon phi chi omega".split())


def _before_parenthesis(plain: str) -> set[str]:
    """Names written directly before '(' : product or function value?"""
    return {m.group(1) for m in re.finditer(r"(?<![\\A-Za-z0-9_])([A-Za-z][A-Za-z0-9_]*)\s*\(", plain)
            if m.group(1) not in _KNOWN | {"n_F", "n_B"} and not re.fullmatch(r"psi\d?", m.group(1))}


_COMPONENT = {"r": "R", "a": "A", "lt": "less", "gt": "greater"}
_KELDYSH_FACTOR = re.compile(r"([A-Za-z][A-Za-z0-9]*?)__(r|a|lt|gt)\s*\(([^()]*)\)")
_TIME_INTEGRAL = re.compile(r"^\\int\s*d\s*t_?\{?\s*1\s*\}?\s*(?:\\[,;!]\s*)?(?P<body>.+)$", re.S)


def _langreth(lhs: str, rhs: str, macros: dict) -> dict | None:
    """X^c(t,t') = int dt_1 [products of B^r, C^<, ...] is a Langreth rule:
    check the component c of the contour product, quoting the integrand."""
    try:
        head = re.fullmatch(r"\s*([A-Za-z][A-Za-z0-9]*?)__(r|a|lt|gt)\s*\([^()]*\)\s*",
                            latex_to_plain(lhs, macros))
    except (ValueError, RecursionError):
        return None
    integral = _TIME_INTEGRAL.match(rhs.strip())
    if not head or not integral:
        return None
    body = integral.group("body").strip()
    try:
        plain = latex_to_plain(body, macros)
    except (ValueError, RecursionError):
        return None
    factors = _KELDYSH_FACTOR.findall(plain)
    if len(factors) < 2:
        return None
    product: list[str] = []
    for name, _, _ in factors:
        if name in product:
            break
        product.append(name)
    if len(product) < 2 or any(name not in product for name, _, _ in factors):
        return None
    if not _chained_arguments(latex_to_plain(lhs, macros), factors, len(product)):
        return None                       # B^<(t', t_1) is not part of the convolution
    notation = {m.group(0): f"{m.group(1)}_{_COMPONENT[m.group(2)]}"
                for m in _KELDYSH_FACTOR.finditer(plain)}
    return {"check": "langreth", "product": product, "component": _COMPONENT[head.group(2)],
            "notation": notation, "source": {"claim": body}}


def _chained_arguments(lhs_plain: str, factors: list, size: int) -> bool:
    """Each term of C(t,t') = int dt_1 A(t,t_1) B(t_1,t') must chain its time
    arguments from t through the integration variables to t'."""
    outer = re.search(r"\(([^()]*)\)", lhs_plain)
    ends = [a.strip() for a in outer.group(1).split(",")] if outer else []
    if len(ends) != 2 or len(factors) % size:
        return False
    for k in range(0, len(factors), size):
        args = [[a.strip() for a in f[2].split(",")] for f in factors[k:k + size]]
        if any(len(a) != 2 for a in args) or args[0][0] != ends[0] or args[-1][1] != ends[1]:
            return False
        if any(args[j][1] != args[j + 1][0] or args[j][1] in ends for j in range(size - 1)):
            return False
    return True


_BARE_FACTOR = re.compile(r"(?<![A-Za-z0-9_])([A-Za-z][A-Za-z0-9]*?)__(r|a|lt|gt)(?![A-Za-z0-9_(])")


_LOCAL_PRODUCT = re.compile(
    r"point-?wise|component-?wise|element-?wise|equal-time\s+product|local\s+product"
    r"|not\s+a\s+(?:contour\s+)?convolution|does\s+not\s+apply", re.I)


def _stated_product(head: str, context: str, document: str = "") -> list[str] | None:
    """The order of a contour convolution as the text states it ("C = A*B",
    "$C = A \ast B$", or "the convolution $C = AB$"). The shorthand
    C^r = A^r B^r shows neither the order nor that the product is a
    convolution; a product written with its arguments, C(t,t') =
    A(t,t') B(t,t'), or called pointwise anywhere in the paper, is not one."""
    text = document or context
    if _LOCAL_PRODUCT.search(text) or re.search(
            rf"(?<![A-Za-z0-9_\\]){re.escape(head)}\s*\([^()]*\)\s*=\s*[A-Z]\s*\([^()]*\)\s*[A-Z]\s*\(", text):
        return None
    for m in re.finditer(rf"(?<![A-Za-z0-9_\\]){re.escape(head)}\s*=\s*"
                         r"((?:[A-Z]\s*(?:\*|\\ast|\\star|\\otimes|\\circ)?\s*){2,4})(?=\s*(?:\$|\\\)|,|\.|;|$))",
                         context):
        names = re.findall(r"[A-Z]", m.group(1))
        marked = re.search(r"\*|\\ast|\\star|\\otimes|\\circ", m.group(1)) or \
            re.search(r"convol", context[max(0, m.start() - 160):m.end() + 80], re.I)
        if marked and len(set(names)) == len(names) >= 2:
            return names
    return None


def _langreth_shorthand(lhs: str, rhs: str, macros: dict, context: str, document: str = "") -> dict | None:
    """C^c = A^r B^< + ... without times: a Langreth rule in shorthand. Drafted
    only when the text states the product (C = A*B) the rule is about."""
    try:
        head = re.fullmatch(r"\s*([A-Za-z][A-Za-z0-9]*?)__(r|a|lt|gt)\s*", latex_to_plain(lhs, macros))
        plain = latex_to_plain(rhs, macros)
    except (ValueError, RecursionError):
        return None
    if not head:
        return None
    factors = _BARE_FACTOR.findall(plain)
    if len(factors) < 2 or re.sub(r"[\s*+\-()]", "", _BARE_FACTOR.sub("", plain)):
        return None                       # anything besides components, products and signs
    product = _stated_product(head.group(1), context, document)
    if not product or {name for name, _ in factors} != set(product):
        return None
    notation = {f"{name}__{c}": f"{name}_{_COMPONENT[c]}" for name, c in factors}
    return {"check": "langreth", "product": product, "component": _COMPONENT[head.group(2)],
            "notation": notation, "source": {"claim": rhs}}



def _statistics(step: dict, freq: str, index: str) -> str | None:
    """Fermionic or bosonic, never guessed from the letter. Structural
    evidence first: the paper's definition of this very frequency symbol,
    (2n+1) pi/beta or 2 n pi/beta. Otherwise the word fermionic/bosonic in the
    sentence that leads into the display. Conflicting or absent evidence ->
    None, so the step is not decided."""
    doc = step.get("document", "")
    defn = re.compile(rf"\\{freq}_\{{?\s*{index}\s*\}}?\s*=\s*([^$\n]{{0,60}})")
    kinds = set()
    for m in defn.finditer(doc):
        rhs = m.group(1)
        if re.search(rf"\(\s*2\s*{index}\s*\+\s*1\s*\)", rhs):
            kinds.add("fermion")
        elif re.search(rf"2\s*{index}\s*\\pi|2\s*\\pi\s*{index}", rhs):
            kinds.add("boson")
    if len(kinds) == 1:
        return kinds.pop()
    if kinds:
        return None                               # the paper defines it both ways
    lead = step.get("sentence", "").lower()
    fermi, bose = "fermion" in lead, "boson" in lead
    if fermi != bose:
        return "fermion" if fermi else "boson"
    return None


def _frequency(body: str, index: str) -> str:
    return next((f for f in ("omega", "nu", "Omega", "xi", "epsilon")
                 if re.search(rf"\\{f}_\{{?{index}\}}?", body)), "omega")


_RESTRICTED_SUM = re.compile(
    r"restricted|non-?negative|positive\s+(?:Matsubara\s+)?frequenc|only\s+(?:positive|negative)"
    r"|[nm]\s*(?:\\ge|\\geq|>|\\gt)\s*0|half\s+of\s+the\s+frequenc", re.I)


def _matsubara_statistics(step: dict, match: re.Match) -> str | None:
    """The statistics of a sum over all Matsubara frequencies, or None. A sum
    the text restricts (n >= 0, positive frequencies) is a different sum,
    and a prefactor T must be stated to be the temperature."""
    body, index = match.group("body"), match.group("index")
    if _RESTRICTED_SUM.search(_lead_in(step.get("before", "")) + " " + step.get("sentence", "")):
        return None
    prefix = match.group(0)[:match.start("index")]
    if re.match(r"\s*T\s*\\sum", prefix) and not _temperature_named_T(step.get("document", "")):
        return None                       # T may be a tunnelling amplitude or a transmission
    return _statistics(step, _frequency(body, index), index)


def _temperature_named_T(document: str) -> bool:
    """The text calls T the temperature ('temperature $T$', '$\\beta = 1/T$',
    '$k_B T$') and gives no other meaning to a bare T."""
    called = re.search(r"temperature\s+(?:\$T\$|\\\(T\\\))|\$T\$\s+is\s+the\s+temperature"
                       r"|\\(?:omega|Omega|nu|xi)_\{?[a-z]\}?\s*=\s*[^$]{0,30}\\pi[^$]{0,10}\bT\b"   # 2 pi m T
                       r"|\\beta\s*=\s*1\s*/\s*(?:k_B\s*)?T\b|\\beta\s*=\s*\\frac\{1\}\{(?:k_B\s*)?T\}", document)
    other = re.search(r"(?:amplitude|transmission|hopping|tunnel\w*|matrix|period)\s+(?:\$T|\\\(T)"
                      r"|\$T\$\s+(?:is|be|denotes?)\s+(?:a|the)\s+(?!temperature)", document)
    return bool(called) and not other


def _card_for(step: dict, doc_name: str, latex: bool, macros: dict) -> tuple[dict, set, set]:
    lhs, rhs = step["lhs"], step["rhs"]
    card: dict[str, Any] = {"label": step["id"], "include": "conventions.yaml",
                            "source_document": doc_name}
    if step.get("display"):
        card["display"] = step["display"]     # quotes must come from this display
    o_term = _O_TERM.search(rhs)
    only_o = _ONLY_O.match(rhs)
    integral = _INTEGRAL.match(lhs) if latex else None
    matsubara = _MATSUBARA.match(lhs.strip()) if latex else None
    series = _SERIES.match(lhs.strip()) if latex else None
    if o_term:
        _remainder(card, lhs, rhs, o_term, step)
    elif only_o:                          # f = O(x^n): the approximant is 0
        _remainder(card, lhs, "0 + " + rhs, _O_TERM.search("0 + " + rhs), step)
        card["approximant"] = "0"
        card["source"] = {"function": lhs}
    elif matsubara and _matsubara_statistics(step, matsubara):
        body, k = matsubara.group("body").strip(), matsubara.group("index")
        freq = _frequency(body, k)
        card.update({"check": "matsubara", "statistics": _matsubara_statistics(step, matsubara),
                     "variable": "z", "beta": "beta",
                     "notation": {f"i{freq}_{k}": "z", f"i {freq}_{k}": "z"}})
        card["source"] = {"summand": body, "claim": rhs}
    elif latex and re.search(r"langreth", step.get("context", ""), re.I) and (
            _langreth(lhs, rhs, macros) or _langreth_shorthand(lhs, rhs, macros, step.get("context", ""),
                                                               step.get("document", ""))):
        # the paper itself invokes Langreth's rules
        card.update(_langreth(lhs, rhs, macros)
                    or _langreth_shorthand(lhs, rhs, macros, step["context"], step.get("document", "")))
    elif series:
        card.update({"check": "series", "variable": series.group("index"),
                     "lower": int(series.group("lower"))})
        card["source"] = {"summand": series.group("body").strip(), "claim": rhs}
    elif integral and re.search(r"n_\{?F", integral.group("body")):
        body = integral.group("body").strip()
        card.update({"check": "fermi_integral",
                     "variable": _var_name(integral.group("v1") or integral.group("v2")),
                     "beta": "beta"})
        entry: Any = body if integral.group("v2") else {"quote": body, "wrap": "({})/(2*pi)"}
        card["source"] = {"integrand": entry, "claim": rhs}
    elif latex and split_integral(lhs):
        # int_a^b dx f = R: checked through a verified antiderivative (entire f only)
        var = latex_to_plain(split_integral(lhs)["variable"], macros).strip()
        name = re.sub(r"\s*'", "_prime", var)
        card.update({"check": "definite_integral", "variable": name})
        if name != var:
            card["notation"] = {var: name}
        card["source"] = {"integral": lhs, "claim": rhs}
    else:
        card["check"] = "identity"
        card["source"] = {"lhs": lhs, "rhs": rhs}
        if matsubara:
            card["hint"] = ("a Matsubara sum, but the text does not say fermionic or bosonic: "
                            "set check: matsubara and statistics: fermion|boson")
        if latex and _langreth(lhs, rhs, macros):
            card["hint"] = ("shaped like a Langreth rule; if the paper claims the exact rule, "
                            "set check: langreth (product, component, notation as for a drafted rule)")
    if step.get("branch"):                  # one sign of a \pm relation
        for key, entry in list(card["source"].items()):
            if key.startswith("define:"):
                continue
            entry = {"quote": entry} if isinstance(entry, str) else dict(entry)
            card["source"][key] = {**entry, "branch": step["branch"]}
    if step.get("conditional"):
        card["conditional"] = step["conditional"]
    try:
        expanded = latex_to_plain(lhs + " = " + rhs, macros) if latex else lhs + rhs
    except (ValueError, RecursionError):
        expanded = ""
    if re.search(r"(?<![A-Za-z0-9_])(?:Tr|tr|Sp|det)\s*\(|\\(?:Tr|tr)\b", expanded + " " + lhs + " " + rhs):
        card["trace"] = True                   # a trace or determinant of matrices
    if re.search(r"\\(?:mathbf|boldsymbol|bm|vec)\b", lhs + " " + rhs):
        card["bold_symbols"] = True           # vectors or matrices: products are not numbers
    if re.search(r"first\s+order|leading\s+order|lowest\s+order|to\s+order|linear\s+(?:in|response|order)"
                 r"|approximat|\\approx|\\simeq|neglect|small\s+(?:\$|\\\()",
                 _lead_in(step.get("before", "")) + " " + step.get("sentence", ""), re.I):
        card["approximation_stated"] = True    # the text says this holds to some order only
    if step.get("equiv_relation"):
        card["equiv_relation"] = True
    if step.get("rhs_display"):           # the right side is quoted from another display
        for key in ("rhs", "claim", "approximant"):
            if isinstance(card["source"].get(key), str):
                card["source"][key] = {"quote": card["source"][key], "display": step["rhs_display"]}
    for d in step.get("definitions", []):
        safe = d["name"].replace("+", "p").replace("-", "m")
        card["source"][f"define:TODO_{re.sub(r'[^A-Za-z0-9]', '_', safe)}()"] = d["quote"]
    names, todo = set(), set()
    for quote in card["source"].values():
        text = quote["quote"] if isinstance(quote, dict) else quote
        try:
            plain = latex_to_plain(text, macros) if latex else text
        except (ValueError, RecursionError):
            todo.add("(unbalanced LaTeX in a quote)")
            continue
        n, t = _tokens(plain)
        names |= n
        todo |= t
        card.setdefault("_before_paren", set()).update(_before_parenthesis(plain))
    if card.get("check") in ("matsubara", "fermi_integral"):
        names.add(str(card.get("beta", "beta")))     # the 1/beta prefix is not in the quote
    if card.get("check") == "definite_integral":
        names.add(card["variable"])
        names -= {"int", "d"} | set(card.get("notation") or {})
    return card, names, todo


def _same_scope(a: dict, b: dict, assigned: dict, sections: list[int], macros: dict, latex: bool) -> bool:
    """No section starts between the two displays, and no name in either right
    side is given a value in the text twice or anywhere between them."""
    lo, hi = sorted((a.get("offset", 0), b.get("offset", 0)))
    if any(lo < s < hi for s in sections):
        return False
    names: set[str] = set()
    for side in (a["rhs"], b["rhs"]):
        try:
            t = _tokens(latex_to_plain(side, macros) if latex else side)
        except (ValueError, RecursionError):
            return False
        names |= t[0] | t[1]
    for name in names & set(assigned):
        if len(assigned[name]) > 1 or any(lo < at < hi for at, _ in assigned[name]):
            return False
    return True


def _consistency_steps(steps: list[dict], latex: bool, macros: dict, assigned: dict | None = None,
                       sections: list[int] | None = None) -> list[dict]:
    """Two displays that give the same left side (T(w) = A here, T(w) = C
    later) imply A = C. Each such pair becomes a step; the paper did not state
    A = C itself, so a mismatch is reported as a disagreement, not a verdict
    (the displays may hold under different conditions). Pairs across a
    section, or across a new value of a name they use, are skipped."""
    assigned, sections = assigned or {}, sections or []
    def norm(text):
        try:
            plain = latex_to_plain(text, macros) if latex else text
        except (ValueError, RecursionError):
            return None
        return re.sub(r"\s+", "", plain)
    heads: dict[str, list[dict]] = {}
    for step in steps:
        key = norm(step["lhs"])
        # a named quantity, T or T(w); x = ... is often a reused variable
        if key and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(?:\([^()]*\))?", key) \
                and not re.fullmatch(r"[A-Za-z]", key):
            heads.setdefault(key, []).append(step)
    out = []
    for group in heads.values():
        for a, b in zip(group, group[1:]):
            if a.get("display") == b.get("display") or norm(a["rhs"]) == norm(b["rhs"]):
                continue
            if not _same_scope(a, b, assigned, sections, macros, latex):
                continue                  # a name may mean something else by then
            if not (a.get("plain_identity") and b.get("plain_identity")):
                continue                  # two integrals or two rules: nothing checkable
            out.append({**a, "id": f"{a['id']}.vs.{b['id']}", "lhs": a["rhs"], "rhs": b["rhs"],
                        "rhs_display": b.get("display"), "consistency_of": a["lhs"],
                        "displays": [a.get("display"), b.get("display")]})
    return out


def _lead_in(context: str) -> str:
    """The paragraph that leads into a display (back to the previous display
    or blank line), where 'to first order in V' and similar are stated."""
    before = context[-800:]
    cut = max(before.rfind("\\end{"), before.rfind("\n\n"))
    return before[cut + 1:] if cut >= 0 else before


def _redefined(values: dict[str, list[tuple[int, str]]]) -> dict[str, list[tuple[int, str]]]:
    """Names given a value more than once: a pair of displays across them may
    compare two different things."""
    return {name: vals for name, vals in values.items() if len(vals) > 1}


_PM = re.compile(r"\\(?:pm|mp)\b|[±∓]")


def _branches(step: dict) -> list[dict]:
    """A relation with \\pm or \\mp states two relations, one per sign: two
    steps, 'id.p' and 'id.m', each quoting with its branch. A sum over both
    signs (\\sum_{\\pm}) is one relation."""
    text = step["lhs"] + " " + step["rhs"]
    if not _PM.search(text) or re.search(r"\\sum_\s*\{?\s*\\(?:pm|mp)", text):
        return [step]                     # the signs of \\sum_\\pm are summed, not split
    return [{**step, "id": f"{step['id']}.{tag}", "branch": sign} for tag, sign in (("p", "+"), ("m", "-"))]


def _safe_card_for(step: dict, doc_name: str, latex: bool, macros: dict) -> tuple[dict, set, set]:
    """_card_for, but LaTeX it cannot read (a typo, unbalanced braces) gives a
    plain identity card whose quotes then fail to translate: the step is
    reported as not decided instead of stopping the whole review."""
    try:
        return _card_for(step, doc_name, latex, macros)
    except (ValueError, RecursionError):
        card = {"label": step["id"], "include": "conventions.yaml", "source_document": doc_name,
                **({"display": step["display"]} if step.get("display") else {}),
                "check": "identity", "source": {"lhs": step["lhs"], "rhs": step["rhs"]}}
        return card, set(), {"(unbalanced LaTeX in a quote)"}


def _definition(step: dict, latex: bool, macros: dict) -> list[tuple[str, Any]] | None:
    """``name(args) = body`` with plain arguments is a definition, not a
    claim: it goes to conventions.yaml as quoted define: entries (both
    branches when the name carries a +- subscript)."""
    plain = latex_to_plain(step["lhs"], macros) if latex else step["lhs"]
    if step.get("equiv"):                 # "X \\equiv ..." in a display names X
        if step.get("equiv_relation") or step.get("conditional"):
            return None
        bare = re.fullmatch(r"\(*\s*([A-Za-z][A-Za-z0-9_]*)\s*\)*", plain)
        if bare and bare.group(1) not in _KNOWN:
            anchor = {"display": step["display"]} if step.get("display") else {}
            name = bare.group(1)
            if "PM" in name or name.endswith("_pm"):          # z_\pm \equiv e \pm i G: both branches
                base = name.replace("PM", "").removesuffix("_pm").rstrip("_") + "_"
                return [(f"define:{base}p()", {"quote": step["rhs"], "branch": "+", **anchor}),
                        (f"define:{base}m()", {"quote": step["rhs"], "branch": "-", **anchor})]
            return [(f"define:{name}()", {"quote": step["rhs"], **anchor} if anchor else step["rhs"])]
        return None
    m = _DEFINITION_LHS.match(plain)
    if not m or _O_TERM.search(step["rhs"]) or _ONLY_O.match(step["rhs"]):
        return None                     # f(x) = ... + O(x^n) is an expansion, not a definition
    if m.group(1) in _KNOWN | {"n_F", "n_B"}:
        return None                     # n_F, exp, ... are already defined
    try:
        body = latex_to_plain(step["rhs"], macros) if latex else step["rhs"]
    except (ValueError, RecursionError):
        return None
    if re.search(rf"(?<![A-Za-z0-9_]){re.escape(m.group(1))}(?![A-Za-z0-9_])", body):
        return None                     # G = g + g Sigma G is an equation for G, not a definition
    if latex and re.search(r"langreth", step.get("context", ""), re.I) and (
            _langreth(step["lhs"], step["rhs"], macros)
            or _langreth_shorthand(step["lhs"], step["rhs"], macros, step.get("context", ""),
                                   step.get("document", ""))):
        return None                     # a Langreth rule the paper states: a claim to check
    name, args = m.group(1), ",".join(a.strip() for a in m.group(2).split(","))
    anchor = {"display": step["display"]} if step.get("display") else {}
    if "PM" in name or name.endswith("_pm"):
        base = name.replace("PM", "").removesuffix("_pm").rstrip("_") + "_"
        return [(f"define:{base}p({args})", {"quote": step["rhs"], "branch": "+", **anchor}),
                (f"define:{base}m({args})", {"quote": step["rhs"], "branch": "-", **anchor})]
    return [(f"define:{name}({args})", {"quote": step["rhs"], **anchor} if anchor else step["rhs"])]


def draft(document: str | Path, out_dir: str | Path) -> dict[str, Any]:
    doc = Path(document)
    raw = doc.read_text(encoding="utf-8")
    latex = doc.suffix == ".tex"
    steps = steps_from_latex(raw) if latex else steps_from_sheet(raw)
    macros = read_macros(raw) if latex else {}
    prose = _dollar_math(raw)             # \( x \) is inline math too
    assigned = prose_assignments(raw, macros) if latex else {}
    values = prose_values(raw, macros) if latex else {}      # conditions such as $p = 0$ too
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rel = Path(os.path.relpath(doc.resolve(), out.resolve()))
    if rel.parts[:4] == ("..",) * 4:                     # far apart: keep it absolute
        rel = doc.resolve()
    positive = _positive_symbols(prose)
    for step in steps:
        step["positive_names"] = set(positive)
    all_names, all_todo, written, shared_quotes = set(), set(), [], {}
    before_paren: set[str] = set()

    def definition_of(step):
        try:
            return _definition(step, latex, macros)
        except (ValueError, RecursionError):
            return None

    # a name "defined" twice with different right-hand sides is not a
    # definition: those relations are claims and are drafted as steps
    bodies: dict[str, set[str]] = {}
    for step in steps:
        for key, _ in definition_of(step) or []:
            bodies.setdefault(key.split(":", 1)[1].split("(")[0], set()).add(" ".join(step["rhs"].split()))
    contested = {name for name, rhs in bodies.items() if len(rhs) > 1}
    drafted_definitions: list[dict] = []
    constants: dict[str, bool] = {}
    pending: list[tuple[Path, dict, set]] = []
    drafted_steps: list[dict] = []
    def squash(text):
        return " ".join(str(text).split())

    # values the displays give bare names (X = ..., X \equiv ...), for scopes and contests
    display_values: dict[str, list[tuple[int, str]]] = {}
    bound_names: set[str] = set()
    equiv_names: set[str] = set()
    for step in steps:
        if step.get("equiv"):
            try:
                equiv_names.add(latex_to_plain(step["lhs"], macros).strip() if latex else step["lhs"].strip())
            except (ValueError, RecursionError):
                pass
        try:
            plain_lhs = latex_to_plain(step["lhs"], macros).strip() if latex else step["lhs"].strip()
        except (ValueError, RecursionError):
            continue
        bare_lhs = re.fullmatch(r"\(*\s*([A-Za-z][A-Za-z0-9_]*)\s*\)*", plain_lhs)
        if bare_lhs:
            display_values.setdefault(bare_lhs.group(1), []).append((step.get("offset", 0), step["rhs"]))
        integral = split_integral(step["lhs"]) if latex else None
        if integral:
            try:
                bound_names.add(latex_to_plain(integral["variable"], macros).strip())
            except (ValueError, RecursionError):
                pass

    def given_otherwise(name, rhs):
        # the text gives the name another value somewhere (Gamma = G_L + G_R + G_phi later)
        return any(squash(other) != squash(rhs) for _, other in assigned.get(name, []))

    for step in steps:
        definition = definition_of(step)
        if definition and definition[0][0].split(":", 1)[1].split("(")[0] in contested:
            definition = None
        if definition and step.get("equiv"):
            name = definition[0][0].split(":", 1)[1][:-2]
            others = [v for _, v in display_values.get(name, [])]
            if given_otherwise(name, step["rhs"]) or name in bound_names \
                    or any(squash(v) != squash(step["rhs"]) for v in others):
                definition = None         # another value elsewhere, or an integration variable
        if definition:
            drafted_definitions.append({"step": step["id"], "defines": [k.split(":", 1)[1] for k, _ in definition],
                                        "display": step.get("display")})
            shared_quotes.update(definition)
            for key, _ in definition:
                if key.endswith("()"):                    # a named constant: Gamma -> Gamma()
                    constants[key.split(":", 1)[1][:-2]] = True
            params = set(definition[0][0].split("(", 1)[1].rstrip(")").split(","))
            try:
                plain_rhs = latex_to_plain(step["rhs"], macros) if latex else step["rhs"]
            except (ValueError, RecursionError):
                plain_rhs = ""
            n, _ = _tokens(plain_rhs)
            all_names |= n - params
            before_paren |= _before_parenthesis(plain_rhs)
            continue
        drafted_steps.append(step)
        for variant in _branches(step):        # A = B \pm C holds for both signs
            card, names, todo = _safe_card_for(variant, str(rel), latex, macros)
            step["plain_identity"] = card.get("check") == "identity"
            step["bound"] = {str(card[k]) for k in ("variable",) if card.get(k)}
            before_paren |= card.pop("_before_paren", set())
            all_names |= names
            all_todo |= todo
            path = out / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', variant['id'])}.yaml"
            pending.append((path, card, todo - set(card.get("notation") or {})))
    body = raw.split("\\begin{document}", 1)[-1]
    sections = [m.start() for m in re.finditer(r"\\(?:sub)*section\*?\s*\{|\\appendix\b", body)]
    scoped = {n: values.get(n, []) + display_values.get(n, []) for n in set(values) | set(display_values)}
    for cstep in _consistency_steps(drafted_steps, latex, macros, _redefined(scoped), sections):
        card, names, todo = _safe_card_for(cstep, str(rel), latex, macros)
        card["consistency"] = {"of": cstep["consistency_of"], "displays": cstep["displays"]}
        card.pop("_before_paren", None)
        all_names |= names
        all_todo |= todo
        path = out / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', cstep['id'])}.yaml"
        pending.append((path, card, todo - set(card.get("notation") or {})))
    # subscripted names (epsilon_d, Gamma_L) are symbols unless the paper gives
    # them a value (a display "X = ...") or they look like a combination of two
    # other names (e_nm next to e_n and e_m): those stay for the reviewer
    valued, valued_functions = set(), set()
    for step in steps:
        for side, is_left in ((step["lhs"], True), (step["rhs"], False)):
            try:
                head = latex_to_plain(side, macros).strip() if latex else side.strip()
            except (ValueError, RecursionError):
                continue
            # "-A = ...", "2A = ..." and "... = -A" give A a value; "... = 2 epsilon"
            # is an ordinary claim about a parameter
            strip = r"^[-+]?\s*(?:\d+(?:\.\d+)?\s*\*?\s*)?" if is_left else r"^[-+]?\s*"
            head = re.sub(strip, "", head).strip(" ()")
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", head):
                valued.add(head)                      # "A = ...", "... = -2A"
            m = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\s*\([^()]*\)", head)
            if m:
                valued_functions.add(m.group(1))      # "A(w) = ..."
    for name in sorted(all_todo):
        if "_" not in name or name in valued or name.startswith("_") or name.endswith("_"):
            continue
        stem, _, sub = name.partition("_")
        combined = len(sub) == 2 and {f"{stem}_{sub[0]}", f"{stem}_{sub[1]}"} <= (all_names | all_todo)
        if not combined and re.fullmatch(r"[A-Za-z0-9_]+", name) and "__" not in name:
            all_todo.discard(name)
            all_names.add(name)
    # definitions stated in the running text ("where $z_\\pm = ...$")
    # a constant (Sigma \equiv -i Gamma/2) also written as Sigma(omega) is not one constant
    for name in [n for n in constants if n in before_paren]:
        constants.pop(name)
        shared_quotes = {k: v for k, v in shared_quotes.items() if k != f"define:{name}()"}
    inline_notation: dict[str, str] = {name: f"{name}()" for name in constants}
    special = special_functions_named(raw) if latex else {}
    inline_notation.update(special)            # zeta -> zeta_fn when the text says so
    all_names -= set(special)
    all_names -= set(constants)
    if latex:
        for key, entry, name in _inline_definitions(prose, macros):
            if key in shared_quotes or any(k.split(":", 1)[1].split("(")[0] == name for k in shared_quotes):
                continue
            if len({squash(rhs) for _, rhs in assigned.get(name, [])}) > 1:
                continue                   # given two different values in the text
            if name in display_values or name in equiv_names:
                continue                   # a display gives it a value too: which one holds where?
            shared_quotes[key] = entry
            if key.endswith("()"):                     # a named constant: z_p -> z_p()
                inline_notation[name] = f"{name}()"
                all_names.discard(name)
            try:
                quote = entry["quote"] if isinstance(entry, dict) else entry
                all_names |= _tokens(latex_to_plain(quote, macros))[0]
            except (ValueError, RecursionError):
                pass
    # a drafted definition whose name is also used as a plain symbol (papers
    # reuse letters) would turn every such use into a function: keep it inactive
    all_names -= set(constants)          # quotes may mention a constant again
    quotes = [q.get("quote") if isinstance(q, dict) else q
              for _, card, _ in pending for q in (card.get("source") or {}).values()]
    quotes += [q.get("quote") if isinstance(q, dict) else q for q in shared_quotes.values()]
    # a name the text calls positive or real as a bare symbol is a number there
    bare = _bare_uses(quotes, macros, latex) | set(_positive_symbols(prose)) | _stated_numbers(prose)
    # a named constant (Gamma -> Gamma()) is used bare on purpose and never clashes
    clashing = {k: v for k, v in shared_quotes.items()
                if not k.endswith("()") and k.split(":", 1)[1].split("(")[0] in bare}
    shared_quotes = {k: v for k, v in shared_quotes.items() if k not in clashing}
    # a shared definition whose quote cannot be found verbatim would block every card using it
    squashed_raw = " ".join(raw.split())
    shared_quotes = {k: v for k, v in shared_quotes.items()
                     if " ".join(str(v.get("quote") if isinstance(v, dict) else v).split()) in squashed_raw}
    all_names -= {k.split(":", 1)[1].split("(")[0] for k in shared_quotes}   # defined, not free
    conventions = out / "conventions.yaml"
    defined = {k.split(":", 1)[1].split("(")[0] for k in shared_quotes}
    all_todo -= defined | {"n_F", "n_B", "im_of", "re_of", "sum_pm"}
    all_todo = {t for t in all_todo if not t.startswith(("sum_", "iomega_", "inu_"))}
    for path, card, todo in pending:       # written now, so the hint lists only what is still open
        header = "# Draft from " + doc.name + ". Quotes are verbatim; do not edit them.\n"
        todo = todo & all_todo
        if todo:
            header += "# Needs notation or definitions for: " + ", ".join(sorted(todo)) + "\n"
        path.write_text(header + yaml.safe_dump(card, sort_keys=False, allow_unicode=True),
                        encoding="utf-8")
        written.append(str(path))
    all_names -= {"d", "int"}
    positive = _positive_symbols(prose)
    real_stated, complex_stated = _stated_realness(prose)
    numbers = _stated_numbers(prose)
    realness_matters = _realness_sensitive(steps, shared_quotes, macros, latex)
    def _stated_number(name):
        # the text calls it real or positive, uses it bare as a symbol and never
        # writes "name(...) = ...": a number, so name(x) is a product
        return (name in numbers or name in positive) and name in all_names \
            and name not in valued_functions
    if not conventions.exists():
        defined_names = {k.split(":", 1)[1].split("(")[0] for k in shared_quotes}
        clash_names = {k.split(":", 1)[1].split("(")[0] for k in clashing}
        ambiguous = sorted(before_paren - defined_names)
        data: dict[str, Any] = {
            "symbols": [_symbol_entry(n, positive, real_stated, complex_stated, realness_matters)
                        for n in sorted(all_names)],
            "notation": dict(inline_notation), "define": {},
            # quantities the paper gives a value; without a definition a card
            # using them is not decided (they are not free symbols)
            "named_quantities": sorted((valued - defined_names - {"x"}) - _KNOWN),
            "named_functions": sorted((valued_functions - defined_names) - _KNOWN - {"n_F", "n_B"}),
            # names written right before "(": a product only if listed here
            # a Greek letter is taken as a product only if the paper also uses it as a
            # plain symbol; sigma(omega) alone is more likely a function
            "multiply": [n for n in ambiguous if n in _CONSTANTS
                         and n not in defined_names and n not in clash_names],
            # names the text calls real or positive as bare symbols: where a card also
            # uses one bare, it cannot be a function there
            "stated_numbers": sorted(n for n in ambiguous if _stated_number(n))}
        collided = sorted(subscript_collisions(raw)) if latex else []
        if collided:
            data["subscript_collisions"] = collided      # X_+ and X_p are both read as X_p
        if log_base_stated(prose):
            data["log_base"] = log_base_stated(prose)    # log is not the natural logarithm here
        redefined = sorted(builtins_redefined(raw)) if latex else []
        if redefined:
            data["builtins_redefined"] = redefined     # the paper's own erf(u) = ..., not the built-in
        operators = sorted(_operator_names(prose))
        if operators:
            data["operators"] = operators     # names the text calls operators: products do not commute
        if _distribution_not_thermal(prose):
            data["distribution_not_thermal"] = _distribution_not_thermal(prose)
        if distribution_defined_in_text(prose):
            data["distribution_in_text"] = distribution_defined_in_text(prose)
        constraints = prose_constraints(raw, macros) if latex else {}
        if constraints:
            # names in relations the text imposes (e^{iqL} = 1, t > s): never refuted as free
            data["constrained"] = sorted(constraints)
        noncommuting = stated_noncommuting(prose)
        if noncommuting:
            # products of matrices do not commute: scalar checks would be wrong
            data["noncommuting"] = noncommuting
        # names the running text gives a value without a definition being used
        # (x = w/Delta, or two values): free symbols for VALID, never refuted
        data["valued_in_text"] = sorted((set(assigned) | set(values)) - defined_names - _KNOWN)
        # numbers the text sets a name to ($a = 0$): a VALID that is singular there is withheld
        numeric = {n: sorted({v for _, v in vals if re.fullmatch(r"-?\s*\d+(?:\.\d+)?", v)})
                   for n, vals in values.items() if n not in defined_names}
        data["stated_values"] = {n: v for n, v in sorted(numeric.items()) if v}
        # names the text calls integers ('integer $n$', 'n \\in \\mathbb{Z}')
        data["integers"] = sorted(_stated_integers(prose) | _matsubara_names(prose))
        # the rest is checked both ways (function and product); a verdict
        # stands only if the readings agree
        data["either"] = [n for n in ambiguous if n not in data["multiply"]
                          and n not in {"im_of", "re_of", "sum_pm"} | _KNOWN]
        if shared_quotes:
            data["source_document"] = str(rel)
            data["source"] = shared_quotes
        header = (f"# Shared conventions for {doc.name}: fill once, used by every card.\n"
                  "# Check the positive: true guesses (taken from 'x > 0' in the text).\n")
        footer = "".join(f"#   {t}\n" for t in sorted(all_todo))
        if footer:
            footer = "# Tokens to map in notation (paper token -> card syntax) or define:\n" + footer
        if data["either"]:
            footer += ("# either: names written right before '(' with no word on whether they\n"
                       "# multiply or are functions. Each card is checked both ways and decided\n"
                       "# only if the two readings agree. Move a name to multiply: or functions:\n"
                       "# (or define it) once you know which it is.\n")
        if clashing:
            footer += ("# Definitions found but not activated: the name is also used as a plain\n"
                       "# symbol elsewhere. Move one under source: if it applies to every card.\n")
            footer += "".join(f"#   {k}: {json.dumps(v if isinstance(v, str) else v.get('quote'))}\n"
                              for k, v in sorted(clashing.items()))
        conventions.write_text(header + yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
                               + footer, encoding="utf-8")
    return {"document": str(doc), "cards": written, "conventions": str(conventions),
            "shared_definitions": sorted(shared_quotes),
            "definitions_drafted": drafted_definitions,
            "inactive_definitions": sorted(clashing),
            "unresolved_tokens": sorted(all_todo), "symbols_guessed": sorted(all_names)}
