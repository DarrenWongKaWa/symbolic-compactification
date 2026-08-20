"""Assumption-aware rewrite rules (v0.2).

A *rule* is a tiny explicit triple:

    (transform function, required assumptions, description)

``apply_rule`` applies the transform ONLY when the DECLARED symbol
assumptions suffice for the rule's requirements; when they do not suffice
the transformation is NOT applied and verification of that rewrite stays
UNKNOWN (fail-closed — an assumption gap is never silently bridged).

Deliberately small: this is a fixed handful of GENERIC built-in rules plus a
mechanism for callers to supply their own. There is NO pattern-language, no
rule engine, no scientific identities — generic rewrites only.

Assumption declaration format: the engine's normalized symbol list,
``[{"name": "x", "real": True, "nonzero": False}, ...]`` (see
``models.normalize_symbols``). Rule requirements map a symbol name to one of
the declared boolean assumptions: ``"real"``, ``"nonzero"``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import sympy

from .models import AdapterError

__all__ = ["RewriteRule", "RuleApplication", "apply_rule", "apply_rules",
           "BUILTIN_RULES", "RULE_ASSUMPTIONS_SUFFICE"]


# --------------------------------------------------------------------------- #
# rule record
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class RewriteRule:
    """One assumption-aware rewrite.

    ``transform(expr, symbols_by_name)`` returns the rewritten expression, or
    ``None`` when the rule does not match / does not change the expression.
    ``required_assumptions`` maps a symbol name to the declared boolean
    assumption the rewrite needs for that symbol (``"real"`` / ``"nonzero"``).
    """

    name: str
    transform: Callable
    required_assumptions: dict = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "required_assumptions": dict(self.required_assumptions),
            "description": self.description,
        }


@dataclass(frozen=True)
class RuleApplication:
    """Outcome of one ``apply_rule`` call (telemetry-friendly)."""

    rule: str
    applied: bool
    before: sympy.Expr
    after: sympy.Expr
    reason: str = ""           # "" | "assumptions_insufficient" | "no_change"
    missing_assumptions: tuple = ()

    def to_dict(self) -> dict:
        return {
            "rule": self.rule,
            "applied": self.applied,
            "before": str(self.before),
            "after": str(self.after),
            "reason": self.reason,
            "missing_assumptions": list(self.missing_assumptions),
        }


# --------------------------------------------------------------------------- #
# assumption sufficiency check
# --------------------------------------------------------------------------- #

def _assumption_gap(rule: RewriteRule,
                    symbols_by_name: dict) -> tuple:
    """Return the missing ``(name, assumption)`` pairs (empty = sufficient)."""
    missing = []
    for name, assumption in sorted(rule.required_assumptions.items()):
        decl = symbols_by_name.get(name)
        if decl is None or not decl.get(assumption, False):
            missing.append(f"{name}:{assumption}")
    return tuple(missing)


RULE_ASSUMPTIONS_SUFFICE = "assumptions_sufficient"


# --------------------------------------------------------------------------- #
# application API
# --------------------------------------------------------------------------- #

def apply_rule(rule: RewriteRule, expr: sympy.Expr,
               symbols) -> RuleApplication:
    """Apply ``rule`` to ``expr`` iff the declared assumptions suffice.

    ``symbols`` is the engine's symbol declaration list (raw or normalized).
    Insufficient assumptions -> the transformation is NOT applied and the
    result records ``reason="assumptions_insufficient"`` (verification of the
    rewrite stays UNKNOWN upstream; the gap is never bridged silently).
    """
    from .models import normalize_symbols  # local import: no cycle at module load

    try:
        declared = normalize_symbols(symbols, allow_reserved=True)
    except AdapterError:
        declared = []
    symbols_by_name = {s["name"]: s for s in declared}

    gap = _assumption_gap(rule, symbols_by_name)
    if gap:
        return RuleApplication(rule=rule.name, applied=False,
                               before=expr, after=expr,
                               reason="assumptions_insufficient",
                               missing_assumptions=gap)
    try:
        candidate = rule.transform(expr, symbols_by_name)
    except Exception:
        candidate = None  # a failing rule is a non-match, never an exception
    if candidate is None or candidate == expr:
        return RuleApplication(rule=rule.name, applied=False,
                               before=expr, after=expr, reason="no_change")
    return RuleApplication(rule=rule.name, applied=True,
                           before=expr, after=candidate)


def apply_rules(rules, expr: sympy.Expr, symbols) -> list:
    """Apply each rule once (independently, in order); return all records."""
    return [apply_rule(r, expr, symbols) for r in rules]


# --------------------------------------------------------------------------- #
# generic built-in rules (no scientific identities, ever)
# --------------------------------------------------------------------------- #

def _conjugate_real_transform(expr, symbols_by_name):
    """conjugate(x) -> x for every declared-real symbol x (exact, no
    further simplification)."""
    real_names = {n for n, s in symbols_by_name.items() if s.get("real")}
    if not real_names:
        return None

    def _rewrite(sub):
        if isinstance(sub, sympy.conjugate):
            arg = sub.args[0]
            if arg.free_symbols and all(
                    str(s) in real_names for s in arg.free_symbols):
                return arg
        return sub

    return expr.replace(lambda sub: isinstance(sub, sympy.conjugate), _rewrite)


def _re_real_transform(expr, symbols_by_name):
    """re(x) -> x for expressions whose free symbols are all declared real."""
    real_names = {n for n, s in symbols_by_name.items() if s.get("real")}
    if not real_names:
        return None

    def _rewrite(sub):
        if isinstance(sub, sympy.re):
            arg = sub.args[0]
            if arg.free_symbols and all(
                    str(s) in real_names for s in arg.free_symbols):
                return arg
        return sub

    return expr.replace(lambda sub: isinstance(sub, sympy.re), _rewrite)


def _sqrt_square_abs_transform(expr, symbols_by_name):
    """sqrt(x**2) -> Abs(x) only when x is known real."""

    real_names = {name for name, declaration in symbols_by_name.items()
                  if declaration.get("real")}

    def _rewrite(sub):
        if isinstance(sub, sympy.Pow) and sub.args[1] == sympy.Rational(1, 2):
            base = sub.args[0]
            if (isinstance(base, sympy.Pow) and base.args[1] == 2):
                arg = base.args[0]
                declared_real = (bool(arg.free_symbols)
                                 and all(symbol.name in real_names
                                         for symbol in arg.free_symbols))
                if arg.is_real is True or declared_real:
                    return sympy.Abs(arg)
        return sub

    return expr.replace(
        lambda sub: isinstance(sub, sympy.Pow)
        and sub.args[1] == sympy.Rational(1, 2), _rewrite)


BUILTIN_RULES = (
    RewriteRule(
        name="conjugate_real_identity",
        transform=_conjugate_real_transform,
        required_assumptions={},   # per-symbol realness checked dynamically
        description="conjugate(e) = e when every free symbol of e is declared "
                    "real; requires the relevant symbols declared real",
    ),
    RewriteRule(
        name="re_real_identity",
        transform=_re_real_transform,
        required_assumptions={},
        description="re(e) = e when every free symbol of e is declared real; "
                    "requires the relevant symbols declared real",
    ),
    RewriteRule(
        name="sqrt_square_abs",
        transform=_sqrt_square_abs_transform,
        required_assumptions={},
        description="sqrt(x**2) = Abs(x) when x is provably real under the "
                    "declared assumptions",
    ),
)


# NOTE on required_assumptions: rules whose applicability depends on WHICH
# symbols are real/nonzero inspect the declaration map inside their transform
# (the exact set of involved symbols is only known per-expression). The
# ``required_assumptions`` field governs rules with FIXED symbol requirements,
# e.g. RewriteRule("divide_by_m", fn, {"m": "nonzero"}, ...): apply_rule then
# refuses the rewrite unless the declaration proves ``m`` nonzero.
