"""What the running text of a paper states: definitions ($z_\\pm = ...$),
real, positive and integer symbols, values given to names, and whether its
quantities are matrices. Displays are read in relations.py."""
from __future__ import annotations

import re
from typing import Any

from .latex import latex_to_plain
from .relations import _DEFINITION_LHS, _ENV_RE, _KNOWN, _tokens, split_top_level

_GREEK_NAMES = "alpha beta gamma delta epsilon varepsilon zeta eta theta kappa lambda mu nu xi rho sigma tau phi chi psi omega Gamma Delta Theta Lambda Xi Sigma Phi Psi Omega".split()


def _names_in(fragment: str) -> set[str]:
    """Symbol names in a short piece of LaTeX ($x, y$ or \\epsilon)."""
    out = set(re.findall(r"\\([A-Za-z]+)", fragment)) & set(_GREEK_NAMES)
    out |= set(re.findall(r"(?<![\\A-Za-z])([A-Za-z])(?![A-Za-z])", re.sub(r"\\[A-Za-z]+", " ", fragment)))
    return {"epsilon" if n == "varepsilon" else n for n in out}


_ITEMS = r"((?:\$[^$]{1,40}\$(?:\s*,\s*|\s+and\s+|\s*,\s*and\s+)?){1,8})"
_REAL_BEFORE = re.compile(r"\breal(?:-valued)?\s+(?:[A-Za-z-]+\s+){0,3}" + _ITEMS)   # real energies $\epsilon$, $\omega$
_REAL_AFTER = re.compile(_ITEMS + r"\s*(?:(?:is|are)\s+(?:a\s+|all\s+)?)?real(?:-valued)?\b")  # $x$, $y$ and $z$ (are) real


def _stated_real_pieces(raw: str):
    """(math piece, match) for every '$...$' the text calls real. In
    '$\\Gamma>0$ and real $\\omega$' only omega is called real."""
    for m in _REAL_BEFORE.finditer(raw):
        gap = raw[m.start():m.start(1)]
        if re.search(r"\b(?:part|parts|axis|line|plane|component|components)\b", gap):
            continue                     # 'the real part of $\omega$' says nothing about omega
        for piece in re.findall(r"\$([^$]{1,40})\$", m.group(1)):
            yield piece, m
    for m in _REAL_AFTER.finditer(raw):
        if _REAL_BEFORE.match(raw, m.end() - 4):
            continue                     # '$\\Gamma$ and real $\\omega$': 'real' is about omega
        for piece in re.findall(r"\$([^$]{1,40})\$", m.group(1)):
            if not re.search(r"[<>]", piece):              # '$\\Gamma>0$' states a sign, not realness
                yield piece, m


def _stated_integers(raw: str) -> set[str]:
    """'integer $n$', 'integers $n$, $m$', '$n$ an integer', '$n \\in \\mathbb{Z}$'."""
    found: set[str] = set()
    for m in re.finditer(r"\bintegers?\s+(?:[A-Za-z-]+\s+){0,2}" + _ITEMS, raw):
        for piece in re.findall(r"\$([^$]{1,40})\$", m.group(1)):
            found |= _names_in(re.split(r"[\\<>=]|\\neq", piece)[0])
    for m in re.finditer(_ITEMS + r"\s*(?:is|are|be)?\s*(?:an?\s+|all\s+)?(?:nonzero\s+|non-zero\s+)?integers?\b", raw):
        for piece in re.findall(r"\$([^$]{1,40})\$", m.group(1)):
            if not re.search(r"[<>=]|\\ne", piece):     # '$\\beta>0$ and $n$ an integer'
                found |= _names_in(piece)
    for m in re.finditer(r"([^$\s]{1,30})\s*\\in\s*\\mathbb\s*\{?\s*Z\s*\}?", raw):
        found |= _names_in(m.group(1))
    return found


_NOT_A_NUMBER = re.compile(r"function|field|operator|kernel|propagator|matri|vector|distribution", re.I)


def _matsubara_names(raw: str) -> set[str]:
    """Names in a sentence that speaks of Matsubara frequencies ('$i\\Omega$ is a
    bosonic Matsubara frequency'): e^{i Omega beta} = 1 there, so a refutation
    with generic values may be wrong."""
    found: set[str] = set()
    for sentence in re.split(r"(?<=[.;])\s+", raw):
        if re.search(r"matsubara", sentence, re.I):
            for piece in re.findall(r"\$([^$]{1,80})\$", sentence):
                found |= _names_in(piece)
    return found


def _stated_numbers(raw: str) -> set[str]:
    """Names called real as bare symbols ('$\\varepsilon$ real'); 'real
    $\\varepsilon(k)$' and 'the real-valued function $A$' name functions and
    do not count."""
    return {n for piece, m in _stated_real_pieces(raw)
            if not re.search(r"[(\[]|\\left", piece) and not _NOT_A_NUMBER.search(m.group(0))
            for n in _names_in(piece)}


def _stated_realness(raw: str) -> tuple[dict[str, str], set[str]]:
    """Names the text calls real ('real $a$', '$x,y$ real', 'x \\in \\mathbb{R}')
    and names it calls complex ('complex $z$', 'z = x + iy', '\\in \\mathbb{C}')."""
    real: dict[str, str] = {}
    complex_: set[str] = set()
    line = lambda pos: f"line {raw.count(chr(10), 0, pos) + 1}"
    for piece, m in _stated_real_pieces(raw):
        for n in _names_in(piece):
            real.setdefault(n, f"{line(m.start())}: {m.group(0)[:40]}")
    for m in re.finditer(r"([^$\s]{1,30})\s*\\in\s*\\mathbb\s*\{?\s*R\s*\}?", raw):
        for n in _names_in(m.group(1)):
            real.setdefault(n, f"{line(m.start())}: {m.group(0)[:40]}")
    for m in re.finditer(r"complex\s+(?:[A-Za-z ]{0,30})?\$([^$]{1,40})\$|([^$\s]{1,30})\s*\\in\s*\\mathbb\{C\}", raw):
        complex_ |= _names_in(m.group(1) or m.group(2))
    for m in re.finditer(r"\$\s*(\\?[A-Za-z]+)\s*=\s*[A-Za-z]\s*\+\s*(?:\\mathrm\{i\}|i|\\ii)\s*[A-Za-z]\s*\$", raw):
        complex_ |= _names_in(m.group(1))
    return real, complex_


def _realness_sensitive(steps, shared_quotes, macros, latex) -> set[str]:
    """Names inside a quote that uses Re, Im, a conjugate or |...|: there the
    verdict can depend on whether the symbol is real."""
    bound = {v for st in steps for v in st.get("bound", ())}     # integration / summation variables
    quotes = [q for st in steps for q in (st["lhs"], st["rhs"])]
    quotes += [v.get("quote") if isinstance(v, dict) else v for v in shared_quotes.values()]
    out: set[str] = set()
    for q in quotes:
        infinite = str(q).lstrip().startswith("\\int") and "\\infty" in str(q)   # decay needs real parts
        if infinite or re.search(r"\\(?:mathrm|operatorname|rm)\s*\{?\s*(?:Re|Im)|\\(?:Re|Im)\b|\^\s*\{?\s*\*|\\bar\b|\\overline|\\ast|\|", str(q)):
            try:
                plain = latex_to_plain(str(q), macros) if latex else str(q)
            except (ValueError, RecursionError):
                continue
            out |= _tokens(plain)[0] | _tokens(plain)[1]
    # |G(w)|^2 depends on the realness of everything inside G's definition
    bodies = {}
    for key, v in shared_quotes.items():
        try:
            quote = v.get("quote") if isinstance(v, dict) else v
            plain = latex_to_plain(str(quote), macros) if latex else str(quote)
        except (ValueError, RecursionError):
            continue
        t = _tokens(plain)
        bodies[key.split(":", 1)[1].split("(")[0]] = t[0] | t[1]
    todo = list(out)
    while todo:
        name = todo.pop()
        for extra in bodies.get(name, set()) - out:
            out.add(extra)
            todo.append(extra)
    return out - bound


def _symbol_entry(name, positive, real_stated, complex_stated, realness_matters) -> dict:
    """Real only when the text says so (or says positive), or when realness
    cannot change a verdict; stated complex is always complex."""
    if name in positive:
        return {"name": name, "positive": True, "stated": positive[name]}
    if name in complex_stated:
        return {"name": name, "real": False, "stated": "complex in the text"}
    if name in real_stated:
        return {"name": name, "real": True, "stated": real_stated[name]}
    if name in realness_matters:
        # read as real, but a card that takes Re/Im/conj/|.| of it is not decided
        return {"name": name, "realness": "unstated",
                "stated": "realness not stated; it appears under Re/Im/conjugate/|.|"}
    return {"name": name}


_INLINE_DEF = re.compile(
    r"(?:\bwhere|\bwith|\blet|\bLet|\bdefine|\bdefining|\bhere)\s+(?:[A-Za-z ,]{0,20}?)\$([^$]{1,160})\$")


def _inline_definitions(raw: str, macros: dict) -> list[tuple[str, Any, str]]:
    """'where $z_\\pm = \\varepsilon_d \\pm i\\Gamma$', 'with $f(x) = ...$': definitions
    stated in the running text, as quoted define: entries. Returns
    (key, entry, name) triples; bare names get zero-argument definitions."""
    out = []
    body = raw.split("\\begin{document}", 1)[-1]
    text = _ENV_RE.sub(" ", body)                       # prose only, displays removed
    for m in _INLINE_DEF.finditer(text):
        math = m.group(1)
        sides = split_top_level(re.sub(r"\\equiv", "=", math))
        if len(sides) != 2 or not sides[0].strip() or not sides[1].strip():
            continue
        lhs = sides[0].strip()
        if re.search(r"\\equiv", math):
            lhs_raw, rhs_raw = math.split("\\equiv", 1)
        else:
            lhs_raw, rhs_raw = math.split("=", 1)
        rhs_raw = rhs_raw.strip()
        try:
            plain = latex_to_plain(lhs, macros).strip()
        except (ValueError, RecursionError):
            continue
        call = _DEFINITION_LHS.match(plain)
        bare = re.fullmatch(r"\(*\s*([A-Za-z][A-Za-z0-9_]*)\s*\)*", plain)
        if call and call.group(1) not in _KNOWN | {"n_F", "n_B"}:
            name, args = call.group(1), ",".join(a.strip() for a in call.group(2).split(","))
        elif bare and bare.group(1) not in _KNOWN and not re.fullmatch(r"[A-Za-z]", bare.group(1)):
            name, args = bare.group(1), ""      # a single Latin letter (x, t, n) is a variable
        else:
            continue
        # a condition ("where $x = 0$", "with $n = 1, 2$") is not a definition:
        # the right side must name something and must not contain the name itself
        try:
            rhs_names = _tokens(latex_to_plain(rhs_raw, macros))[0] | _tokens(latex_to_plain(rhs_raw, macros))[1]
        except (ValueError, RecursionError):
            continue
        base_name = name.replace("PM", "").removesuffix("_pm")
        if not rhs_names or name in rhs_names or base_name in rhs_names or "," in rhs_raw or "\\dots" in rhs_raw:
            continue
        if "PM" in name or name.endswith("_pm"):
            base = name.replace("PM", "").removesuffix("_pm").rstrip("_") + "_"
            out.append((f"define:{base}p({args})", {"quote": rhs_raw, "branch": "+"}, base + "p"))
            out.append((f"define:{base}m({args})", {"quote": rhs_raw, "branch": "-"}, base + "m"))
        else:
            out.append((f"define:{name}({args})", rhs_raw, name))
    return out


def prose_assignments(raw: str, macros: dict) -> dict[str, list[tuple[int, str]]]:
    """Names the running text gives a value: '$x = \\omega/\\Delta$', '$\\Gamma =
    \\Gamma_L + \\Gamma_R$', '$X \\equiv ...$'. name -> [(offset in the body, right
    side)], conditions ('$x = 0$', '$n = 1, 2, \\dots$') left out."""
    body = _dollar_math(raw).split("\\begin{document}", 1)[-1]
    displays = [(m.start(), m.end()) for m in _ENV_RE.finditer(body)]
    out: dict[str, list[tuple[int, str]]] = {}
    for m in re.finditer(r"\$([^$]{1,160})\$", body):
        if any(a <= m.start() < b for a, b in displays):
            continue
        sides = split_top_level(re.sub(r"\\equiv", "=", m.group(1)))
        if len(sides) != 2:
            continue
        try:
            lhs = latex_to_plain(sides[0], macros).strip()
            rhs_plain = latex_to_plain(sides[1], macros)
        except (ValueError, RecursionError):
            continue
        bare = re.fullmatch(r"\(*\s*([A-Za-z][A-Za-z0-9_]*)\s*\)*", lhs)
        rhs_names = _tokens(rhs_plain)[0] | _tokens(rhs_plain)[1]
        if not bare or bare.group(1) in _KNOWN or not rhs_names or bare.group(1) in rhs_names \
                or "," in sides[1] or "\\dots" in sides[1]:
            continue
        out.setdefault(bare.group(1), []).append((m.start(), " ".join(sides[1].split())))
    return out


def prose_values(raw: str, macros: dict) -> dict[str, list[tuple[int, str]]]:
    """Every value the running text gives a bare name, conditions included:
    '$p = 0$', '$a = 0$', '$x = \\omega/\\Delta$'. name -> [(offset, right side)]."""
    body = _dollar_math(raw).split("\\begin{document}", 1)[-1]
    displays = [(m.start(), m.end()) for m in _ENV_RE.finditer(body)]
    out: dict[str, list[tuple[int, str]]] = {}
    for m in re.finditer(r"\$([^$]{1,160})\$", body):
        if any(a <= m.start() < b for a, b in displays):
            continue
        sides = split_top_level(re.sub(r"\\equiv", "=", m.group(1)))
        if len(sides) != 2 or not sides[1].strip():
            continue
        try:
            lhs = latex_to_plain(sides[0], macros).strip()
        except (ValueError, RecursionError):
            continue
        bare = re.fullmatch(r"\(*\s*([A-Za-z][A-Za-z0-9_]*)\s*\)*", lhs)
        if bare and bare.group(1) not in _KNOWN:
            out.setdefault(bare.group(1), []).append((m.start(), " ".join(sides[1].split())))
    return out


_NONCOMMUTING = re.compile(
    r"\b(?:are|is|as|be)\s+(?:[^\s.,;]+\s+){0,3}matri(?:x|ces)\b|\bmatri(?:x|ces)\s+in\s+\w+(?:\s+\w+)?\s+space"
    r"|\bdo(?:es)?\s+not\s+commute|\bnon-?commut\w*|\boperator-valued|\bNambu\b|\bspinor"
    r"|\d\s*(?:\\times|\u00d7|x)\s*\d\s+(?:matri|Green|self-energy|Nambu|Keldysh)"
    r"|\$\\(?:mathbf|boldsymbol|bm)\s*\{\s*\\?[A-Z]", re.I)


def stated_noncommuting(raw: str) -> str | None:
    """Where the text says its quantities are matrices or do not commute."""
    m = _NONCOMMUTING.search(raw.split("\\begin{document}", 1)[-1])
    return None if m is None else f"{m.group(0)[:60]}"


def _dollar_math(raw: str) -> str:
    """\\( ... \\) written as $ ... $, for the scans of the running text."""
    return raw.replace("\\(", "$").replace("\\)", "$")


def _positive_symbols(raw: str) -> dict[str, str]:
    """Names stated positive in the text, e.g. $\\Gamma>0$ or beta > 0, with
    where they are stated (so a reviewer can confirm the guess). 'Im z > 0'
    says nothing about z itself."""
    found: dict[str, str] = {}
    for m in re.finditer(r"(\\?[A-Za-z]+(?:_\{?\\?[A-Za-z0-9]+\}?)?)\s*>\s*0(?![.\d])", raw):
        before = raw[max(0, m.start() - 16):m.start()]
        if re.search(r"(?:Im|Re|\\Im|\\Re|\|)\s*\}?\s*(?:\\[,;!]\s*)*[({]?\s*$", before):
            continue
        if re.search(r"[-+*/^_A-Za-z0-9)}]\s*$", before):
            continue                     # '$\epsilon - \mu > 0$' says nothing about mu alone
        for name in _names_in(m.group(1)):
            found.setdefault(name, f"line {raw.count(chr(10), 0, m.start()) + 1}: {m.group(0)}")
    return found
