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
            "lbrace": "(", "rbrace": ")", "lbrack": "(", "rbrack": ")",
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
    text = text.replace("/", "_").replace("|", "_")          # A_{L/R} -> A_L_R, never a division
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
            m = re.match(r"\\([A-Za-z]+|.)", text[i:], re.S)
            if m is None:                       # a lone trailing backslash
                out.append("\\")
                i += 1
                continue
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
            elif name == "psi" and re.match(r"\s*('+)", text[i:]):
                primes = re.match(r"\s*('+)", text[i:])
                out.append(f"psi{len(primes.group(1))}")
                i += primes.end()
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
            # G^r, G^{<}, c^\dagger, T^{nm}: letters (and <, >, dagger, prime) are
            # labels in physics, never powers; they become part of the name
            letters = re.fullmatch(r"\s*(?:[A-Za-z<>*/|,]+|\\dagger|\\prime|\\ast)\s*", arg)
            glued = out and re.search(r"[A-Za-z0-9_)]\s*$", "".join(out))
            if re.search(r"(?<![A-Za-z0-9_])[eE]\s*$", "".join(out)):
                letters = None                        # e^{i x} is the exponential
            if label and glued:
                _strip_trailing_space(out)
                out.append("__" + _flatten(_convert(label.group(1))))   # rho^{(0)} is a label
            elif letters and glued:
                _strip_trailing_space(out)
                tag = (arg.strip().replace("\\", "").replace("<", "lt").replace(">", "gt")
                       .replace("*", "star").replace("/", "_").replace("|", "_").replace(",", ""))
                joined = "".join(out)
                boxed = re.search(r"\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)$", joined)   # {\mathbf G}^r
                if boxed:
                    out[:] = [joined[:boxed.start()] + boxed.group(1)]
                out.append("__" + tag)
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
    text = rewrite_over(normalize_exponential(text))
    # Re / Im of the next factor: \mathrm{Im}\,\psi(z) -> im_of psi(z)
    text = re.sub(r"\{?\s*\\(?:mathrm|operatorname|rm)\s*\{?\s*(Re|Im)\s*\}?\s*\}?|\\(Re|Im)(?![A-Za-z])",
                  lambda m: f" {(m.group(1) or m.group(2)).lower()}_of ", text)
    plain = _convert(text)
    # e^{-x}, e^{i w t} are exponentials; e^2 (as in e^2/h) is the charge squared
    plain = re.sub(r"(?<![A-Za-z0-9_])e\^\((?!\s*\d+\s*\))", "E^(", plain)
    return re.sub(r"_\s+", "_", plain)


def looks_like_latex(text: str) -> bool:
    return "\\" in text or bool(re.search(r"[_^]\{", text))


_NUMBERED_ENVS = ("equation", "align", "eqnarray", "gather", "multline", "flalign")
_ENV_OPEN = re.compile(r"\\begin\{(" + "|".join(_NUMBERED_ENVS) + r")(\*?)\}")


_LAYOUT = re.compile(r"\\label\{[^}]*\}|\\nonumber|\\notag|\\\\(?:\[[^\]]*\])?|&")


_ROW_BREAK = re.compile(r"\\\\(?:\[[^\]]*\])?")
ROW = "\u00b6"          # marks where a display row ended, for quote boundaries


def layout_rows(text: str) -> str:
    """layout_free, but row breaks are kept as a marker (a row end is a
    legitimate place for a quote to stop)."""
    return layout_free(_ROW_BREAK.sub(f" {ROW} ", text))


def layout_free(text: str) -> str:
    """Text with alignment and row layout removed (&, \\\\, \\nonumber,
    \\label) and whitespace squashed: the form verbatim quotes are compared in."""
    return " ".join(_LAYOUT.sub(" ", text).replace(ROW, ROW).split())


def _squash_with_map(text: str) -> tuple[str, list[int]]:
    """layout_free text and, for each kept character, its raw offset."""
    blank = set()
    for m in _LAYOUT.finditer(text):
        blank.update(range(m.start(), m.end()))
    out, where, space = [], [], False
    for i, ch in enumerate(text):
        if ch.isspace() or i in blank:
            if out and not space:
                out.append(" ")
                where.append(i)
            space = True
            continue
        out.append(ch)
        where.append(i)
        space = False
    return "".join(out), where


def document_title(raw: str) -> str | None:
    m = re.search(r"\\title(?:\[[^\]]*\])?\s*\{", raw)
    if not m:
        return None
    try:
        body, _ = _group(raw, m.end() - 1)
    except ValueError:
        return None
    body = re.sub(r"\\(thanks|footnote)\{[^{}]*\}", "", body)
    return " ".join(re.sub(r"\\\\|[{}]|\\[A-Za-z]+\s*", " ", body).split()) or None


def locate_quote(raw: str, quote: str, within: tuple[int, int] | None = None) -> dict | None:
    """Where a verbatim quote sits: line, enclosing display environment,
    its \\label, and its number when displays are numbered in order.
    ``within`` restricts the search to a character span (the card's display)."""
    squashed, where = _squash_with_map(raw)
    target = layout_free(quote)
    hits, k = [], squashed.find(target)
    while k >= 0 and len(hits) < 200:
        if within is None or within[0] <= where[k] < within[1]:
            hits.append(where[k])
        k = squashed.find(target, k + 1)
    if not hits:
        return None
    inside = [h for h in hits if _enclosing_env(raw, h) is not None]
    pos = (inside or hits)[0]                  # prefer an occurrence in displayed math
    info: dict = {"line": raw.count("\n", 0, pos) + 1}
    if len(hits) > 1:
        info["occurrences"] = len(hits)
    opens = [m for m in _ENV_OPEN.finditer(raw, 0, pos)]
    if opens:
        env = opens[-1]
        end = raw.find(f"\\end{{{env.group(1)}{env.group(2)}}}", env.end())
        if end == -1 or end >= pos:
            info["environment"] = env.group(1) + env.group(2)
            body = raw[env.end(): end if end != -1 else len(raw)]
            label = re.search(r"\\label\{([^}]*)\}", body)
            if label:
                info["label"] = label.group(1)
            number = None if env.group(2) else _appendix_aware_number(raw, env, pos)
            if number:
                info["number"] = number
    return info


def _enclosing_env(raw: str, pos: int):
    opens = list(_ENV_OPEN.finditer(raw, 0, pos))
    if not opens:
        return None
    env = opens[-1]
    end = raw.find(f"\\end{{{env.group(1)}{env.group(2)}}}", env.end())
    return env if end == -1 or end >= pos else None


def _equation_number(raw: str, env: re.Match, pos: int) -> int | None:
    """Count numbered displays (and numbered align rows) up to pos."""
    count = 0
    for m in _ENV_OPEN.finditer(raw, 0, env.end()):
        if m.group(2):
            continue
        end = raw.find(f"\\end{{{m.group(1)}}}", m.end())
        stop = pos if m.start() == env.start() else (end if end != -1 else len(raw))
        body = raw[m.end():stop]
        if m.group(1) in ("equation", "multline"):
            count += 1
            continue
        numbered = lambda row: not re.search(r"\\(nonumber|notag)", row)
        rows = re.split(r"\\\\", body)
        if m.start() == env.start():
            # complete rows before the quote, then the row that holds it
            rest = raw[pos:end if end != -1 else len(raw)]
            current = rows[-1] + re.split(r"\\\\", rest, maxsplit=1)[0]
            count += sum(1 for r in rows[:-1] if r.strip() and numbered(r))
            if not numbered(current):
                # an unnumbered row belongs to the number printed further down
                # the same display (eqnarray rows ending in \\nonumber); none -> None
                later = re.split(r"\\\\", rest)[1:]
                if not any(r.strip() and numbered(r) for r in later):
                    return None
            count += 1
        else:
            count += sum(1 for r in rows if r.strip() and numbered(r))
    return count


_OVER = re.compile(r"\\over(?![A-Za-z])")


def rewrite_over(text: str) -> str:
    """Plain-TeX fractions: '{a \\over b}' -> '\\frac{a}{b}' at every depth."""
    def top_level_over(body: str) -> int:
        depth = 0
        for m in re.finditer(r"[{}]|\\over(?![A-Za-z])", body):
            tok = m.group(0)
            if tok == "{":
                depth += 1
            elif tok == "}":
                depth -= 1
            elif depth == 0:
                return m.start()
        return -1

    def rewrite(body: str) -> str:
        out, i = [], 0
        while i < len(body):
            if body[i] == "{":
                try:
                    inner, j = _group(body, i)
                except ValueError:
                    out.append(body[i:])
                    break
                out.append("{" + rewrite(inner) + "}")
                i = j
            else:
                out.append(body[i])
                i += 1
        joined = "".join(out)
        k = top_level_over(joined)
        if k < 0:
            return joined
        return "\\frac{" + joined[:k] + "}{" + joined[k + len("\\over"):] + "}"

    return rewrite(text) if _OVER.search(text) else text


def normalize_exponential(text: str) -> str:
    """{\\mathrm{ e}}^{x}, {\\rm e}^{x}, \\mathrm{e}^{x} -> e^{x}."""
    return re.sub(r"\{\s*\\(?:mathrm|rm)\s*\{?\s*e\s*\}?\s*\}\s*\^|\\mathrm\{\s*e\s*\}\s*\^", "E^", text)


def _appendix_aware_number(raw: str, env: re.Match, pos: int):
    """Sequential number, or A1, B3, ... after \\appendix (RevTeX style:
    each appendix section restarts the count with the next letter)."""
    appendix = raw.rfind("\\appendix", 0, pos)
    if appendix == -1:
        return _equation_number(raw, env, pos)
    sections = [m.start() for m in re.finditer(r"\\section\*?\s*[\[{]", raw[appendix:pos])]
    if not sections:
        return _equation_number(raw, env, pos)
    start = appendix + sections[-1]
    sub = raw[start:]
    local = next((m for m in _ENV_OPEN.finditer(sub) if m.start() == env.start() - start), None)
    if local is None:
        return _equation_number(raw, env, pos)
    count = _equation_number(sub, local, pos - start)
    return None if count is None else f"{chr(ord('A') + len(sections) - 1)}{count}"
