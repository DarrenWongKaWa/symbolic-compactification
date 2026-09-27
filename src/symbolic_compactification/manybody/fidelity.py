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
                      "approximant", "summand")


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
    text = text.replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")")
    text = text.replace("^", "**")
    calls = set(callables)
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
                raise AdapterError("SOURCE_CHARACTER_UNSUPPORTED")
            kind, tok = ("open" if op == "(" else "close" if op == ")" else "op"), op
        if prev == "name" and kind == "open" and multiply is not None \
                and out[-1] not in _ALWAYS_MULTIPLY and not out[-1].startswith("(I*") \
                and out[-1] not in multiply:
            # beta(x) is a product, G(x) a function value: the source cannot tell
            raise AdapterError(f"SOURCE_APPLICATION_AMBIGUOUS:{out[-1]}")
        if prev in ("num", "name", "close") and kind in ("num", "name", "call", "open"):
            out.append("*")
        elif prev == "call" and kind != "open":
            raise AdapterError("SOURCE_FUNCTION_WITHOUT_ARGUMENTS")
        out.append(tok)
        prev = kind
    return "".join(out)


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
    text = re.sub(r"(?<=_)([A-Za-z0-9]*)([±∓])", lambda m: m.group(1) + signs[m.group(2)]
                  .replace("+", "p").replace("-", "m"), text)
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
    callables = {*_ALLOWED_FUNCTIONS, *funcs, *def_names, "Diff",
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
    ValueError when the quote is outside the supported grammar."""
    quote, wrap, branch = _quote(entry)
    text = erratum_of(entry) or quote
    if ctx.latex or looks_like_latex(text):
        text = latex_to_plain(text, ctx.macros)
    text = _pick_branch(expand_sum_pm(expand_re_im(text)), branch)
    expression = translate(text, ctx.notation, ctx.callables, ctx.keep_i, ctx.names,
                           multiply=ctx.multiply)
    if not _balanced(expression):
        raise AdapterError("SOURCE_BRACKETS_UNBALANCED")
    return quote, wrap.replace("{}", expression)


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
    r"(?:^|=|\\approx|\\simeq|\\equiv|,|;|:|\\[,;!]|\\q?quad|\\left\s*\.|"
    r"\\begin\{[A-Za-z*]+\}|\\end\{[A-Za-z*]+\}|\\\[|\$\$|\$|"
    r"\\sum_\{[^{}]*\}(?:\^\{?[^{}\s]*\}?)?|\\sum_[A-Za-z]|"
    r"\bd\s*\\?[A-Za-z]+(?:_\{?\w+\}?)?(?:\s*\\[,;!])?)\s*$")
_RIGHT_OK = re.compile(
    r"^\s*(?:$|=|\\approx|\\simeq|\\equiv|,|\.|;|:|\\[,;!]|\\q?quad|\\label|\\nonumber|"
    r"\\\\|\\end|\\\]|\$|\+\s*(?:\\mathcal\{O\}|O)\s*[(\[]|\\text)")


_PROSE_LEFT = re.compile(r"(?:^|\s)[A-Za-z]{2,}\s*$")


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
        left, right = region[:m.start()], region[m.end():]
        left_ok = _LEFT_OK.search(left) or left.rstrip().endswith(ROW) or (
            not latex and _PROSE_LEFT.search(left))
        right_ok = _RIGHT_OK.match(right) or right.lstrip().startswith(ROW)
        if left_ok and right_ok:
            return True
    return False


def display_text(raw: str, display: str) -> str | None:
    from .draft import latex_equations
    if display.startswith("#"):
        try:
            k = int(display[1:])
        except ValueError:
            return None
        eqs = latex_equations(raw)
        return "\\\\".join(eqs[k - 1]["rows"]) if 0 < k <= len(eqs) else None
    for eq in latex_equations(raw):
        if eq["label"] == display:
            return "\\\\".join(eq["rows"])
    return None


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
    space = CalculusSpace(symbols, funcs, definitions=definitions)
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
            where = locate_quote(ctx.raw, quote)
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
                record["translated"] = quote_expression(entry, ctx)[1]
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
            translated = quote_expression(entry, ctx)[1]
            record["translated"] = translated
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


def _used_definition_names(card: dict, definitions: dict) -> set[str]:
    """Definitions a card's expressions use, directly or through each other."""
    bodies = {k.split("(")[0].strip(): str(v) for k, v in definitions.items()}
    source_defs = {str(k).split(":", 1)[1].split("(")[0].strip()
                   for k in (card.get("source") or {}) if str(k).startswith("define:")}
    texts = [str(card[k]) for k in _EXPRESSION_FIELDS if k in card]
    texts += [str(v.get("quote") if isinstance(v, dict) else v)
              for k, v in (card.get("source") or {}).items() if not str(k).startswith("define:")]
    texts += [str(v) for v in (card.get("notation") or {}).values()]
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
