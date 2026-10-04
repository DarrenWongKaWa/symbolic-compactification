"""Transcription check: does a step card say what the source says?

Benchmark v1 showed that the checker's verdicts were right for every card,
and that the remaining errors were in the cards: a dropped term, an extra
factor, a derivative of the wrong object, an example copied instead of the
claim. This module checks the card against the source text mechanically.

A card may carry

    source_document: sheet.md          # the text the step comes from
    notation:                          # paper token -> card syntax
      f_+: fp
      e_nm: (e_n - e_m)
      iG: I*G
    source:                            # card field -> verbatim quote
      claim: "[rho0_n - rho0_m + r_+ + r_-]/(w + e_nm + 2iG)"
      define:rp(): "iG (f_+(e_n) - f_+(e_m + w))/(w + e_nm)"
      integrand: {quote: "2G/(w_b^2 + G^2) f0(e_n + w_b)", wrap: "({})/(2*pi)"}
      define:fp(e): {quote: "1/2 pm (i/pi) psi(1/2 pm i beta (e mp iG - mu)/(2 pi))",
                     branch: "+"}

For each entry:
1. the quote must occur verbatim, up to whitespace, in ``source_document``;
2. the quote is translated by a fixed set of rules: the chosen ``branch`` of
   ``pm``/``mp``, Unicode, ``^``, brackets, implicit multiplication, a
   standalone ``i``, and the card's ``notation`` (whole tokens only, applied
   once). ``wrap`` adds a visible outer template such as a ``1/(2 pi)``
   measure that the quote leaves out;
3. the translation must equal the card field *identically*, i.e. for all
   symbol values and every declared function (nF and nB are treated as
   arbitrary functions here).

The only agent-authored bridge is the notation table, which is short and
reused across steps. The structure of the claim comes from the source.
"""
from __future__ import annotations

import functools
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from ..models import AdapterError
from ..parser import _ALLOWED_FUNCTIONS
from .calculus import CalculusSpace, compare
from .latex import ROW, latex_to_plain, layout_free, layout_rows, locate_quote, looks_like_latex, read_macros

MATCH, MISMATCH, UNCHECKED, NOT_IN_DOCUMENT, ABSENT = (
    "MATCH", "MISMATCH", "UNCHECKED", "NOT_IN_DOCUMENT", "ABSENT")

_UNICODE = {
    "−": "-", "–": "-", "·": "*", "×": "*", "⋅": "*", "²": "^2", "³": "^3",
    "ψ": "psi", "β": "beta", "Γ": "Gamma", "π": "pi", "ω": "omega",
    "ε": "epsilon", "μ": "mu", "ρ": "rho", "∂": "partial",
}
_TOKEN = re.compile(r"\s*(?:(\d+(?:\.\d+)?)|([A-Za-z_][A-Za-z0-9_]*)|(\*\*|.))")
_LEADING_NUMBER = re.compile(r"(?<![A-Za-z0-9_.])(\d+(?:\.\d+)?)(?=[A-Za-z_(])")
_EXPRESSION_FIELDS = ("lhs", "rhs", "claim", "expr", "integrand", "function",
                      "approximant", "summand", "lower_limit", "upper_limit")


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _notation_pattern(notation: dict[str, str]):
    if not notation:
        return None
    parts = []
    for key in sorted(notation, key=len, reverse=True):
        left = r"(?<![A-Za-z0-9_])" if re.match(r"[A-Za-z0-9_]", key) else ""
        right = r"(?![A-Za-z0-9_])" if re.search(r"[A-Za-z0-9_]$", key) else ""
        parts.append(left + re.escape(key) + right)
    return re.compile("|".join(parts))


def _ascii(text: str) -> str:
    for u, a in _UNICODE.items():
        text = text.replace(u, a)
    return text


_ALWAYS_MULTIPLY = frozenset({"I", "pi", "E"})


def translate(text: str, notation: dict[str, str], callables: Iterable[str],
              keep_i: bool = False, names: Iterable[str] = (),
              multiply: Iterable[str] | None = None) -> str:
    """Source text -> explicit card syntax. Raises AdapterError if a
    character is outside the supported grammar.

    ``names`` are the declared symbols: a token ``i<name>`` that is not
    itself declared, such as ``iG``, is read as ``I*<name>``.
    """
    text = " ".join(_ascii(text).split())
    notation = {" ".join(_ascii(k).split()): v for k, v in notation.items()}
    known = set(names) | {"pi"}
    text = _LEADING_NUMBER.sub(r"\1 ", text)
    pattern = _notation_pattern(notation)
    if pattern is not None:
        text = pattern.sub(lambda m: f" ({notation[m.group(0)]}) "
                           if not re.fullmatch(r"[A-Za-z_]\w*", notation[m.group(0)])
                           else f" {notation[m.group(0)]} ", text)
    if re.search(r"/\s*(?:\d+(?:\.\d+)?|[A-Za-z_][A-Za-z0-9_]*)\s+(?=[A-Za-z_])|/\s*\d+(?:\.\d+)?(?=[A-Za-z_])",
                 text):
        # omega/2T: omega/(2T) to a physicist, (omega/2)*T to a parser
        raise AdapterError("SOURCE_SLASH_PRECEDENCE")
    calls = set(callables)
    bracketed = re.search(r"(?<![A-Za-z0-9_])([A-Za-z_][A-Za-z0-9_]*)\s*\[", text)
    if bracketed and bracketed.group(1) in calls and bracketed.group(1) not in _ALLOWED_FUNCTIONS:
        # log[...] is log(...); f[x, y] may be a divided difference
        # f[x, y] is a divided difference or a functional, not the value f(x, y)
        raise AdapterError("SOURCE_BRACKET_AFTER_FUNCTION")
    text = text.replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")")
    text = text.replace("^", "**")
    out: list[str] = []
    prev = None                       # kind of previous token: num, name, call, close, op
    pos = 0
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        num, name, op = m.groups()
        if num is not None:
            kind, tok = "num", num
        elif name is not None:
            if name == "lambda":                  # a Python keyword: SymPy's own spelling
                name = "lamda"
            if name == "i" and not keep_i:
                name = "I"
            elif (not keep_i and name.startswith("i") and name not in known
                  and name not in calls and name[1:] in known):
                name = f"(I*{name[1:]})"
            kind, tok = ("call" if name in calls else "name"), name
        else:
            if op.isspace():
                continue
            if op not in "+-*/(),**" and op != "**":
                raise AdapterError(f"SOURCE_CHARACTER_UNSUPPORTED:{op}")
            kind, tok = ("open" if op == "(" else "close" if op == ")" else "op"), op
        if prev == "name" and kind == "open" and multiply is not None \
                and out[-1] not in _ALWAYS_MULTIPLY and not out[-1].startswith("(I*") \
                and out[-1] not in multiply:
            # beta(x) is a product, G(x) a function value: the source cannot tell
            raise AdapterError(f"SOURCE_APPLICATION_AMBIGUOUS:{out[-1]}")
        if prev == "name" and kind == "open" and multiply and out[-1] in multiply \
                and _top_level_comma(text, pos):
            # G(t, t') cannot be a product: this reading of G is impossible
            raise AdapterError(f"SOURCE_PRODUCT_WITH_COMMA:{out[-1]}")
        if prev in ("num", "name", "close") and kind in ("num", "name", "call", "open"):
            out.append("*")
        elif prev == "call" and kind != "open":
            raise AdapterError(f"SOURCE_FUNCTION_WITHOUT_ARGUMENTS:{out[-1]}")
        out.append(tok)
        prev = kind
    return "".join(out)


def _top_level_comma(text: str, pos: int) -> bool:
    """Whether the bracket group opened just before ``pos`` holds a comma."""
    depth = 1
    for ch in text[pos:]:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return False
        elif ch == "," and depth == 1:
            return True
    return False


_BRANCH = {"+": {"pm": "+", "mp": "-", "±": "+", "∓": "-", "PM": "p", "MP": "m"},
           "-": {"pm": "-", "mp": "+", "±": "-", "∓": "+", "PM": "m", "MP": "p"}}
_DEFAULT_NOTATION = {"n_F": "nF", "n_B": "nB"}
DEFAULT_FUNCTIONS = {"psi(z)": "polygamma(0, z)",
                     **{f"psi{k}(z)": f"polygamma({k}, z)" for k in range(7)}}


# A wrap may only restore an integration measure the quote leaves out;
# anything else (a sign, a factor, a shift) would change the claim.
ALLOWED_WRAPS = frozenset({"{}", "({})", "({})/(2*pi)", "({})/(2*pi)**2", "({})/(2*pi)**3"})


def _quote(entry: Any) -> tuple[str, str, str | None]:
    if isinstance(entry, dict):
        if not isinstance(entry.get("quote"), str) or not entry["quote"].strip():
            raise AdapterError("SOURCE_QUOTE_MISSING")
        branch = entry.get("branch")
        if branch is not None and str(branch) not in _BRANCH:
            raise AdapterError("SOURCE_BRANCH_MUST_BE_PLUS_OR_MINUS")
        wrap = " ".join(str(entry.get("wrap", "{}")).split()).replace(" ", "")
        if wrap not in ALLOWED_WRAPS:
            raise AdapterError("SOURCE_WRAP_NOT_ALLOWED")
        return str(entry["quote"]), wrap, None if branch is None else str(branch)
    if not isinstance(entry, str) or not entry.strip():
        raise AdapterError("SOURCE_QUOTE_MISSING")
    return entry, "{}", None


def _term_end(text: str, i: int) -> int:
    """End of the factor starting at text[i]: a name with its call
    parentheses, or one bracketed group."""
    while i < len(text) and text[i] == " ":
        i += 1
    j = i
    while j < len(text) and (text[j].isalnum() or text[j] in "_"):
        j += 1
    name_end = j
    while j < len(text) and text[j] == " ":
        j += 1
    if j < len(text) and text[j] in "([":
        depth = 0
        for k in range(j, len(text)):
            depth += text[k] in "(["
            depth -= text[k] in ")]"
            if depth == 0:
                return k + 1
    return name_end


def expand_sum_pm(text: str) -> str:
    """sum_pm X -> ((X at +) + (X at -)), X being the next factor."""
    pattern = re.compile(r"(?<![A-Za-z0-9_])sum_pm")
    for _ in range(16):
        m = pattern.search(text)
        if not m:
            return text
        end = _term_end(text, m.end())
        term = text[m.end():end]
        if not term.strip() or not term.rstrip().endswith((")", "]")):
            raise AdapterError("SUM_PM_REQUIRES_GROUP")     # sum_pm A + B is ambiguous
        text = (text[:m.start()] + f"(({_pick_branch(term, '+')}) + ({_pick_branch(term, '-')}))"
                + text[end:])
    return text


def expand_re_im(text: str) -> str:
    """re_of X / im_of X -> re(X) / im(X), X being the next factor."""
    pattern = re.compile(r"(?<![A-Za-z0-9_])(re|im)_of")
    for _ in range(16):
        m = pattern.search(text)
        if not m:
            return text
        end = _term_end(text, m.end())
        term = text[m.end():end]
        if not term.strip():
            raise AdapterError("RE_IM_WITHOUT_ARGUMENT")
        text = text[:m.start()] + f"{m.group(1)}({term})" + text[end:]
    return text


def _pick_branch(text: str, branch: str | None) -> str:
    """Resolve pm/mp, ±/∓ and subscript markers (_pm, _PM, ...) to one sign.
    In a subscript the sign becomes a letter: z0_pm -> z0_p or z0_m."""
    if branch is None:
        return text
    signs = _BRANCH[branch]
    letter = {"+": "p", "-": "m"}
    text = re.sub(r"(?<=_)(\w*?)(PM|MP)", lambda m: m.group(1) + signs[m.group(2)], text)
    text = re.sub(r"(?<=[A-Za-z0-9]_)pm(?![A-Za-z0-9])",      # _mp may be two labels m, p
                  lambda m: letter[signs["pm"]], text)
    # z_± is a subscript sign; in k_0∓k the sign after the subscript 0 is an operator
    text = re.sub(r"(?<=_)[±∓]", lambda m: signs[m.group(0)].replace("+", "p").replace("-", "m"), text)
    return re.sub(r"(?<![A-Za-z0-9_])(pm|mp)(?![A-Za-z0-9_])|[±∓]",
                  lambda m: f" {signs[m.group(0)]} ", text)


def with_default_functions(definitions: dict[str, str], texts: Iterable[str],
                           declared: Iterable[str] = ()) -> dict[str, str]:
    """Add psi(z), psi0(z)..psi6(z) = polygamma when a text uses them and
    the card does not define or declare that name itself."""
    have = {k.split("(")[0].strip() for k in definitions} | set(declared)
    blob = " ".join(texts)
    extra = {k: v for k, v in DEFAULT_FUNCTIONS.items()
             if k.split("(")[0] not in have and re.search(rf"\b{k.split('(')[0]}\s*\(", blob)}
    return {**definitions, **extra}


@dataclass
class SourceContext:
    document: str | None            # whitespace-squashed text, for the verbatim test
    raw: str | None
    macros: dict
    latex: bool
    notation: dict[str, str]
    callables: set[str]
    names: set[str]
    keep_i: bool
    error: str | None = None
    multiply: frozenset = frozenset()


def _symbol_names(symbols: Any) -> set[str]:
    return {(s if isinstance(s, str) else str(s.get("name"))) for s in symbols or []}


def source_context(card: dict, base_dir: Path | None, *, symbols: Any,
                   functions: Iterable[str], definitions: dict) -> SourceContext:
    raw = None
    error = None
    if card.get("source_document"):
        path = Path(str(card["source_document"]))
        if not path.is_absolute() and base_dir is not None:
            path = base_dir / path
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            error = "SOURCE_DOCUMENT_UNREADABLE"
        latex = path.suffix == ".tex" or str(card.get("source_format", "")) == "latex"
    else:
        latex = str(card.get("source_format", "")) == "latex"
    source_defs = [str(k).split(":", 1)[1] for k in (card.get("source") or {})
                   if str(k).startswith("define:")]
    def_names = {k.split("(")[0].strip() for k in [*definitions, *source_defs, *DEFAULT_FUNCTIONS]}
    params = {p.strip() for k in [*definitions, *source_defs] if "(" in k
              for p in k.split("(", 1)[1].rstrip(")").split(",") if p.strip()}
    funcs = [*functions, "nF", "nB"]
    callables = {*_ALLOWED_FUNCTIONS, *funcs, *def_names, "Diff", "Sum",
                 *(f"{p}_{f}" for f in [*funcs, *def_names] for p in ("DD", "D"))}
    names = _symbol_names(symbols) | params
    return SourceContext(
        document=None if raw is None else layout_free(raw), raw=raw,
        macros=read_macros(raw) if (raw and latex) else {},
        latex=latex,
        notation={**_DEFAULT_NOTATION,
                  **{str(k): str(v) for k, v in (card.get("notation") or {}).items()}},
        callables=callables, names=names, keep_i="i" in _symbol_names(symbols), error=error,
        multiply=frozenset(str(m) for m in (card.get("multiply") or [])))


_BRACKETS = "()[]{}"


def erratum_of(entry: Any) -> str | None:
    """A declared correction of a printed formula. It may only add, remove or
    move bracket characters; anything else is refused."""
    if not isinstance(entry, dict) or entry.get("erratum") in (None, ""):
        return None
    fixed, quote = str(entry["erratum"]), str(entry.get("quote", ""))
    strip = lambda t: "".join(ch for ch in t if not ch.isspace() and ch not in _BRACKETS)
    if strip(fixed) != strip(quote):
        raise AdapterError("ERRATUM_MAY_ONLY_CHANGE_BRACKETS")
    return fixed


def _balanced(text: str) -> bool:
    depth = 0
    for ch in text:
        depth += ch == "("
        depth -= ch == ")"
        if depth < 0:
            return False
    return depth == 0


def quote_expression(entry: Any, ctx: SourceContext) -> tuple[str, str]:
    """(verbatim quote, card-syntax expression). Raises AdapterError or
    ValueError when the quote is outside the supported grammar, and, for a
    LaTeX quote, when SymPy's own LaTeX reader reads it differently."""
    return _quote_expression(entry, ctx)[:2]


def expand_macros_safe(text: str, macros: dict) -> str:
    from .latex import expand_macros
    try:
        return expand_macros(text, macros or {})
    except (ValueError, RecursionError):
        return text


_DIGIT_SUPERSCRIPT = re.compile(r"(\\?[A-Za-z]+)\s*\^\s*\{\s*(\d{2,})\s*\}")


@functools.lru_cache(maxsize=8)
def _index_pair_bases(raw: str) -> frozenset:
    """Names the document writes with two or more different two-digit
    superscripts (L^{11}, L^{12}, L^{22}): those superscripts are index pairs."""
    seen: dict[str, set[str]] = {}
    for m in _DIGIT_SUPERSCRIPT.finditer(raw):
        if len(m.group(2)) == 2:                 # an index pair has two digits; x^{100000} is a power
            seen.setdefault(m.group(1), set()).add(m.group(2))
    return frozenset(base for base, digits in seen.items() if len(digits) >= 2)


_SUM_INDEX_TEX = re.compile(r"\\sum\s*(?:\\limits\s*)?_\s*\{?\s*([A-Za-z]|\\[A-Za-z]+)\s*[=}]?")


def _sum_index_superscript(text: str) -> None:
    """Inside a sum over n, x^n is a power but Omega^n_{ab} a band label; both
    readers share one reading, so the quote is refused instead."""
    for m in _SUM_INDEX_TEX.finditer(text):
        index = re.escape(m.group(1))
        if re.search(r"\^\s*(?:" + index + r"(?![A-Za-z])|\{\s*" + index + r"\s*\})", text[m.end():]):
            raise AdapterError(f"SUM_INDEX_AS_SUPERSCRIPT:{m.group(1)}")


def _index_or_power(text: str, raw: str | None) -> None:
    """A multi-digit superscript is an index pair, not a power, when it starts
    with 0 (T^{00}) or when the paper writes the same name with other such
    superscripts (L^{12} next to L^{11}). Both readers would read a power, so
    the quote is refused instead."""
    pairs = _index_pair_bases(raw) if raw else frozenset()
    for m in _DIGIT_SUPERSCRIPT.finditer(text):
        if m.group(2).startswith("0") or (len(m.group(2)) == 2 and m.group(1) in pairs):
            raise AdapterError(f"SUPERSCRIPT_INDEX_OR_POWER:{m.group(1)}^{{{m.group(2)}}}")


def _quote_expression(entry: Any, ctx: SourceContext) -> tuple[str, str, str | None]:
    quote, wrap, branch = _quote(entry)
    source = erratum_of(entry) or quote
    text = source
    latex = ctx.latex or looks_like_latex(text)
    if latex:
        _index_or_power(expand_macros_safe(source, ctx.macros), ctx.raw)
        _sum_index_superscript(expand_macros_safe(source, ctx.macros))
    if latex:
        text = latex_to_plain(text, ctx.macros)
    text = _pick_branch(expand_sum_pm(expand_re_im(text)), branch)
    expression = translate(text, ctx.notation, ctx.callables, ctx.keep_i, ctx.names,
                           multiply=ctx.multiply)
    if not _balanced(expression):
        raise AdapterError("SOURCE_BRACKETS_UNBALANCED")
    reading_b = _second_reader(source, text, branch, ctx) if latex else None
    return quote, wrap.replace("{}", expression), reading_b


def _pre_notation_callables(ctx: SourceContext) -> frozenset:
    """Names read as functions before the notation is applied: the callables,
    and paper tokens the notation maps to a callable (Gamma -> gamma_fn)."""
    keys = {k: str(v).strip() for k, v in ctx.notation.items() if re.fullmatch(r"[A-Za-z_]\w*", k)}
    mapped = {k for k, v in keys.items() if v in ctx.callables}
    constants = {k for k, v in keys.items() if v not in ctx.callables}   # x -> x(): a symbol before
    # 'A__r(t,t_1)' -> A_R: the paper's A__r is applied to (t, t_1) before the notation
    applied = {name for k in ctx.notation if not re.fullmatch(r"[A-Za-z_]\w*", k)
               for name in re.findall(r"([A-Za-z_]\w*)\s*\(", k)}
    return frozenset((ctx.callables - constants) | mapped | applied)


def _second_reader(source: str, plain: str, branch: str | None, ctx: SourceContext) -> str:
    """Our reading before the notation, compared with SymPy's reading of the
    same quote. Raises AdapterError (READERS_DISAGREE, SECOND_READER_FAILED)."""
    callables = _pre_notation_callables(ctx)
    return _agreement(source, plain, branch, callables, frozenset(ctx.names), ctx.multiply,
                      ctx.keep_i, tuple(sorted(ctx.macros.items())))


@functools.lru_cache(maxsize=4096)
def _agreement(source: str, plain: str, branch: str | None, callables: frozenset, names: frozenset,
               multiply: frozenset, keep_i: bool, macros: tuple) -> str:
    from . import dualread
    from .latex import expand_macros
    dualread.check_size(expand_macros(source, dict(macros)))    # before either reader computes
    pre = translate(plain, {}, callables, keep_i, names, multiply=multiply)
    builtin = set(_ALLOWED_FUNCTIONS) | {"Diff", "Sum"}
    functions = sorted(c for c in callables if c not in builtin and not c.startswith(("DD_", "D_")))
    used = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", pre))
    symbols = sorted(used - set(callables) - {"I", "pi", "E", "oo"})
    space = CalculusSpace([{"name": s, "real": False} for s in symbols] or ["unused_symbol"],
                          [f for f in functions if f in used])
    reading_a = space.parse_expanded(pre)
    return dualread.require_agreement(source, reading_a, macros=dict(macros), callables=callables,
                                      keep_i=keep_i, branch=branch)["reader_b"]


_INTEGRAL_FIELDS = ("integrand", "lower_limit", "upper_limit")


def integral_fields(entry: Any, ctx: SourceContext, variable: str | None) -> dict[str, str]:
    """A quoted '\\int_a^b dx f' -> integrand, lower, upper in card syntax.
    The integration variable, after the card's notation, must be the card's
    ``variable``."""
    from .latex import split_integral
    quote, wrap, branch = _quote(entry)
    if wrap != "{}" or branch is not None:
        raise AdapterError("INTEGRAL_QUOTE_TAKES_NO_WRAP_OR_BRANCH")
    parts = split_integral(erratum_of(entry) or quote)
    if parts is None:
        raise AdapterError("INTEGRAL_NOT_UNDERSTOOD")
    pieces = {k: quote_expression(parts[v], ctx)[1]
              for k, v in (("integrand", "body"), ("lower_limit", "lower"), ("upper_limit", "upper"))}
    var = quote_expression(parts["variable"], ctx)[1].strip("() ")
    if not variable or var != str(variable):
        raise AdapterError("INTEGRATION_VARIABLE_MISMATCH")
    return pieces


def in_document(quote: str, ctx: SourceContext, display: str | None = None) -> bool:
    """Verbatim up to whitespace and layout (&, row breaks, \\nonumber, \\label).
    With a display anchor (a \\label, or #n for the n-th display) the quote must
    sit in that display: a stale card cannot pass on text found elsewhere."""
    if ctx.document is None:
        return True
    if display and ctx.raw is not None:
        region = display_text(ctx.raw, display)
        return region is not None and _whole_occurrence(layout_free(quote), layout_rows(region),
                                                          ctx.latex)
    return _whole_occurrence(layout_free(quote), layout_rows(ctx.raw) if ctx.raw is not None
                             else ctx.document, ctx.latex)


_LEFT_OK = re.compile(
    r"(?:^|=|\\approx|\\simeq|\\equiv|,|;|:|\\[,;! ]|\\q?quad|\\left\s*\.|"
    r"\\begin\{[A-Za-z*]+\}|\\end\{[A-Za-z*]+\}|\\\[|\$\$|\$|"
    r"\\sum_\{[^{}]*\}(?:\^\{?[^{}\s]*\}?)?|\\sum_[A-Za-z]|"
    r"\bd\s*\\?[A-Za-z]+(?:_\{?\w+\}?)?(?:\s*\\[,;!])?)\s*$")
_RIGHT_OK = re.compile(
    r"^\s*(?:$|=|\\approx|\\simeq|\\equiv|,|\.|;|:|\\[,;! ]|~|\\q?quad|\\label|\\nonumber|"
    r"\\\\|\\end|\\\]|\$|\+\s*(?:\\mathcal\{O\}|O)\s*[(\[]|\\text)")


_PROSE_LEFT = re.compile(r"(?:^|\s)[A-Za-z]{2,}\s*$")


def _near(text: str, width: int = 400, end: bool = True) -> str:
    """The part of the text next to a match: its end before the match, its
    start after it. That is enough for the boundary patterns; the whole text
    is kept when that part is blank, so '^' and '$' keep their meaning."""
    part = text[-width:] if end else text[:width]
    return part if len(text) <= width or part.strip() else text


def _whole_occurrence(quote: str, region: str, latex: bool = True) -> bool:
    """The quote occurs as a whole piece: bounded by the display edge, a row
    end, a relation sign, punctuation, spacing, an integration measure or a
    sum, or '+ O(...)' -- never as a fragment such as 'a + b' inside 'a + b^2'.
    In a plain-text sheet a quote may also follow a word of prose."""
    if not quote:
        return False
    gap = r"(?:\s*" + ROW + r"\s*|\s+)"         # a space in the quote may be a row end in the display
    pattern = re.compile(gap.join(re.escape(tok) for tok in quote.split(" ")))
    for m in pattern.finditer(region):
        # only the text next to the match matters; a whole paper before it is slow to scan
        left, right = _near(region[:m.start()]), _near(region[m.end():], end=False)
        left_ok = _LEFT_OK.search(left) or left.rstrip().endswith(ROW) or (
            not latex and _PROSE_LEFT.search(left))
        right_ok = _RIGHT_OK.match(right) or right.lstrip().startswith(ROW)
        braced = re.search(r"\\(?:under|over)brace\s*\{\s*$", left) and re.match(r"\s*\}\s*[_^]", right)
        if (left_ok and right_ok) or braced:        # \underbrace{quote}_{K_1A} is a whole piece
            return True
    return False


_SECTION = re.compile(r"\\(?:section|chapter)\*?\s*[\[{]|\\appendix\b")


@functools.lru_cache(maxsize=4)
def _displays(raw: str) -> dict[str, tuple[str, int]]:
    """{'#n' and label: (display text, section number)}, the first display
    for a repeated label. Cached: every quote of every card looks here, and
    a long paper is slow to split into displays."""
    from .relations import latex_equations
    eqs = latex_equations(raw)
    starts = [m.start() for m in _SECTION.finditer(eqs[0]["document"])] if eqs else []
    index: dict[str, tuple[str, int]] = {}
    for k, eq in enumerate(eqs, start=1):
        entry = ("\\\\".join(eq["rows"]), sum(1 for s in starts if s < eq["offset"]))
        index[f"#{k}"] = entry
        if eq["label"] is not None:
            index.setdefault(eq["label"], entry)
    return index


def _display_entry(raw: str, display: str) -> tuple[str, int] | None:
    if display.startswith("#"):
        try:
            display = f"#{int(display[1:])}"
        except ValueError:
            return None
    return _displays(raw).get(display)


def display_text(raw: str, display: str) -> str | None:
    entry = _display_entry(raw, display)
    return entry[0] if entry else None


def display_section(raw: str, display: str) -> int | None:
    """The number of \\section (or \\appendix) commands before a display."""
    entry = _display_entry(raw, display)
    return entry[1] if entry else None


def fill_from_source(card: dict, base_dir: Path | None, *, symbols: Any,
                     functions: Iterable[str]) -> tuple[dict, list[str]]:
    """Fields the card leaves out are built from their quotes, so nothing
    is transcribed by hand. Returns the completed card and the filled keys."""
    source = card.get("source") or {}
    if not isinstance(source, dict):
        return card, []
    definitions = {str(k): str(v) for k, v in (card.get("define") or {}).items()}
    ctx = source_context(card, base_dir, symbols=symbols, functions=functions,
                         definitions=definitions)
    filled, card = [], dict(card)
    new_defs = dict(definitions)
    for key, entry in source.items():
        key = str(key)
        try:
            if key.startswith("define:"):
                target = key.split(":", 1)[1].strip()
                name = target.split("(")[0].strip()
                if any(k.split("(")[0].strip() == name for k in definitions):
                    continue
                new_defs[target] = quote_expression(entry, ctx)[1]
            elif key == "integral":
                if any(k in card for k in _INTEGRAL_FIELDS):
                    continue           # hand-written pieces are not checked against the quote
                card.update(integral_fields(entry, ctx, card.get("variable")))
            elif key in _EXPRESSION_FIELDS and key not in card:
                card[key] = quote_expression(entry, ctx)[1]
            else:
                continue
        except AdapterError as exc:
            card.setdefault("_source_failures", {})[key] = exc.code
            continue
        except ValueError:
            card.setdefault("_source_failures", {})[key] = "LATEX_UNBALANCED"
            continue
        filled.append(key)
    if new_defs != definitions:
        card["define"] = new_defs
    return card, filled


def check_transcription(card: dict, *, symbols: Any, functions: Iterable[str],
                        definitions: dict, positive: tuple[str, ...],
                        base_dir: Path | None, filled: Iterable[str] = ()) -> dict[str, Any]:
    source = card.get("source")
    if not source:
        return {"status": ABSENT, "fields": {}}
    if not isinstance(source, dict):
        raise AdapterError("SOURCE_MUST_BE_A_MAPPING")
    ctx = source_context(card, base_dir, symbols=symbols, functions=functions,
                         definitions=definitions)
    if ctx.error:
        return {"status": UNCHECKED, "fields": {}, "reason": ctx.error}
    filled = set(filled)
    used_defs = _used_definition_names(card, definitions)
    funcs = [*functions, "nF", "nB"]
    space = None                       # built when a hand-written field needs comparing
    fields: dict[str, dict] = {}
    for key, entry in source.items():
        key = str(key)
        if key.startswith("define:") and key.split(":", 1)[1].split("(")[0].strip() not in used_defs:
            continue                  # a shared definition this card does not use
        try:
            quote = _quote(entry)[0]
        except AdapterError as exc:
            fields[key] = {"quote": None, "status": UNCHECKED, "reason": exc.code}
            continue
        record: dict[str, Any] = {"quote": quote}
        anchor = (entry.get("display") if isinstance(entry, dict) else None) or \
            (None if key.startswith("define:") else card.get("display"))
        if not in_document(quote, ctx, anchor):
            fields[key] = {**record, "status": NOT_IN_DOCUMENT}
            continue
        if ctx.raw:
            span = None
            if anchor:
                region = display_text(ctx.raw, anchor)
                start = ctx.raw.find(region) if region else -1
                span = (start, start + len(region)) if start >= 0 else None
            where = locate_quote(ctx.raw, quote, within=span)   # the card's own display
            if where:
                record["location"] = where
        failure = (card.get("_source_failures") or {}).get(key)
        if failure:
            fields[key] = {**record, "status": UNCHECKED, "reason": failure}
            continue
        if isinstance(entry, dict) and entry.get("erratum"):
            record["erratum"] = str(entry["erratum"])
            if entry.get("note"):
                record["erratum_note"] = str(entry["note"])
        if key in filled:
            try:
                _, record["translated"], reading_b = _quote_expression(entry, ctx)
                if reading_b is not None:
                    record["reader_b"] = reading_b
            except (AdapterError, ValueError):
                pass
            fields[key] = {**record, "status": MATCH, "from_source": True}
            continue
        if key.startswith("define:"):
            name = key.split(":", 1)[1].strip().split("(")[0].strip()
            match = [k for k in definitions if k.split("(")[0].strip() == name]
            if not match:
                fields[key] = {**record, "status": UNCHECKED, "reason": "NO_SUCH_DEFINITION"}
                continue
            card_text = definitions[match[0]]
        elif key in _EXPRESSION_FIELDS and key in card:
            card_text = str(card[key])
        else:
            fields[key] = {**record, "status": UNCHECKED, "reason": "NOT_AN_EXPRESSION_FIELD"}
            continue
        try:
            _, translated, reading_b = _quote_expression(entry, ctx)
            record["translated"] = translated
            if reading_b is not None:
                record["reader_b"] = reading_b
            space = space or CalculusSpace(symbols, funcs, definitions=definitions)
            src = space.parse_expanded(translated)
            mine = space.parse_expanded(card_text)
        except AdapterError as exc:
            fields[key] = {**record, "status": UNCHECKED, "reason": f"PARSE_FAILED:{exc.code}"}
            continue
        except ValueError:
            fields[key] = {**record, "status": UNCHECKED, "reason": "LATEX_UNBALANCED"}
            continue
        try:
            result = compare(mine, src, space, positive)
        except (TypeError, ValueError, ZeroDivisionError):   # e.g. a function called with the wrong arity
            fields[key] = {**record, "status": UNCHECKED, "reason": "COMPARISON_FAILED"}
            continue
        status = {"ZERO": MATCH, "NONZERO": MISMATCH}.get(result["verdict"], UNCHECKED)
        fields[key] = {**record, "status": status,
                       **({"diagnosis": result.get("diagnosis")} if status == MISMATCH else {})}
    statuses = {f["status"] for f in fields.values()}
    for worst in (NOT_IN_DOCUMENT, MISMATCH, UNCHECKED):
        if worst in statuses:
            return {"status": worst, "fields": fields}
    return {"status": MATCH if fields else ABSENT, "fields": fields}


_SLOT = re.compile(r"([_^])(\s*)(\{(?:[^{}]|\{[^{}]*\})*\}|\\[A-Za-z]+|[A-Za-z0-9])")
_WORD = re.compile(r"\\(?:mathrm|text|textrm|textit|rm|it|operatorname|mathit|mbox)\s*(?:\{[^{}]*\}|[A-Za-z]+)")


def _index_slots(tex: str) -> list[re.Match]:
    """Sub- and superscripts of names; the exponent of a bare e is not one."""
    return [m for m in _SLOT.finditer(tex)
            if not (m.group(1) == "^" and re.search(r"(?<![A-Za-z\\])e\s*$", tex[:m.start()]))]


def rename_indices(tex: str, rename: dict) -> str:
    """The same relation with index letters renamed (b -> c turns g_{ab} into
    g_{ac}). Refused unless every occurrence of a renamed letter is an index:
    in 'x^{b} = b', 'e^{-\beta b}' or '_{\rm max}' the letter is something else."""
    if not rename:
        return tex
    if not isinstance(rename, dict):
        raise AdapterError("GIVEN_RENAME_MUST_BE_A_MAPPING")
    mapping = {str(k): str(v) for k, v in rename.items()}
    if not all(re.fullmatch(r"[A-Za-z]", k) and re.fullmatch(r"[A-Za-z0-9]", v) for k, v in mapping.items()):
        raise AdapterError("GIVEN_RENAME_MUST_MAP_A_LETTER_TO_A_LETTER_OR_DIGIT")
    slots = _index_slots(tex)
    outside, pos = [], 0
    for m in slots:
        outside.append(tex[pos:m.start()])
        pos = m.end()
    outside.append(tex[pos:])
    letters = re.compile(r"\\[A-Za-z]+|[A-Za-z]")
    rest = " ".join(outside)
    if any(t in mapping for t in letters.findall(rest)):
        raise AdapterError("GIVEN_RENAME_LETTER_NOT_ONLY_AN_INDEX")
    if any(t in mapping for m in slots for w in _WORD.findall(m.group(3))
           for t in re.findall(r"[A-Za-z]", re.sub(r"^\\[A-Za-z]+", "", w))):
        raise AdapterError("GIVEN_RENAME_LETTER_INSIDE_A_WORD")

    def swap(group: str) -> str:
        # every letter of a subscript is an index of its own (g_{ab}); commands stay
        return letters.sub(lambda t: t.group(0) if t.group(0).startswith("\\") else mapping.get(t.group(0), t.group(0)),
                           group)
    out, pos = [], 0
    for m in slots:
        out.append(tex[pos:m.start()] + m.group(1) + m.group(2) + swap(m.group(3)))
        pos = m.end()
    out.append(tex[pos:])
    return "".join(out)


def _renamed(quote: str, instance: dict, macros: dict) -> str:
    """The quote with the instance's index renames applied after the document's
    macros are expanded (\\rpq is r_{pq}: its p and q are indices too). A rename
    that cannot reach a macro, or changes nothing, is refused: the relation would
    otherwise be used unrenamed while reported as renamed."""
    if not instance:
        return quote
    text = expand_macros_safe(quote, macros)
    if any(re.search(r"\\" + re.escape(name.lstrip("\\")) + r"(?![A-Za-z])", text) for name in macros or {}):
        raise AdapterError("GIVEN_RENAME_INSIDE_AN_UNEXPANDED_MACRO")
    renamed = rename_indices(text, instance)
    if renamed == text:
        raise AdapterError("GIVEN_RENAME_CHANGED_NOTHING")
    return renamed


def given_relations(card: dict, base_dir: Path | None, *, symbols: Any, functions: Iterable[str],
                    definitions: dict) -> list[dict[str, Any]]:
    """The relations a step uses (``given:``), each a verbatim quote 'A = B' from
    the source, read by both readers. One record per relation and instance."""
    entries = card.get("given") or []
    if not isinstance(entries, list):
        raise AdapterError("GIVEN_MUST_BE_A_LIST")
    ctx = source_context(card, base_dir, symbols=symbols, functions=functions, definitions=definitions)
    step_texts = _step_display_texts(card, ctx)
    records: list[dict[str, Any]] = []
    for k, entry in enumerate(entries):
        entry = entry if isinstance(entry, dict) else {"quote": entry}
        quote = str(entry.get("quote") or "")
        anchor = entry.get("display")
        instances = entry.get("instances") or [{}]
        for instance in instances:
            record: dict[str, Any] = {"index": k, "quote": quote, "display": anchor,
                                      **({"rename": dict(instance)} if instance else {})}
            records.append(record)
            if not quote.strip() or not in_document(quote, ctx, anchor):
                record["status"] = NOT_IN_DOCUMENT
                continue
            given_text = display_text(ctx.raw, str(anchor)) if (anchor and ctx.raw is not None) else None
            if ctx.raw is not None and (given_text in step_texts if anchor else any(
                    _whole_occurrence(layout_free(quote), layout_rows(t), ctx.latex) for t in step_texts)):
                record["status"] = UNCHECKED
                record["reason"] = "GIVEN_FROM_THE_STEP_DISPLAY"  # the step would justify itself
                continue
            try:
                relation = re.sub(r"\\equiv(?![A-Za-z])|:=", "=", _renamed(quote, instance, ctx.macros))
                sides = [s for s in _top_level_split(relation, "=") if s.strip()]
                if len(sides) != 2:
                    raise AdapterError("GIVEN_NOT_ONE_RELATION")
                left = _quote_expression(sides[0].strip(), ctx)
                right = _quote_expression(sides[1].strip(), ctx)
            except AdapterError as exc:
                record.update(status=UNCHECKED, reason=exc.code)
                continue
            except ValueError:
                record.update(status=UNCHECKED, reason="LATEX_UNBALANCED")
                continue
            record.update(status=MATCH, lhs=left[1], rhs=right[1],
                          **({"reader_b": [left[2], right[2]]} if left[2] is not None else {}))
    return records


def _step_display_texts(card: dict, ctx: SourceContext) -> list[str]:
    """The text of every display that holds a side of the step: the displays the
    ledger names, and every display in which a side's quote occurs."""
    if ctx.raw is None:
        return []
    texts = []
    for key in ("lhs", "rhs"):
        entry = (card.get("source") or {}).get(key)
        if entry is None:
            continue
        quote = layout_free(_quote(entry)[0])
        anchor = entry.get("display") if isinstance(entry, dict) else None
        for name, (text, _) in _displays(ctx.raw).items():
            if (anchor and display_text(ctx.raw, str(anchor)) == text) or (
                    name.startswith("#") and _whole_occurrence(quote, layout_rows(text), ctx.latex)):
                texts.append(text)
    return texts


def _top_level_split(text: str, sep: str) -> list[str]:
    from .relations import split_top_level
    return split_top_level(text, sep)


def check_under(card: dict, base_dir: Path | None, *, symbols: Any, functions: Iterable[str],
                definitions: dict) -> str | None:
    r"""``under: '\sum_n'``: both sides carry the same outer sum or integral, and
    the quotes are what it acts on. The wrapper must open the side of the
    relation (nothing else in front of it), and each quote must be one bracket
    group or a product (in '\sum_n a_n + b' the reach of the sum is a
    convention). Returns a blocker, or None when the wrapper is as declared."""
    wrapper = str(card.get("under") or "").strip()
    if not wrapper:
        return None
    ctx = source_context(card, base_dir, symbols=symbols, functions=functions, definitions=definitions)
    for key in ("lhs", "rhs"):
        entry = (card.get("source") or {}).get(key)
        if entry is None:
            return f"UNDER_WITHOUT_QUOTE:{key}"
        quote = _quote(entry)[0]
        anchor = entry.get("display") if isinstance(entry, dict) else card.get("display")
        region = display_text(ctx.raw, str(anchor)) if (anchor and ctx.raw is not None) else ctx.raw
        if region is None or not _opens_a_side(layout_free(wrapper), layout_free(quote), layout_rows(region)):
            return f"UNDER_NOT_BEFORE_QUOTE:{key}"
        if _top_level_sum(quote):
            return f"UNDER_SCOPE_AMBIGUOUS:{key}"
    return None


_SIDE_START = re.compile(r"(?:^|=|&|\\approx|\\simeq|\\equiv|\\begin\{[A-Za-z*]+\}|\$|\\\[)\s*$")


def _opens_a_side(wrapper: str, quote: str, region: str) -> bool:
    """The wrapper followed by the quote occurs as a whole side of a relation: only
    a relation sign, a row start or the display edge before it (an integration
    measure is not enough). The source may or may not put a space between them
    (\\sum_{n=1}^{\\infty}\\frac{...})."""
    gap = r"(?:\s*" + ROW + r"\s*|\s+)"
    def tokens(text: str) -> str:
        return gap.join(re.escape(tok) for tok in text.split(" "))
    spacing = r"(?:\s|\\[,;:! ]|~|" + ROW + r")*"            # \sum_{j=1}^\infty \ d_j
    pattern = re.compile(tokens(wrapper) + spacing + tokens(quote))
    for m in pattern.finditer(region):
        left, right = _near(region[:m.start()]), _near(region[m.end():], end=False)
        if (_SIDE_START.search(left) or left.rstrip().endswith(ROW)) and (
                _RIGHT_OK.match(right) or right.lstrip().startswith(ROW)):
            return True
    return False


def _closing(text: str, i: int) -> int | None:
    """Index of the bracket closing the one at text[i]."""
    depth = 0
    for j in range(i, len(text)):
        depth += text[j] in "([{"
        depth -= text[j] in ")]}"
        if depth == 0:
            return j
    return None


def _top_level_sum(tex: str) -> bool:
    """A '+' or '-' outside every bracket, after the first term."""
    text = re.sub(r"\\(?:left|right|big|Big|bigg|Bigg)[lr]?(?![A-Za-z])", "", tex).strip()
    if text[:1] in "([" and _closing(text, 0) == len(text) - 1:
        return False                                 # one bracket group
    depth = 0
    for i, ch in enumerate(text):
        depth += ch in "([{"
        depth -= ch in ")]}"
        if depth == 0 and ch in "+-" and text[:i].strip() and not text[:i].rstrip().endswith(("^", "_", "{")):
            return True
    return False


def _used_definition_names(card: dict, definitions: dict) -> set[str]:
    """Definitions a card's expressions use, directly or through each other."""
    bodies = {k.split("(")[0].strip(): str(v) for k, v in definitions.items()}
    source_defs = {str(k).split(":", 1)[1].split("(")[0].strip()
                   for k in (card.get("source") or {}) if str(k).startswith("define:")}
    texts = [str(card[k]) for k in _EXPRESSION_FIELDS if k in card]
    texts += [str(v.get("quote") if isinstance(v, dict) else v)
              for k, v in (card.get("source") or {}).items() if not str(k).startswith("define:")]
    written = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", " ".join(texts)))
    # a notation entry counts only when the card writes its token: the shared table maps
    # every defined constant of the paper, and most of them are not in this step
    texts += [str(v) for k, v in (card.get("notation") or {}).items()
              if set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(k))) & written]
    names = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", " ".join(texts)))
    used, frontier = set(), (set(bodies) | source_defs) & names
    while frontier:
        used |= frontier
        more = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", " ".join(bodies.get(n, "") for n in frontier)))
        frontier = ((set(bodies) | source_defs) & more) - used
    return used


def decide(verdict: str | None, transcription: str) -> str:
    """The one field an agent should report."""
    if transcription in (MISMATCH, NOT_IN_DOCUMENT):
        return "NOT_DECIDED"
    if verdict in ("ZERO", "CERTIFIED_BY_RULE"):
        return "VALID"
    if verdict == "NONZERO":
        return "INVALID"
    return "NOT_DECIDED"
