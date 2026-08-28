"""Exact additive atom decomposition of a local kernel.

After a spectator peel via ``split_edge(..., degeneration=var)``, a kernel
of the form ``pref * Sum_i T_i`` is split so each ``T_i`` has at most one
polygamma. Reconstruction is an independent gate: ``pref * Sum T_i`` must
equal the original. Failure is not treated as success.

No LLM. No Guo identities. Does not call ``together`` on a full kernel
and does not emit hop ZERO.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

import sympy
from sympy.core.function import AppliedUndef

from research.coefficient_laurent.schema import (
    ATOM_CLASSES,
    METHOD_VERSION,
    LaurentAtom,
)
from research.iterated_confluence.spectator import split_edge

POLYGAMMA, RATIONAL, POWER, LOG, OTHER_UNSUPPORTED = ATOM_CLASSES

_ONE = sympy.Integer(1)
_ZERO = sympy.Integer(0)


class ReconstructionError(Exception):
    """Atom fields could not be rebuilt into an expression."""


@dataclass
class AtomDecomposition:
    """``pref * Sum atoms`` plus peel metadata. Not a hop certificate."""

    pref: sympy.Expr
    atoms: list[LaurentAtom]
    spectator: sympy.Expr = field(default_factory=lambda: _ONE)
    local: sympy.Expr = field(default_factory=lambda: _ZERO)
    original: sympy.Expr = field(default_factory=lambda: _ZERO)
    reconstruction_ok: bool = False
    atom_decomposition_hash: str = ""
    note: str = ""
    terms: tuple[sympy.Expr, ...] = ()
    split_note: str = ""
    method_version: str = METHOD_VERSION

    def to_dict(self) -> dict[str, Any]:
        classes: dict[str, int] = {}
        for atom in self.atoms:
            classes[atom.atom_class] = classes.get(atom.atom_class, 0) + 1
        return {
            "pref": str(self.pref),
            "pref_srepr": sympy.srepr(self.pref),
            "spectator": str(self.spectator),
            "n_atoms": len(self.atoms),
            "atom_classes": classes,
            "reconstruction_ok": self.reconstruction_ok,
            "atom_decomposition_hash": self.atom_decomposition_hash,
            "note": self.note,
            "split_note": self.split_note,
            "method_version": self.method_version,
            "atoms": [atom.to_dict() for atom in self.atoms],
        }


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()


def canonical_atom_hash(
    *,
    atom_class: str,
    coefficient: sympy.Expr,
    function_head: str,
    function_order: Any,
    argument: Any,
) -> str:
    """Hash of mathematical atom content (not hop provenance)."""
    payload = json.dumps(
        {
            "argument": _srepr_or_empty(argument),
            "atom_class": atom_class,
            "coefficient": sympy.srepr(coefficient),
            "function_head": function_head or "",
            "function_order": _srepr_or_empty(function_order),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256_text(payload)


def decomposition_hash(
    pref: sympy.Expr,
    atoms: Sequence[LaurentAtom],
    *,
    reconstruction_ok: bool,
) -> str:
    payload = json.dumps(
        {
            "atom_hashes": [atom.canonical_atom_hash for atom in atoms],
            "pref": sympy.srepr(pref),
            "reconstruction_ok": bool(reconstruction_ok),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256_text(payload)


def atom_expr(atom: LaurentAtom) -> sympy.Expr:
    """Rebuild a term from ``LaurentAtom`` fields. Fail closed."""
    coeff = _from_srepr(atom.coefficient) if atom.coefficient else _ONE
    head = atom.function_head or ""
    if not head:
        return coeff
    if head == "polygamma":
        if not atom.argument:
            raise ReconstructionError("polygamma missing argument")
        order = _from_srepr(atom.function_order) if atom.function_order else _ZERO
        return coeff * sympy.polygamma(order, _from_srepr(atom.argument))
    if head == "log":
        if not atom.argument:
            raise ReconstructionError("log missing argument")
        return coeff * sympy.log(_from_srepr(atom.argument))
    raise ReconstructionError(f"unsupported function_head:{head}")


def decompose(
    expr: Any,
    var: Any,
    point: Any,
    source_member: str,
    source_text_hash: str,
    *,
    partner: Any = None,
) -> AtomDecomposition:
    """Peel spectator, then split ``pref * Sum T_i``.

    ``partner`` is the hop target when known; otherwise the source is
    split against itself. Only a certified multiplicative peel is kept.
    """
    try:
        original = _as_expr(expr)
        degeneration = _as_var(var)
        target_value = _as_var(point)
    except (TypeError, ValueError, sympy.SympifyError) as exc:
        return _failed(
            original=expr if isinstance(expr, sympy.Expr) else _ZERO,
            note=f"bad_input:{type(exc).__name__}",
        )

    partner_expr: Optional[sympy.Expr] = None
    if partner is not None:
        try:
            partner_expr = _as_expr(partner)
        except (TypeError, ValueError, sympy.SympifyError):
            partner_expr = None

    spectator, local, split = _peel_spectator(original, degeneration, partner_expr)
    split_note = str(split.get("note") or "")

    local_pref, add, pref_ok = _split_pref_add(local)
    terms = tuple(sympy.Add.make_args(add))
    pref = spectator * local_pref

    atoms = _atoms_from_terms(
        terms,
        source_member=str(source_member or ""),
        source_text_hash=str(source_text_hash or ""),
        degeneration=degeneration,
        target_value=target_value,
        spectator=spectator,
    )
    encoding_ok = True
    try:
        rebuilt = [atom_expr(atom) for atom in atoms]
    except ReconstructionError:
        encoding_ok = False
        rebuilt = []
    if encoding_ok:
        rebuilt_add = sympy.Add(*rebuilt) if rebuilt else _ZERO
        encoding_ok = _exact_eq(rebuilt_add, add)
    kernel_ok = pref_ok and _exact_eq(pref * add, original)
    reconstruction_ok = encoding_ok and kernel_ok
    note = "pref_add" if reconstruction_ok else "reconstruction_failed"
    digest = decomposition_hash(pref, atoms, reconstruction_ok=reconstruction_ok)
    return AtomDecomposition(
        pref=pref,
        atoms=atoms,
        spectator=spectator,
        local=local,
        original=original,
        reconstruction_ok=reconstruction_ok,
        atom_decomposition_hash=digest,
        note=note,
        terms=terms,
        split_note=split_note,
    )


def reconstruct(pref: Any, atoms_or_exprs: Any = None) -> sympy.Expr:
    """``pref * Sum T_i``. Accepts an ``AtomDecomposition`` or ``(pref, atoms)``.

    Does not substitute the original on failure.
    """
    if atoms_or_exprs is None:
        if isinstance(pref, AtomDecomposition):
            return reconstruct(pref.pref, pref.atoms)
        raise TypeError("reconstruct(pref, atoms_or_exprs)")

    pref_expr = pref if isinstance(pref, sympy.Expr) else _as_expr(pref)
    terms: list[sympy.Expr] = []
    for item in atoms_or_exprs:
        if isinstance(item, sympy.Expr):
            terms.append(item)
        elif isinstance(item, LaurentAtom):
            terms.append(atom_expr(item))
        elif isinstance(item, dict):
            terms.append(atom_expr(_atom_from_dict(item)))
        else:
            raise ReconstructionError(f"bad_atom:{type(item).__name__}")
    if not terms:
        return pref_expr * _ZERO
    return pref_expr * sympy.Add(*terms)


def _failed(*, original: sympy.Expr, note: str) -> AtomDecomposition:
    return AtomDecomposition(
        pref=_ONE,
        atoms=[],
        spectator=_ONE,
        local=original,
        original=original,
        reconstruction_ok=False,
        atom_decomposition_hash=decomposition_hash(_ONE, [], reconstruction_ok=False),
        note=note,
        terms=(),
        split_note="",
    )


def _peel_spectator(
    expr: sympy.Expr,
    var: sympy.Expr,
    partner: Optional[sympy.Expr],
) -> tuple[sympy.Expr, sympy.Expr, dict[str, Any]]:
    other = partner if partner is not None else expr
    split = split_edge(expr, other, degeneration=var)
    if not split.get("certified"):
        return _ONE, expr, split
    if split.get("mode") != "multiplicative":
        return _ONE, expr, split
    local = split["A_local"]
    spectator = split["S"]
    if local in (1, -1, _ONE, sympy.Integer(-1)):
        return _ONE, expr, split
    if not isinstance(local, sympy.Expr) or not isinstance(spectator, sympy.Expr):
        return _ONE, expr, split
    return spectator, local, split


def _split_pref_add(expr: sympy.Expr) -> tuple[sympy.Expr, sympy.Expr, bool]:
    """``expr = pref * Add``. Reconstruction required. No ``together``."""
    if isinstance(expr, sympy.Add):
        return _ONE, expr, True
    args = list(sympy.Mul.make_args(expr))
    adds = [a for a in args if isinstance(a, sympy.Add)]
    if not adds:
        return _ONE, expr, True
    pg_adds = [a for a in adds if a.atoms(sympy.polygamma)]
    if pg_adds:
        chosen = max(pg_adds, key=_ops)
    else:
        chosen = max(adds, key=_ops)
    rest = list(args)
    try:
        rest.remove(chosen)
    except ValueError:
        return _ONE, expr, False
    pref = sympy.Mul(*rest) if rest else _ONE
    ok = (pref * chosen) == expr
    if not ok:
        ok = _exact_eq(pref * chosen, expr)
    return pref, chosen, bool(ok)


def _atoms_from_terms(
    terms: Sequence[sympy.Expr],
    *,
    source_member: str,
    source_text_hash: str,
    degeneration: sympy.Expr,
    target_value: sympy.Expr,
    spectator: sympy.Expr,
) -> list[LaurentAtom]:
    prepared: list[tuple[tuple[Any, ...], LaurentAtom]] = []
    spec_s = str(spectator) if spectator != 1 else ""
    var_s = str(degeneration)
    point_s = str(target_value)
    for term in terms:
        atom_class, coeff, head, order, argument = _factor_term(term)
        digest = canonical_atom_hash(
            atom_class=atom_class,
            coefficient=coeff,
            function_head=head,
            function_order=order,
            argument=argument,
        )
        atom = LaurentAtom(
            atom_id="",
            source_member=source_member,
            coefficient=sympy.srepr(coeff),
            function_head=head,
            function_order=_srepr_or_empty(order),
            argument=_srepr_or_empty(argument),
            degeneration_variable=var_s,
            target_value=point_s,
            spectator=spec_s,
            source_text_hash=source_text_hash,
            canonical_atom_hash=digest,
            atom_class=atom_class,
        )
        prepared.append((_sort_key(atom, order), atom))
    prepared.sort(key=lambda row: row[0])
    out: list[LaurentAtom] = []
    for i, (_key, atom) in enumerate(prepared):
        atom.atom_id = f"{source_member}:{i:02d}:{atom.canonical_atom_hash[:12]}"
        out.append(atom)
    return out


def _factor_term(
    term: sympy.Expr,
) -> tuple[str, sympy.Expr, str, Any, Any]:
    factors = list(sympy.Mul.make_args(term))
    specials: list[sympy.Expr] = []
    others: list[sympy.Expr] = []
    for factor in factors:
        if isinstance(factor, sympy.polygamma) or isinstance(factor, sympy.log):
            specials.append(factor)
        elif isinstance(factor, sympy.Pow) and isinstance(
            factor.base, (sympy.polygamma, sympy.log)
        ):
            specials.append(factor)
        else:
            others.append(factor)
    coeff = sympy.Mul(*others) if others else _ONE
    if len(specials) == 1 and isinstance(specials[0], sympy.polygamma):
        pg = specials[0]
        if coeff.has(sympy.polygamma):
            return OTHER_UNSUPPORTED, term, "", "", ""
        return POLYGAMMA, coeff, "polygamma", pg.args[0], pg.args[1]
    if len(specials) == 1 and isinstance(specials[0], sympy.log):
        lg = specials[0]
        if coeff.has(sympy.log, sympy.polygamma):
            return OTHER_UNSUPPORTED, term, "", "", ""
        arg = lg.args[0] if lg.args else ""
        return LOG, coeff, "log", "", arg
    if specials:
        return OTHER_UNSUPPORTED, term, "", "", ""
    return _classify_nonspecial(term), term, "", "", ""


def _classify_nonspecial(term: sympy.Expr) -> str:
    if term.has(sympy.log):
        return LOG
    if term.has(sympy.polygamma):
        return OTHER_UNSUPPORTED
    if _is_power_monomial(term):
        return POWER
    try:
        if term.is_rational_function():
            return RATIONAL
    except Exception:
        pass
    return OTHER_UNSUPPORTED


def _is_power_monomial(term: sympy.Expr) -> bool:
    if isinstance(term, (sympy.Integer, sympy.Rational, sympy.Float, sympy.Symbol)):
        return True
    if isinstance(term, AppliedUndef):
        return True
    if isinstance(term, sympy.Pow):
        return not term.base.has(sympy.Add)
    if isinstance(term, sympy.Mul):
        return all(_is_power_monomial(arg) for arg in term.args)
    if term.is_number:
        return True
    return False


def _sort_key(atom: LaurentAtom, order: Any) -> tuple[Any, ...]:
    order_key: Any
    try:
        order_key = int(order) if order not in ("", None) else ""
    except (TypeError, ValueError):
        order_key = atom.function_order
    return (
        atom.atom_class,
        atom.function_head,
        order_key,
        atom.argument,
        atom.coefficient,
        atom.canonical_atom_hash,
    )


def _exact_eq(left: sympy.Expr, right: sympy.Expr) -> bool:
    if left == right:
        return True
    try:
        if sympy.expand(left - right) == 0:
            return True
    except Exception:
        pass
    try:
        if sympy.cancel(left - right) == 0:
            return True
    except Exception:
        pass
    return False


def _ops(expr: sympy.Expr) -> int:
    try:
        return int(sympy.count_ops(expr, visual=False))
    except Exception:
        return 0


def _as_expr(value: Any) -> sympy.Expr:
    if isinstance(value, sympy.Expr):
        return value
    if isinstance(value, bool):
        raise TypeError("bool is not a symbolic expression")
    if isinstance(value, int):
        return sympy.Integer(value)
    raise TypeError(type(value).__name__)


def _as_var(value: Any) -> sympy.Expr:
    if isinstance(value, sympy.Expr):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if raw.startswith("epsilon(") and raw.endswith(")"):
            name = raw[len("epsilon(") : -1]
            return sympy.Function("epsilon")(sympy.Symbol(name, real=True))
        if raw:
            return sympy.Symbol(raw)
        raise ValueError("empty variable")
    raise TypeError(type(value).__name__)


def _srepr_or_empty(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, sympy.Basic):
        return sympy.srepr(value)
    return str(value)


def _from_srepr(text: str) -> sympy.Expr:
    try:
        val = sympy.sympify(text)
    except Exception as exc:
        raise ReconstructionError(f"srepr:{type(exc).__name__}") from exc
    if not isinstance(val, sympy.Expr):
        raise ReconstructionError("srepr:not_expr")
    return val


def _atom_from_dict(blob: dict[str, Any]) -> LaurentAtom:
    fields = LaurentAtom.__dataclass_fields__
    kwargs = {key: blob.get(key, "") for key in fields}
    return LaurentAtom(**kwargs)
