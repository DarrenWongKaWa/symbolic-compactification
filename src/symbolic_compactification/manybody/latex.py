"""LaTeX math -> the plain notation that fidelity.translate reads.

Only a fixed, reviewable subset is converted; anything else is left in
place, so the strict parser later refuses it (the quote is then UNCHECKED,
never silently misread):

- macros defined in the document with \\newcommand, \\renewcommand or \\def
  (with or without arguments) are expanded first;
- \\frac, \\dfrac, \\tfrac, \\sqrt; ^{...}; subscripts are flattened into the
  name (e_{nm} -> e_nm, f_{\\pm} -> f_±);
- Greek letters, \\psi^{(k)} -> psik, \\exp, \\cosh, \\ln, ...;
- spacing and sizing commands (\\left, \\right, \\big, \\,, \\quad, &, \\\\) and
  \\mathrm{}, \\text{}, \\operatorname{} wrappers are dropped.
"""
from __future__ import annotations

import re

_GREEK = ("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi "
          "pi rho sigma tau upsilon phi chi psi omega Gamma Delta Theta Lambda Xi Pi "
          "Sigma Upsilon Phi Psi Omega").split()
_ALIASES = {"varepsilon": "epsilon", "vartheta": "theta", "varphi": "phi", "varrho": "rho",
            "ell": "l", "infty": "oo", "ln": "log", "cdot": "*", "times": "*",
            "pm": "±", "mp": "∓", "exp": "exp", "log": "log", "cosh": "cosh",
            "sinh": "sinh", "tanh": "tanh", "cos": "cos", "sin": "sin", "tan": "tan"}
_DROP = ("left", "right", "big", "Big", "bigg", "Bigg", "bigl", "bigr", "Bigl", "Bigr",
         "biggl", "biggr", "nonumber", "notag", "displaystyle", "quad", "qquad")
_WRAPPERS = ("mathrm", "text", "operatorname", "mathit", "mathbf", "boldsymbol", "rm")
_MACRO_DEF = re.compile(
    r"\\(?:re)?newcommand\*?\s*\{?\\([A-Za-z]+)\}?\s*(?:\[(\d)\])?\s*\{"
    r"|\\def\s*\\([A-Za-z]+)\s*((?:#\d)*)\s*\{")


def _group(text: str, start: int) -> tuple[str, int]:
    """Content of the brace group opening at text[start] == '{', and the
    index after its closing brace."""
    depth, i = 0, start
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
        i += 1
    raise ValueError("unbalanced braces")


def _argument(text: str, i: int) -> tuple[str, int]:
    while i < len(text) and text[i].isspace():
        i += 1
    if i < len(text) and text[i] == "{":
        return _group(text, i)
    if i < len(text) and text[i] == "\\":
        m = re.match(r"\\[A-Za-z]+", text[i:])
        if m:
            return m.group(0), i + m.end()
    return (text[i], i + 1) if i < len(text) else ("", i)


def read_macros(document: str) -> dict[str, tuple[int, str]]:
    """{name: (number of arguments, body)} from the document preamble."""
    macros: dict[str, tuple[int, str]] = {}
    for m in _MACRO_DEF.finditer(document):
        try:
            body, _ = _group(document, m.end() - 1)
        except ValueError:
            continue
        if m.group(1):
            macros[m.group(1)] = (int(m.group(2) or 0), body)
        else:
            macros[m.group(3)] = (len(m.group(4) or "") // 2, body)
    return macros


def expand_macros(text: str, macros: dict[str, tuple[int, str]], depth: int = 0) -> str:
    if not macros or depth > 8:
        return text
    out, i, changed = [], 0, False
    while i < len(text):
        m = re.match(r"\\([A-Za-z]+)", text[i:])
        if m and m.group(1) in macros:
            nargs, body = macros[m.group(1)]
            j = i + m.end()
            for k in range(1, nargs + 1):
                arg, j = _argument(text, j)
                body = body.replace(f"#{k}", arg)
            out.append(body)
            i, changed = j, True
        else:
            out.append(text[i])
            i += 1
    result = "".join(out)
    return expand_macros(result, macros, depth + 1) if changed else result


_SUB_SIGNS = {"+": "p", "-": "m", "±": "PM", "∓": "MP"}


def _flatten(text: str) -> str:
    r"""Subscript/label text -> identifier characters: e_{n,+} -> e_np,
    f_{\pm} -> f_PM (a branch marker, see fidelity._pick_branch)."""
    text = re.sub(r"[\s{},()]", "", text)
    return "".join(_SUB_SIGNS.get(ch, ch) for ch in text)


def _strip_trailing_space(out: list[str]) -> None:
    while out and out[-1].endswith(" "):
        out[-1] = out[-1].rstrip()
        if not out[-1]:
            out.pop()


def _convert(text: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\":
            m = re.match(r"\\([A-Za-z]+|.)", text[i:])
            name, i = m.group(1), i + m.end()
            sum_pm = re.match(r"_\s*\{?\s*\\(pm|mp)\s*\}?", text[i:]) if name == "sum" else None
            if sum_pm:
                out.append(" sum_pm ")
                i += sum_pm.end()
            elif name in ("frac", "dfrac", "tfrac"):
                num, i = _argument(text, i)
                den, i = _argument(text, i)
                out.append(f"(({_convert(num)})/({_convert(den)}))")
            elif name == "sqrt":
                arg, i = _argument(text, i)
                out.append(f"sqrt({_convert(arg)})")
            elif name in _WRAPPERS:
                arg, i = _argument(text, i)
                out.append(_convert(arg))
            elif name == "psi" and re.match(r"\s*\^\s*\{?\s*\((\d)\)\s*\}?", text[i:]):
                k = re.match(r"\s*\^\s*\{?\s*\((\d)\)\s*\}?", text[i:])
                out.append(f"psi{k.group(1)}")
                i += k.end()
            elif name in _DROP or name in (",", ";", "!", ":", " ", "\\"):
                out.append(" ")
            elif name in _GREEK:
                out.append(f" {name} " if not text[i:i + 1] == "_" else name)
            elif name in _ALIASES:
                out.append(f" {_ALIASES[name]} " if _ALIASES[name].isalpha() else _ALIASES[name])
            elif name in ("{", "}"):
                out.append(name)
            else:
                out.append("\\" + name)          # unsupported: the parser will refuse it
        elif c == "_":
            arg, i = _argument(text, i + 1)
            _strip_trailing_space(out)
            out.append("_" + _flatten(_convert(arg)))
        elif c == "^":
            arg, i = _argument(text, i + 1)
            label = re.fullmatch(r"\s*\((.*)\)\s*", arg)
            if label and out and re.search(r"[A-Za-z0-9_]\s*$", "".join(out)):
                _strip_trailing_space(out)
                out.append("__" + _flatten(_convert(label.group(1))))   # rho^{(0)} is a label
            else:
                out.append(f"^({_convert(arg)})")
        elif c in "&~":
            out.append(" ")
            i += 1
        elif c == "{":
            arg, i = _group(text, i)
            out.append(f"({_convert(arg)})")
        else:
            out.append(c)
            i += 1
    return "".join(out)


def latex_to_plain(text: str, macros: dict[str, tuple[int, str]] | None = None) -> str:
    """Convert a LaTeX math fragment; raises ValueError on unbalanced braces."""
    text = re.sub(r"\\label\{[^}]*\}", "", text)
    text = expand_macros(text, macros or {})
    plain = _convert(text)
    plain = re.sub(r"(?<![A-Za-z0-9_])e\^\(", "E^(", plain)   # e^{x} is the exponential
    return re.sub(r"_\s+", "_", plain)


def looks_like_latex(text: str) -> bool:
    return "\\" in text or bool(re.search(r"[_^]\{", text))
