"""Operator identities in the free associative algebra.

Operators (H, rho, c_k, Green's-function blocks) are noncommutative symbols;
scalars commute. A polynomial identity holds in the free algebra exactly
when the expanded difference is zero: expansion into ordered words is a
normal form, so ``expand(lhs - rhs) == 0`` is a decision procedure, and a
nonzero word proves the identity fails for some operators. This covers
commutator algebra, the Lindblad generator versus the effective
non-Hermitian Hamiltonian plus jump terms, and (through ``keldysh``) the
Langreth rules. Relations such as H = H^dagger are declared as ``hermitian``;
infinite series (BCH, exponentials) are out of scope.

Expressions accept + - * / ** with integer powers, I, numbers, declared
names, and Comm(A, B), Anti(A, B), Dag(X). Names are checked against a
whitelist before SymPy sees the text.
"""
from __future__ import annotations

import re
from typing import Iterable, Mapping

import sympy
from sympy.parsing.sympy_parser import parse_expr

from ..models import AdapterError

_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_ALLOWED_CHARS = re.compile(r"[A-Za-z0-9_+\-*/(), .\s]*\Z")
_BUILTINS = {"Comm", "Anti", "Dag", "I", "Rational", "sqrt", "pi"}
MAX_CHARS = 20000


class OperatorSpace:
    """Declared operators, scalars and Hermitian operators."""

    def __init__(self, operators: Iterable[str], scalars: Iterable[str] = (),
                 hermitian: Iterable[str] = ()):
        operators, scalars, hermitian = list(operators), list(scalars), set(hermitian)
        for name in (*operators, *scalars):
            if not _NAME.fullmatch(name) or name in _BUILTINS or name.endswith("_dag"):
                raise AdapterError("OPERATOR_NAME_INVALID")
        if len(set(operators) | set(scalars)) != len(operators) + len(scalars):
            raise AdapterError("OPERATOR_NAME_DUPLICATE")
        if not hermitian <= set(operators):
            raise AdapterError("HERMITIAN_NAME_UNDECLARED")
        self.ops = {name: sympy.Symbol(name, commutative=False) for name in operators}
        self.daggers = {name: (self.ops[name] if name in hermitian
                               else sympy.Symbol(name + "_dag", commutative=False))
                        for name in operators}
        self.scalars = {name: sympy.Symbol(name) for name in scalars}

    def dagger(self, expr: sympy.Expr) -> sympy.Expr:
        """Adjoint: reverse words, conjugate scalars, map X -> X^dagger."""
        expr = sympy.expand(expr)
        inverse = {self.daggers[n]: self.ops[n] for n in self.ops if self.daggers[n] != self.ops[n]}
        forward = {self.ops[n]: self.daggers[n] for n in self.ops}

        def word(term):
            coeff, factors = term.args_cnc()
            out = sympy.conjugate(sympy.Mul(*coeff))
            for factor in reversed(factors):
                base, power = factor.as_base_exp()
                image = inverse.get(base, forward.get(base, base))
                out = out * image ** power
            return out
        return sympy.Add(*(word(t) for t in sympy.Add.make_args(expr)))

    def parse(self, text: str) -> sympy.Expr:
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_CHARS:
            raise AdapterError("EMPTY_OR_OVERSIZED_EXPRESSION")
        if not _ALLOWED_CHARS.fullmatch(text) or "__" in text:
            raise AdapterError("DISALLOWED_CHARACTER")
        names = set(_IDENT.findall(text)) - _BUILTINS
        if names - set(self.ops) - set(self.scalars):
            raise AdapterError("UNDECLARED_OR_DISALLOWED_NAME")
        local = {**self.ops, **self.scalars, "I": sympy.I, "pi": sympy.pi,
                 "Rational": sympy.Rational, "sqrt": sympy.sqrt,
                 "Comm": lambda a, b: a * b - b * a,
                 "Anti": lambda a, b: a * b + b * a,
                 "Dag": self.dagger}
        try:
            expr = parse_expr(text, local_dict=local, global_dict={"__builtins__": {},
                              "Integer": sympy.Integer, "Float": sympy.Float,
                              "Symbol": sympy.Symbol})
        except (SyntaxError, TypeError, ValueError, sympy.SympifyError):
            raise AdapterError("SYMBOLIC_PARSE_FAILED") from None
        # Inverses leave the free algebra, where expansion is no longer a
        # decision procedure; refuse them rather than risk a false NONZERO.
        for power in expr.atoms(sympy.Pow):
            if not power.base.is_commutative and not (
                    power.exp.is_Integer and power.exp > 0):
                raise AdapterError("OPERATOR_INVERSE_NOT_SUPPORTED")
        return expr


def free_algebra_residual(lhs: sympy.Expr, rhs: sympy.Expr) -> sympy.Expr:
    return sympy.expand(lhs - rhs)


def verify_operator_identity(lhs: str, rhs: str, *, operators: Iterable[str],
                             scalars: Iterable[str] = (),
                             hermitian: Iterable[str] = ()) -> Mapping:
    """ZERO / NONZERO in the free algebra, with the first surviving words."""
    try:
        space = OperatorSpace(operators, scalars, hermitian)
        residual = free_algebra_residual(space.parse(lhs), space.parse(rhs))
    except AdapterError as exc:
        return {"verdict": "UNKNOWN", "reasons": [f"PARSE_FAILED:{exc.code}"]}
    if residual == 0:
        return {"verdict": "ZERO", "reasons": [], "residual": "0"}
    words = [str(t) for t in sympy.Add.make_args(residual)][:6]
    return {"verdict": "NONZERO", "reasons": ["FREE_ALGEBRA_RESIDUAL_NONZERO"],
            "residual": str(residual)[:2000], "surviving_words": words}
