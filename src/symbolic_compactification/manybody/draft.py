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

from ..parser import _ALLOWED_FUNCTIONS
from .latex import latex_to_plain, read_macros

_ENVIRONMENTS = ("equation", "align", "gather", "multline", "eqnarray", "flalign")
_ENV_RE = re.compile(r"\\begin\{(" + "|".join(_ENVIRONMENTS) + r")\*?\}(.*?)\\end\{\1\*?\}", re.S)
_DISPLAY_RE = re.compile(r"\\\[(.*?)\\\]|\$\$(.*?)\$\$", re.S)
_LABEL_RE = re.compile(r"\\label\{([^}]*)\}")
_O_TERM = re.compile(r"\s*\+\s*(?:\\mathcal\{O\}|O)\s*[\(\[]\s*(.+?)\s*[\)\]]\s*[.,;]?\s*$")
_ONLY_O = re.compile(r"^\s*(?:\\mathcal\{O\}|O)\s*[\(\[]\s*(.+?)\s*[\)\]]\s*[.,;]?\s*$")
_KNOWN = set(_ALLOWED_FUNCTIONS) | {"pi", "E", "I", "oo", "i", "nF", "nB", "Diff", "exp", "log"}


def split_top_level(text: str, sep: str = "=") -> list[str]:
    """Split at ``sep`` outside brackets; ``==``, ``<=``, ``>=``, ``!=`` are kept."""
    parts, depth, start, i = [], 0, 0, 0
    while i < len(text):
        c = text[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif (c == sep and depth == 0 and text[i - 1:i] not in ("<", ">", "!", "=")
              and text[i + 1:i + 2] != "="):
            parts.append(text[start:i])
            start = i + 1
        i += 1
    parts.append(text[start:])
    return parts


def _clean(fragment: str) -> str:
    fragment = _LABEL_RE.sub("", fragment)
    fragment = re.sub(r"\\(nonumber|notag)", "", fragment)
    fragment = fragment.replace("&", " ")
    fragment = " ".join(fragment.split())
    previous = None
    while previous != fragment:                  # trailing \; \, \quad and punctuation
        previous = fragment
        # strip(" ,.;") can leave the backslash of a trailing "\;" behind
        fragment = re.sub(r"(\\[,;:!]|\\q?quad|\\\\|\\)\s*$", "", fragment).strip(" ,.;")
    return fragment


def latex_equations(document: str) -> list[dict[str, Any]]:
    """[{label, rows: [text, ...]}] for every display in a LaTeX document."""
    body = document.split("\\begin{document}", 1)[-1]
    found = []
    for m in _ENV_RE.finditer(body):
        label = _LABEL_RE.search(m.group(2))
        rows = [r for r in re.split(r"\\\\", m.group(2)) if r.strip()]
        found.append({"label": label.group(1) if label else None, "rows": rows,
                      "offset": m.start(),
                      "context": body[max(0, m.start() - 800):m.start()] + body[m.end():m.end() + 300],
                      "sentence": _last_sentence(body[max(0, m.start() - 800):m.start()]),
                      "document": body})
    for m in _DISPLAY_RE.finditer(body):
        text = m.group(1) or m.group(2)
        found.append({"label": None, "rows": [text], "offset": m.start(),
                      "context": body[max(0, m.start() - 800):m.start()] + body[m.end():m.end() + 300],
                      "sentence": _last_sentence(body[max(0, m.start() - 800):m.start()]),
                      "document": body})
    return sorted(found, key=lambda e: e["offset"])


def _document_fragment(raw: str, fragment: str) -> str | None:
    """The verbatim document text for a cleaned fragment (whitespace aside).
    Cleaning only removes labels, '&' and surrounding punctuation, so the
    fragment is verbatim unless an '&' sat inside it."""
    squashed = " ".join(raw.split())
    return fragment if fragment and fragment in squashed else None


_CONTINUES = re.compile(r"^(?:\s|&|\\q?quad|\\[,;!]|\\nonumber)*"
                       r"(?:[-+*/(\[]|\\(?:times|cdot|pm|mp|left|Bigl|bigl|biggl|Big|big|bigg|lbrace)\b)")


def steps_from_latex(raw: str) -> list[dict[str, Any]]:
    steps = []
    for n, eq in enumerate(latex_equations(raw), start=1):
        chains: list[list[str]] = []
        for row in eq["rows"]:
            pieces = split_top_level(row)
            head = _clean(pieces[0])
            if not chains:
                chains.append(pieces)
            elif len(pieces) == 1:                 # no '=': continues only if it starts
                if _CONTINUES.match(row):          # with an operator or a bracket
                    chains[-1][-1] += " " + row
            elif not head:                         # "&= C": the chain continues
                chains[-1] += pieces[1:]
            else:                                  # "A &= B" on its own row: a new relation
                chains.append(pieces)
        base = eq["label"] or f"eq{n}"
        relations = [[_clean(p) for p in chain if _clean(p)] for chain in chains]
        relations = [r for r in relations if len(r) >= 2]
        for j, chain in enumerate(relations):
            stem = base if len(relations) == 1 else f"{base}.r{j + 1}"
            for k in range(len(chain) - 1):
                steps.append({"id": stem if len(chain) == 2 else f"{stem}.{k + 1}",
                              "lhs": chain[k], "rhs": chain[k + 1],
                              "context": eq.get("context", ""), "sentence": eq.get("sentence", ""),
                              "document": eq.get("document", "")})
    return steps


def steps_from_sheet(raw: str) -> list[dict[str, Any]]:
    """Plain-text sheets: '### ID' headings followed by 'Claim: A = B'."""
    steps, current = [], None
    for line in raw.splitlines():
        head = re.match(r"#{2,4}\s+(\S+)", line)
        if head:
            current = head.group(1)
            continue
        claim = re.match(r"\s*Claim:\s*(.+)", line)
        if claim and current:
            text = claim.group(1).strip()
            clauses = split_top_level(text, ",")
            main = clauses[0]
            sides = split_top_level(main)
            extra = []
            for clause in clauses[1:]:
                kv = split_top_level(clause)
                if len(kv) == 2 and re.fullmatch(r"\s*[A-Za-z_][\w+\-^()]*\s*", kv[0]):
                    extra.append({"name": kv[0].strip(), "quote": kv[1].strip()})
            if len(sides) >= 2:
                for k in range(len(sides) - 1):
                    steps.append({"id": current if len(sides) == 2 else f"{current}.{k + 1}",
                                  "lhs": sides[k].strip(), "rhs": sides[k + 1].strip(),
                                  "definitions": extra})
            current = None
    return steps


def _tokens(plain: str) -> tuple[set[str], set[str]]:
    """(plain names, names that need notation or a definition)."""
    names, todo = set(), set()
    for m in re.finditer(r"(?<![\\A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*(?:_[+\-])?(\()?", plain):
        name = m.group(0).rstrip("(")
        if name in _KNOWN or re.fullmatch(r"psi\d?", name):
            continue
        if m.group(1) or "_" in name:
            todo.add(name)
        else:
            names.add(name)
    return names, todo


# a Fermi integral over the whole real line only: \int or \int_{-\infty}^{\infty};
# other limits are a different integral and are never drafted as fermi_integral
_INTEGRAL = re.compile(
    r"^\\int(?:\\limits)?(?:_\{\s*-\s*\\infty\s*\}\^\{?\s*\+?\s*\\infty\s*\}?)?\s*"
    r"(?:\\frac\{\s*d\s*(?P<v1>\\?[A-Za-z]+)\s*\}\{\s*2\s*\\pi\s*\}|d\s*(?P<v2>\\?[A-Za-z]+))"
    r"\s*(?:\\[,;!]\s*)?(?P<body>.+)$", re.S)
_MATSUBARA = re.compile(
    r"^(?:\\frac\{1\}\{\\beta\}|\{\s*1\s*\\over\s*\\beta\s*\}|T|k_B\s*T)\s*"
    r"\\sum_\{?\s*(?P<index>[a-z])\s*\}?\s*(?P<body>.+)$", re.S)
_SERIES = re.compile(
    r"^\\sum_\{\s*(?P<index>[a-z])\s*=\s*(?P<lower>-?\d+)\s*\}\^\{?\s*\\infty\s*\}?\s*(?P<body>.+)$", re.S)
_DEFINITION_LHS = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*([A-Za-z_][\w\s,]*)\)\s*$")


def _var_name(token: str) -> str:
    return token.lstrip("\\")


def _limit_point(var: str, text: str) -> str | None:
    """'x \\to \\infty' / 'large x' -> oo, 'x \\to 0' / 'small x' -> 0, else None."""
    v = rf"\\?{re.escape(var)}"
    infinity = re.search(rf"{v}\s*\\(?:to|rightarrow)\s*\+?\s*\\infty|large\s+\$?{v}\b", text)
    zero = re.search(rf"{v}\s*\\(?:to|rightarrow)\s*0|small\s+\$?{v}\b", text)
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
        point = said or ("oo" if order < 0 else "unstated")
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
    head = re.fullmatch(r"\s*([A-Za-z][A-Za-z0-9]*?)__(r|a|lt|gt)\s*\([^()]*\)\s*",
                        latex_to_plain(lhs, macros))
    integral = _TIME_INTEGRAL.match(rhs.strip())
    if not head or not integral:
        return None
    body = integral.group("body").strip()
    plain = latex_to_plain(body, macros)
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
    notation = {m.group(0): f"{m.group(1)}_{_COMPONENT[m.group(2)]}"
                for m in _KELDYSH_FACTOR.finditer(plain)}
    return {"check": "langreth", "product": product, "component": _COMPONENT[head.group(2)],
            "notation": notation, "source": {"claim": body}}


def _last_sentence(text: str) -> str:
    """The sentence that leads into a display: text after the last full stop,
    paragraph break or previous display."""
    cut = max(text.rfind(". "), text.rfind(".\n"), text.rfind("\n\n"), text.rfind("\\par"),
              text.rfind("\\end{"))
    return text[cut + 1:] if cut >= 0 else text


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


def _matsubara_statistics(step: dict, match: re.Match) -> str | None:
    body, index = match.group("body"), match.group("index")
    return _statistics(step, _frequency(body, index), index)


def _card_for(step: dict, doc_name: str, latex: bool, macros: dict) -> tuple[dict, set, set]:
    lhs, rhs = step["lhs"], step["rhs"]
    card: dict[str, Any] = {"label": step["id"], "include": "conventions.yaml",
                            "source_document": doc_name}
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
    elif latex and _langreth(lhs, rhs, macros) and re.search(r"langreth", step.get("context", ""), re.I):
        card.update(_langreth(lhs, rhs, macros))      # the paper itself invokes Langreth's rules
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
    else:
        card["check"] = "identity"
        card["source"] = {"lhs": lhs, "rhs": rhs}
        if matsubara:
            card["hint"] = ("a Matsubara sum, but the text does not say fermionic or bosonic: "
                            "set check: matsubara and statistics: fermion|boson")
        if latex and _langreth(lhs, rhs, macros):
            card["hint"] = ("shaped like a Langreth rule; if the paper claims the exact rule, "
                            "set check: langreth (product, component, notation as for a drafted rule)")
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
    return card, names, todo


def _definition(step: dict, latex: bool, macros: dict) -> list[tuple[str, Any]] | None:
    """``name(args) = body`` with plain arguments is a definition, not a
    claim: it goes to conventions.yaml as quoted define: entries (both
    branches when the name carries a +- subscript)."""
    plain = latex_to_plain(step["lhs"], macros) if latex else step["lhs"]
    m = _DEFINITION_LHS.match(plain)
    if not m or _O_TERM.search(step["rhs"]) or _ONLY_O.match(step["rhs"]):
        return None                     # f(x) = ... + O(x^n) is an expansion, not a definition
    if m.group(1) in _KNOWN | {"n_F", "n_B"}:
        return None                     # n_F, exp, ... are already defined
    name, args = m.group(1), ",".join(a.strip() for a in m.group(2).split(","))
    if "PM" in name or name.endswith("_pm"):
        base = name.replace("PM", "").removesuffix("_pm").rstrip("_") + "_"
        return [(f"define:{base}p({args})", {"quote": step["rhs"], "branch": "+"}),
                (f"define:{base}m({args})", {"quote": step["rhs"], "branch": "-"})]
    return [(f"define:{name}({args})", step["rhs"])]


def _positive_symbols(raw: str) -> dict[str, str]:
    """Names stated positive in the text, e.g. $\\Gamma>0$ or beta > 0, with
    where they are stated (so a reviewer can confirm the guess)."""
    found: dict[str, str] = {}
    for m in re.finditer(r"\\?([A-Za-z]+)\s*>\s*0(?![.\d])", raw):
        found.setdefault(m.group(1), f"line {raw.count(chr(10), 0, m.start()) + 1}: {m.group(0)}")
    return found


def draft(document: str | Path, out_dir: str | Path) -> dict[str, Any]:
    doc = Path(document)
    raw = doc.read_text(encoding="utf-8")
    latex = doc.suffix == ".tex"
    steps = steps_from_latex(raw) if latex else steps_from_sheet(raw)
    macros = read_macros(raw) if latex else {}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rel = Path(os.path.relpath(doc.resolve(), out.resolve()))
    if rel.parts[:4] == ("..",) * 4:                     # far apart: keep it absolute
        rel = doc.resolve()
    positive = _positive_symbols(raw)
    for step in steps:
        step["positive_names"] = set(positive)
    all_names, all_todo, written, shared_quotes = set(), set(), [], {}
    before_paren: set[str] = set()
    for step in steps:
        try:
            definition = _definition(step, latex, macros)
        except (ValueError, RecursionError):
            definition = None
        if definition:
            shared_quotes.update(definition)
            params = set(definition[0][0].split("(", 1)[1].rstrip(")").split(","))
            plain_rhs = latex_to_plain(step["rhs"], macros) if latex else step["rhs"]
            n, _ = _tokens(plain_rhs)
            all_names |= n - params
            before_paren |= _before_parenthesis(plain_rhs)
            continue
        card, names, todo = _card_for(step, str(rel), latex, macros)
        before_paren |= card.pop("_before_paren", set())
        all_names |= names
        all_todo |= todo
        path = out / f"{re.sub(r'[^A-Za-z0-9_.-]', '_', step['id'])}.yaml"
        header = "# Draft from " + doc.name + ". Quotes are verbatim; do not edit them.\n"
        todo = todo - {"n_F", "n_B", "im_of", "re_of", "sum_pm"} - {k.split(":", 1)[1].split("(")[0] for k in shared_quotes}
        todo = {t for t in todo if not t.startswith(("sum_", "iomega_", "inu_"))}
        if todo:
            header += "# Needs notation or definitions for: " + ", ".join(sorted(todo)) + "\n"
        path.write_text(header + yaml.safe_dump(card, sort_keys=False, allow_unicode=True),
                        encoding="utf-8")
        written.append(str(path))
    # a drafted definition whose name is also used as a plain symbol (papers
    # reuse letters) would turn every such use into a function: keep it inactive
    clashing = {k: v for k, v in shared_quotes.items()
                if k.split(":", 1)[1].split("(")[0] in all_names}
    shared_quotes = {k: v for k, v in shared_quotes.items() if k not in clashing}
    conventions = out / "conventions.yaml"
    defined = {k.split(":", 1)[1].split("(")[0] for k in shared_quotes}
    all_todo -= defined | {"n_F", "n_B", "im_of", "re_of", "sum_pm"}
    all_todo = {t for t in all_todo if not t.startswith(("sum_", "iomega_", "inu_"))}
    all_names -= {"d", "int"}
    positive = _positive_symbols(raw)
    if not conventions.exists():
        defined_names = {k.split(":", 1)[1].split("(")[0] for k in shared_quotes}
        clash_names = {k.split(":", 1)[1].split("(")[0] for k in clashing}
        ambiguous = sorted(before_paren - defined_names)
        data: dict[str, Any] = {
            "symbols": [{"name": n, **({"positive": True, "stated": positive[n]} if n in positive else {})}
                        for n in sorted(all_names)],
            "notation": {}, "define": {},
            # names written right before "(": a product only if listed here
            # a Greek letter is taken as a product only if the paper also uses it as a
            # plain symbol; sigma(omega) alone is more likely a function
            "multiply": [n for n in ambiguous if n in _CONSTANTS
                         and n not in defined_names and n not in clash_names]}
        if shared_quotes:
            data["source_document"] = str(rel)
            data["source"] = shared_quotes
        header = (f"# Shared conventions for {doc.name}: fill once, used by every card.\n"
                  "# Check the positive: true guesses (taken from 'x > 0' in the text).\n")
        footer = "".join(f"#   {t}\n" for t in sorted(all_todo))
        if footer:
            footer = "# Tokens to map in notation (paper token -> card syntax) or define:\n" + footer
        undecided = [n for n in ambiguous if n not in data["multiply"]]
        if undecided:
            footer += ("# Written right before '(': product or function value? Add a name to\n"
                       "# multiply: if it multiplies, or define it as a function:\n")
            footer += "".join(f"#   {n}\n" for n in undecided)
        if clashing:
            footer += ("# Definitions found but not activated: the name is also used as a plain\n"
                       "# symbol elsewhere. Move one under source: if it applies to every card.\n")
            footer += "".join(f"#   {k}: {json.dumps(v if isinstance(v, str) else v.get('quote'))}\n"
                              for k, v in sorted(clashing.items()))
        conventions.write_text(header + yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
                               + footer, encoding="utf-8")
    return {"document": str(doc), "cards": written, "conventions": str(conventions),
            "shared_definitions": sorted(shared_quotes),
            "inactive_definitions": sorted(clashing),
            "unresolved_tokens": sorted(all_todo), "symbols_guessed": sorted(all_names)}
