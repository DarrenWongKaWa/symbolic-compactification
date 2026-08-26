"""Structure Constructor: H → explicit reconstruction.

Does not decide scientific truth. Always emits a closed expression (or
marks constructable=False). Named auxiliaries are expanded before verify.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import sympy
from sympy.core.function import AppliedUndef

from research.method_v2.expand import expand_text
from research.structure_discovery.prototype.hypothesis import StructureHypothesis
from symbolic_compactification import parse_expression
from symbolic_compactification.models import AdapterError
from symbolic_compactification.transforms import (
    collect_common_factor,
    combine_identical_sums,
)


@dataclass
class Construction:
    hypothesis_type: str
    structured_text: str
    closed_text: str
    definitions: dict
    constructable: bool
    notes: str = ""
    d_level: str = ""
    extras: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "hypothesis_type": self.hypothesis_type,
            "structured_text": self.structured_text,
            "closed_text": self.closed_text,
            "definitions": self.definitions,
            "constructable": self.constructable,
            "notes": self.notes,
            "d_level": self.d_level,
        }


def _parse(text, symbols, functions):
    return parse_expression(text, symbols, functions=functions or None)


def _symbol_by_name(expr: sympy.Expr, name: str) -> sympy.Symbol:
    for s in expr.free_symbols:
        if s.name == name:
            return s
    return sympy.Symbol(name)


def _swap_applied(term: sympy.Expr, pair: list[str] | None) -> sympy.Expr:
    """Swap two named symbols using the expression's own Symbol objects.

    ``sympy.symbols('n')`` is not equal to a parsed ``n`` with assumptions,
    so a naive xreplace is a silent no-op and can emit ``2*F(n, m)``.
    """
    if pair and len(pair) == 2:
        a = _symbol_by_name(term, pair[0])
        b = _symbol_by_name(term, pair[1])
        tmp = sympy.Dummy("swap_tmp")
        return term.xreplace({a: tmp}).xreplace({b: a, tmp: b})
    if isinstance(term, AppliedUndef) and len(term.args) == 2:
        return term.func(term.args[1], term.args[0])
    return term


def _first_add_terms(expr: sympy.Expr) -> list[sympy.Expr]:
    if isinstance(expr, sympy.Add):
        return list(expr.args)
    return [expr]


def construct(
    hyp: StructureHypothesis,
    current: str,
    symbols: list,
    functions: list | None,
) -> list[Construction]:
    functions = functions or []
    out: list[Construction] = []
    try:
        expr = _parse(current, symbols, functions)
    except AdapterError as exc:
        return [Construction(
            hyp.hypothesis_type, current, current, {}, False,
            notes=f"parse_current:{exc.code}", d_level=hyp.d_level,
        )]

    def emit(structured: str, defs: dict, notes: str) -> None:
        closed = expand_text(structured, defs)
        out.append(Construction(
            hypothesis_type=hyp.hypothesis_type,
            structured_text=structured,
            closed_text=closed,
            definitions=defs,
            constructable=True,
            notes=notes,
            d_level=hyp.d_level,
        ))

    ht = hyp.hypothesis_type
    targets = hyp.target_subexpressions
    aux = hyp.proposed_auxiliaries

    try:
        if ht == "structural_regrouping":
            r = combine_identical_sums(expr)
            e2 = r.after if r.applied else expr
            r2 = collect_common_factor(e2)
            e3 = r2.after if r2.applied else e2
            emit(str(e3), {}, "cheap_transforms")

        elif ht == "repeated_kernel" and targets:
            sub = _parse(targets[0], symbols, functions)
            name = aux[0].name if aux else "K0"
            named = expr.xreplace({sub: sympy.Symbol(name)})
            defs = {name: str(sub)}
            emit(str(named), defs, "xreplace_kernel")
            # also try collecting the kernel as a factor of an Add
            if isinstance(expr, sympy.Add):
                factored = sympy.collect(expr, sub)
                if factored != expr:
                    emit(str(factored), {}, "sympy.collect_on_kernel")

        elif ht == "identical_kernel_merge" and targets:
            # Aggressive: n_terms * first kernel. Often NONZERO.
            kdef = aux[0].definition if aux else targets[0]
            n = max(len(_first_add_terms(expr)), 2)
            name = aux[0].name if aux else "Kmerge"
            emit(f"{n}*({kdef})", {name: kdef}, "n_times_first_kernel")
            emit(f"{n}*{name}", {name: kdef}, "n_times_named_kernel")

        elif ht in ("permutation_orbit", "symmetry_invariant", "tensor_generator"):
            if not targets:
                raise AdapterError("EMPTY_EXPRESSION")
            t0 = _parse(targets[0], symbols, functions)
            # Reconstruct from the full summand containing the generator,
            # not the generator call alone (T(i,j)*v(i)*v(j) not T(i,j)).
            host = t0
            for term in _first_add_terms(expr):
                if term == t0 or term.has(t0):
                    host = term
                    break
            if host.atoms(sympy.Sum) or host.atoms(sympy.Product):
                out.append(Construction(
                    ht, current, current, {}, False,
                    notes="orbit_host_contains_sum", d_level=hyp.d_level,
                ))
                return out
            swapped = _swap_applied(host, hyp.swap_pair)
            # Pure equal-weight orbit — NONZERO when coefficients break it.
            closed = host + swapped
            defs = {}
            if aux:
                defs[aux[0].name] = str(host)
            emit(str(closed), defs, "equal_weight_orbit")

        elif ht == "master_function" and targets:
            # Reconstruction: sum of the observed specializations (identity)
            # PLUS a factored form if they share a coefficient.
            parts = []
            for t in targets:
                try:
                    parts.append(_parse(t, symbols, functions))
                except AdapterError:
                    continue
            if parts:
                s = parts[0]
                for p in parts[1:]:
                    s = s + p
                name = aux[0].name if aux else "Phi0"
                emit(str(s), {name: str(parts[0])}, "sum_of_specializations")

        elif ht == "divided_difference" and targets:
            name = aux[0].name if aux else "DD0"
            emit(name, {name: targets[0]}, "name_divided_difference")
            emit(targets[0], {}, "identity_dd")

        elif ht == "confluent_representation" and targets:
            # If all Piecewise values equal, use that value; else first value
            # (aggressive, often NONZERO).
            pw_text = targets[0]
            try:
                pw = _parse(pw_text, symbols, functions)
            except AdapterError:
                pw = expr
            if isinstance(pw, sympy.Piecewise):
                vals = [val for val, _cond in pw.args]
                if vals and all(v == vals[0] for v in vals):
                    emit(str(vals[0]), {}, "identical_branch_values")
                elif vals:
                    emit(str(vals[0]), {}, "aggressive_first_branch")
            elif len(targets) >= 2:
                emit(targets[1], {}, "use_first_recorded_value")

        elif ht == "derivative_family" and targets:
            name = aux[0].name if aux else "PsiMaster"
            # Keep the original expression; naming only.
            emit(current, {name: targets[0]}, "name_lowest_polygamma")

        elif ht == "spectral_family" and targets:
            name = aux[0].name if aux else "Res0"
            sub = _parse(targets[0], symbols, functions)
            named = expr.xreplace({sub: sympy.Symbol(name)})
            emit(str(named), {name: str(sub)}, "name_spectral_call")

        else:
            return [Construction(
                ht, current, current, {}, False,
                notes="no_constructor_for_type", d_level=hyp.d_level,
            )]
    except AdapterError as exc:
        return [Construction(
            ht, current, current, {}, False,
            notes=f"construct_parse:{exc.code}", d_level=hyp.d_level,
        )]
    except Exception as exc:  # constructor must fail closed, not crash the run
        return [Construction(
            ht, current, current, {}, False,
            notes=f"construct_error:{type(exc).__name__}", d_level=hyp.d_level,
        )]

    if not out:
        out.append(Construction(
            ht, current, current, {}, False, notes="empty", d_level=hyp.d_level,
        ))
    return out
