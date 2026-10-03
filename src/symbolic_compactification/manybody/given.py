"""An identity checked under relations the paper states ("using R, X becomes Y").

A derivation step often holds only because of a relation stated elsewhere: a
metric-velocity identity, epsilon_21 = -epsilon_12, a Feynman-Hellmann
relation. The step is then not an identity of its two sides alone, so a plain
``lhs - rhs`` is not zero; but it is zero *whenever the relations hold*.

The check is ideal membership, with a certificate anyone can re-check:

    numerator(lhs - rhs) = sum_i q_i * (l_i - r_i)

with explicit cofactors q_i (polynomials in the symbols and in any function
values, which are treated as further unknowns). ``ZERO`` then means: the
step holds for every value of the symbols at which the stated relations hold
and the denominators do not vanish. It certifies nothing about the relations
themselves; they are the paper's, quoted, and listed with the verdict.

``NONZERO`` needs a counterexample at which every relation holds exactly:
each relation is solved for a symbol in which it is linear, and the residual
is shown nonzero at a rational point. When no such point is constructed the
result is ``UNKNOWN``, never ``NONZERO``.
"""
from __future__ import annotations

from typing import Any, Iterable, Sequence

import sympy

from ..models import AdapterError
from .calculus import CalculusSpace, compare

ZERO, NONZERO, UNKNOWN = "ZERO", "NONZERO", "UNKNOWN"


def _numerator(expr: sympy.Expr) -> tuple[sympy.Expr, sympy.Expr]:
    num, den = sympy.fraction(sympy.together(expr))
    return sympy.expand(num), den


def _numerators(exprs: list[sympy.Expr]) -> list[tuple[sympy.Expr, sympy.Expr]]:
    return [_numerator(e) for e in exprs]


def _reduce(target: sympy.Expr, polys: list[sympy.Expr]):
    return sympy.reduced(target, polys)


def _basis(polys: list[sympy.Expr]) -> list[sympy.Expr]:
    # the same (lex) order that reduced() divides in: a remainder is only zero
    # for a member when the basis is a Groebner basis for that order
    return list(sympy.groebner(polys, order="lex").exprs)


def _vanishing(dens: list[sympy.Expr], polys: list[sympy.Expr]) -> bool:
    """Some denominator is zero wherever the relations hold: d is in the radical
    of the ideal, i.e. 1 is in the ideal of the relations and 1 - t*d."""
    t = sympy.Dummy("t")
    for d in dens:
        if d.is_number:
            continue
        if list(sympy.groebner([*polys, 1 - t * d], order="grevlex").exprs) == [1]:
            return True
    return False


def _budgeted(fn, *args):
    """A symbolic step under the engine's time budget; None when it fails or runs out."""
    from sympy.polys.polyerrors import BasePolynomialError

    from ..budgets import BudgetExceeded, run_symbolic_operation
    try:
        return run_symbolic_operation("simplify", fn, args)
    except (BudgetExceeded, AdapterError, BasePolynomialError, sympy.PolynomialError,
            sympy.GeneratorsNeeded, ValueError, TypeError, ZeroDivisionError, OverflowError):
        return None


def _degenerate(polys: list[sympy.Expr]) -> str | None:
    """Relations that are contradictory, or that force a quantity to vanish,
    make every step 'hold': refuse them instead of using them."""
    if not polys:
        return None
    basis = _budgeted(_basis, polys)
    if basis is None:
        return "GIVEN_TOO_COMPLEX"
    for b in basis:
        if b.is_number and b != 0:
            return "GIVEN_INCONSISTENT"
        terms = sympy.Add.make_args(sympy.expand(b))
        stated = any(sympy.cancel(b / p).is_number for p in polys)    # the text says 'X = 0' itself
        if len(terms) == 1 and b.free_symbols and not stated:
            return "GIVEN_FORCES_ZERO:" + ",".join(sorted(str(x) for x in b.free_symbols))
    return None


def _cofactors(target: sympy.Expr, polys: list[sympy.Expr]) -> list[sympy.Expr] | None:
    """q with target == sum(q_i * polys_i) exactly, or None."""
    if not polys:
        return None
    reduced = _budgeted(_reduce, target, polys)
    if reduced is None:
        return None
    quotients, remainder = reduced
    if sympy.expand(remainder) != 0:
        return None
    combination = sum(q * p for q, p in zip(quotients, polys))
    if sympy.expand(target - combination) != 0:       # re-check: never trust the division alone
        return None
    return [sympy.expand(q) for q in quotients]


def _restates(target: sympy.Expr, polys: list[sympy.Expr], defines: list[bool]) -> bool:
    """The residual is a constant multiple of one relation that defines nothing:
    the 'relation' is the step itself. Substituting a definition (a bare name on
    one side, Omega = i(...)) is a step of its own and is allowed."""
    for p, definition in zip(polys, defines):
        if p == 0 or definition:
            continue
        ratio = sympy.cancel(target / p)
        if ratio != 0 and not ratio.free_symbols and not ratio.atoms(sympy.Function):
            return True
    return False


def _solve_linear(polys: list[sympy.Expr], protected: set) -> dict | None:
    """Solve each relation for a symbol it contains linearly, one symbol per
    relation, substituting as it goes. None when some relation cannot be solved."""
    solution: dict = {}
    for p in polys:
        p = sympy.expand(p.subs(solution))
        if p == 0:
            continue
        for s in sorted(p.free_symbols - protected - set(solution), key=str):
            poly = sympy.Poly(p, s) if p.is_polynomial(s) else None
            if poly is None or poly.degree() != 1:
                continue
            a, b = poly.all_coeffs()
            if a == 0:
                continue
            value = sympy.cancel(-b / a)
            solution = {k: sympy.cancel(v.subs(s, value)) for k, v in solution.items()}
            solution[s] = value
            break
        else:
            return None
    return solution


def verify_identity_given(lhs: str, rhs: str, relations: Sequence[tuple[str, str]], *,
                          symbols: Any, functions: Iterable[str] = (),
                          positive: tuple[str, ...] = (), definitions: dict | None = None) -> dict:
    """ZERO / NONZERO / UNKNOWN for ``lhs = rhs`` under ``l_i = r_i`` for all i."""
    try:
        space = CalculusSpace(symbols, functions, definitions=definitions)
        left, right = space.parse_expanded(lhs), space.parse_expanded(rhs)
        rels = [(space.parse_expanded(l), space.parse_expanded(r)) for l, r in relations]
        plain = compare(left, right, space, positive)
    except AdapterError as exc:
        return {"verdict": UNKNOWN, "reasons": [f"PARSE_FAILED:{exc.code}"], "given_used": []}
    except (OverflowError, ValueError, TypeError, ZeroDivisionError):
        return {"verdict": UNKNOWN, "reasons": ["COMPARISON_FAILED"], "given_used": []}
    if plain["verdict"] == ZERO:
        return {**plain, "given_used": []}
    parts = _budgeted(_numerators, [left - right, *[l - r for l, r in rels]])
    if parts is None:
        return {"verdict": UNKNOWN, "reasons": ["GIVEN_TOO_COMPLEX"], "given_used": []}
    (target, denominator), pairs = parts[0], parts[1:]
    kept = [k for k, (num, _) in enumerate(pairs) if num != 0]          # 'a = a' says nothing
    if any(pairs[k][0].is_number for k in kept):
        return {"verdict": UNKNOWN, "reasons": ["GIVEN_INCONSISTENT"], "given_used": []}
    polys = [pairs[k][0] for k in kept]
    nonzero = [d for d in [denominator, *(den for _, den in pairs)] if d != 1]
    degenerate = _degenerate(polys)
    if degenerate:
        return {"verdict": UNKNOWN, "reasons": [degenerate], "given_used": []}
    defines = [isinstance(rels[k][0], sympy.Symbol) or isinstance(rels[k][1], sympy.Symbol) for k in kept]
    if _restates(target, polys, defines):
        return {"verdict": UNKNOWN, "reasons": ["GIVEN_RESTATES_THE_STEP"], "given_used": []}
    certificate = None
    quotients = _cofactors(target, polys)
    if quotients is not None:
        used = [kept[i] for i, q in enumerate(quotients) if q != 0]
        certificate = {"method": "cofactors", "cofactors": [str(q) for q in quotients],
                       "relations_used": [kept[i] for i in range(len(polys))]}
    else:
        substituted = _by_definitions(left, right, rels, kept, space, positive)
        if substituted is not None:
            used, certificate = substituted
        elif len(polys) > 1:
            basis = _budgeted(_basis, polys) or []
            if basis and _cofactors(target, basis) is not None:
                used = list(kept)
                certificate = {"method": "groebner", "basis": [str(b) for b in basis]}
    if certificate is not None:
        vacuous = _budgeted(_vanishing, nonzero, polys)
        if vacuous is None:
            return {"verdict": UNKNOWN, "reasons": ["GIVEN_TOO_COMPLEX"], "given_used": []}
        if vacuous:          # the relations force a denominator to zero: the step says nothing
            return {"verdict": UNKNOWN, "reasons": ["GIVEN_MAKES_A_DENOMINATOR_VANISH"], "given_used": []}
        return {"verdict": ZERO, "reasons": ["IDEAL_MEMBERSHIP"], "given_used": used,
                "certificate": {**certificate, "nonzero": [str(d) for d in nonzero]}}
    solution = _solve_linear(polys, set())
    if solution:
        try:
            reduced = compare(left.subs(solution), right.subs(solution), space, positive)
        except (OverflowError, ValueError, TypeError, ZeroDivisionError):
            reduced = {"verdict": UNKNOWN}
        hit = reduced.get("counterexample") if reduced["verdict"] == NONZERO else None
        from sympy.core.function import AppliedUndef
        if hit and not (left - right).atoms(AppliedUndef):   # declared functions the step never uses don't count
            others = set().union(*(p.free_symbols for p in polys), (left - right).free_symbols)
            full = _complete_point(hit["point"], solution, others)
            if full is not None and _refutes(left - right, polys, nonzero, full,
                                             _domain(symbols, positive)):
                return {"verdict": NONZERO, "reasons": ["COUNTEREXAMPLE_UNDER_GIVEN"],
                        "given_used": list(kept),
                        "counterexample": {k: str(v) for k, v in full.items()}}
    return {"verdict": UNKNOWN, "reasons": ["NOT_IN_THE_IDEAL_OF_THE_GIVEN"], "given_used": []}


def _by_definitions(left, right, rels, kept, space, positive) -> tuple[list[int], dict] | None:
    """Relations that give a name a value (alpha_2 = ..., the name not on the other
    side) substituted into the step, chains included. ZERO after that means the
    step holds wherever those definitions hold."""
    mapping: dict = {}
    used: list[int] = []
    for k in kept:
        l, r = rels[k]
        for name, value in ((l, r), (r, l)):
            if isinstance(name, sympy.Symbol) and name not in value.free_symbols and name not in mapping:
                mapping[name] = value
                used.append(k)
                break
    if not mapping:
        return None
    for _ in range(len(mapping) + 1):                       # alpha_3 may use alpha_2
        resolved = {k: v.xreplace(mapping) for k, v in mapping.items()}
        if resolved == mapping:
            break
        mapping = resolved
    if any(k in v.free_symbols for k, v in mapping.items()):
        return None                                         # a cycle defines nothing
    try:
        result = compare(left.xreplace(mapping), right.xreplace(mapping), space, positive)
    except (OverflowError, ValueError, TypeError, ZeroDivisionError):
        return None
    if result["verdict"] != ZERO:
        return None
    return used, {"method": "substitution", "substituted": {str(k): str(v) for k, v in mapping.items()},
                  "relations_used": used}


def _domain(symbols: Any, positive: tuple[str, ...]) -> dict[str, str]:
    """name -> 'positive' / 'nonzero' / 'complex' as declared; every other symbol is real."""
    out = {str(n): "positive" for n in positive}
    for s in symbols or []:
        if isinstance(s, dict):
            if s.get("positive"):
                out[str(s["name"])] = "positive"
            elif s.get("real") is False:
                out.setdefault(str(s["name"]), "complex")
            elif s.get("nonzero"):
                out.setdefault(str(s["name"]), "nonzero")
    return out


def _complete_point(point: dict, solution: dict, others: set = frozenset()) -> dict | None:
    """The counterexample with the solved symbols filled in, all rational. A
    symbol that cancelled from the residual but still occurs in a relation (A,
    once mu is eliminated) gets a value of its own first."""
    try:
        values = {name: sympy.Rational(str(v)) for name, v in point.items()}
    except (TypeError, ValueError):
        return None
    spare = iter(sympy.Rational(p, q) for p, q in ((11, 7), (13, 9), (17, 10), (19, 11), (23, 12), (29, 13),
                                                    (31, 14), (37, 15), (41, 16), (43, 17)) * 8)
    for x in sorted(others, key=str):
        if str(x) not in values and x not in solution:
            values[str(x)] = next(spare)
    full = dict(values)
    for s, expr in solution.items():
        value = expr.xreplace({x: values[str(x)] for x in expr.free_symbols if str(x) in values})
        if value.free_symbols or value.atoms(sympy.Function) or not value.is_finite:
            return None
        full[str(s)] = value
    return full


def _refutes(residual: sympy.Expr, polys: list[sympy.Expr], nonzero: list[sympy.Expr], full: dict,
             domain: dict[str, str]) -> bool:
    """Exactly: the point lies in the declared domain, every relation holds there, no
    denominator vanishes, and the residual does not vanish."""
    for name, value in full.items():
        kind = domain.get(name, "real")
        if kind != "complex" and not value.is_real:
            return False                       # a real symbol cannot take x = 160 i/91
        if kind == "positive" and not value > 0 or kind == "nonzero" and value == 0:
            return False
    symbols = residual.free_symbols.union(*(p.free_symbols for p in polys), *(d.free_symbols for d in nonzero))
    if any(str(x) not in full for x in symbols):
        return False
    at = {x: full[str(x)] for x in symbols}
    if any(sympy.simplify(p.xreplace(at)) != 0 for p in polys):
        return False
    if any(sympy.simplify(d.xreplace(at)) == 0 for d in nonzero):
        return False
    value = sympy.simplify(residual.xreplace(at))
    return bool(value.is_number and value.is_finite and value != 0)
