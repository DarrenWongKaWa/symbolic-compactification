"""Two readers for every LaTeX quote: a quote counts as read only when both agree.

Reader A is ours (``latex.latex_to_plain`` + ``fidelity.translate``). Reader B
is SymPy's own LaTeX parser (``sympy.parsing.latex``, ANTLR backend), which was
written independently of A. Each reads the same macro-expanded quote into an
expression; the quote is accepted only when the two expressions are equal.
When they differ, or B cannot read the quote, the quote is refused
(``READERS_DISAGREE``, ``SECOND_READER_FAILED``): the step it belongs to is
then not decided, never decided on a misreading.

What B is told in advance is limited to conventions, never structure:

- layout is dropped (``\\left``/``\\right`` sizes, spacing, ``\\label``, ``&``);
- a *name* -- a letter or Greek letter with subscripts, primes, accents or a
  label superscript (``\\Gamma_L``, ``v_{12}^a``, ``\\tilde G^r``, ``\\mathcal T``,
  ``\\mathrm{Tr}``) -- is one symbol. B receives a placeholder for it, named
  by A's reading of that name alone. A name that A reads differently inside
  the quote makes the two readings differ, and the quote is refused;
- a subscript written after a superscript is given to B first: TeX reads
  ``X^{s}_{t}`` as ``X_{t}^{s}``, and B would drop it;
- after B, its tree follows A's documented conventions: ``i`` is the imaginary
  unit (unless declared), ``e^{x}`` is the exponential but ``e^2`` the charge
  squared, a capital ``E``/``I`` is a quantity, and a name declared a product
  (``multiply:``) multiplies the bracket after it.

Structure -- fraction bars, the reach of a power or a function, brackets,
implicit products, derivatives -- is read by each reader on its own, and that
is what the comparison tests.
"""
from __future__ import annotations

import functools
import re
from typing import Iterable

import sympy

from ..models import AdapterError

READERS_DISAGREE = "READERS_DISAGREE"
SECOND_READER_FAILED = "SECOND_READER_FAILED"
SECOND_READER_UNAVAILABLE = "SECOND_READER_UNAVAILABLE"

_PLACEHOLDER = "Z_{%d}"
_PLACEHOLDER_BASE = 900001

# Greek letters and the few other commands that are a name on their own
_NAME_COMMANDS = frozenset((
    "alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu xi "
    "pi rho varrho sigma tau upsilon phi varphi chi psi omega Gamma Delta Theta Lambda Xi Pi Sigma "
    "Upsilon Phi Psi Omega hbar ell").split())
_ACCENT_COMMANDS = ("tilde", "widetilde", "hat", "widehat", "dot", "ddot", "check", "breve",
                    "mathcal", "mathscr", "mathfrak", "mathsf")
_WORD_COMMANDS = ("mathrm", "text", "textrm", "textit", "mbox", "operatorname", "mathit", "rm",
                  "mathbf", "boldsymbol", "bm")
_PART_COMMANDS = ("Re", "Im")               # real and imaginary part: A reads re_of / im_of
_OLD_FONTS = ("cal", "rm", "it", "sf", "bf", "bm")

_GROUP = r"\{(?:[^{}]|\{[^{}]*\})*\}"
_BASE = (
    r"\\(?:" + "|".join(_ACCENT_COMMANDS) + r")\s*(?:" + _GROUP + r"|\\[A-Za-z]+|[A-Za-z])"
    r"|\\(?:" + "|".join(_WORD_COMMANDS) + r")\s*\{\s*[A-Za-z]+\s*\}"
    r"|\{\s*\\(?:" + "|".join(_OLD_FONTS) + r")\s+[A-Za-z]+\s*\}"
    r"|\\(?:" + "|".join(_PART_COMMANDS) + r")(?![A-Za-z])"
    r"|\\(?:" + "|".join(sorted(_NAME_COMMANDS, key=len, reverse=True)) + r")(?![A-Za-z])"
    r"|[A-Za-z]")                          # in math mode every letter is a symbol of its own
_WORD_SCRIPT = r"\\(?:" + "|".join(_WORD_COMMANDS) + r")\s*" + _GROUP   # x_\text{eff}: the command with its group
_DECORATION = r"(?:\s*_\s*(?:" + _GROUP + "|" + _WORD_SCRIPT + r"|\\[A-Za-z]+|[A-Za-z0-9+\-<>])|\s*\^\s*(?:" + _GROUP + \
    "|" + _WORD_SCRIPT + r"|\\[A-Za-z]+|[A-Za-z0-9<>*])|\s*'+)"
_ATOM = re.compile(r"(" + _BASE + r")(" + _DECORATION + r"*)")    # anchored: .match(text, i)
_ONE_DECORATION = re.compile(_DECORATION)
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_ALIASES = {"varepsilon": "epsilon", "vartheta": "theta", "varphi": "phi", "varrho": "rho",
            "lambda": "lamda", "ell": "l"}


def available() -> bool:
    """SymPy's LaTeX grammar runs only on the 4.11 ANTLR runtime."""
    from importlib.metadata import PackageNotFoundError, version
    try:
        import antlr4  # noqa: F401
        return version("antlr4-python3-runtime").startswith("4.11")
    except (ImportError, PackageNotFoundError):
        return False


def _a_name(atom: str, branch: str | None, keep_i: bool) -> str | None:
    """Reader A's identifier for a name read on its own, or None."""
    from .fidelity import _pick_branch, translate
    from .latex import latex_to_plain
    try:
        plain = _pick_branch(latex_to_plain(atom), branch)
        text = translate(plain, {}, (), keep_i, (), multiply=None)
    except (AdapterError, ValueError):
        return None
    return text if _IDENTIFIER.fullmatch(text) else None


def _shrink(base: str, decorations: str, branch: str | None, keep_i: bool) -> tuple[str, str, str] | None:
    """The longest prefix of the decorations that A reads as part of one name:
    (atom, A's name, decorations left in the text)."""
    parts = [m.group(0) for m in _ONE_DECORATION.finditer(decorations)]
    for k in range(len(parts), -1, -1):
        atom = base + "".join(parts[:k])
        name = _a_name(atom, branch, keep_i)
        if name is not None:
            return atom, name, "".join(parts[k:])
    return None


def _subscript_first(decorations: str) -> str | None:
    """The decorations with a subscript written right after a superscript moved
    before it; None when there is none. TeX gives both scripts of X^{2}_{a} to X,
    as in X_{a}^{2}; SymPy drops or misplaces such a subscript (x^2_a -> x**2)."""
    parts = [m.group(0) for m in _ONE_DECORATION.finditer(decorations)]
    if "".join(parts) != decorations:
        return None
    for k in range(len(parts) - 1):
        if parts[k].lstrip().startswith("^") and parts[k + 1].lstrip().startswith("_"):
            return "".join(parts[:k] + [parts[k + 1], parts[k]] + parts[k + 2:])
    return None


def _layout_free(text: str) -> str:
    text = re.sub(r"\\label\s*\{[^{}]*\}|\\(?:nonumber|notag|displaystyle|textstyle|scriptstyle|nn)(?![A-Za-z])",
                  " ", text)
    text = re.sub(r"\\(?:left|right)\s*\.", " ", text)
    text = re.sub(r"\\(?:left|right|bigg|Bigg|big|Big)[lrm]?(?![A-Za-z])", "", text)
    text = re.sub(r"\\[lr]?vert(?![A-Za-z])", "|", text)
    text = re.sub(r"\\(?:dfrac|tfrac)(?![A-Za-z])", r"\\frac", text)
    text = re.sub(r"\\[,;:!> ]|\\q?quad(?![A-Za-z])|~|&|\\\\", " ", text)
    return text


def _with_placeholders(text: str, branch: str | None, keep_i: bool) -> tuple[str, dict[str, str]]:
    """The quote with every decorated name replaced by a placeholder symbol, and
    {placeholder: A's name}. Other commands (\\frac, \\sum, \\partial) are copied
    whole, so their letters are never taken for names."""
    names: dict[str, str] = {}
    out: list[str] = []
    i = 0
    while i < len(text):
        m = _ATOM.match(text, i)
        if m is None:
            command = re.match(r"\\(?:[A-Za-z]+|.)", text[i:], re.S)
            step = command.end() if command else 1
            out.append(text[i:i + step])
            i += step
            continue
        base, decorations = m.group(1), m.group(2)
        found = _shrink(base, decorations, branch, keep_i) if decorations.strip() or base.startswith(("\\", "{")) \
            else (base, base, "")
        if found is None:
            raise AdapterError(f"{SECOND_READER_FAILED}:name {m.group(0).strip()[:40]}")
        atom, name, rest = found
        reordered = _subscript_first(rest)
        if reordered is not None:          # read the name again, its subscript now first
            start = m.start() + len(atom)
            text = text[:start] + reordered + text[start + len(rest):]
            continue
        if re.fullmatch(r"[A-Za-z]", atom) or (atom.startswith("\\") and atom[1:] in _NAME_COMMANDS):
            out.append(atom)               # nothing to hide: B reads it as A does
        else:
            key = _PLACEHOLDER % (_PLACEHOLDER_BASE + len(names))
            names[key.replace("{", "").replace("}", "")] = name
            out.append(f" {key} ")
        i = m.start() + len(atom)          # the rest (a power, an exponent group) is read on
    return "".join(out), names


_BARE_FUNCTION_FRAC = re.compile(
    r"(\\(?:sin|cos|tan|cot|sinh|cosh|tanh|coth|ln|log|exp))\s*(\\frac\s*" + _GROUP + r"\s*" + _GROUP
    + r")(?=\s*(?:$|[-+=,;)\]]|\\(?:sin|cos|tan|cot|sinh|cosh|tanh|coth|ln|log|exp)(?![A-Za-z])))")


_BARE_FUNCTION_SYMBOL = re.compile(
    r"(\\(?:sin|cos|tan|cot|sinh|cosh|tanh|coth|ln|log|exp))\s*(\\(?:"
    + "|".join(sorted(_NAME_COMMANDS, key=len, reverse=True)) + r")(?![A-Za-z])|[A-Za-z])"
    r"(?=\s*(?:$|[-+=,;)\]]))")


def _brace_end(text: str, i: int) -> int | None:
    """Index after the brace group opening at text[i], at any depth."""
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{" and (j == 0 or text[j - 1] != "\\"):
            depth += 1
        elif text[j] == "}" and (j == 0 or text[j - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return j + 1
    return None


def _exponentials(text: str) -> str:
    """e^{x} -> \\exp({x}) at any brace depth; e^2 (a plain number) stays a power."""
    out, i = [], 0
    for m in re.finditer(r"(?<![A-Za-z\\])e\s*\^\s*", text):
        if m.start() < i:
            continue
        j = m.end()
        if j < len(text) and text[j] == "{":
            end = _brace_end(text, j)
            if end is None:
                continue
        else:
            token = re.match(r"\\[A-Za-z]+|[A-Za-z0-9]", text[j:])
            if token is None:
                continue
            end = j + token.end()
        power = text[j:end]
        if re.fullmatch(r"\{?\s*\d+\s*\}?", power):
            continue
        out.append(text[i:m.start()] + f"\\exp({power})")
        i = end
    out.append(text[i:])
    return "".join(out)


def _conventions(text: str) -> str:
    """A's documented conventions, written out for B: e^{x} is the exponential
    (e^2, a plain number, is the charge squared); {a \\over b} is a fraction;
    \\coth\\frac{x}{2} or \\coth\\tau with nothing after it is coth of that."""
    text = _exponentials(text)
    text = _BARE_FUNCTION_FRAC.sub(r"\1(\2)", text)
    text = _BARE_FUNCTION_SYMBOL.sub(r"\1(\2)", text)
    return _over_to_frac(text)


def _over_to_frac(text: str) -> str:
    """{A \\over B} -> {\\frac{A}{B}}, innermost group first."""
    for _ in range(16):
        m = re.search(r"\{((?:[^{}]|\{[^{}]*\})*?)\\over(?![A-Za-z])((?:[^{}]|\{[^{}]*\})*)\}", text)
        if m is None:
            return text
        text = text[:m.start()] + "{\\frac{" + m.group(1) + "}{" + m.group(2) + "}}" + text[m.end():]
    return text


_SUM_PM = re.compile(r"\\sum(?:\\limits)?\s*_\s*(?:\{\s*\\pm\s*\}|\\pm(?![A-Za-z]))\s*")


def _next_factor(text: str, i: int) -> int | None:
    """End of a bracket group or a \\frac{..}{..} starting at text[i]."""
    m = re.match(r"\\frac\s*(" + _GROUP + r")\s*(" + _GROUP + r")", text[i:])
    if m:
        return i + m.end()
    if i < len(text) and text[i] in "([":
        depth = 0
        for j in range(i, len(text)):
            depth += text[j] in "(["
            depth -= text[j] in ")]"
            if depth == 0:
                return j + 1
    return None


def _expand_sum_pm(text: str) -> str:
    """\\sum_{\\pm} X -> (X at +) + (X at -): the documented 'both signs' sum.
    X must be one bracket group or one fraction, as for reader A."""
    for _ in range(8):
        m = _SUM_PM.search(text)
        if m is None:
            return text
        end = _next_factor(text, m.end())
        if end is None:
            raise AdapterError(f"{SECOND_READER_FAILED}:sum over both signs needs a group")
        term = text[m.end():end]
        text = (text[:m.start()] + f"(({_pick_sign(term, '+')}) + ({_pick_sign(term, '-')}))"
                + text[end:])
    return text


_SUM = re.compile(r"\\sum\s*(?:\\limits\s*)?_\s*(" + _GROUP + r"|[A-Za-z])(?:\s*\^\s*(" + _GROUP
                  + r"|\\[A-Za-z]+|[A-Za-z0-9]))?")


def _sum_ranges(text: str, branch: str | None, keep_i: bool) -> tuple[str, dict[str, str]]:
    """A sum written without limits (\\sum_n, \\sum_{n=0}) gets placeholder limits
    named as A names them (sumlo_n, sumhi_n): SymPy needs both limits, and
    both sides of a step share them. The summand is still read by SymPy."""
    names: dict[str, str] = {}

    def placeholder(name: str) -> str:
        key = _PLACEHOLDER % (800001 + len(names))
        names[key.replace("{", "").replace("}", "")] = name
        return key

    def explicit(m):
        sub = m.group(1)[1:-1] if m.group(1).startswith("{") else m.group(1)
        spec = re.fullmatch(r"\s*([A-Za-z]|\\[A-Za-z]+)\s*(?:=\s*(\S.*?))?\s*", sub, re.S)
        if spec is None:
            return m.group(0)                      # \sum_{n,m}: A refuses it, so does B
        index = _a_name(spec.group(1), branch, keep_i) or spec.group(1)
        lower = spec.group(2) if spec.group(2) else placeholder(f"sumlo_{index}")
        upper = m.group(2)[1:-1] if (m.group(2) or "").startswith("{") else m.group(2)
        upper = upper if upper else placeholder(f"sumhi_{index}")
        return f"\\sum_{{{spec.group(1)}={lower}}}^{{{upper}}}"
    return _SUM.sub(explicit, text), names


def _pick_sign(text: str, branch: str | None) -> str:
    if branch is None:
        return text
    plus, minus = ("+", "-") if branch == "+" else ("-", "+")
    text = re.sub(r"\\pm(?![A-Za-z])|±", f" {plus} ", text)
    return re.sub(r"\\mp(?![A-Za-z])|∓", f" {minus} ", text)


@functools.lru_cache(maxsize=4096)
def _read_b(text: str, branch: str | None, keep_i: bool) -> tuple[sympy.Expr, tuple[tuple[str, str], ...]]:
    if not available():
        raise AdapterError(SECOND_READER_UNAVAILABLE)
    from sympy.parsing.latex import parse_latex
    if "Z_{9000" in text:
        raise AdapterError(f"{SECOND_READER_FAILED}:placeholder in the source")
    prepared, names = _with_placeholders(_conventions(_pick_sign(_expand_sum_pm(_layout_free(text)), branch)),
                                         branch, keep_i)
    prepared, ranges = _sum_ranges(prepared, branch, keep_i)
    names.update(ranges)
    try:
        expr = parse_latex(prepared.strip().rstrip(",.;"), strict=True, backend="antlr")
    except Exception as exc:                          # the parser raises several kinds
        raise AdapterError(f"{SECOND_READER_FAILED}:{type(exc).__name__}") from None
    if not isinstance(expr, sympy.Expr):
        raise AdapterError(f"{SECOND_READER_FAILED}:not an expression")
    return expr, tuple(sorted(names.items()))


_CONSTANTS = {"I": sympy.I, "pi": sympy.pi, "E": sympy.E, "oo": sympy.oo}


def _symbol_name(raw: str, names: dict[str, str], keep_i: bool):
    key = raw.replace("{", "").replace("}", "")
    if key in names:                        # \\mathrm{i} is A's I: the constant, not a symbol
        return _CONSTANTS.get(names[key]) or sympy.Symbol(names[key])
    if raw == "i" and not keep_i:
        return sympy.I
    if raw == "pi":
        return sympy.pi
    if raw in ("E", "I"):
        return sympy.Symbol(raw + "sym")          # a capital E or I is a quantity in A
    return sympy.Symbol(_ALIASES.get(raw, raw))


_PARTS = {"re_of": sympy.re, "im_of": sympy.im}


def _apply(name: str, args: list, callables: set[str], exponent=None):
    """name(args) as A reads it: a call when the name is callable, else a product."""
    from ..parser import _ALLOWED_FUNCTIONS
    if name in _PARTS and len(args) == 1:         # Re(...) / Im(...) of the bracket after it
        part = _PARTS[name](args[0])
        return part if exponent is None else part ** exponent
    if name in _ALLOWED_FUNCTIONS and isinstance(getattr(sympy, name, None), sympy.FunctionClass):
        call = getattr(sympy, name)(*args)          # B leaves \coth(x) an undefined coth
        return call if exponent is None else call ** exponent
    if name in callables:
        call = sympy.Function(name)(*args)
        return call if exponent is None else call ** exponent
    if len(args) != 1:
        raise AdapterError(f"{READERS_DISAGREE}:{name} takes {len(args)} arguments")
    factor = sympy.Symbol(name)
    return factor * (args[0] if exponent is None else args[0] ** exponent)


def _normalize(expr, names: dict[str, str], callables: set[str], keep_i: bool):
    from sympy.core.function import AppliedUndef

    def _call(node, exponent=None):
        head = walk(sympy.Symbol(node.func.__name__))
        args = [walk(a) for a in node.args]
        if not isinstance(head, sympy.Symbol):        # i(x), pi(x): a constant times the bracket
            if len(args) != 1:
                raise AdapterError(f"{READERS_DISAGREE}:{head} takes {len(args)} arguments")
            return head * (args[0] if exponent is None else args[0] ** exponent)
        return _apply(head.name, args, callables, exponent)

    def walk(node):
        if isinstance(node, sympy.Symbol):
            return _symbol_name(node.name, names, keep_i)
        if isinstance(node, sympy.Float):
            return sympy.nsimplify(node, rational=True)
        if isinstance(node, sympy.Pow):
            base, exponent = node.args
            if isinstance(base, AppliedUndef):
                return _call(base, walk(exponent))
            base, exponent = walk(base), walk(exponent)
            if base.is_Integer and exponent.is_Integer and _too_many_digits(int(base), int(exponent)):
                raise AdapterError("QUOTE_NUMBER_TOO_LARGE")    # never evaluate 2**(3**20)
            return sympy.Pow(base, exponent)
        if isinstance(node, AppliedUndef):
            return _call(node)
        if isinstance(node, sympy.log) and len(node.args) == 2 and node.args[1] == sympy.E:
            return sympy.log(walk(node.args[0]))
        if isinstance(node, sympy.Derivative):     # conventions first, then differentiate
            return sympy.diff(walk(node.expr), *[(walk(v), int(c)) for v, c in node.variable_count])
        if isinstance(node, sympy.Mul):
            factors = [walk(a) for a in node.args]
            parts = [f for f in factors if isinstance(f, sympy.Symbol) and f.name in _PARTS]
            rest = [f for f in factors if f not in parts]
            others = [f for f in rest if not f.is_number]
            if len(parts) == 1 and len(others) == 1:
                # Re X with one factor after it: the only possible reading of the product
                return sympy.Mul(*[f for f in rest if f.is_number]) * _PARTS[parts[0].name](others[0])
            return sympy.Mul(*factors)
        if node.args:
            return node.func(*[walk(a) for a in node.args])
        return node
    return walk(expr)


def _plain(expr: sympy.Expr) -> sympy.Expr:
    """Every symbol as a plain complex symbol of the same name: the comparison is
    about the reading, not about what the paper assumes of the symbols."""
    return expr.xreplace({s: sympy.Symbol(s.name) for s in expr.atoms(sympy.Symbol)})   # bound indices too


_BIG_INTEGER = re.compile(r"\d{257,}")
_NUMBER_POWER = re.compile(r"(\d+)\s*\^\s*\{?\s*(-?)\s*(\d+)")
_NESTED_NUMBER_POWER = re.compile(r"\d\s*\^\s*\{[^{}]*\^")
_MAX_DIGITS = 5_000_000                    # 10^{100000} is computed; 2^{99999999999} is not


def _too_many_digits(base: int, exponent: int) -> bool:
    import math
    return abs(base) > 1 and abs(exponent) * math.log10(abs(base)) > _MAX_DIGITS


def check_size(tex: str) -> None:
    """Refuse a number no reader can compute in reasonable time, before either
    evaluates anything: a 257-digit integer (the parser's own limit), a power of a
    number with more than five million digits (2^{99999999999}), or a power of a
    number whose exponent is itself a power (2^{3^{20}})."""
    if _BIG_INTEGER.search(tex) or _NESTED_NUMBER_POWER.search(tex):
        raise AdapterError("QUOTE_NUMBER_TOO_LARGE")
    for m in _NUMBER_POWER.finditer(tex):
        if len(m.group(3)) > 12 or _too_many_digits(int(m.group(1)), int(m.group(3))):
            raise AdapterError("QUOTE_NUMBER_TOO_LARGE")


def _expansion_size(expr: sympy.Expr) -> float:
    """A rough count of the terms that expand() would produce."""
    if expr.is_Atom:
        return 1.0
    if isinstance(expr, sympy.Pow) and isinstance(expr.base, sympy.Add) and expr.exp.is_Integer:
        return float(len(expr.base.args)) ** min(abs(int(expr.exp)), 64)
    sizes = [_expansion_size(a) for a in expr.args]
    if isinstance(expr, sympy.Mul):
        total = 1.0
        for size in sizes:
            total *= size
        return total
    return float(sum(sizes))


def _difference_is_zero(a: sympy.Expr, b: sympy.Expr) -> bool:
    difference = sympy.expand(a - b)
    if difference == 0:
        return True
    if sympy.count_ops(difference) > 400:
        return False
    try:
        return sympy.cancel(sympy.together(difference)) == 0
    except (sympy.PolynomialError, TypeError, ValueError):
        return False


def _expand_summands(expr: sympy.Expr) -> sympy.Expr:
    return expr.replace(lambda e: isinstance(e, sympy.Sum),
                        lambda e: sympy.Sum(sympy.expand(e.function), *e.limits))


def _equal(a: sympy.Expr, b: sympy.Expr) -> bool:
    if a == b:                             # also oo == oo, where oo - oo is nan
        return True
    if a.has(sympy.Sum) or b.has(sympy.Sum):
        a, b = _expand_summands(a), _expand_summands(b)
        if a == b:
            return True
    if _expansion_size(a) + _expansion_size(b) <= 20000:
        return _difference_is_zero(a, b)
    from ..budgets import BudgetExceeded, run_symbolic_operation
    try:                                   # a large expansion runs under the engine's budget
        return bool(run_symbolic_operation("expand", _difference_is_zero, (a, b)))
    except (BudgetExceeded, AdapterError):
        return False


def _short(expr: sympy.Expr, size: int) -> str:
    try:
        return str(expr)[:size]
    except ValueError:                     # an integer too long to print
        return "<too long to print>"


def require_agreement(tex: str, reading_a: sympy.Expr, *, macros: dict, callables: Iterable[str],
                      keep_i: bool, branch: str | None = None) -> dict:
    """Raise unless SymPy's reading of ``tex`` equals ``reading_a``.

    ``reading_a`` is A's expression before the card's notation is applied;
    ``callables`` are the names A reads as functions."""
    from .latex import expand_macros
    text = expand_macros(tex, macros or {})
    check_size(text)
    expr, names = _read_b(text, branch, keep_i)
    reading_b = _normalize(expr, dict(names), set(callables), keep_i)
    a, b = _plain(reading_a), _plain(reading_b)
    only_a = sorted(str(s) for s in a.free_symbols - b.free_symbols)
    only_b = sorted(str(s) for s in b.free_symbols - a.free_symbols)
    if only_a or only_b:
        raise AdapterError(f"{READERS_DISAGREE}:symbols {','.join(only_a[:3])} | {','.join(only_b[:3])}")
    if not _equal(a, b):
        raise AdapterError(f"{READERS_DISAGREE}:{_short(a, 60)} | {_short(b, 60)}")
    return {"reader_b": _short(b, 400)}
