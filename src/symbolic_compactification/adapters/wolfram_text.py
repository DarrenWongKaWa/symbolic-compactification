"""Neutral Wolfram-language text ingestion adapter (translation only).

Converts Wolfram-syntax expression TEXT into SymPy expressions. There is NO
Wolfram/Mathematica runtime and no second CAS anywhere in this module: it is
a pure text-to-SymPy translation layer. Translated expressions earn no
verdict here — they still flow through the engine's strict parser and exact
verifier before certification.

Design rules
------------
* Fail-closed: every malformed input raises an ``AdapterError`` subclass with
  a stable machine-readable ``.code``. Nothing is guessed silently.
* Structure-first: structure is preserved, never silently flattened.
    - ``Sum[...]``       -> ``sympy.Sum`` with SYMBOLIC bounds
    - ``Piecewise[...]`` -> ``sympy.Piecewise`` preserving every branch and
                            condition symbolically
    - ``f[n]``, ``h[a,n,m]`` -> structural indexed calls, represented as
      ``sympy.Function('f')(n)`` (AppliedUndef). This representation was
      chosen over ``IndexedBase`` because it keeps arguments as ordinary
      SymPy expressions (substitution, free-symbol analysis and the exact
      verifier all work unchanged) while remaining visually structural.
* Fully parameterized: NOTHING workload-specific is hardcoded. Function maps,
  indexed-call handlers, flat-indexed name sets and assumption lists are all
  explicit keyword arguments (see ``translate_wolfram_text``).

Precedence ladder (mirrors the strict parser's safety philosophy):
  1. blank input                                   -> EMPTY_EXPRESSION
  2. text over policy ``max_expr_chars``           -> EXPRESSION_TOO_LARGE
  3. character outside the tokenizer's grammar     -> WOLFRAM_TOKEN_ERROR
  4. grammar violation / trailing input            -> WOLFRAM_SYNTAX_ERROR
  5. structural violation (bad Sum/Piecewise/list) -> WOLFRAM_STRUCTURE_ERROR
  6. unknown mapped function name                  -> WOLFRAM_FUNC_UNKNOWN
  7. result over policy ``max_nodes`` (count_ops)  -> EXPRESSION_TOO_LARGE
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional

import sympy

from ..models import AdapterError
from ..parser import _effective_policy

# A leading ``lhs = `` assignment prefix (single ``=``, not ``==/<=/>=/!=``).
_ASSIGNMENT_PREFIX_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\s*=(?!=)")

# --------------------------------------------------------------------------- #
# errors (stable machine-readable codes, fail-closed)
# --------------------------------------------------------------------------- #


class WolframAdapterError(AdapterError):
    """Base class for Wolfram-text adapter failures."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.detail = detail

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"{self.code}: {self.detail}" if self.detail else self.code


class WolframTokenError(WolframAdapterError):
    """A character outside the tokenizer grammar was encountered."""

    def __init__(self, detail: str = ""):
        super().__init__("WOLFRAM_TOKEN_ERROR", detail)


class WolframSyntaxError(WolframAdapterError):
    """The token stream violates the expression grammar."""

    def __init__(self, detail: str = ""):
        super().__init__("WOLFRAM_SYNTAX_ERROR", detail)


class WolframStructureError(WolframAdapterError):
    """A structurally meaningful call (Sum/Piecewise/list) is malformed."""

    def __init__(self, detail: str = ""):
        super().__init__("WOLFRAM_STRUCTURE_ERROR", detail)


class WolframFuncUnknownError(WolframAdapterError):
    """A configured function name does not resolve to a SymPy callable."""

    def __init__(self, detail: str = ""):
        super().__init__("WOLFRAM_FUNC_UNKNOWN", detail)


# --------------------------------------------------------------------------- #
# neutral defaults (generic names only; extend per-call, never in-place)
# --------------------------------------------------------------------------- #

# Wolfram function name -> SymPy name (resolved via getattr(sympy, ...)).
DEFAULT_FUNC_MAP: dict[str, str] = {
    "PolyGamma": "polygamma",
    "Sin": "sin", "Cos": "cos", "Tan": "tan",
    "Exp": "exp", "Log": "log", "Sqrt": "sqrt",
    "Abs": "Abs", "Conjugate": "conjugate", "Re": "re", "Im": "im",
    "Sinh": "sinh", "Cosh": "cosh", "Tanh": "tanh",
    "ArcSin": "asin", "ArcCos": "acos", "ArcTan": "atan",
}

# Wolfram constant identifier -> SymPy constant.
DEFAULT_CONST_MAP: dict[str, sympy.Expr] = {
    "Pi": sympy.pi,
    "I": sympy.I,
    "E": sympy.E,
    "Infinity": sympy.oo,
    "True": sympy.S.true,
    "False": sympy.S.false,
}

_TWO_CHAR_OPS = ("<=", ">=", "==", "&&", "||", "!=")


# --------------------------------------------------------------------------- #
# comments + tokenizer
# --------------------------------------------------------------------------- #

def strip_wolfram_comments(text: str) -> str:
    """Remove ``(* ... *)`` comments, handling arbitrary nesting."""
    result: list[str] = []
    depth = 0
    i = 0
    while i < len(text):
        if text[i:i + 2] == "(*":
            depth += 1
            i += 2
        elif text[i:i + 2] == "*)":
            if depth == 0:
                raise WolframSyntaxError(
                    f"unmatched comment terminator at offset {i}")
            depth -= 1
            i += 2
        elif depth == 0:
            result.append(text[i])
            i += 1
        else:
            i += 1
    if depth:
        raise WolframSyntaxError("unterminated comment")
    return "".join(result)


def tokenize(text: str) -> list[tuple[str, str]]:
    """Tokenize Wolfram expression text.

    Token kinds: ``NUM`` (integers and decimals), ``ID`` (identifiers),
    ``OP`` (single/double operators incl. ``<= >= == && || !=``, brackets,
    braces and commas). Raises ``WolframTokenError`` fail-closed on any
    character outside the grammar.
    """
    tokens: list[tuple[str, str]] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
        elif text[i:i + 2] in _TWO_CHAR_OPS:
            tokens.append(("OP", text[i:i + 2]))
            i += 2
        elif ch in "+-*/^()[]{},":
            tokens.append(("OP", ch))
            i += 1
        elif ch in "<>!":
            tokens.append(("OP", ch))
            i += 1
        elif ch.isdigit() or (ch == "." and i + 1 < n and text[i + 1].isdigit()):
            j = i
            dot = False
            while j < n and (text[j].isdigit() or (text[j] == "." and not dot)):
                if text[j] == ".":
                    dot = True
                j += 1
            tokens.append(("NUM", text[i:j]))
            i = j
        elif ch.isalpha() or ch == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            tokens.append(("ID", text[i:j]))
            i = j
        else:
            raise WolframTokenError(
                f"bad character {ch!r} at offset {i}")
    return tokens


# --------------------------------------------------------------------------- #
# recursive-descent parser -> AST tuples
# --------------------------------------------------------------------------- #
# Precedence (low to high): || , && , comparisons, +-, */, unary, ^, atoms.
# AST node shapes: ('num', s) ('id', name) ('unary', op, e)
#                  ('binop', op, l, r) ('call', name, [args]) ('list', [elems])

_COMP_OPS = ("==", "!=", "<", ">", "<=", ">=")


class _WolframParser:
    def __init__(self, tokens: list[tuple[str, str]]):
        self.tok = tokens
        self.pos = 0

    def peek(self) -> Optional[tuple[str, str]]:
        return self.tok[self.pos] if self.pos < len(self.tok) else None

    def advance(self) -> tuple[str, str]:
        t = self.tok[self.pos]
        self.pos += 1
        return t

    def expect(self, op: str) -> tuple[str, str]:
        t = self.peek()
        if t is None or t != ("OP", op):
            raise WolframSyntaxError(f"expected {op!r}, got {t!r} at pos {self.pos}")
        return self.advance()

    # ---- grammar ---- #

    def parse_expr(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.peek() == ("OP", "||"):
            self.advance()
            left = ("binop", "||", left, self.parse_and())
        return left

    def parse_and(self):
        left = self.parse_comp()
        while self.peek() == ("OP", "&&"):
            self.advance()
            left = ("binop", "&&", left, self.parse_comp())
        return left

    def parse_comp(self):
        left = self.parse_arith()
        t = self.peek()
        if t is not None and t[0] == "OP" and t[1] in _COMP_OPS:
            op = self.advance()[1]
            return ("binop", op, left, self.parse_arith())
        return left

    def parse_arith(self):
        left = self.parse_term()
        while self.peek() in (("OP", "+"), ("OP", "-")):
            op = self.advance()[1]
            left = ("binop", op, left, self.parse_term())
        return left

    def parse_term(self):
        left = self.parse_unary()
        while self.peek() in (("OP", "*"), ("OP", "/")):
            op = self.advance()[1]
            left = ("binop", op, left, self.parse_unary())
        return left

    def parse_unary(self):
        if self.peek() == ("OP", "-"):
            self.advance()
            return ("unary", "-", self.parse_unary())
        if self.peek() == ("OP", "+"):
            self.advance()
            return self.parse_unary()
        if self.peek() == ("OP", "!"):
            self.advance()
            return ("unary", "!", self.parse_unary())
        return self.parse_power()

    def parse_power(self):
        base = self.parse_atom()
        if self.peek() == ("OP", "^"):
            self.advance()
            return ("binop", "^", base, self.parse_unary())
        return base

    def parse_atom(self):
        t = self.peek()
        if t is None:
            raise WolframSyntaxError("unexpected end of input")
        if t[0] == "NUM":
            self.advance()
            return ("num", t[1])
        if t[0] == "ID":
            name = self.advance()[1]
            if self.peek() == ("OP", "["):
                self.advance()
                args = []
                if self.peek() != ("OP", "]"):
                    args.append(self.parse_expr())
                    while self.peek() == ("OP", ","):
                        self.advance()
                        args.append(self.parse_expr())
                self.expect("]")
                return ("call", name, args)
            return ("id", name)
        if t == ("OP", "("):
            self.advance()
            e = self.parse_expr()
            self.expect(")")
            return e
        if t == ("OP", "{"):
            self.advance()
            elems = []
            if self.peek() != ("OP", "}"):
                elems.append(self.parse_expr())
                while self.peek() == ("OP", ","):
                    self.advance()
                    elems.append(self.parse_expr())
            self.expect("}")
            return ("list", elems)
        raise WolframSyntaxError(f"unexpected token {t!r} at pos {self.pos}")


# --------------------------------------------------------------------------- #
# translation result
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class TranslationResult:
    """Outcome of one Wolfram-text translation.

    ``expr``      the SymPy expression (structure preserved)
    ``text``      canonical SymPy text form ``str(expr)``
    ``symbols``   normalized declarations for every FREE symbol, in the
                  engine's ``{"name","real","nonzero"}`` form
    ``functions`` sorted names used as generic/indexed function calls
                  (candidates for the parser's declared-functions namespace)
    ``bound_symbols`` sorted names bound as Sum/Product iterators (dummy
                  indices). They are NOT free symbols, but must still be
                  declared when the text is re-parsed by the strict parser.
    """

    expr: sympy.Expr
    text: str
    symbols: list[dict] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    bound_symbols: list[str] = field(default_factory=list)
    source_chars: int = 0
    finite_expansion: bool = False

    def to_dict(self) -> dict:
        return {
            "expr": self.text,
            "symbols": list(self.symbols),
            "functions": list(self.functions),
            "bound_symbols": list(self.bound_symbols),
            "source_chars": self.source_chars,
            "finite_expansion": self.finite_expansion,
        }


# --------------------------------------------------------------------------- #
# AST -> SymPy conversion (structure-preserving)
# --------------------------------------------------------------------------- #

class _Translator:
    def __init__(self, *, func_map: Mapping[str, str],
                 const_map: Mapping[str, sympy.Expr],
                 complex_symbols: frozenset,
                 real_symbols: frozenset,
                 nonzero_symbols: frozenset,
                 flat_indexed_names: frozenset,
                 indexed_handlers: Mapping[str, Callable]):
        self.func_map = dict(func_map)
        self.const_map = dict(const_map)
        self.complex_symbols = complex_symbols
        self.real_symbols = real_symbols
        self.nonzero_symbols = nonzero_symbols
        self.flat_indexed_names = flat_indexed_names
        self.indexed_handlers = dict(indexed_handlers)
        self._symbol_cache: dict[str, sympy.Symbol] = {}
        self.functions_used: set[str] = set()
        self.bound_names: set[str] = set()

    # -- symbol construction with declared assumptions ---- #

    def symbol_for(self, name: str, *, bound: bool = False) -> sympy.Symbol:
        """One Symbol object per name; explicit declarations win.

        Precedence: ``real_symbols`` forces real; otherwise membership in
        ``complex_symbols`` makes it complex; the engine default is real.
        Sum iterator (bound) variables additionally carry ``integer=True``.
        """
        if name in self._symbol_cache:
            return self._symbol_cache[name]
        real = True if name in self.real_symbols else name not in self.complex_symbols
        kwargs: dict[str, Any] = {"real": real}
        if name in self.nonzero_symbols:
            kwargs["nonzero"] = True
        if bound:
            kwargs["integer"] = True
        sym = sympy.Symbol(name, **kwargs)
        self._symbol_cache[name] = sym
        return sym

    # -- conversion ---- #

    def convert(self, node) -> sympy.Expr:
        tag = node[0]
        if tag == "num":
            v = node[1]
            return sympy.Rational(v) if "." in v else sympy.Integer(int(v))
        if tag == "id":
            name = node[1]
            if name in self.const_map:
                return self.const_map[name]
            return self.symbol_for(name)
        if tag == "unary":
            inner = self.convert(node[2])
            if node[1] == "-":
                return -inner
            if node[1] == "!":
                return sympy.Not(inner)
            return inner
        if tag == "binop":
            return self._convert_binop(node)
        if tag == "list":
            raise WolframStructureError(
                "bare list has no SymPy representation outside "
                "Sum iterators / Piecewise branches")
        if tag == "call":
            return self._convert_call(node)
        raise WolframSyntaxError(f"unknown AST node {tag!r}")

    def _convert_binop(self, node) -> sympy.Expr:
        op = node[1]
        left = self.convert(node[2])
        right = self.convert(node[3])
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            return left / right
        if op == "^":
            return left ** right
        if op == "==":
            return sympy.Eq(left, right)
        if op == "!=":
            return sympy.Ne(left, right)
        if op == "<":
            return sympy.Lt(left, right)
        if op == ">":
            return sympy.Gt(left, right)
        if op == "<=":
            return sympy.Le(left, right)
        if op == ">=":
            return sympy.Ge(left, right)
        if op == "&&":
            return sympy.And(left, right)
        if op == "||":
            return sympy.Or(left, right)
        raise WolframSyntaxError(f"unknown binary operator {op!r}")

    # -- calls ---- #

    def _convert_call(self, node) -> sympy.Expr:
        name, args = node[1], node[2]
        if name == "Sum":
            return self._convert_iterated(args, sympy.Sum, "Sum")
        if name == "Product":
            return self._convert_iterated(args, sympy.Product, "Product")
        if name == "Piecewise":
            return self._convert_piecewise(args)
        if name in self.indexed_handlers:
            return self.indexed_handlers[name]([self.convert(a) for a in args])
        if name in self.flat_indexed_names:
            return _flat_indexed_symbol(name, args, self)
        if name in self.func_map:
            target_name = self.func_map[name]
            target = getattr(sympy, target_name, None)
            if target is None or not callable(target):
                raise WolframFuncUnknownError(
                    f"{name!r} maps to unknown SymPy name {target_name!r}")
            return target(*[self.convert(a) for a in args])
        # generic / indexed function call: structural Function application
        self.functions_used.add(name)
        return sympy.Function(name)(*[self.convert(a) for a in args])

    def _convert_iterated(self, args, constructor, label: str) -> sympy.Expr:
        """Translate a structural Sum/Product without finite expansion.

        Bounds stay SYMBOLIC; no finite expansion ever happens silently.
        Two-element iterators ``{var, hi}`` use lower bound 1 (Wolfram
        convention). Infinite bounds are allowed via ``Infinity``.
        """
        if len(args) < 2:
            raise WolframStructureError(
                f"{label} needs a body and at least one iterator")
        limits = []
        for it in args[1:]:
            if it[0] != "list":
                raise WolframStructureError(
                    f"{label} iterators must be brace lists")
            elems = it[1]
            if len(elems) == 3:
                var_ast, lo_ast, hi_ast = elems
            elif len(elems) == 2:
                var_ast, hi_ast = elems
                lo_ast = ("num", "1")
            else:
                raise WolframStructureError(
                    f"{label} iterator must be {{var, lo, hi}} or {{var, hi}}")
            if var_ast[0] != "id":
                raise WolframStructureError(
                    f"{label} iterator variable must be an identifier")
            var = self.symbol_for(var_ast[1], bound=True)
            self.bound_names.add(var_ast[1])
            limits.append((var, self.convert(lo_ast), self.convert(hi_ast)))
        # Iterator symbols are installed before the body is converted, so the
        # body and limits share the exact same bound Symbol objects.
        body = self.convert(args[0])
        return constructor(body, *limits)

    def _convert_piecewise(self, args) -> sympy.Expr:
        """``Piecewise[{{e1, c1}, ...}]`` -> symbolic ``sympy.Piecewise``.

        Every branch and condition is preserved symbolically; an optional
        trailing default argument becomes the ``(default, True)`` branch.
        """
        if not args or args[0][0] != "list":
            raise WolframStructureError(
                "Piecewise expects a list of {expr, cond} branches")
        branches = []
        for br in args[0][1]:
            if br[0] != "list" or len(br[1]) != 2:
                raise WolframStructureError(
                    "each Piecewise branch must be {expr, cond}")
            expr = self.convert(br[1][0])
            cond = self.convert(br[1][1])
            branches.append((expr, cond))
        if len(args) == 2:  # trailing default value
            branches.append((self.convert(args[1]), sympy.S.true))
        elif len(args) > 2:
            raise WolframStructureError("Piecewise accepts at most one default value")
        if not branches:
            raise WolframStructureError("Piecewise needs at least one branch")
        # Branch order is semantically meaningful and must not be normalized
        # away during ingestion.
        return sympy.Piecewise(*branches, evaluate=False)


def _flat_indexed_symbol(name: str, arg_asts, translator: _Translator) -> sympy.Symbol:
    parts = []
    for a in arg_asts:
        if a[0] in ("id", "num"):
            parts.append(a[1])
        else:
            parts.append(str(translator.convert(a)))
    return sympy.Symbol(f"{name}_{'_'.join(parts)}", real=True)


# --------------------------------------------------------------------------- #
# public API
# --------------------------------------------------------------------------- #

def translate_wolfram_text(text: Any, *,
                           real_symbols=(),
                           complex_symbols=(),
                           nonzero_symbols=(),
                           func_map: Optional[Mapping[str, str]] = None,
                           const_map: Optional[Mapping[str, sympy.Expr]] = None,
                           indexed_handlers: Optional[Mapping[str, Callable]] = None,
                           flat_indexed_names=(),
                           policy: Optional[dict] = None) -> TranslationResult:
    """Translate Wolfram-syntax expression text to a SymPy expression.

    Fail-closed on any malformed input (see module docstring ladder). All
    behaviour that a one-off script might hardcode is parameterized here:

    * ``real_symbols`` / ``complex_symbols`` / ``nonzero_symbols``:
      assumption lists for discovered symbols. Engine default is real;
      ``real_symbols`` wins over ``complex_symbols``.
    * ``func_map``: Wolfram-name -> SymPy-name mapping (defaults provided;
      pass your own to extend, e.g. more special functions).
    * ``const_map``: identifier -> SymPy constant overrides.
    * ``indexed_handlers``: name -> callable([arg exprs]) -> Expr, taking
      precedence over every other indexed-call interpretation.
    * ``flat_indexed_names``: names whose calls collapse to flat symbols
      ``name_i_j`` (opt-in legacy flattening; structural Function calls are
      the default).
    * ``policy``: parse-policy overrides (``max_expr_chars``, ``max_nodes``).
    """
    if not isinstance(text, str) or not text.strip():
        raise AdapterError("EMPTY_EXPRESSION")
    pol = _effective_policy(policy)
    if len(text) > pol["max_expr_chars"]:
        raise AdapterError("EXPRESSION_TOO_LARGE")
    stripped = strip_wolfram_comments(text).strip()
    if not stripped:
        raise AdapterError("EMPTY_EXPRESSION")
    if len(stripped) > pol["max_expr_chars"]:
        raise AdapterError("EXPRESSION_TOO_LARGE")

    tokens = tokenize(stripped)
    if len(tokens) > pol["max_tokens"]:
        raise AdapterError("EXPRESSION_TOO_LARGE")
    depth = 0
    for token in tokens:
        if token in (("OP", "("), ("OP", "["), ("OP", "{")):
            depth += 1
            if depth > pol["max_nesting_depth"]:
                raise AdapterError("EXPRESSION_TOO_LARGE")
        elif token in (("OP", ")"), ("OP", "]"), ("OP", "}")):
            depth -= 1
            if depth < 0:
                raise WolframSyntaxError("unbalanced closing delimiter")
    if depth != 0:
        raise WolframSyntaxError("unbalanced delimiter")
    for kind, value in tokens:
        if (kind == "NUM" and "." not in value
                and len(value) > pol["max_integer_digits"]):
            raise AdapterError("EXPRESSION_TOO_LARGE")
    for index, token in enumerate(tokens):
        if token != ("OP", "^") or index + 1 >= len(tokens):
            continue
        exponent_index = index + 1
        if tokens[exponent_index] in (("OP", "+"), ("OP", "-")):
            exponent_index += 1
        if (exponent_index < len(tokens)
                and tokens[exponent_index][0] == "NUM"
                and "." not in tokens[exponent_index][1]
                and int(tokens[exponent_index][1])
                    > pol["max_numeric_exponent"]):
            raise AdapterError("EXPRESSION_TOO_LARGE")
    parser = _WolframParser(tokens)
    try:
        ast = parser.parse_expr()
    except RecursionError:
        raise WolframSyntaxError("nesting too deep") from None
    if parser.pos != len(tokens):
        raise WolframSyntaxError(
            f"trailing input after expression at pos {parser.pos}")

    translator = _Translator(
        func_map=func_map if func_map is not None else DEFAULT_FUNC_MAP,
        const_map=const_map if const_map is not None else DEFAULT_CONST_MAP,
        complex_symbols=frozenset(complex_symbols),
        real_symbols=frozenset(real_symbols),
        nonzero_symbols=frozenset(nonzero_symbols),
        flat_indexed_names=frozenset(flat_indexed_names),
        indexed_handlers=indexed_handlers or {},
    )
    try:
        expr = translator.convert(ast)
    except (RecursionError, MemoryError, OverflowError, ValueError):
        raise WolframStructureError("expression construction exceeded limits") \
            from None

    if sympy.count_ops(expr, visual=False) > pol["max_nodes"]:
        raise AdapterError("EXPRESSION_TOO_LARGE")

    # Symbol declarations are derived from the expression's OWN free symbols
    # so the exact Symbol objects (with assumptions) round-trip into the
    # verifier. Bound variables (Sum iterators) are not free and stay out.
    free = {str(s): s for s in getattr(expr, "free_symbols", set())}
    symbols = []
    for name in sorted(free):
        sym = free[name]
        symbols.append({
            "name": name,
            "real": sym.is_real is not False,
            "nonzero": name in translator.nonzero_symbols,
        })
    return TranslationResult(
        expr=expr,
        text=str(expr),
        symbols=symbols,
        functions=sorted(translator.functions_used),
        bound_symbols=sorted(translator.bound_names),
        source_chars=len(stripped),
    )


def extract_expression_text(raw: str) -> str:
    """Generic file-level cleanup before translation.

    Strips comments, preserves the complete multi-line expression, removes a LEADING
    ``lhs =`` assignment (a single ``=`` that is not part of ``==``,
    ``<=``, ``>=`` or ``!=``) and a trailing ``;``. Pure text handling —
    no parsing happens here.
    """
    text = strip_wolfram_comments(raw).strip()
    if not text:
        raise AdapterError("EMPTY_EXPRESSION")
    expr_text = text
    m = _ASSIGNMENT_PREFIX_RE.match(expr_text)
    if m:
        expr_text = expr_text[m.end():].strip()
    if expr_text.endswith(";"):
        expr_text = expr_text[:-1].strip()
    if not expr_text:
        raise AdapterError("EMPTY_EXPRESSION")
    return expr_text
