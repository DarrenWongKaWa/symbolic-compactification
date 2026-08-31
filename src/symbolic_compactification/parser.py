"""Strict whitelist SymPy parser with an isolated construction namespace.

Validation ladder (first failure wins):
  1. non-string / blank                          -> EMPTY_EXPRESSION
  2. length over policy max_expr_chars           -> EXPRESSION_TOO_LARGE
  3. token/depth/literal source bound exceeded   -> EXPRESSION_TOO_LARGE
  4. character outside the token grammar         -> DISALLOWED_CHARACTERS
  5. identifier not in declared_symbols ∪
     allowed_functions ∪ constants               -> UNDECLARED_OR_DISALLOWED_NAME
  6. construction under isolated locals/globals  -> SYMBOLIC_PARSE_FAILED
  7. count_ops(expr) over policy max_nodes       -> EXPRESSION_TOO_LARGE

The construction namespace contains only safe SymPy constructors, declared
Symbol/Function objects, whitelisted functions, structural builtins, and
constants. Python builtins are empty. ``^`` is converted to power.

Symbol namespace policy
------------------------------
Three DISTINCT namespaces exist and are never merged implicitly:

  1. DECLARED SYMBOLS   - the ``symbols`` declaration list
  2. DECLARED FUNCTIONS - the optional ``functions`` declaration (a
     symbols.json ``"functions"`` key, or ``parse_expression(functions=...)``)
  3. BUILT-INS          - the allowed-functions whitelist, the structural
     builtins (Sum/Piecewise/relations/logic) and the constants pi/E/I/oo

Documented precedence: EXPLICIT DECLARATION BEATS BUILT-IN. A declared
function name is bound to ``sympy.Function(name)`` AFTER the built-ins, so
an explicit declaration shadows a built-in of the same name (the engine
never silently prefers a built-in over an explicit declaration). The
reserved-name rejection is the guard for the UNDECLARED direction: names
that collide with built-ins may never be declared as SYMBOLS
(``SYMBOL_NAME_RESERVED``), and function names may never collide with
declared symbols (``FUNCTION_NAME_COLLIDES_WITH_SYMBOL``) or with reserved
constants/structural builtins (``FUNCTION_NAME_RESERVED``).
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Optional

import sympy
from sympy.parsing.sympy_parser import (
    convert_xor,
    parse_expr,
    standard_transformations,
)

from .models import (AdapterError, ExpressionRecord, HARD_RESERVED_NAMES,
                     normalize_symbols)

# --------------------------------------------------------------------------- #
# parse policy (module-level defaults, overridable per-call or via setter)
# --------------------------------------------------------------------------- #

_ALLOWED_FUNCTIONS = sorted([
    "sin", "cos", "tan", "exp", "log", "sqrt", "Abs", "conjugate", "re", "im",
    "sinh", "cosh", "tanh", "asin", "acos", "atan", "atan2", "Rational",
    # polygamma family: admitted deliberately as part of the explicit
    # allowed-functions policy; admission is a policy decision, never
    # an implicit side effect of ingestion.
    "polygamma",
])

_DEFAULT_POLICY: dict = {
    # raised from the historical 4000-char limit so ~20-30KB expressions can
    # be ingested; still bounded, and the node cap below bounds parsed size
    "max_expr_chars": 65536,
    # raised from 4000 together with max_expr_chars; limits are POLICY —
    # reviewed, named and tunable here, never silently edited constants
    "max_nodes": 8000,          # enforced via count_ops cap after parsing
    # source-shape caps are enforced BEFORE SymPy construction.  They stop
    # deeply nested or auto-collapsing input from doing unbounded parser work
    # before the post-parse count_ops limit can see it.
    "max_tokens": 16000,
    "max_nesting_depth": 256,
    "max_integer_digits": 256,
    "max_numeric_exponent": 10000,
    "max_symbols": 40,
    "allowed_functions": list(_ALLOWED_FUNCTIONS),
}

# module-level view exposed for inspection/tests; mutate via set_parse_policy()
PARSE_POLICY: dict = dict(_DEFAULT_POLICY)

_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# ``<`` and ``>`` are admitted so relational conditions of preserved
# structure (``n > 1``) round-trip. ``&`` / ``|`` round-trip SymPy's infix
# And/Or on relational conditions (``Eq(n, m) & Eq(m, ell)``). Assignment-like
# ``=`` stays OUT (relational Ge/Le render with ``=`` and therefore must be
# expressed via the functional forms Ge(...) / Le(...) or rewritten).
_TOKEN_RE = re.compile(
    r"\s+|(?:\d+(?:\.\d*)?|\.\d+)|[A-Za-z_][A-Za-z0-9_]*|"
    r"\*\*|[+\-*/^(),<>&|]")

_SAFE_GLOBALS = {
    "__builtins__": {},
    # parse_expr(evaluate=False) emits these constructors.  They are not
    # reachable by source identifiers unless separately whitelisted.
    "Symbol": sympy.Symbol,
    "Integer": sympy.Integer,
    "Float": sympy.Float,
    "Rational": sympy.Rational,
    "Add": sympy.Add,
    "Mul": sympy.Mul,
    "Pow": sympy.Pow,
}
_TRANSFORMATIONS = standard_transformations + (convert_xor,)


def get_parse_policy() -> dict:
    """Return a fresh copy of the current default policy."""
    policy = dict(PARSE_POLICY)
    policy["allowed_functions"] = list(PARSE_POLICY["allowed_functions"])
    return policy


def set_parse_policy(**overrides) -> dict:
    """Update module-level defaults (tests only). Unknown keys are rejected."""
    unknown = set(overrides) - set(_DEFAULT_POLICY)
    if unknown:
        raise AdapterError("PARSE_POLICY_KEY_UNKNOWN")
    previous = get_parse_policy()
    PARSE_POLICY.update(overrides)
    try:
        _effective_policy(None)
    except AdapterError:
        PARSE_POLICY.clear()
        PARSE_POLICY.update(previous)
        raise
    return get_parse_policy()


def _effective_policy(policy: Optional[dict]) -> dict:
    merged = get_parse_policy()
    if policy:
        unknown = set(policy) - set(_DEFAULT_POLICY)
        if unknown:
            raise AdapterError("PARSE_POLICY_KEY_UNKNOWN")
        merged.update(policy)
    for key in ("max_expr_chars", "max_nodes", "max_tokens",
                "max_nesting_depth", "max_integer_digits",
                "max_numeric_exponent", "max_symbols"):
        if (not isinstance(merged[key], int) or isinstance(merged[key], bool)
                or merged[key] <= 0):
            raise AdapterError("PARSE_POLICY_VALUE_INVALID")
    allowed = merged["allowed_functions"]
    if not isinstance(allowed, (list, tuple)) or not all(
            isinstance(name, str) and _IDENTIFIER_RE.fullmatch(name)
            and callable(getattr(sympy, name, None)) for name in allowed):
        raise AdapterError("PARSE_POLICY_VALUE_INVALID")
    merged["allowed_functions"] = sorted(set(allowed))
    return merged


# --------------------------------------------------------------------------- #
# structural builtins: Sum / Product / Piecewise / relations / logic
# --------------------------------------------------------------------------- #
# These names round-trip the structure-preserving representations produced by
# the adapters (symbolic ``Sum``, ``Piecewise``, relational/logical
# conditions). They are admitted as CALLABLES only — never as declared symbol
# names — so the whitelist stays closed while structure survives parsing.
def _piecewise_preserved(*branches):
    """Construct Piecewise without discarding or merging ordered branches."""
    return sympy.Piecewise(*branches, evaluate=False)


def _is_boolean_expr(expr) -> bool:
    """True when ``expr`` is a relational/boolean, not an integer bitmask."""
    if expr in (sympy.S.true, sympy.S.false, True, False):
        return True
    return isinstance(expr, (
        sympy.core.relational.Relational,
        sympy.logic.boolalg.BooleanAtom,
        sympy.logic.boolalg.BooleanFunction,
    ))


def _strict_and(*args):
    if not args or not all(_is_boolean_expr(a) for a in args):
        raise TypeError("non-boolean And")
    return sympy.And(*args)


def _strict_or(*args):
    if not args or not all(_is_boolean_expr(a) for a in args):
        raise TypeError("non-boolean Or")
    return sympy.Or(*args)


_STRUCTURAL_BUILTINS: dict = {
    "Sum": sympy.Sum,
    "Product": sympy.Product,
    "diff": sympy.diff,
    "Piecewise": _piecewise_preserved,
    "Eq": sympy.Eq,
    "Ne": sympy.Ne,
    "Lt": sympy.Lt,
    "Le": sympy.Le,
    "Gt": sympy.Gt,
    "Ge": sympy.Ge,
    "And": _strict_and,
    "Or": _strict_or,
    "Not": sympy.Not,
    "True": sympy.S.true,
    "False": sympy.S.false,
}


# --------------------------------------------------------------------------- #
# symbol object helpers
# --------------------------------------------------------------------------- #

def _symbol_locals(symbols: list[dict], policy: dict,
                   functions: Optional[list] = None) -> dict:
    """Restricted locals map: declared symbols + whitelisted functions + consts.

    NOTHING else is reachable from sympify, so arbitrary attribute access /
    code execution through the expression string is impossible.

    ``functions`` are declared undefined-function names (indexed calls such as
    ``f(n)``); each is bound to ``sympy.Function(name)`` so structure survives.
    """
    local: dict = {}
    for f in policy["allowed_functions"]:
        local[f] = getattr(sympy, f, None)
    local.update({"pi": sympy.pi, "E": sympy.E, "I": sympy.I, "oo": sympy.oo})
    # structure-preserving builtins (callables + relational/logical helpers)
    local.update(_STRUCTURAL_BUILTINS)
    # DECLARED SYMBOLS are bound AFTER the built-ins on purpose: with the
    # explicit ``allow_reserved`` opt-in, a declared symbol named like a
    # function builtin is treated as a SYMBOL (explicit declaration beats
    # built-in). Without the opt-in no declared name can ever collide, so
    # this ordering changes nothing on the default path.
    for s in symbols:
        kwargs: dict = {"real": s["real"]}
        if s.get("nonzero"):
            kwargs["nonzero"] = True
        local[s["name"]] = sympy.Symbol(s["name"], **kwargs)
    # declared undefined functions for indexed calls — bound LAST on purpose:
    # explicit declaration beats built-in, so a declared function name may
    # shadow a function builtin (never a hard-reserved constant/structural
    # builtin; those are rejected up front).
    for fname in (functions or []):
        local[fname] = sympy.Function(fname)
    return local


def normalize_functions(functions: Any,
                        declared_symbol_names=()) -> list[str]:
    """Validate and canonicalize the declared undefined-function namespace."""
    if functions is None:
        return []
    if not isinstance(functions, (list, tuple)):
        raise AdapterError("CLAIM_FUNCTIONS_MALFORMED")
    out: list[str] = []
    for fname in functions:
        if (not isinstance(fname, str) or not fname.strip()
                or not _IDENTIFIER_RE.fullmatch(fname)):
            raise AdapterError("CLAIM_FUNCTIONS_MALFORMED")
        out.append(fname)
    if len(out) != len(set(out)):
        raise AdapterError("CLAIM_FUNCTIONS_MALFORMED")
    if set(out) & set(declared_symbol_names):
        raise AdapterError("FUNCTION_NAME_COLLIDES_WITH_SYMBOL")
    if HARD_RESERVED_NAMES & set(out):
        raise AdapterError("FUNCTION_NAME_RESERVED")
    return sorted(out)


def infer_namespace(text: str) -> tuple[list[str], list[str]]:
    """Infer symbols/functions for INSPECTION ONLY, never verification.

    Unknown identifiers immediately followed by ``(`` are treated as
    undefined functions; structural builtins, allowed SymPy functions and
    constants are excluded. The result is canonical and deterministic.
    """
    if not isinstance(text, str):
        raise AdapterError("EMPTY_EXPRESSION")
    identifiers = set(_IDENTIFIER_RE.findall(text))
    builtins = (set(get_parse_policy()["allowed_functions"])
                | set(_STRUCTURAL_BUILTINS) | {"pi", "E", "I", "oo"})
    called = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", text))
    functions = sorted(called - builtins)
    symbols = sorted(identifiers - builtins - set(functions))
    return symbols, functions


def _tokenize_expr(expr_str: str) -> list[str]:
    """Split ``expr_str`` with the character-gate token regex (no spaces)."""
    tokens: list[str] = []
    pos = 0
    for match in _TOKEN_RE.finditer(expr_str):
        if match.start() != pos:
            raise AdapterError("DISALLOWED_CHARACTERS")
        token = match.group(0)
        pos = match.end()
        if token.isspace():
            continue
        tokens.append(token)
    if pos != len(expr_str):
        raise AdapterError("DISALLOWED_CHARACTERS")
    return tokens


def _matching_paren(tokens: list[str], start: int) -> int:
    depth = 0
    for index in range(start, len(tokens)):
        if tokens[index] == "(":
            depth += 1
        elif tokens[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    raise AdapterError("SYMBOLIC_PARSE_FAILED")


def _rewrite_groups(tokens: list[str]) -> list[str]:
    """Rewrite parenthesized interiors, then fold top-level ``&`` / ``|``."""
    grouped: list[str] = []
    index = 0
    while index < len(tokens):
        if tokens[index] == "(":
            end = _matching_paren(tokens, index)
            grouped.extend(
                ["("] + _rewrite_groups(tokens[index + 1:end]) + [")"])
            index = end + 1
        else:
            grouped.append(tokens[index])
            index += 1
    return _fold_logic(grouped)


def _split_top(tokens: list[str], separator: str) -> list[list[str]]:
    parts: list[list[str]] = []
    current: list[str] = []
    depth = 0
    for token in tokens:
        if token == "(":
            depth += 1
            current.append(token)
        elif token == ")":
            depth -= 1
            current.append(token)
        elif token == separator and depth == 0:
            parts.append(current)
            current = []
        else:
            current.append(token)
    parts.append(current)
    return parts


def _call_tokens(name: str, arguments: list[list[str]]) -> list[str]:
    out: list[str] = [name, "("]
    for offset, argument in enumerate(arguments):
        if not argument:
            raise AdapterError("SYMBOLIC_PARSE_FAILED")
        if offset:
            out.append(",")
        out.extend(argument)
    out.append(")")
    return out


def _fold_logic(tokens: list[str]) -> list[str]:
    comma_parts = _split_top(tokens, ",")
    if len(comma_parts) > 1:
        folded = [_fold_logic(part) for part in comma_parts]
        out: list[str] = []
        for offset, part in enumerate(folded):
            if offset:
                out.append(",")
            out.extend(part)
        return out
    or_parts = _split_top(tokens, "|")
    if len(or_parts) > 1:
        return _call_tokens("Or", [_fold_logic(part) for part in or_parts])
    and_parts = _split_top(tokens, "&")
    if len(and_parts) > 1:
        return _call_tokens("And", [_fold_logic(part) for part in and_parts])
    return tokens


def _rewrite_infix_logic(expr_str: str) -> str:
    """Turn infix ``&`` / ``|`` into ``And(...)`` / ``Or(...)`` calls.

    Prevents ``1|2`` from evaluating as integer bitwise OR during
    ``parse_expr(evaluate=True)``. Combined with strict And/Or constructors
    that reject non-boolean operands.
    """
    return "".join(_rewrite_groups(_tokenize_expr(expr_str)))


def _validate_source_shape(expr_str: str, policy: dict) -> None:
    """Tokenize the small expression grammar and enforce pre-parse bounds."""
    tokens: list[str] = []
    pos = 0
    depth = 0
    for match in _TOKEN_RE.finditer(expr_str):
        if match.start() != pos:
            raise AdapterError("DISALLOWED_CHARACTERS")
        token = match.group(0)
        pos = match.end()
        if token.isspace():
            continue
        tokens.append(token)
        if len(tokens) > policy["max_tokens"]:
            raise AdapterError("EXPRESSION_TOO_LARGE")
        if token == "(":
            depth += 1
            if depth > policy["max_nesting_depth"]:
                raise AdapterError("EXPRESSION_TOO_LARGE")
        elif token == ")":
            depth -= 1
            if depth < 0:
                raise AdapterError("SYMBOLIC_PARSE_FAILED")
    if pos != len(expr_str):
        raise AdapterError("DISALLOWED_CHARACTERS")
    if depth != 0:
        raise AdapterError("SYMBOLIC_PARSE_FAILED")
    for token in tokens:
        if token[0].isdigit() and "." not in token \
                and len(token) > policy["max_integer_digits"]:
            raise AdapterError("EXPRESSION_TOO_LARGE")
    for index, token in enumerate(tokens):
        if token != "**" or index + 1 >= len(tokens):
            continue
        sign = 1
        exponent_index = index + 1
        if tokens[exponent_index] in ("+", "-"):
            sign = -1 if tokens[exponent_index] == "-" else 1
            exponent_index += 1
        if exponent_index < len(tokens) and tokens[exponent_index].isdigit():
            exponent = sign * int(tokens[exponent_index])
            if abs(exponent) > policy["max_numeric_exponent"]:
                raise AdapterError("EXPRESSION_TOO_LARGE")


def syms_like(expr, names: list[str]) -> list:
    """Return the expression's OWN symbol objects for ``names``.

    Critical: never reconstruct ``Symbol(name)`` by name — an assumption-less
    rebuild silently fails to substitute into expressions parsed with
    assumptions (e.g. real=True) because it is a different object.
    """
    by_name = {str(s): s for s in getattr(expr, "free_symbols", set())}
    return [by_name.get(n, sympy.Symbol(n)) for n in names]


# --------------------------------------------------------------------------- #
# strict parser
# --------------------------------------------------------------------------- #

def parse_expression(expr_str: Any, symbols: Any, *,
                     functions: Any = None,
                     allow_reserved: bool = False,
                     policy: Optional[dict] = None) -> sympy.Expr:
    """Reject before parsing; parse only with a restricted whitelist locals map.

    ``symbols`` may be raw (["x"]) or normalized ([{"name": "x", ...}]); it is
    normalized here, so reserved-name / shape violations surface as AdapterError.
    ``functions`` is an optional list of declared undefined-function names
    (indexed calls such as ``f(n)``); they are bound to ``sympy.Function`` so
    structure-preserving representations round-trip. ``allow_reserved`` is the
    explicit namespace-policy opt-in letting declared symbols shadow function
    builtins (see the module docstring). Raises AdapterError on any
    violation. No unrestricted Python namespace is reachable.
    """
    pol = _effective_policy(policy)
    declared = normalize_symbols(symbols, allow_reserved=allow_reserved)
    if len(declared) > pol["max_symbols"]:
        raise AdapterError("CLAIM_SYMBOLS_TOO_MANY")

    # A declared function MAY shadow a function builtin: explicit declaration
    # beats built-in. Constants and structural builtins remain hard-reserved.
    func_names = normalize_functions(
        functions, declared_symbol_names={s["name"] for s in declared})

    if not isinstance(expr_str, str) or not expr_str.strip():
        raise AdapterError("EMPTY_EXPRESSION")
    if len(expr_str) > pol["max_expr_chars"]:
        raise AdapterError("EXPRESSION_TOO_LARGE")
    _validate_source_shape(expr_str, pol)
    if "&" in expr_str or "|" in expr_str:
        expr_str = _rewrite_infix_logic(expr_str)

    identifiers = set(_IDENTIFIER_RE.findall(expr_str))
    allowed = ({s["name"] for s in declared}
               | set(pol["allowed_functions"])
               | set(_STRUCTURAL_BUILTINS)
               | set(func_names)
               | {"pi", "E", "I", "oo"})
    if identifiers - allowed:
        raise AdapterError("UNDECLARED_OR_DISALLOWED_NAME")

    try:
        expr = parse_expr(
            expr_str,
            local_dict=_symbol_locals(declared, pol, func_names),
            global_dict=dict(_SAFE_GLOBALS),
            transformations=_TRANSFORMATIONS,
            # SymPy canonicalizes ordinary commutative arithmetic here, while
            # semantic containers (Sum/Product and the guarded Piecewise
            # constructor) remain structural. Source-shape limits above stop
            # evaluation from becoming an unbounded front-door operation.
            evaluate=True,
        )
    except (sympy.SympifyError, SyntaxError, TypeError, AttributeError,
            ValueError, RecursionError, MemoryError, OverflowError):
        raise AdapterError("SYMBOLIC_PARSE_FAILED") from None

    if sympy.count_ops(expr, visual=False) > pol["max_nodes"]:
        raise AdapterError("EXPRESSION_TOO_LARGE")
    return expr


# --------------------------------------------------------------------------- #
# file ingestion (read-only: the source file is never modified)
# --------------------------------------------------------------------------- #

def load_expression(path, symbols: Any, *,
                    functions: Any = None,
                    allow_reserved: bool = False,
                    policy: Optional[dict] = None) -> ExpressionRecord:
    """Read a .txt expression file (utf-8), hash raw bytes, parse strictly.

    The file is opened read-only and never written back. The sha256 is taken
    over the RAW file bytes (before stripping) so ingestion is auditable.
    ``functions`` / ``allow_reserved`` follow ``parse_expression`` semantics.
    """
    p = Path(path)
    try:
        raw = p.read_bytes()
    except OSError:
        raise AdapterError("EXPRESSION_SOURCE_UNREADABLE") from None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise AdapterError("EXPRESSION_SOURCE_UNREADABLE") from None

    digest = hashlib.sha256(raw).hexdigest()
    declared = normalize_symbols(symbols, allow_reserved=allow_reserved)
    func_names = normalize_functions(
        functions, declared_symbol_names={s["name"] for s in declared})
    expr = parse_expression(text.strip(), declared, functions=functions,
                            allow_reserved=allow_reserved, policy=policy)
    return ExpressionRecord(
        text=text.strip(),
        sha256=digest,
        source_path=str(p),
        parsed_expr=expr,
        symbols=declared,
        functions=func_names,
    )
