"""Strict whitelist SymPy parser. Fail-closed. No eval/exec anywhere.

Validation ladder (first failure wins):
  1. non-string / blank                          -> EMPTY_EXPRESSION
  2. length over policy max_expr_chars           -> EXPRESSION_TOO_LARGE
  3. character outside the global char gate      -> DISALLOWED_CHARACTERS
  4. identifier not in declared_symbols ∪
     allowed_functions ∪ constants               -> UNDECLARED_OR_DISALLOWED_NAME
  5. sympify under a restricted locals map fails -> SYMBOLIC_PARSE_FAILED
  6. count_ops(expr) over policy max_nodes       -> EXPRESSION_TOO_LARGE

The restricted locals map contains ONLY the declared Symbol objects (with
their declared assumptions), the whitelisted functions and the constants
pi/E/I/oo.  ``^`` is handled by sympify(convert_xor=True).

Symbol namespace policy (v0.2)
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

from .models import (AdapterError, ExpressionRecord, HARD_RESERVED_NAMES,
                     normalize_symbols)

# --------------------------------------------------------------------------- #
# parse policy (module-level defaults, overridable per-call or via setter)
# --------------------------------------------------------------------------- #

_ALLOWED_FUNCTIONS = sorted([
    "sin", "cos", "tan", "exp", "log", "sqrt", "Abs", "conjugate", "re", "im",
    "sinh", "cosh", "tanh", "asin", "acos", "atan", "atan2", "Rational",
    # polygamma family: admitted deliberately as part of the explicit
    # allowed-functions policy (v0.2); admission is a policy decision, never
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
    "max_symbols": 40,
    "allowed_functions": list(_ALLOWED_FUNCTIONS),
}

# module-level view exposed for inspection/tests; mutate via set_parse_policy()
PARSE_POLICY: dict = dict(_DEFAULT_POLICY)

_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_ALLOWED_CHARS_RE = re.compile(r"^[A-Za-z0-9_+\-*/().,\s^]*$")


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
    PARSE_POLICY.update(overrides)
    return get_parse_policy()


def _effective_policy(policy: Optional[dict]) -> dict:
    merged = get_parse_policy()
    if policy:
        unknown = set(policy) - set(_DEFAULT_POLICY)
        if unknown:
            raise AdapterError("PARSE_POLICY_KEY_UNKNOWN")
        merged.update(policy)
    return merged


# --------------------------------------------------------------------------- #
# structural builtins (v0.2): Sum / Piecewise / relations / logic
# --------------------------------------------------------------------------- #
# These names round-trip the structure-preserving representations produced by
# the adapters (symbolic ``Sum``, ``Piecewise``, relational/logical
# conditions). They are admitted as CALLABLES only — never as declared symbol
# names — so the whitelist stays closed while structure survives parsing.
_STRUCTURAL_BUILTINS: dict = {
    "Sum": sympy.Sum,
    "Product": sympy.Product,
    "Piecewise": sympy.Piecewise,
    "Eq": sympy.Eq,
    "Ne": sympy.Ne,
    "Lt": sympy.Lt,
    "Le": sympy.Le,
    "Gt": sympy.Gt,
    "Ge": sympy.Ge,
    "And": sympy.And,
    "Or": sympy.Or,
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
    violation. There is no eval/exec path.
    """
    pol = _effective_policy(policy)
    declared = normalize_symbols(symbols, allow_reserved=allow_reserved)
    if len(declared) > pol["max_symbols"]:
        raise AdapterError("CLAIM_SYMBOLS_TOO_MANY")

    # Declared function names must be valid identifiers and not collide with
    # declared symbols or hard-reserved names (constants / Rational /
    # structural builtins). A declared function MAY shadow a function
    # builtin: explicit declaration beats built-in.
    func_names: list[str] = []
    if functions is not None:
        if not isinstance(functions, (list, tuple)):
            raise AdapterError("CLAIM_FUNCTIONS_MALFORMED")
        for fname in functions:
            if not isinstance(fname, str) or not fname.strip():
                raise AdapterError("CLAIM_FUNCTIONS_MALFORMED")
            if not _IDENTIFIER_RE.fullmatch(fname):
                raise AdapterError("CLAIM_FUNCTIONS_MALFORMED")
            func_names.append(fname)
        if len(func_names) != len(set(func_names)):
            raise AdapterError("CLAIM_FUNCTIONS_MALFORMED")
        if set(func_names) & {s["name"] for s in declared}:
            raise AdapterError("FUNCTION_NAME_COLLIDES_WITH_SYMBOL")
        if HARD_RESERVED_NAMES & set(func_names):
            raise AdapterError("FUNCTION_NAME_RESERVED")

    if not isinstance(expr_str, str) or not expr_str.strip():
        raise AdapterError("EMPTY_EXPRESSION")
    if len(expr_str) > pol["max_expr_chars"]:
        raise AdapterError("EXPRESSION_TOO_LARGE")
    if not _ALLOWED_CHARS_RE.match(expr_str):
        raise AdapterError("DISALLOWED_CHARACTERS")

    identifiers = set(_IDENTIFIER_RE.findall(expr_str))
    allowed = ({s["name"] for s in declared}
               | set(pol["allowed_functions"])
               | set(_STRUCTURAL_BUILTINS)
               | set(func_names)
               | {"pi", "E", "I", "oo"})
    if identifiers - allowed:
        raise AdapterError("UNDECLARED_OR_DISALLOWED_NAME")

    try:
        expr = sympy.sympify(expr_str,
                             locals=_symbol_locals(declared, pol, func_names),
                             evaluate=True, convert_xor=True)
    except (sympy.SympifyError, SyntaxError, TypeError, AttributeError, ValueError):
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
    expr = parse_expression(text.strip(), declared, functions=functions,
                            allow_reserved=allow_reserved, policy=policy)
    return ExpressionRecord(
        text=text.strip(),
        sha256=digest,
        source_path=str(p),
        parsed_expr=expr,
        symbols=declared,
    )
