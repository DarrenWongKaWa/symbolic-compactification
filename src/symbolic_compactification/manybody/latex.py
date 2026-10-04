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

import functools
import re

_GREEK = ("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi "
          "pi rho sigma tau upsilon phi chi psi omega Gamma Delta Theta Lambda Xi Pi "
          "Sigma Upsilon Phi Psi Omega hbar").split()
_ALIASES = {"varepsilon": "epsilon", "vartheta": "theta", "varphi": "phi", "varrho": "rho",
            "ell": "l", "infty": "oo", "ln": "log", "cdot": "*", "times": "*",
            "lbrace": "(", "rbrace": ")", "lbrack": "(", "rbrack": ")",
            "pm": "±", "mp": "∓", "exp": "exp", "log": "log", "cosh": "cosh",
            "sinh": "sinh", "tanh": "tanh", "cos": "cos", "sin": "sin", "tan": "tan",
            "coth": "coth", "cot": "cot", "sec": "sec", "csc": "csc", "sech": "sech", "csch": "csch",
            "arctan": "atan", "arcsin": "asin", "arccos": "acos", "arccot": "acot",
            "arctanh": "atanh", "artanh": "atanh", "arcsinh": "asinh", "arsinh": "asinh",
            "arccosh": "acosh", "arcosh": "acosh"}
_BARE_FUNCTIONS = frozenset({"sin", "cos", "tan", "cot", "sec", "csc", "sinh", "cosh", "tanh", "coth",
                             "sech", "csch", "ln", "log", "exp", "arctan", "arcsin", "arccos", "arctanh",
                             "artanh", "arcsinh", "arccosh"})
_INVERSES = {"sin": "asin", "cos": "acos", "tan": "atan", "cot": "acot", "sinh": "asinh",
             "cosh": "acosh", "tanh": "atanh"}
# accents that make a new name: \dot N -> N__dot, \tilde G -> G__tilde (never a conjugate:
# \bar and \overline stay unread, since they often mean complex conjugation)
_ACCENTS = {"mathsf": "sf", "dot": "dot", "ddot": "ddot", "tilde": "tilde", "widetilde": "tilde", "hat": "hat",
            "widehat": "hat", "check": "check", "breve": "breve", "mathcal": "cal", "mathscr": "scr",
            "mathfrak": "frak"}
_DIFF_NUM = re.compile(r"^\s*(?:\\partial|\\mathrm\{d\}|d)\s*(?:\^\s*\{?\s*(\d)\s*\}?)?\s*(\S.*)$", re.S)
_DIFF_OPERATOR = re.compile(r"^\s*(?:\\partial|\\mathrm\{d\}|d)\s*(?:\^\s*\{?\s*(\d)\s*\}?)?\s*$")
# the denominator of a derivative: \partial y, \mathrm{d}y, dy, d\ln T (not d_0 or 2)
_DIFFERENTIAL = re.compile(r"^\s*(?:\\partial|\\mathrm\s*\{\s*d\s*\}|d(?=\s*[A-Za-z\\(]))")
# \delta X over \delta Y: a functional derivative, not (delta X)/(delta Y) = X/Y
_VARIATION = re.compile(r"^\s*\\delta(?![A-Za-z])\s*[^\s_^]")


# \Delta T, \delta n, \Delta\mu: the increment of a quantity or Delta times it.
# Both readers would read a product, and \Delta T / \Delta V would cancel to T / V.
_INCREMENT = re.compile(r"(?:\s|\\[,;:! ])*(?:[A-Za-z]|\\(?:" + "|".join(_GREEK) + r"|hat|bar|tilde|vec|dot|"
                        r"mathbf|mathcal|mathrm|boldsymbol|varepsilon|vartheta|varphi|ell)(?![A-Za-z]))")
_SIZED = r"\\(?:big|Big|bigg|Bigg)[lr]?\s*"           # \bigl( \Bigr) \biggl[ ...
_DELIMITER = r"\s*(?:\\[A-Za-z]+|\\.|[^\sA-Za-z\\])"   # ( [ | . \{ \langle after \left / \right
_OPEN = re.compile(r"\\left" + _DELIMITER + "|" + _SIZED + r"[(\[]|\(|\[|\{")
_CLOSE = re.compile(r"\\right" + _DELIMITER + "|" + _SIZED + r"[)\]]|\)|\]|\}")


def _bracket_group(text: str, i: int) -> tuple[str, int] | None:
    """The content of '(...)', '\\left( ... \\right)', '\\Bigl( ... \\Bigr)',
    '[...]' or '{...}' starting at text[i] (after spaces and thin spaces), and
    the index after it. Each delimiter inside (\\left|, \\Bigr), ']') counts once."""
    m = re.match(r"(?:\s|\\[,;:!])*(\\left\s*[(\[]|" + _SIZED + r"[(\[]|\(|\[|\{)", text[i:])
    if not m:
        return None
    start = i + m.end()
    depth, j = 1, start
    while j < len(text):
        opening, close = _OPEN.match(text, j), _CLOSE.match(text, j)
        if opening:
            depth += 1
            j = opening.end()
        elif close:
            depth -= 1
            if depth == 0:
                return text[start:j], close.end()
            j = close.end()
        elif text[j] == "\\":                  # any other command, \{ and \} included
            j = re.match(r"\\(?:[A-Za-z]+|.)", text[j:], re.S).end() + j
        else:
            j += 1
    return None


_DIFF_DEN = re.compile(r"^\s*(?:\\partial|\\mathrm\{d\}|d)\s*(\\?[A-Za-z]+(?:_\{?\s*[A-Za-z0-9]+\s*\}?)?)"
                       r"\s*(?:\^\s*\{?\s*(\d)\s*\}?)?\s*$")
_DROP = ("left", "right", "big", "Big", "bigg", "Bigg", "bigl", "bigr", "Bigl", "Bigr",
         "biggl", "biggr", "Biggl", "Biggr", "bigm", "Bigm", "nonumber", "notag", "displaystyle",
         "textstyle", "scriptstyle", "quad", "qquad", "nn")
_WRAPPERS = ("mathrm", "text", "operatorname", "mathit", "mathbf", "boldsymbol", "rm", "textrm",
             "mbox", "hbox", "textit", "mathop", "bm", "bf", "it", "mit", "emph", "textnormal")
# a macro name: letters, or one other character (\\< and \\> for angle brackets)
_NAME = r"([A-Za-z]+|[^A-Za-z\s\\{}])"
_MACRO_DEF = re.compile(
    r"\\(?:re|provide)?newcommand\*?\s*\{?\\" + _NAME + r"\}?\s*(?:\[(\d)\])?\s*\{"
    r"|\\def\s*\\" + _NAME + r"\s*((?:#\d)*)\s*\{"
    r"|\\providecommand\*?\s*\{?\\" + _NAME + r"\}?\s*(?:\[(\d)\])?\s*\{"
    r"|\\DeclareMathOperator\*?\s*\{?\\" + _NAME + r"\}?\s*\{")


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
    return dict(_read_macros(document))


@functools.lru_cache(maxsize=4)
def _read_macros(document: str) -> dict[str, tuple[int, str]]:
    macros: dict[str, tuple[int, str]] = {}
    found = re.search(r"\\begin\s*\{\s*document\s*\}", document)
    begin = found.start() if found else None
    body_defined: set[str] = set()
    for m in _MACRO_DEF.finditer(document):
        try:
            body, _ = _group(document, m.end() - 1)
        except ValueError:
            continue
        if m.group(1):
            name, entry = m.group(1), (int(m.group(2) or 0), body)
        elif m.group(3):
            name, entry = m.group(3), (len(m.group(4) or "") // 2, body)
        elif m.group(5):
            name, entry = m.group(5), (int(m.group(6) or 0), body)
        else:                              # \DeclareMathOperator{\Tr}{Tr}: an upright name
            name, entry = m.group(7), (0, "\\operatorname{" + body + "}")
        if m.group(5) and name in macros:
            continue                         # \\providecommand leaves an existing macro alone
        in_body = begin is not None and m.start() > begin
        if name in macros and macros[name] != entry and (in_body or name in body_defined):
            # redefined in the body: which meaning a display has depends on where it
            # sits, so the macro is left unexpanded and quotes using it are refused
            entry = (entry[0], "\\MACROREDEFINED")
        if in_body:
            body_defined.add(name)
        macros[name] = entry                 # in the preamble the last definition holds
    return macros


def expand_macros(text: str, macros: dict[str, tuple[int, str]], depth: int = 0) -> str:
    if not macros or depth > 8:
        return text
    out, i, changed = [], 0, False
    while i < len(text):
        m = re.match(r"\\" + _NAME, text[i:])
        if m and m.group(1) in macros:
            nargs, body = macros[m.group(1)]
            j = i + m.end()
            for k in range(1, nargs + 1):
                arg, j = _argument(text, j)
                body = body.replace(f"#{k}", arg)
            out.append(body)
            if re.search(r"\\[A-Za-z]+$", body) and re.match(r"[A-Za-z]", text[j:j + 1]):
                out.append(" ")          # \\<T: the body's \\langle must not run into T
            i, changed = j, True
        else:
            out.append(text[i])
            i += 1
    result = "".join(out)
    return expand_macros(result, macros, depth + 1) if changed else result


_SUB_SIGNS = {"+": "p", "-": "m", "±": "PM", "∓": "MP", "<": "lt", ">": "gt"}   # G_> is G_gt


# after a bare function's argument: more of the argument follows (\\ln x y), so it is refused
_ARGUMENT_GOES_ON = re.compile(
    r"\s*(?:\\(?!right|,|;|!|quad|qquad|cdot|times|pm|mp|label|nonumber|\\)[A-Za-z]|[A-Za-z0-9({^/])")


def _flatten(text: str) -> str:
    r"""Subscript/label text -> identifier characters: e_{n,+} -> e_np,
    f_{\pm} -> f_PM (a branch marker, see fidelity._pick_branch)."""
    text = re.sub(r"[\s{},()]", "", text)
    text = text.replace("/", "_").replace("|", "_")          # A_{L/R} -> A_L_R, never a division
    # a prime inside the label belongs to it: r_{l'l} -> r_l_primel, not r_l_prime times l
    text = re.sub(r"'+", lambda m: f"_{'p' * (len(m.group(0)) - 1)}prime", text)
    return "".join(_SUB_SIGNS.get(ch, ch) for ch in text)


_SUM_GROUP = r"\{(?:[^{}]|\{[^{}]*\})*\}"
_SUM_RELATIONS = frozenset(("approx", "simeq", "equiv", "le", "ge", "leq", "geq", "neq", "ne", "sim", "quad",
                            "qquad", "to", "rightarrow", "longrightarrow", "propto", "label", "nonumber", "notag"))
_OPEN_COMMANDS = frozenset(("{", "langle", "lbrace", "lbrack"))
_CLOSE_COMMANDS = frozenset(("}", "rangle", "rbrace", "rbrack"))


def _sum_limits(text: str, i: int) -> tuple[str, str | None, str | None, int] | None:
    """(index, lower, upper, end) of '\\sum_{n=a}^{b}' or '\\sum_n' starting at text[i];
    None when the sum is over anything but one letter (\\sum_{n,m}, \\sum_{k \\in S})."""
    m = re.match(r"\s*(?:\\limits\s*)?_\s*(" + _SUM_GROUP + r"|[A-Za-z])", text[i:])
    if m is None:
        return None
    sub = m.group(1)[1:-1] if m.group(1).startswith("{") else m.group(1)
    spec = re.fullmatch(r"\s*([A-Za-z]|\\[A-Za-z]+)\s*(?:=\s*(\S.*?))?\s*", sub, re.S)
    if spec is None or (spec.group(1).startswith("\\") and spec.group(1)[1:] not in _GREEK):
        return None
    j = i + m.end()
    sup = re.match(r"\s*\^\s*(" + _SUM_GROUP + r"|\\[A-Za-z]+|[A-Za-z0-9])", text[j:])
    upper = None
    if sup:
        upper = sup.group(1)[1:-1] if sup.group(1).startswith("{") else sup.group(1)
        j += sup.end()
    return spec.group(1), spec.group(2), upper, j


def _summand_end(text: str, j: int) -> int:
    """End of the summand starting at text[j]: TeX's sum acts on the product that
    follows it, up to a + or - (or a relation, a comma, a row end) outside brackets."""
    depth, k, started = 0, j, False
    while k < len(text):
        c = text[k]
        if c == "\\":
            cmd = re.match(r"\\([A-Za-z]+|.)", text[k:], re.S)
            name = cmd.group(1) if cmd else ""
            if depth == 0 and (name in _SUM_RELATIONS or name == "\\"):
                break
            if name in _OPEN_COMMANDS:
                depth += 1
            elif name in _CLOSE_COMMANDS:
                if depth == 0:
                    break
                depth -= 1
            k += cmd.end() if cmd else 1
            started = True
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            if depth == 0:
                break
            depth -= 1
        elif depth == 0 and (c in "=&,;" or (c in "+-" and started)):
            break
        if not c.isspace():
            started = True
        k += 1
    return k


def _strip_trailing_space(out: list[str]) -> None:
    while out and out[-1].endswith(" "):
        out[-1] = out[-1].rstrip()
        if not out[-1]:
            out.pop()


def _script_argument(text: str, i: int) -> tuple[str, int]:
    """A sub- or superscript: one character, a group, or a word command with its
    group (r_\\mathrm{H}, \\Psi_\\text{GL}: TeX gives the script \\mathrm{H} whole)."""
    arg, j = _argument(text, i)
    if arg[1:] in _WRAPPERS:
        inner, j = _argument(text, j)
        arg = arg + "{" + inner + "}"
    return arg, j


def _one_group(arg: str) -> str | None:
    """The content of a superscript that is one bracket group, (2) or
    \\left(2\\right); None for anything else, (a)/(b) included."""
    m = re.fullmatch(r"\s*(\\left\s*)?\((.*?)(\\right\s*)?\)\s*", arg, re.S)
    if m is None or bool(m.group(1)) != bool(m.group(3)):
        return None
    depth = 0
    for ch in m.group(2):
        depth += ch == "("
        depth -= ch == ")"
        if depth < 0:
            return None
    return m.group(2) if depth == 0 else None


def _ends_in_name(out: list[str]) -> bool:
    """Whether the text so far ends in a name a subscript can attach to
    (x, \\Gamma, \\dot{x}, x', x^{a}), and not in a bracket or an operator."""
    return bool(re.search(r"[A-Za-z0-9_']$", "".join(out)))


def _new_factor_follows(text: str, i: int) -> bool:
    """A letter right after a finished name starts a new factor: x_{d}f, G^{R}G, \\hat{p}x."""
    return bool(re.match(r"[A-Za-z]", text[i:i + 1]))


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
            limits = _sum_limits(text, i) if name == "sum" and not sum_pm else None
            if sum_pm:
                out.append(" sum_pm ")
                i += sum_pm.end()
            elif limits is not None:
                # \sum_{n=a}^{b} X: the summand runs to the next + or - outside brackets
                index, lower, upper, j = limits
                end = _summand_end(text, j)
                if end == j:
                    out.append("\\sum")
                    continue
                name_of = _convert(index).strip()
                lo = f"({_convert(lower)})" if lower is not None else f"sumlo_{name_of}"
                hi = f"({_convert(upper)})" if upper is not None else f"sumhi_{name_of}"
                out.append(f" Sum((({_convert(text[j:end])})), ({name_of}, {lo}, {hi})) ")
                i = end
            elif name in ("frac", "dfrac", "tfrac"):
                num, i = _argument(text, i)
                den, i = _argument(text, i)
                if _VARIATION.match(num) and _VARIATION.match(den):
                    out.append("\\delta")           # both readers would cancel the deltas: unread
                    continue
                top, bottom = _DIFF_NUM.match(num), _DIFF_DEN.match(den)
                variable = _flatten(_convert(bottom.group(1))).strip() if bottom else ""
                operator = _DIFF_OPERATOR.match(num)
                if operator and _DIFFERENTIAL.match(den):
                    # \frac{\partial}{\partial y}\left( X \right): the operator acts on the next
                    # group. Before anything else (\frac{d}{dx} x^2) it is refused, never d/(d x)
                    group = _bracket_group(text, i) if bottom and \
                        (operator.group(1) or "1") == (bottom.group(2) or "1") else None
                    operand = None
                    if group is not None:
                        inner, i = group
                        operand = _convert(inner)
                    if operand is not None and \
                            re.search(rf"(?<![A-Za-z0-9_]){re.escape(variable)}(?![A-Za-z0-9_])", operand):
                        out.append(f" Diff(({operand}), {variable}, {operator.group(1) or 1}) ")
                    else:
                        out.append("\\partial")
                    continue
                operand = _convert(top.group(2)) if top else ""
                if top and bottom and (top.group(1) or "1") == (bottom.group(2) or "1") \
                        and not re.match(r"[_^]", top.group(2)) \
                        and re.search(rf"(?<![A-Za-z0-9_]){re.escape(variable)}(?![A-Za-z0-9_])", operand):
                    # \frac{\partial X}{\partial y}: a derivative of X in y, read only when X
                    # shows y; dE/dk with a bare E would be the derivative of a constant
                    out.append(f" Diff(({operand}), {variable}, {top.group(1) or 1}) ")
                elif top and bottom:
                    out.append("\\partial")             # a derivative the reader cannot place
                else:
                    out.append(f"(({_convert(num)})/({_convert(den)}))")
            elif name in _BARE_FUNCTIONS and not re.match(r"\s*(?:\(|\\left\s*[(\[]|\\big[lr]?\s*\(|\[)", text[i:]):
                # \ln x, \coth\frac{\beta\omega}{2}, \sin^2\theta: the argument is the next factor;
                # \cos\omega t (cos(w) t or cos(w t)?) is refused
                power = re.match(r"\s*\^\s*(\{[^{}]*\}|\d)", text[i:])
                if power:
                    i += power.end()
                inverse = power and re.fullmatch(r"\{?\s*-\s*1\s*\}?", power.group(1)) and name in _INVERSES
                if power and re.match(r"\s*(?:\(|\\left\s*\()", text[i:]):
                    # \tan^{-1}(x) is arctan(x); \sin^2(x) is (sin(x))^2
                    if inverse:
                        out.append(f" {_INVERSES[name]}")
                        continue
                    group = _bracket_group(text, i)
                    if group is None:
                        out.append("\\" + name)
                        continue
                    inner, i = group
                    out.append(f"( {_ALIASES.get(name, name)}({_convert(inner)}))^({_convert(power.group(1).strip('{}'))})")
                    continue
                bars = re.match(r"\s*\|([^|]+)\|", text[i:])
                if bars and not power and not _ARGUMENT_GOES_ON.match(text[i + bars.end():]):
                    out.append(f" {_ALIASES.get(name, name)}(Abs({_convert(bars.group(1))}))")   # \\ln|x|
                    i += bars.end()
                    continue
                arg, i = _argument(text, i)
                if arg.startswith("\\frac") or arg.startswith("\\tfrac") or arg.startswith("\\dfrac"):
                    first, i = _argument(text, i)
                    second, i = _argument(text, i)
                    arg = f"\\frac{{{first}}}{{{second}}}"
                sub = re.match(r"\s*_\s*(\{[^{}]*\}|\\?[A-Za-z0-9])", text[i:])
                if sub:
                    arg += "_" + sub.group(1)
                    i += sub.end()
                if _ARGUMENT_GOES_ON.match(text[i:]):
                    out.append("\\" + name)            # the argument does not end here: refuse
                else:
                    exponent = power.group(1).strip("{}") if power else None
                    if inverse:                    # \tan^{-1} x is arctan x, not 1/tan x
                        out.append(f" {_INVERSES[name]}({_convert(arg)})")
                    else:
                        call = f" {_ALIASES.get(name, name)}({_convert(arg)})"
                        out.append(f"({call})^({_convert(exponent)})" if exponent else call)
            elif name in _ACCENTS:
                arg, i = _argument(text, i)
                inner = _convert(arg).strip()
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", inner):
                    out.append(f" {inner}__{_ACCENTS[name]}")
                    if _new_factor_follows(text, i):
                        out.append(" ")            # \mathcal{C}e is C__cal times e
                else:
                    out.append("\\" + name)       # an accent on an expression: unread
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
            elif name in _DROP or name in (",", ";", "!", ":", ">", " ", "\\"):   # \\> is a medium space
                out.append(" ")
            elif name == "lambda":                # a Python keyword: SymPy's own spelling
                out.append(" lamda " if not text[i:i + 1] == "_" else " lamda")
            elif name in ("Delta", "delta") and _INCREMENT.match(text, i):
                out.append("\\" + name)          # an increment or a product: unread
            elif name in _GREEK:
                # always a space before (\Gamma_L\Gamma_R is two names, not one);
                # none after when a subscript follows (\Gamma_L stays one name)
                out.append(f" {name} " if not text[i:i + 1] == "_" else f" {name}")
            elif name in _ALIASES:
                out.append(f" {_ALIASES[name]} " if _ALIASES[name].isalpha() else _ALIASES[name])
            elif name in ("{", "}"):
                out.append(name)
            else:
                out.append("\\" + name)          # unsupported: the parser will refuse it
        elif c == "_":
            arg, i = _script_argument(text, i + 1)
            _strip_trailing_space(out)
            if not _ends_in_name(out):
                # (a+b)_{x}, R^\alpha\,_{\beta}: a subscript on no name is unread,
                # never a stray symbol '_x'
                out.append("\\_")
            out.append("_" + _flatten(_convert(arg)))
            if _new_factor_follows(text, i):
                out.append(" ")                # x_{d}f is x_d times f, not one name
        elif c == "^":
            arg, i = _script_argument(text, i + 1)
            label = _one_group(arg)
            # G^r, G^{<}, c^\dagger, T^{nm}: letters (and <, >, dagger, prime) are
            # labels in physics, never powers; they become part of the name
            letters = re.fullmatch(r"\s*(?:[A-Za-z<>*/|,]+|\\dagger|\\prime|\\ast)\s*", arg)
            glued = out and re.search(r"[A-Za-z0-9_)]\s*$", "".join(out))
            if re.search(r"(?<![A-Za-z0-9_])[eE]\s*$", "".join(out)):
                letters = None                        # e^{i x} is the exponential
            if letters and re.fullmatch(r"\s*[b-qs-z]\s*", arg) and re.search(
                    r"(?:(?<![A-Za-z0-9_])\d+|\))\s*$", "".join(out)) \
                    and not re.search(r"(?<![A-Za-z0-9_])\(\s*[A-Za-z_][A-Za-z0-9_]*\s*\)\s*$", "".join(out)):
                letters = None             # (-1)^n, 2^k: a power; (AB)^R, G^r stay labels
            name_before = re.search(r"(?:[A-Za-z]|\\[A-Za-z]+)\s*$", text[:text.rfind("^", 0, i)])
            if re.fullmatch(r"\s*0\s*", arg) and glued and name_before and (
                    re.match(r"\s*[(_]", text[i:]) or re.match(r"[A-Z\\]", name_before.group(0).strip())):
                label = "0"                  # G^0, f^0(e): the bare/equilibrium one, not **0
            rm = re.fullmatch(r"\s*\\(?:rm|mathrm|text)\s*\{?\s*([A-Za-z]+)\s*\}?\s*", arg)
            if rm and glued:
                label = rm.group(1)          # G^{\rm R}: a label
            if label and glued:
                _strip_trailing_space(out)
                out.append("__" + _flatten(_convert(label)))   # rho^{(0)} is a label
                if _new_factor_follows(text, i):
                    out.append(" ")            # G^{(0)}G is two names
            elif letters and glued:
                _strip_trailing_space(out)
                tag = (arg.strip().replace("\\", "").replace("<", "lt").replace(">", "gt")
                       .replace("*", "star").replace("/", "_").replace("|", "_").replace(",", ""))
                joined = "".join(out)
                # {\mathbf G}^r; not f(x)^r, where (x) is an argument
                boxed = re.search(r"(?<![A-Za-z0-9_])\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)$", joined)
                if boxed:
                    out[:] = [joined[:boxed.start()] + boxed.group(1)]
                out.append("__" + tag)
                if _new_factor_follows(text, i):
                    out.append(" ")            # \Sigma^{<}G is two names, not Sigma__ltG
            else:
                sub = re.match(r"\s*_", text[i:])
                if sub:
                    # X^{2}_{a} is X_{a}^{2} in TeX: the subscript belongs to X. After a
                    # bracket, or with D^{-1}_{ij} (an element of the inverse matrix), unread
                    script, i = _script_argument(text, i + sub.end())
                    _strip_trailing_space(out)
                    if not _ends_in_name(out) or re.match(r"\s*-", arg):
                        out.append("\\_")
                    out.append("_" + _flatten(_convert(script)))
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


_VERBATIM_GROUPS = frozenset({"mathrm", "text", "textrm", "textit", "mbox", "operatorname", "label",
                              "ref", "eqref", "begin", "end", "mathsf", "mathcal", "mathscr", "mathfrak",
                              "mathbb", "mathit", "rm", "it", "cite"})


def split_letter_runs(text: str) -> str:
    """In math mode 'px' is p times x and 'eV' is e times V: a run of Latin
    letters outside commands, \\mathrm{...}/\\text{...}, subscripts and
    letter-only superscripts (labels: G^{ra}) is split into single letters;
    an exponent such as e^{-iEt} is math and is split."""
    out, i = [], 0
    stack: list[bool] = []                 # for each open brace: is its content kept as written?
    while i < len(text):
        c = text[i]
        if c == "\\":
            m = re.match(r"\\([A-Za-z]+|.)", text[i:], re.S)
            name = m.group(1) if m else ""
            out.append(text[i:i + (m.end() if m else 1)])
            i += m.end() if m else 1
            if name in _VERBATIM_GROUPS:
                j = i
                while j < len(text) and text[j].isspace():
                    j += 1
                if j < len(text) and text[j] == "{":
                    out.append(text[i:j + 1])
                    stack.append(True)
                    i = j + 1
            continue
        if c in "_^":
            j = i + 1
            while j < len(text) and text[j].isspace():
                j += 1
            out.append(text[i:j])
            exponential = c == "^" and re.search(r"(?<![A-Za-z\\])e\s*$", text[:i])
            i = j
            if i < len(text) and text[i] == "{":
                try:
                    inner = _group(text, i)[0]
                except ValueError:
                    inner = ""
                label = c == "_" or (re.fullmatch(r"\s*[A-Za-z<>*]+\s*", inner) and not exponential)
                out.append("{")
                stack.append(bool(label))      # a subscript or G^{ra} is a label: kept as written
                i += 1
            elif i < len(text) and text[i].isalpha():
                out.append(text[i])            # x_d f: only one letter belongs to the subscript
                i += 1
            continue
        if c == "{":
            stack.append(bool(stack and stack[-1]))
            out.append(c)
            i += 1
            continue
        if c == "}":
            if stack:
                stack.pop()
            out.append(c)
            i += 1
            continue
        if c.isascii() and c.isalpha() and not (stack and stack[-1]):
            m = re.match(r"[A-Za-z]+", text[i:])
            run = m.group(0)
            out.append(" ".join(run) if len(run) > 1 else run)
            i += len(run)
            continue
        out.append(c)
        i += 1
    return "".join(out)


def latex_to_plain(text: str, macros: dict[str, tuple[int, str]] | None = None) -> str:
    """Convert a LaTeX math fragment; raises ValueError on unbalanced braces."""
    text = re.sub(r"\\label\{[^}]*\}", "", text)
    text = expand_macros(text, macros or {})
    text = re.sub(r"\{\s*\\(cal|bf|rm|it|sf|bm)\s+([^{}]*)\}",
                  lambda m: "\\" + {"cal": "mathcal", "bf": "mathbf", "rm": "mathrm", "it": "mathit",
                                    "sf": "mathsf", "bm": "mathbf"}[m.group(1)] + "{" + m.group(2).strip() + "}", text)
    # \mathcal{R}e, \mathcal{I}m: a calligraphic Re / Im, never R times e; unread
    text = re.sub(r"\\mathcal\s*\{\s*(?:R\s*\}\s*e|I\s*\}\s*m)(?![A-Za-z])", r"\\calReIm ", text)
    text = split_letter_runs(text)
    # a capital E or I written in LaTeX is a quantity (an energy, a current),
    # never Euler's number or the imaginary unit, which are written e and i
    # (as a whole script, f_I and G^E become f_{Isym} and G^{Esym}, never f_I times sym)
    text = re.sub(r"([_^]\s*)?(?<![\\A-Za-z])([EI])(?![A-Za-z])",
                  lambda m: f"{m.group(1)}{{{m.group(2)}sym}}" if m.group(1) else f"{m.group(2)}sym", text)
    text = rewrite_over(normalize_exponential(text))
    # Re / Im of the next factor: \mathrm{Im}\,\psi(z) -> im_of psi(z)
    text = re.sub(r"\{?\s*\\(?:mathrm|operatorname|rm)\s*\{?\s*(Re|Im)\s*\}?\s*\}?|\\(Re|Im)(?![A-Za-z])",
                  lambda m: f" {(m.group(1) or m.group(2)).lower()}_{{of}} ", text)
    text = re.sub(r"\\(?:left|right|big|Big|bigg|Bigg)[lr]?\s*\|", "|", text)
    text = re.sub(r"\\[lr]vert\b|\\vert\b", "|", text)
    plain = _absolute_values(_convert(text))
    # e^{-x}, e^{i w t} are exponentials; e^2 (as in e^2/h) is the charge squared
    plain = re.sub(r"(?<![A-Za-z0-9_])e\^\((?!\s*\d+\s*\))", "E^(", plain)
    # primes are part of the name: t' -> t_prime, \omega'' -> omega_pprime; a letter
    # after the primes starts a new factor (x'y is x_prime times y)
    plain = re.sub(r"([A-Za-z0-9_])\s*('+)(?=([A-Za-z]?))",
                   lambda m: f"{m.group(1)}_{'p' * (len(m.group(2)) - 1)}prime" + (" " if m.group(3) else ""),
                   plain)
    return re.sub(r"_\s+", "_", plain)


def _absolute_values(plain: str) -> str:
    """|X| -> Abs(X), innermost first. An odd or nested use of '|' is left
    alone and the parser then refuses the quote."""
    for _ in range(8):
        # e|V| is e times |V|: a name right before the bar must not absorb Abs
        new = re.sub(r"(?<=[A-Za-z0-9_])\|([^|]+)\||\|([^|]+)\|",
                     lambda m: f" Abs({m.group(1)})" if m.group(1) is not None else f"Abs({m.group(2)})",
                     plain, count=1)
        if new == plain:
            break
        plain = new
    return plain


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


@functools.lru_cache(maxsize=4)
def _squash_with_map(text: str) -> tuple[str, tuple[int, ...]]:
    """layout_free text and, for each kept character, its raw offset.
    Cached: every quote of every card is located in the same paper."""
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
    return "".join(out), tuple(where)


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


_INTEGRAL_HEAD = re.compile(r"^\s*\\int(?:\\limits|\\nolimits)?\s*")
_VARIABLE = r"(\\[A-Za-z]+|[A-Za-z])((?:\s*')+|\s*_\s*\{?\s*[A-Za-z0-9]+\s*\}?)?"
_MEASURE_FIRST = re.compile(r"^(?:\\[,;!]\s*)*d\s*" + _VARIABLE + r"\s*(?:\\[,;!]\s*)*")
_MEASURE_LAST = re.compile(r"(?:\\[,;!]\s*)*(?<![A-Za-z0-9_\\])d\s*" + _VARIABLE + r"\s*$")


def _top_level_sum(body: str) -> bool:
    """A + or - outside brackets, after the first character."""
    depth = 0
    for k, ch in enumerate(body):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch in "+-" and depth == 0 and body[:k].strip():
            return True
    return False


def split_integral(text: str) -> dict[str, str] | None:
    """'\\int_a^b dx f' or '\\int_a^b f dx' -> {lower, upper, variable, body}
    as LaTeX pieces; None for anything else (no limits, two integrals, a
    measure that cannot be found)."""
    m = _INTEGRAL_HEAD.match(text)
    if not m:
        return None
    i, limits = m.end(), {}
    try:
        for _ in range(2):
            while i < len(text) and text[i].isspace():
                i += 1
            if i < len(text) and text[i] in "_^" and text[i] not in limits:
                key = text[i]
                arg, i = _argument(text, i + 1)
                limits[key] = arg
    except ValueError:
        return None
    if set(limits) != {"_", "^"} or not all(v.strip() for v in limits.values()):
        return None
    rest = text[i:].strip()
    first = _MEASURE_FIRST.match(rest)
    last = _MEASURE_LAST.search(rest)
    if first and rest[first.end():].strip():
        var, body = first.group(1) + (first.group(2) or ""), rest[first.end():]
    elif last and rest[:last.start()].strip():
        var, body = last.group(1) + (last.group(2) or ""), rest[:last.start()]
    else:
        return None
    if "\\int" in body:
        return None
    if first and _top_level_sum(body):
        return None                       # \int dx f + g: where does the integrand end?
    return {"lower": limits["_"].strip(), "upper": limits["^"].strip(),
            "variable": " ".join(var.split()), "body": body.strip()}
