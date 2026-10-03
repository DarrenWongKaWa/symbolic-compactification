"""What the running text of a paper states: definitions ($z_\\pm = ...$),
real, positive and integer symbols, values given to names, and whether its
quantities are matrices. Displays are read in relations.py."""
from __future__ import annotations

import re
from typing import Any

from .latex import latex_to_plain
from .relations import document_body, _DEFINITION_LHS, _KNOWN, _tokens, display_spans, split_top_level

_GREEK_NAMES = "alpha beta gamma delta epsilon varepsilon zeta eta theta kappa lambda mu nu xi rho sigma tau phi chi psi omega Gamma Delta Theta Lambda Xi Sigma Phi Psi Omega".split()


def _names_in(fragment: str) -> set[str]:
    """Symbol names in a short piece of LaTeX, as the cards spell them:
    '$x, y$' -> x, y; '\\epsilon' -> epsilon; '\\Gamma_L' -> Gamma_L (not
    Gamma and L); '\\Gamma_{L,R}' -> Gamma_L, Gamma_R."""
    fragment = re.sub(r"(\\?[A-Za-z]+)_\{\s*([A-Za-z0-9]+)\s*,\s*([A-Za-z0-9]+)\s*\}",
                      r"\1_\2, \1_\3", fragment)
    try:
        plain = latex_to_plain(fragment)
    except (ValueError, RecursionError):
        return set()
    plain = re.sub(r"\\[A-Za-z]+", " ", plain)           # commands the reader leaves (\in, \neq)
    names = set(re.findall(r"(?<![A-Za-z0-9_])([A-Za-z][A-Za-z0-9_]*)", plain))
    return {n for n in names if n not in _KNOWN | {"i", "E", "I", "oo", "mathbb", "d"}}


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
    return _stated_integer_words(raw) | {n for m in re.finditer(
        r"\$\s*(\\?[A-Za-z]+)\s*=\s*0\s*,\s*(?:\\pm\s*)?1\s*,", raw) for n in _names_in(m.group(1))}


def _stated_integer_words(raw: str) -> set[str]:
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


_OPERATOR_WORDS = re.compile(r"operator|\bspin\b|angular\s+momentum|Pauli|creation|annihilation"
                             r"|matri(?:x|ces)|spinor|Hamiltonian|anti-?commut|\bcommut|\bTr\b|\\mathrm\{Tr\}"
                             r"|\btrace\b|Grassmann|generator|non-?Abelian|Lie\s+algebra|\bSU\(|\bSO\(|quaternion",
                             re.I)


_OPERATOR_NOUN = (r"(?:operator|Hamiltonian|matri(?:x|ce)|Pauli\s+matri(?:x|ce)|spin|generator|Grassmann"
                  r"|creation|annihilation|component|spinor|projector)")



def _name_roots(fragment: str) -> set[str]:
    """Roots of the names in a fragment (d_k -> d): unlike _names_in, d is
    kept, since an operator may be called d_k."""
    try:
        plain = latex_to_plain(fragment)
    except (ValueError, RecursionError):
        return set()
    plain = re.sub(r"\\[A-Za-z]+", " ", plain)
    return {re.split(r"__|_", n)[0] for n in re.findall(r"(?<![A-Za-z0-9_])([A-Za-z][A-Za-z0-9_]*)", plain)}

def _operator_names(raw: str) -> set[str]:
    """Names in a sentence that calls them operators, spin components,
    creation or annihilation operators or matrices ('the fermionic operators
    $p$ and $q$'), plus daggered and hatted names: their products need not
    commute."""
    found: set[str] = set()
    for sentence in re.split(r"(?<=[.;:])\s+", raw):
        if not _OPERATOR_WORDS.search(sentence) or re.search(r"density\s+matri|T-matri|S-matri", sentence):
            continue
        for m in re.finditer(r"\$([^$]{1,60})\$", sentence):
            # only math the word describes: 'the fermionic operators $p$ and $q$',
            # 'the Hamiltonian of the dot is $H_0 + V$', '$A$ and $B$ denote the
            # components of one spin' -- not every symbol in the sentence
            before, after = sentence[max(0, m.start() - 80):m.start()], sentence[m.end():m.end() + 120]
            named_before = re.search(_OPERATOR_NOUN + r"s?\s+(?:[A-Za-z-]+\s+){0,4}(?:\$[^$]*\$\s*(?:,|and)\s*)*$",
                                     before, re.I)
            # '$a$ is the annihilation operator', '$p$ and $q$ are operators': a list
            # takes a plural verb, and a relation ('$K \\equiv (k_0, k)$, $a$ is ...')
            # is never what the word describes
            named_after = re.match(r"\s*(?:is|are|denotes?|be|being|as)\s+(?:[A-Za-z-]+\s+){0,5}"
                                   + _OPERATOR_NOUN, after, re.I) or \
                re.match(r"\s*(?:(?:,|and)\s*\$[^$=]*\$\s*)+(?:are|denote|be|being|as)\s+"
                         r"(?:[A-Za-z-]+\s+){0,5}" + _OPERATOR_NOUN, after, re.I)
            if re.search(r"=|\\equiv", m.group(1)):
                continue
            if named_before or named_after:
                # the operator itself, not the labels on it (\hat I^{e(h)}_p: not e, h)
                # nor its arguments ($a(k)$ is the annihilation operator: not k)
                bare = re.sub(r"[_^]\s*(?:\{[^{}]*\}|\\?[A-Za-z0-9]+)", " ", m.group(1))
                bare = re.sub(r"(?<=[A-Za-z}])\s*\((?:[^()]|\([^()]*\))*\)", " ", bare)
                roots = _name_roots(bare)
                found |= {n for n in _names_in(m.group(1))
                          if (len(n) <= 3 or "_" in n) and re.split(r"__|_", n)[0] in roots}
    for m in re.finditer(r"\\(?:hat|widehat)\s*\{?\s*\\?[A-Za-z]+\s*\}?|\\?[A-Za-z]+\s*\^\s*\{?\s*\\dagger", raw):
        found |= _names_in(m.group(0))
    return found


def distribution_defined_in_text(raw: str) -> str | None:
    """Where the text writes its own n_F / n_B / f (n_F(\\omega) = 1/(e^{\\beta(\\omega-\\mu)}+1)),
    or puts a chemical potential into the occupations: the built-in
    nF(x) = 1/(e^{beta x}+1) may then not be the paper's."""
    for m in re.finditer(r"\$([^$]*?)\b(n_F|n_\{F\}|n_B|n_\{B\})\s*\(([^)]*)\)\s*=([^$]*)\$", raw):
        if not _is_builtin_distribution(m.group(2), m.group(3), m.group(4)):
            return " ".join(m.group(0).split())[:80]
    m = re.search(r"chemical\s+potential\s+(?:of\s+)?(?:\$\\mu|\\\(\\mu)|\$\\mu[^$]*\$\s+is\s+the\s+chemical", raw)
    return None if m is None else " ".join(m.group(0).split())[:80]


def _is_builtin_distribution(name: str, arg: str, body: str) -> bool:
    """Whether '$n_F(x) = 1/(e^{\\beta x}+1)$' is exactly the built-in one."""
    import sympy
    try:
        x = sympy.Symbol(latex_to_plain(arg).strip())
        beta = sympy.Symbol("beta")
        from sympy.parsing.sympy_parser import (implicit_multiplication, parse_expr,
                                                standard_transformations)
        text = latex_to_plain(body).replace("^", "**").replace("E**", "exp")
        expr = parse_expr(" ".join(text.split()), local_dict={"beta": beta, str(x): x, "exp": sympy.exp},
                          transformations=standard_transformations + (implicit_multiplication,))
    except Exception:
        return False
    sign = 1 if "F" in name else -1
    return sympy.simplify(expr - 1 / (sympy.exp(beta * x) + sign)) == 0


def _distribution_not_thermal(raw: str) -> str | None:
    """Where the text says n_F (or the Fermi function f) is not the thermal
    distribution: then n_F must not be expanded as one."""
    for sentence in re.split(r"(?<=[.;])\s+", raw):
        if re.search(r"n_F|n_\{F\}|n_B|Fermi\s+function|occupation|distribution", sentence) and re.search(
                r"arbitrary|non-?equilibrium|not\s+the\s+(?:thermal\s+|equilibrium\s+)?(?:Fermi|Bose)"
                r"|out\s+of\s+equilibrium|generic\s+occupation", sentence, re.I):
            return " ".join(sentence.split())[:80]
    return None


def special_functions_named(raw: str) -> dict[str, str]:
    """Notation for special functions the text names: '$\\zeta$ is the Riemann
    zeta function' -> zeta: zeta_fn, '$\\Gamma$ is the gamma function' ->
    Gamma: gamma_fn. The symbol must be named in the same sentence, and the
    letter must never be used otherwise: not bare in the text ('$\\Gamma$ is
    the broadening', '$\\Gamma > 0$') and not bare in a display."""
    from .relations import display_spans
    text = _dollar_math(raw)
    body = document_body(text)
    out: dict[str, str] = {}
    negation = re.compile(r"\bnot\b|instead|rather\s+than|unlike|confused|differs?\s+from|spectral|generali[sz]ed", re.I)
    sentences = re.split(r"(?<=[.;])\s+", body)
    for letter, name, words in (("zeta", "zeta_fn", r"(?:Riemann|Hurwitz)\s+zeta[- ]function"),
                                ("Gamma", "gamma_fn", r"(?:Euler(?:'s)?\s+)?gamma[- ]function")):
        symbol = rf"\$[^$]*\\{letter}(?![A-Za-z])[^$]*\$"
        naming = [sent for sent in sentences if re.search(symbol, sent) and re.search(words, sent, re.I)]
        if not naming or any(negation.search(sent) for sent in naming):
            continue
        # every sentence that writes the letter must be one that names the function
        if any(re.search(symbol, sent) and sent not in naming for sent in sentences):
            continue
        bare_prose = [m for m in re.finditer(rf"\$([^$]*\\{letter}(?![A-Za-z])[^$]*)\$", body)
                      if re.search(rf"\\{letter}(?![A-Za-z])\s*(?![\s(]|\\left\s*\()", m.group(1) + " ")
                      and not re.fullmatch(rf"\s*\\{letter}\s*", m.group(1))]
        lone = [m for m in re.finditer(rf"\$\s*\\{letter}\s*\$", body)
                if not re.search(words, body[max(0, m.start() - 80):m.end() + 80], re.I)]
        in_displays = any(re.search(rf"\\{letter}(?![A-Za-z])\s*(?!\(|\\left|_|\^)", d.group(0))
                          for d in display_spans(body, raw))
        if bare_prose or lone or in_displays:
            continue                       # the letter also means something else here
        out[letter] = name
    return out


def subscript_collisions(raw: str) -> set[str]:
    """Names where '_+' and '_p' (or '_-' and '_m') both occur on one base:
    both are read as X_p, so the two would become one symbol."""
    seen: dict[str, set[str]] = {}
    for m in re.finditer(r"(\\?[A-Za-z]+)\s*_\s*\{?\s*([+\-pm])\s*\}?(?![A-Za-z0-9])", raw):
        seen.setdefault(m.group(1), set()).add(m.group(2))
    out: set[str] = set()
    for base, subs in seen.items():
        for sign, letter in (("+", "p"), ("-", "m")):
            if {sign, letter} <= subs:
                out |= {n + "_" + letter for n in _names_in(base)}
    return out


def dependence_stated(raw: str) -> set[str]:
    """Names the text says depend on something ('$\\mu$ depends on the density',
    'a time-dependent frequency $\\omega(t)$', '$\\Gamma(\\epsilon)$ is energy dependent')."""
    out: set[str] = set()
    for sentence in re.split(r"(?<=[.;])\s+", _dollar_math(raw)):
        if re.search(r"depend|varies|varying|changes?\s+with|function\s+of", sentence, re.I):
            for piece in re.findall(r"\$([^$]{1,60})\$", sentence):
                out |= _names_in(re.sub(r"\([^()]*\)", " ", piece))
    return out


def log_base_stated(raw: str) -> str | None:
    """'All logarithms are to base 2': log is then not the natural logarithm."""
    m = re.search(r"logarithms?\s+(?:are\s+)?(?:taken\s+)?(?:to|in|with)\s+(?:the\s+)?base\s*\$?\s*(\d+|e)\b", raw, re.I)
    return None if m is None or m.group(1) == "e" else m.group(1)


def builtins_redefined(raw: str) -> set[str]:
    """Built-in function names the paper defines itself ('$\\ERF(u) = 1 + u$'
    with \\ERF set to erf): the built-in must not stand in for them."""
    from .latex import read_macros
    macros = read_macros(raw)
    found: set[str] = set()
    for m in re.finditer(r"\$([^$]{1,120})\$", _dollar_math(raw)):
        sides = split_top_level(m.group(1))
        if len(sides) != 2:
            continue
        try:
            lhs = latex_to_plain(sides[0], macros).strip()
        except (ValueError, RecursionError):
            continue
        call = _DEFINITION_LHS.match(lhs)
        if call and call.group(1) in _KNOWN:
            found.add(call.group(1))
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
        infinite = str(q).lstrip().startswith("\\int") and (            # decay, or a real n_F shift
            "\\infty" in str(q) or re.search(r"n_\{?F|n_\{?B", str(q)) is not None)
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
    body = document_body(raw)
    text = body
    for m in reversed(display_spans(body, raw)):        # prose only, displays removed
        text = text[:m.start()] + " " + text[m.end():]
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
        if re.fullmatch(r"\s*\\?[A-Za-z]+(?:_\{?\\?[A-Za-z0-9]+\}?)?\s*", rhs_raw):
            continue                     # 'with $\Gamma_R = \Gamma_L$' is a condition, not a definition
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
    body = document_body(_dollar_math(raw))
    displays = [(m.start(), m.end()) for m in display_spans(body, raw)]
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
    body = document_body(_dollar_math(raw))
    displays = [(m.start(), m.end()) for m in display_spans(body, raw)]
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
    r"\$[^$]{1,60}\$\s*(?:(?:,|and)\s*\$[^$]{1,60}\$\s*)*(?:is|are|be)\s+(?:[^\s.,;$]+\s+){0,3}matri(?:x|ces)\b"
    r"|\bmatri(?:x|ces)\s+in\s+\w+(?:\s+\w+)?\s+space"
    # 'do not commute' needs a math subject in the same clause: '$A$ and $B$ do not
    # commute', 'the spin operators do not commute', '$H_0$ does not commute with $V$';
    # not 'fixing the divergence does not commute with the gauge fixing' (procedures)
    r"|(?:\$[^$]{1,60}\$|\b(?:operators?|matri(?:x|ces)|generators?|components|fields|charges)\b)"
    r"[^.;:$]{0,60}\bdo(?:es)?\s+not\s+commute|\bdo(?:es)?\s+not\s+commute\s+with\s+\$"
    r"|\bnon-?commuting\s+(?:matri|operator|quantit)|\boperator-valued|\bNambu\b"
    r"|\d\s*(?:\\times|\u00d7|x)\s*\d\s+(?:matri|Green|self-energy|Nambu|Keldysh)", re.I)


def stated_noncommuting(raw: str) -> str | None:
    """Where the text says its quantities are matrices or do not commute
    ('the density matrix', 'the transfer matrix element', 'the S-matrix'
    are single objects, not a statement that the quantities are matrices)."""
    for m in _NONCOMMUTING.finditer(document_body(raw)):
        if re.search(r"density|transfer|scattering|transmission|hopping|tunnel|[TSK]-|matrix\s+elements?",
                     m.group(0) + raw[m.end():m.end() + 10], re.I):
            continue
        return f"{m.group(0)[:60]}"
    return None


def _dollar_math(raw: str) -> str:
    """\\( ... \\) written as $ ... $, with comments and other text TeX does not
    print blanked out, for the scans of the running text."""
    from .relations import blank_inactive
    return blank_inactive(raw).replace("\\(", "$").replace("\\)", "$")


def _positive_symbols(raw: str) -> dict[str, str]:
    """Names stated positive in the text ($\\Gamma>0$, $\\Gamma_{L,R}>0$,
    'positive rates $\\Gamma_L$ and $\\Gamma_R$'), with where they are stated.
    'Im z > 0' and '$\\epsilon - \\mu > 0$' say nothing about one name, and a
    name the text also calls negative or nonpositive anywhere is left out."""
    found: dict[str, str] = {}
    line = lambda pos: f"line {raw.count(chr(10), 0, pos) + 1}"
    for m in re.finditer(r"(\\?[A-Za-z]+(?:_\{[^{}]*\}|_\\?[A-Za-z0-9]+)?)\s*>\s*0(?![.\d])", raw):
        before = raw[max(0, m.start() - 16):m.start()]
        if re.search(r"(?:Im|Re|\\Im|\\Re|\|)\s*\}?\s*(?:\\[,;!]\s*)*[({]?\s*$", before):
            continue
        if re.search(r"[-+*/^_A-Za-z0-9)}]\s*$", before):
            continue                     # '$\epsilon - \mu > 0$' says nothing about mu alone
        for name in _names_in(m.group(1)):
            found.setdefault(name, f"{line(m.start())}: {m.group(0)}")
    for m in re.finditer(r"\bpositive\s+(?:[A-Za-z-]+\s+){0,3}" + _ITEMS, raw):
        for piece in re.findall(r"\$([^$]{1,40})\$", m.group(1)):
            if not re.search(r"[(<>=]", piece):
                for name in _names_in(piece):
                    found.setdefault(name, f"{line(m.start())}: {m.group(0)[:40]}")
    for name in _signs_contested(raw):
        found.pop(name, None)
    return found


def _signs_contested(raw: str) -> set[str]:
    """Names the text also calls negative, nonpositive or of either sign
    ($\\eta<0$, '$\\epsilon$ takes either sign')."""
    out: set[str] = set()
    for m in re.finditer(r"(\\?[A-Za-z]+(?:_\{[^{}]*\}|_\\?[A-Za-z0-9]+)?)\s*(?:<|\\le|\\leq)\s*0(?![.\d])", raw):
        out |= _names_in(m.group(1))
    for m in re.finditer(r"\$([^$]{1,40})\$[^.$]{0,40}\b(?:either\s+sign|any\s+sign|negative|both\s+signs)", raw):
        out |= _names_in(m.group(1))
    return out


def prose_constraints(raw: str, macros: dict) -> dict[str, str]:
    """Names in relations the text imposes that are not definitions of a new
    name: '$e^{iqL} = 1$', '$\\Omega T = 2\\pi$', '$x = \\beta\\epsilon = \\epsilon/T$',
    '$t > s$', '$\\eta < 0$', '$k \\neq q$'. A refutation that treats them as
    free may be wrong. name -> where."""
    out: dict[str, str] = {}
    for name, sources in constraint_sources(raw, macros).items():
        out[name] = sources[0][0]
    return out


def constraint_sources(raw: str, macros: dict) -> dict[str, list[tuple[str, str | None]]]:
    """name -> [(where, the relation as written, or None for a sentence about
    discrete values)], for every constraint ``prose_constraints`` reports."""
    body = document_body(_dollar_math(raw))
    displays = [(m.start(), m.end()) for m in display_spans(body, raw)]
    out: dict[str, list[tuple[str, str | None]]] = {}
    for m in re.finditer(r"\$([^$]{1,160})\$", body):
        if any(a <= m.start() < b for a, b in displays):
            continue
        math = m.group(1)
        if not re.search(r"=|<|>|\\le|\\ge|\\neq|\\ne\b", math):
            continue
        if re.fullmatch(r"\s*\\?[A-Za-z]+(?:_\{[^{}]*\}|_\\?[A-Za-z0-9]+)?\s*>\s*0\s*", math):
            continue                     # a plain positivity statement is used as an assumption
        sides = split_top_level(re.sub(r"\\equiv|:=", "=", math))
        try:
            lhs = latex_to_plain(sides[0], macros).strip() if len(sides) == 2 else ""
        except (ValueError, RecursionError):
            lhs = ""
        if len(sides) == 2 and (re.fullmatch(r"\(*\s*[A-Za-z][A-Za-z0-9_]*\s*\)*", lhs)
                                or _DEFINITION_LHS.match(lhs)) \
                and not re.search(r"<|>|\\le|\\ge|\\neq", math):
            continue                     # 'X = expr', 'f(x) = expr': a value or definition, handled elsewhere
        where = f"line {raw.count(chr(10), 0, raw.find(m.group(0)))+1}: ${' '.join(math.split())[:50]}$"
        for name in _names_in(math):
            out.setdefault(name, []).append((where, math))
    # names that take only discrete values ('take only the values $+1$ and $-1$')
    for sentence in re.split(r"(?<=[.;])\s+", body):
        if re.search(r"projector|idempoten|nilpoten|involution|Ising|occupation\s+number|number\s+operator"
                     r"|eigenvalues?|\bvalues?\s+(?:\$?[+-]?\s*[01]\b|plus|minus|zero|one)"
                     r"|\\pm\s*1\b|\$\s*[+-]?[01]\s*\$\s+(?:and|or)\s+\$\s*[+-]?[01]\s*\$", sentence, re.I):
            for piece in re.findall(r"\$([^$]{1,60})\$", sentence):
                for name in _names_in(piece):
                    out.setdefault(name, []).append((" ".join(sentence.split())[:60], None))
    return out