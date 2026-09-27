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
                      "offset": m.start()})
    for m in _DISPLAY_RE.finditer(body):
        text = m.group(1) or m.group(2)
        found.append({"label": None, "rows": [text], "offset": m.start()})
    return sorted(found, key=lambda e: e["offset"])


def _document_fragment(raw: str, fragment: str) -> str | None:
    """The verbatim document text for a cleaned fragment (whitespace aside).
    Cleaning only removes labels, '&' and surrounding punctuation, so the
    fragment is verbatim unless an '&' sat inside it."""
    squashed = " ".join(raw.split())
    return fragment if fragment and fragment in squashed else None


def steps_from_latex(raw: str) -> list[dict[str, Any]]:
    steps = []
    for n, eq in enumerate(latex_equations(raw), start=1):
        chain: list[str] = []
        for row in eq["rows"]:
            pieces = [p for p in split_top_level(row)]
            if not chain:
                chain += pieces
            else:                                  # "&= C" continues the chain
                if pieces and not pieces[0].strip(" &"):
                    pieces = pieces[1:]
                chain += pieces
        chain = [_clean(p) for p in chain if _clean(p)]
        base = eq["label"] or f"eq{n}"
        for k in range(len(chain) - 1):
            steps.append({"id": base if len(chain) == 2 else f"{base}.{k + 1}",
                          "lhs": chain[k], "rhs": chain[k + 1]})
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


_INTEGRAL = re.compile(
    r"^\\int(?:\\limits)?(?:_\{?[^\s{}]*\}?\^\{?[^\s{}]*\}?)?\s*"
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


def _remainder(card: dict, lhs: str, rhs: str, o_term) -> None:
    approx = rhs[:o_term.start()].strip()
    order_text = o_term.group(1)
    var_order = re.fullmatch(r"\s*\\?([A-Za-z]+)\s*(?:\^\s*\{?\s*(-?\d+)\s*\}?)?\s*", order_text)
    card["check"] = "remainder"
    if var_order:
        order = int(var_order.group(2) or 1)
        card["variable"] = var_order.group(1)
        card["order"] = order
        if order < 0:
            card["point"] = "oo"
        else:
            card["point"], card["direction"] = "0", "+"
    else:
        card.update({"variable": "TODO", "order": 1, "point": "0", "direction": "+"})
    card["source"] = {"function": lhs, "approximant": approx}


_LOWER_GREEK = frozenset("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu "
                         "xi rho sigma tau upsilon phi chi omega".split())


def _before_parenthesis(plain: str) -> set[str]:
    """Names written directly before '(' : product or function value?"""
    return {m.group(1) for m in re.finditer(r"(?<![\\A-Za-z0-9_])([A-Za-z][A-Za-z0-9_]*)\s*\(", plain)
            if m.group(1) not in _KNOWN | {"n_F", "n_B"} and not re.fullmatch(r"psi\d?", m.group(1))}


def _card_for(step: dict, doc_name: str, latex: bool, macros: dict) -> tuple[dict, set, set]:
    lhs, rhs = step["lhs"], step["rhs"]
    card: dict[str, Any] = {"include": "conventions.yaml", "source_document": doc_name}
    o_term = _O_TERM.search(rhs)
    integral = _INTEGRAL.match(lhs) if latex else None
    matsubara = _MATSUBARA.match(lhs.strip()) if latex else None
    series = _SERIES.match(lhs.strip()) if latex else None
    if o_term:
        _remainder(card, lhs, rhs, o_term)
    elif matsubara:
        body, k = matsubara.group("body").strip(), matsubara.group("index")
        boson = re.search(rf"\\nu_\{{?{k}\}}?", body) is not None
        freq = "nu" if boson else "omega"
        card.update({"check": "matsubara", "statistics": "boson" if boson else "fermion",
                     "variable": "z", "beta": "beta",
                     "notation": {f"i{freq}_{k}": "z", f"i {freq}_{k}": "z"}})
        card["source"] = {"summand": body, "claim": rhs}
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
    return card, names, todo


def _definition(step: dict, latex: bool, macros: dict) -> list[tuple[str, Any]] | None:
    """``name(args) = body`` with plain arguments is a definition, not a
    claim: it goes to conventions.yaml as quoted define: entries (both
    branches when the name carries a +- subscript)."""
    plain = latex_to_plain(step["lhs"], macros) if latex else step["lhs"]
    m = _DEFINITION_LHS.match(plain)
    if not m:
        return None
    name, args = m.group(1), ",".join(a.strip() for a in m.group(2).split(","))
    if "PM" in name or name.endswith("_pm"):
        base = name.replace("PM", "").removesuffix("_pm").rstrip("_") + "_"
        return [(f"define:{base}p({args})", {"quote": step["rhs"], "branch": "+"}),
                (f"define:{base}m({args})", {"quote": step["rhs"], "branch": "-"})]
    return [(f"define:{name}({args})", step["rhs"])]


def _positive_symbols(raw: str) -> set[str]:
    """Names stated positive in the text, e.g. $\\Gamma>0$ or beta > 0."""
    return {m.group(1) for m in re.finditer(r"\\?([A-Za-z]+)\s*>\s*0(?![.\d])", raw)}


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
        ambiguous = sorted(before_paren - defined_names)
        data: dict[str, Any] = {
            "symbols": [{"name": n, **({"positive": True} if n in positive else {})}
                        for n in sorted(all_names)],
            "notation": {}, "define": {},
            # names written right before "(": a product only if listed here
            "multiply": [n for n in ambiguous if n in _LOWER_GREEK]}
        if shared_quotes:
            data["source_document"] = str(rel)
            data["source"] = shared_quotes
        header = (f"# Shared conventions for {doc.name}: fill once, used by every card.\n"
                  "# Check the positive: true guesses (taken from 'x > 0' in the text).\n")
        footer = "".join(f"#   {t}\n" for t in sorted(all_todo))
        if footer:
            footer = "# Tokens to map in notation (paper token -> card syntax) or define:\n" + footer
        undecided = [n for n in ambiguous if n not in _LOWER_GREEK]
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
