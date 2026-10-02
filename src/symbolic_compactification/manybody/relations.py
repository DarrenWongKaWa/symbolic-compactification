"""Displays of a LaTeX document as relations: rows, chains and the
pieces of one relation. Shared by the drafter and the prose scans."""
from __future__ import annotations

import re
from typing import Any

from ..parser import _ALLOWED_FUNCTIONS

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


def _top_level_rows(body: str) -> list[str]:
    """Split a display at row ends that sit outside braces: the \\\\ inside
    \\substack{k \\\\ sigma} does not end a row."""
    rows, depth, start, i = [], 0, 0, 0
    while i < len(body):
        c = body[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "\\" and body.startswith("\\\\", i) and depth == 0:
            rows.append(body[start:i])
            i += 2
            start = i
            continue
        elif c == "\\":
            i += 2                      # skip an escaped character such as \{
            continue
        i += 1
    return rows + [body[start:]]


_INACTIVE = re.compile(
    r"(?<!\\)%[^\n]*"                                          # a comment
    r"|\\iffalse\b.*?\\fi\b"                                    # \iffalse ... \fi
    r"|\\begin\{(verbatim\*?|comment|lstlisting|minted)\}.*?\\end\{\1\}", re.S)


def blank_inactive(text: str) -> str:
    """Comments, \\iffalse ... \\fi and verbatim or comment environments
    replaced by spaces (newlines kept, so every offset stays where it was):
    TeX prints none of them, so nothing in them is a claim of the paper."""
    return _INACTIVE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


_ALIAS_DEF = re.compile(
    r"\\(?:re)?newcommand\*?\s*\{?\\([A-Za-z]+)\}?\s*\{\s*\\(begin|end)\s*\{(" + "|".join(_ENVIRONMENTS)
    + r")(\*?)\}\s*\}|\\def\s*\\([A-Za-z]+)\s*\{\s*\\(begin|end)\s*\{(" + "|".join(_ENVIRONMENTS) + r")(\*?)\}\s*\}")


class _Display:
    """A display found by display_spans: the same interface as a regex match."""

    def __init__(self, start: int, end: int, inner: str):
        self._start, self._end, self._inner = start, end, inner

    def start(self) -> int:
        return self._start

    def end(self) -> int:
        return self._end

    def group(self, k: int = 0) -> str:
        return self._inner


def display_spans(body: str, document: str | None = None) -> list[_Display]:
    """Every display environment in ``body``, also when the paper opens and
    closes it with its own macros (\newcommand{\be}{\begin{equation}})."""
    aliases: dict[str, tuple[str, str]] = {}            # macro -> (begin|end, environment)
    for m in _ALIAS_DEF.finditer(document or body):
        name, kind, env = (m.group(1), m.group(2), m.group(3)) if m.group(1) else (m.group(5), m.group(6), m.group(7))
        aliases[name] = (kind, env)
    if not aliases:
        return list(_ENV_RE.finditer(body))
    opener = re.compile(r"\\begin\{(" + "|".join(_ENVIRONMENTS) + r")\*?\}|\\("
                        + "|".join(re.escape(a) for a, (k, _) in aliases.items() if k == "begin")
                        + r")(?![A-Za-z])" if any(k == "begin" for k, _ in aliases.values()) else
                        r"\\begin\{(" + "|".join(_ENVIRONMENTS) + r")\*?\}()")
    out, pos = [], 0
    while True:
        m = opener.search(body, pos)
        if not m:
            return out
        env = m.group(1) or aliases[m.group(2)][1]
        ends = [r"\\end\{" + env + r"\*?\}"] + [r"\\" + re.escape(a) + r"(?![A-Za-z])"
                                               for a, (k, e) in aliases.items() if k == "end" and e == env]
        close = re.compile("|".join(ends)).search(body, m.end())
        if not close:
            return out
        out.append(_Display(m.start(), close.end(), body[m.end():close.start()]))
        pos = close.end()


def latex_equations(document: str) -> list[dict[str, Any]]:
    """[{label, rows: [text, ...]}] for every display in a LaTeX document."""
    body = blank_inactive(document.split("\\begin{document}", 1)[-1].split("\\end{document}", 1)[0])
    found = []
    for m in display_spans(body, document):
        label = _LABEL_RE.search(m.group(2))
        # aligned/split/gathered inside an equation only lay out its rows
        inner = re.sub(r"\\(?:begin|end)\{(?:aligned|split|gathered|alignedat)\}(?:\[[tbc]\])?(?:\{\d+\})?",
                       lambda t: " " * len(t.group(0)), m.group(2))
        rows = [r for r in _top_level_rows(inner) if r.strip()]
        found.append({"label": label.group(1) if label else None, "rows": rows,
                      "offset": m.start(),
                      "context": body[max(0, m.start() - 800):m.start()] + body[m.end():m.end() + 300],
                      "sentence": _last_sentence(body[max(0, m.start() - 800):m.start()]),
                      "before": body[max(0, m.start() - 800):m.start()],
                      "document": body})
    for m in _DISPLAY_RE.finditer(body):
        text = m.group(1) or m.group(2)
        found.append({"label": None, "rows": [text], "offset": m.start(),
                      "context": body[max(0, m.start() - 800):m.start()] + body[m.end():m.end() + 300],
                      "sentence": _last_sentence(body[max(0, m.start() - 800):m.start()]),
                      "before": body[max(0, m.start() - 800):m.start()],
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


_SEPARATOR = re.compile(r",?\s*(?:\\q?quad\b|\\text\{\s*and\s*\})\s*")
_RELATION = re.compile(r"(?<![<>!=])=(?!=)|\\equiv\b")


def _tangled(row: str) -> bool:
    """A row holding two '=' relations side by side ('A &= B, \\qquad C = D'):
    a following '&= E' row could continue either one."""
    segments = _segments(row)
    return len(segments) > 1 and any(_RELATION.search(seg) and "=" in seg for seg in segments[1:])


def _segments(row: str) -> list[str]:
    """The row cut at every top-level \\quad, \\qquad or 'and'."""
    cuts, depth, i = [], 0, 0
    while i < len(row):
        c = row[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif depth == 0 and c in ",\\":
            m = _SEPARATOR.match(row, i)
            # a \qquad that opens a continuation row ("&& \qquad + B C") is layout
            if m and m.end() > i and row[:i].replace("&", "").strip():
                cuts.append((i, m.end()))
                i = m.end()
                continue
        i += 1
    segments, start = [], 0
    for a, b in cuts:
        segments.append(row[start:a])
        start = b
    return segments + [row[start:]]


_CONSTANT_TOKENS = frozenset({"\\pi", "\\infty", "\\frac", "\\left", "\\right", "\\cdot", "\\times",
                              "\\sqrt", "\\mathrm", "\\rm", "e", "i", "\\tfrac", "\\dfrac"})


def _symbolic(text: str) -> bool:
    """Whether the text names a quantity (pi, e, i and numbers do not)."""
    return any(t not in _CONSTANT_TOKENS for t in re.findall(r"\\[A-Za-z]+|[A-Za-z]", text))


def _definition_segment(segment: str) -> list[str] | None:
    """'X \\equiv expr' or 'X := expr' with a name on the left and a quantity
    on the right: [X, expr]. '\\Omega t \\equiv \\pi' and '\\varphi \\equiv \\pi' are
    conditions, not definitions."""
    text = segment.replace(":=", "\\equiv")
    if text.count("\\equiv") != 1 or "=" in text.replace("\\equiv", ""):
        return None
    lhs, rhs = text.split("\\equiv")
    if not re.fullmatch(r"\s*\\?[A-Za-z]+\s*(?:_\s*(?:\{[^{}]*\}|\\?[A-Za-z0-9]+)\s*)?"
                        r"(?:\^\s*(?:\{[^{}]*\}|\\?[A-Za-z0-9<>]+)\s*)?", lhs) or not _symbolic(rhs):
        return None
    return [lhs, rhs]


def _top_level_text(row: str) -> bool:
    """Words in the row itself (\\text{at}, \\mbox{for}), not in a subscript."""
    depth = 0
    for m in re.finditer(r"[{}]|\\(?:text|mbox|textrm|mathrm\{\s*(?:at|for|if|when|with|where|and)\b)", row):
        if m.group(0) == "{":
            depth += 1
        elif m.group(0) == "}":
            depth -= 1
        elif depth == 0 and row[max(0, m.start() - 1):m.start()] not in ("_", "^"):
            return True
    return False


def _condition_in_row(row: str) -> str | None:
    """A row that carries more than its relation: a second relation or a
    condition after \\quad (only 'X \\equiv expr' may sit there), or words.
    Its steps are not decided, because the extra piece may restrict them."""
    if _top_level_text(row):
        return "words in the display"
    segments = _segments(row)
    for extra in segments[1:]:
        bare = re.sub(r"\^\s*\{?\s*[<>]\s*\}?", "", extra)      # G^< is a label, not '<'
        if _RELATION.search(extra) or ":=" in extra or re.search(r"[<>]|\\neq|\\in\b", bare):
            if _definition_segment(extra) is None:
                return "a second relation or a condition in the display"
    return None


_OPEN_END = re.compile(r"(?:[-+=]|\\times|\\cdot|\\pm|\\mp)\s*$")


def _join_open_rows(rows: list[str]) -> list[str]:
    """A row that ends in an operator ('\frac{e^x}{2} +') continues on the
    next row, whatever that row starts with."""
    out: list[str] = []
    for row in rows:
        text = re.sub(r"\\(?:nonumber|notag)\b", " ", row).rstrip()
        if out and _OPEN_END.search(re.sub(r"[&\s]+$", "", out[-1])):
            out[-1] = out[-1].rstrip() + " " + re.sub(r"^\s*&?\s*(?:\\q?quad\s*)*", "", row)
        else:
            out.append(text if text else row)
    return out


def _two_columns(row: str) -> bool:
    """'A &= 1 & B &= -1': two relations side by side in an align."""
    return bool(re.search(r"&\s*=[^&]*[^\s&][^&]*&[^&=]*[^\s&][^&=]*&\s*=", row))


def steps_from_latex(raw: str) -> list[dict[str, Any]]:
    steps = []
    seen_labels: set = set()
    for n, eq in enumerate(latex_equations(raw), start=1):
        chains: list[list[str]] = []
        equivs: list[list[str]] = []
        rows = []
        conditional = None
        for row in eq["rows"]:
            row = re.sub(r"\\(?:nonumber|notag)\b", " ", _LABEL_RE.sub(" ", row))
            conditional = conditional or _condition_in_row(row)
            segments = _segments(row)
            definitions = [_definition_segment(seg) for seg in segments]
            if len(segments) > 1 and all(d is not None for d in definitions[1:]):
                kept = [segments[0]]
                equivs += definitions[1:]
            else:
                kept = [row]
            for segment in kept:
                whole = _definition_segment(segment)
                if whole is not None:
                    equivs.append(whole)
                elif re.search(r"\\equiv\b|:=", segment) and not re.search(r"(?<![<>!=:])=(?!=)", segment):
                    # 1/tau \\equiv ..., hbar omega_c \\equiv ...: a definition in disguise
                    equivs.append(re.split(r"\\equiv|:=", segment, maxsplit=1) + ["relation"])
                else:
                    rows.append(segment)
        rows = _join_open_rows(rows)
        if any(_two_columns(row) for row in rows):
            conditional = conditional or "two columns of relations side by side"
        tangled = False
        for row in rows:
            pieces = split_top_level(row)
            head = _clean(pieces[0])
            if chains and len(pieces) > 1 and _CONTINUES.match(pieces[0]) and head:
                # "&\quad - X = Y": the row continues the last side, then relates it
                chains[-1][-1] += " " + pieces[0]
                chains[-1] += pieces[1:]
                tangled = tangled or _tangled(row)
                continue
            if not chains:
                chains.append(pieces)
            elif len(pieces) == 1:                 # no '=': continues only if it starts
                if _CONTINUES.match(row) and not tangled:      # with an operator or a bracket
                    chains[-1][-1] += " " + row
                elif row.strip():                  # a row that is not read: the relation is cut
                    conditional = conditional or "a row of the display is not read"
            elif not head:                         # "&= C": the chain continues
                if tangled:                        # ... but which of the two relations?
                    chains.append([])
                chains[-1] += pieces[1:]
            else:                                  # "A &= B" on its own row: a new relation
                chains.append(pieces)
            # a new relation resets it; continuation rows of a tangled one stay ambiguous
            tangled = _tangled(row) or (tangled and not head)
        label = eq["label"] if eq["label"] not in seen_labels else None    # a duplicate \label
        seen_labels.add(eq["label"])
        base = label or f"eq{n}"
        display = label or f"#{n}"
        relations = [[_clean(p) for p in chain if _clean(p)] for chain in chains]
        relations = [r for r in relations if len(r) >= 2]
        for pair in equivs:                         # "X \\equiv ..." in a display: a definition
            sides = [_clean(p) for p in pair[:2]]
            if len(sides) == 2 and all(sides):
                steps.append({"id": f"{base}.def", "lhs": sides[0], "rhs": sides[1], "equiv": True,
                              "offset": eq.get("offset", 0),
                              **({"equiv_relation": True} if pair[2:] else {}),
                              **({"conditional": conditional} if conditional else {}),
                              "context": eq.get("context", ""), "sentence": eq.get("sentence", ""),
                              "before": eq.get("before", ""),
                              "document": eq.get("document", ""), "display": display})
        for j, chain in enumerate(relations):
            stem = base if len(relations) == 1 else f"{base}.r{j + 1}"
            for k in range(len(chain) - 1):
                steps.append({"id": stem if len(chain) == 2 else f"{stem}.{k + 1}",
                              "lhs": chain[k], "rhs": chain[k + 1], "offset": eq.get("offset", 0),
                              **({"conditional": conditional} if conditional else {}),
                              "context": eq.get("context", ""), "sentence": eq.get("sentence", ""),
                              "before": eq.get("before", ""),
                              "document": eq.get("document", ""), "display": display})
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

def _last_sentence(text: str) -> str:
    """The sentence that leads into a display: text after the last full stop,
    paragraph break or previous display."""
    cut = max(text.rfind(". "), text.rfind(".\n"), text.rfind("\n\n"), text.rfind("\\par"),
              text.rfind("\\end{"))
    return text[cut + 1:] if cut >= 0 else text
