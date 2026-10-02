"""Step cards: one YAML file per derivation step, run by one command.

A card spells out what an agent would otherwise have to thread through
several flags: the symbols (with ``positive: true`` where a sign matters),
arbitrary smooth functions, named definitions that may call each other, and
the check to run. See docs/encoding-cookbook.md for one card per step type.

    symbols:
      - {name: beta, positive: true}
      - {name: G, positive: true}
      - {name: e}
    functions: [f]                 # arbitrary smooth functions (optional)
    labels: [n, m]                 # label symbols for index-swap diagnosis
    define:
      zp(x): 1/2 + beta*(G + I*x)/(2*pi)
      fp(x): 1/2 + I/pi*polygamma(0, zp(x))
    check: identity                # identity | coefficient | remainder |
                                   # fermi_integral | matsubara | operator |
                                   # langreth | numeric_integral
    lhs: ...
    rhs: ...
    source_document: sheet.md      # optional transcription check, see fidelity.py
    notation: {e_nm: (e_n - e_m)}
    source: {rhs: "verbatim quote of the claim"}

The result carries ``decision`` (VALID / INVALID / NOT_DECIDED), which is
NOT_DECIDED whenever the card does not match its quoted source.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from ..models import AdapterError

CHECKS = ("identity", "coefficient", "remainder", "fermi_integral", "series", "matsubara",
          "operator", "langreth", "numeric_integral", "definite_integral")


class CardError(ValueError):
    pass


def _names(value) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(v.strip() for v in value.split(",") if v.strip())
    return tuple(str(v) for v in value)


def _need(card: dict, *keys: str) -> list:
    missing = [k for k in keys if k not in card]
    if missing:
        raise CardError(f"card for check '{card.get('check')}' needs: {', '.join(missing)}")
    return [str(card[k]) if not isinstance(card[k], (int, list)) else card[k] for k in keys]


def load_card(source: str | Path | dict) -> dict:
    if isinstance(source, dict):
        card = source
    else:
        card = yaml.safe_load(Path(source).read_text(encoding="utf-8"))
    if not isinstance(card, dict) or card.get("check") not in CHECKS:
        raise CardError(f"card must be a mapping with check in {CHECKS}")
    return card


REQUIRE_SOURCE_ENV = "SYMBOLIC_COMPACTIFICATION_REQUIRE_SOURCE"
_MERGED_MAPS = ("define", "notation")
_EXPRESSION_KEYS = ("lhs", "rhs", "claim", "expr", "integrand", "function",
                    "approximant", "summand", "lower_limit", "upper_limit")


def _symbol_entries(value) -> dict[str, dict]:
    out = {}
    for s in value or []:
        entry = {"name": s} if isinstance(s, str) else {k: v for k, v in dict(s).items() if k != "stated"}
        out[str(entry["name"])] = entry
    return out


def _squash(text: Any) -> str:
    return " ".join(str(text).split())


def resolve_includes(card: dict, base_dir: Path | None) -> tuple[dict, list[str]]:
    """Merge shared convention files named under ``include:``.

    A card may add names, but it may not give a shared symbol, definition or
    notation entry a different meaning; each such override is returned as a
    conflict, and a card with a conflict is not decided.
    """
    includes = card.get("include") or []
    if isinstance(includes, str):
        includes = [includes]
    if not includes:
        return card, []
    shared: dict[str, Any] = {"symbols": {}, "define": {}, "notation": {}, "functions": [],
                              "source": {}, "multiply": []}
    conflicts: list[str] = []
    for item in includes:
        path = Path(str(item))
        if not path.is_absolute() and base_dir is not None:
            path = base_dir / path
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise CardError(f"include {item} must be a mapping")
        for name, entry in _symbol_entries(data.get("symbols")).items():
            if name in shared["symbols"] and shared["symbols"][name] != entry:
                conflicts.append(f"symbol {name} differs between includes")
            shared["symbols"][name] = entry
        for key in _MERGED_MAPS:
            for k, v in (data.get(key) or {}).items():
                if k in shared[key] and _squash(shared[key][k]) != _squash(v):
                    conflicts.append(f"{key} {k} differs between includes")
                shared[key][str(k)] = str(v)
        shared["functions"] += list(_names(data.get("functions")))
        shared["multiply"] += list(_names(data.get("multiply")))
        if data.get("noncommuting"):
            shared["noncommuting"] = str(data["noncommuting"])
        for key in ("distribution_not_thermal", "distribution_in_text", "log_base"):
            if data.get(key):
                shared[key] = str(data[key])
        if isinstance(data.get("stated_values"), dict):
            shared.setdefault("stated_values", {}).update(data["stated_values"])
        shared.setdefault("either", []).extend(_names(data.get("either")))
        for key in ("named_quantities", "named_functions", "integers", "valued_in_text", "stated_numbers",
                    "operators", "constrained", "builtins_redefined", "subscript_collisions"):
            shared.setdefault(key, []).extend(_names(data.get(key)))
        for k, v in (data.get("source") or {}).items():       # quoted shared definitions
            if not str(k).startswith("define:"):
                raise CardError(f"include {item}: only define: quotes may be shared")
            shared["source"][str(k)] = v
        if data.get("source_document") and "source_document" not in shared:
            doc = Path(str(data["source_document"]))
            shared["source_document"] = str(doc if doc.is_absolute() else path.parent / doc)
    merged = dict(card)
    own_symbols = _symbol_entries(card.get("symbols"))
    for name, entry in own_symbols.items():
        if name in shared["symbols"] and shared["symbols"][name] != entry:
            conflicts.append(f"card redefines shared symbol {name}")
    merged["symbols"] = list({**shared["symbols"], **own_symbols}.values())
    for key in _MERGED_MAPS:
        own = {str(k): str(v) for k, v in (card.get(key) or {}).items()}
        for k, v in own.items():
            if k in shared[key] and _squash(shared[key][k]) != _squash(v):
                conflicts.append(f"card redefines shared {key} {k}")
        merged[key] = {**shared[key], **own}
    merged["functions"] = sorted(set(shared["functions"]) | set(_names(card.get("functions"))))
    merged["multiply"] = sorted(set(shared["multiply"]) | set(_names(card.get("multiply"))))
    for key in ("named_quantities", "named_functions", "either", "integers", "valued_in_text",
                "stated_numbers", "operators", "constrained", "builtins_redefined",
                "subscript_collisions"):
        merged[key] = sorted(set(shared.get(key, [])) | set(_names(card.get(key))))
    own_source = dict(card.get("source") or {})
    for k, v in shared["source"].items():
        if k in own_source and own_source[k] != v:
            conflicts.append(f"card redefines shared quote {k}")
    if shared["source"]:
        merged["source"] = {**shared["source"], **own_source}
    for key in ("noncommuting", "distribution_not_thermal", "distribution_in_text", "log_base"):
        if shared.get(key) and key not in card:
            merged[key] = shared[key]
    if shared.get("stated_values"):
        merged["stated_values"] = {**shared["stated_values"], **(card.get("stated_values") or {})}
    if "source_document" not in card and "source_document" in shared:
        merged["source_document"] = shared["source_document"]
    return merged, conflicts


def _require_source(flag: bool | None) -> bool:
    if flag is not None:
        return flag
    return os.environ.get(REQUIRE_SOURCE_ENV, "").strip().lower() in ("1", "true", "yes")


def _missing_quotes(card: dict, transcription: dict) -> list[str]:
    """Expression fields not backed by a matching quote. A bare integer such
    as the 0 of 'f = O(x^n)' cannot be mistranscribed and needs no quote."""
    fields = dict(transcription.get("fields", {}))
    if fields.get("integral", {}).get("status") == "MATCH":   # one quote backs all three pieces
        fields.update({k: fields["integral"] for k in ("integrand", "lower_limit", "upper_limit")})
    return [k for k in _EXPRESSION_KEYS
            if k in card and fields.get(k, {}).get("status") != "MATCH"
            and not (k == "approximant" and re.fullmatch(r"\s*0\s*", str(card[k])))]


def _declared_beta(card: dict, symbols: list) -> str | None:
    """The inverse temperature, when the card declares it (for nF / nB)."""
    name = str(card.get("beta", "beta"))
    return name if any((s if isinstance(s, str) else s.get("name")) == name for s in symbols) else None


def _remainder_both(card, f, P, variable, order, symbols, functions, positive, defs,
                    points=None) -> dict:
    """The text states no limit point: check x -> 0 and x -> oo (or x -> +oo and
    x -> -oo for a tail with no stated side), decide only when both agree (a
    remainder true at one point and false at the other means the claim
    depends on a point the paper did not state)."""
    from . import certify_remainder
    runs = {}
    points = points or (("0", str(card.get("direction", "+-"))), ("oo", "+-"))
    for point, direction in points:
        runs[point] = certify_remainder(
            f, P, variable=variable, point=point, order=order, direction=direction,
            symbols=symbols, functions=functions, positive=positive, definitions=defs,
            beta=_declared_beta(card, symbols)).to_dict()
    statuses = {r["status"] for r in runs.values()}
    first = runs[points[0][0]]
    if len(statuses) == 1 and statuses & {"CERTIFIED_BY_RULE", "NONZERO"}:
        out = dict(first)
        out["reasons"] = list(out.get("reasons", [])) + [
            "SAME_VERDICT_AT_" + "_AND_".join(p for p, _ in points)]
        return out
    return {**first, "status": "UNKNOWN",
            "reasons": ["LIMIT_POINT_UNSTATED: the verdict differs between "
                        + " and ".join(f"x -> {p}" for p, _ in points)
                        if statuses >= {"CERTIFIED_BY_RULE", "NONZERO"} else "LIMIT_POINT_UNSTATED"],
            **{f"at_{p}": r["status"] for p, r in runs.items()}}


def _named_quantity_blockers(card: dict, defs: dict, check: str) -> list[str]:
    """Names the paper gives a value somewhere (a side of a relation that is
    just the name, up to sign and a number). Used without a definition, they
    would be free symbols, and a restatement such as '-S = ...' could be
    refuted wrongly."""
    if check == "langreth":
        return []
    plain = set(_names(card.get("named_quantities")))
    funcs = set(_names(card.get("named_functions")))
    if not plain and not funcs:
        return []
    defined = {k.split("(")[0].strip() for k in defs}
    texts = " ".join(str(card[k]) for k in _EXPRESSION_KEYS if k in card)
    used_plain = set(re.findall(r"(?<![A-Za-z0-9_])([A-Za-z_][A-Za-z0-9_]*)(?!\s*\(|[A-Za-z0-9_])", texts))
    used_calls = set(re.findall(r"(?<![A-Za-z0-9_])([A-Za-z_][A-Za-z0-9_]*)\s*\(", texts))
    return sorted(((plain & used_plain) | (funcs & used_calls)) - defined)


_INDEX_LETTERS = frozenset("nmljk")


def _integer_like(name: str, stated: set[str]) -> bool:
    """n, m, l, j, k, a Matsubara-style name (omega_n, nu_m, omega_nu) or a
    name the text calls an integer or a Matsubara frequency."""
    return name in stated or name in _INDEX_LETTERS or bool(re.search(r"_(?:[nmljk]|nu)$", name))


def _periodic_blockers(card: dict, symbols: list, functions, defs: dict) -> list[str]:
    """Integer-like names inside exp, sin or cos. e^{2 pi i n} = 1 holds for an
    integer n and fails for a generic one, so a refutation found with n
    generic may be wrong; such an INVALID is not reported."""
    import sympy
    from .calculus import CalculusSpace
    stated = set(_names(card.get("integers")))
    bound = {str(card.get("variable"))} if card.get("variable") else set()
    try:
        space = CalculusSpace(symbols, functions, definitions=defs)
        exprs = [space.parse_expanded(str(card[k])) for k in _EXPRESSION_KEYS if k in card]
    except Exception:                    # an unreadable card cannot be refuted anyway
        return []
    hits = set()
    for expr in exprs:
        for f in expr.atoms(sympy.exp, sympy.sin, sympy.cos, sympy.tan, sympy.Pow):
            if isinstance(f, sympy.Pow) and not f.exp.free_symbols:
                continue                 # x**2: not periodic
            hits |= {str(x) for x in f.free_symbols if _integer_like(str(x), stated)} - bound
    return sorted(hits)


def _branch_sensitive(card: dict, symbols: list, functions, defs: dict, positive) -> list[str]:
    """Symbols not stated positive inside sqrt, log, |.| or a non-integer power."""
    import sympy
    from .calculus import CalculusSpace
    try:
        space = CalculusSpace(symbols, functions, definitions=defs)
        exprs = [space.parse_expanded(str(card[k])) for k in _EXPRESSION_KEYS if k in card]
    except Exception:
        return []
    sure = {str(x) for x in positive}
    hits: set[str] = set()
    for e in exprs:
        for a in e.atoms(sympy.Pow, sympy.log, sympy.Abs):
            if isinstance(a, sympy.Pow) and (a.exp.is_Integer or not a.base.free_symbols):
                continue
            hits |= {str(x) for x in a.free_symbols} - sure
    return sorted(hits)


def _holds_at_special_phases(card: dict, symbols: list, functions, defs: dict, check: str,
                             out: dict) -> bool:
    """Whether the refuted equality becomes exact once a phase factor takes a
    special value: e^{iu} = 1 or -1, sin u = 0, cos u = 1 or -1."""
    import sympy
    from .calculus import CalculusSpace, _simplify_zero
    try:
        space = CalculusSpace(symbols, functions, definitions=defs)
        if check == "identity":
            residual = space.parse_expanded(str(card["lhs"])) - space.parse_expanded(str(card["rhs"]))
        elif check == "definite_integral" and out.get("derived"):
            residual = sympy.sympify(str(out["derived"]), locals={str(x): x for x in
                                     space.parse_expanded(str(card["claim"])).free_symbols}) \
                - space.parse_expanded(str(card["claim"]))
        else:
            return False
    except Exception:
        return False
    phases = [a for a in residual.atoms(sympy.exp) if a.args[0].has(sympy.I)]
    trig = list(residual.atoms(sympy.sin, sympy.cos))
    if not phases and not trig:
        return False
    for value in (1, -1):
        trial = residual.subs({a: value for a in phases})
        trial = trial.subs({a: (0 if isinstance(a, sympy.sin) else value) for a in trig})
        try:
            if _simplify_zero(sympy.expand(trial)):
                return True
        except Exception:
            return True                    # cannot tell: do not refute
    return False


def _reordering_only(card: dict, check: str) -> bool:
    """lhs and rhs are the same product up to the order of factors and a sign
    (A B = B A, c_k c_q = -c_q c_k): a statement about operators."""
    if check != "identity" or "lhs" not in card or "rhs" not in card:
        return False
    factors = lambda t: re.findall(r"[A-Za-z_][A-Za-z0-9_]*(?:\([^()]*\))?", t)
    lhs, rhs = (re.sub(r"\s+", "", str(card[k])).lstrip("-+") for k in ("lhs", "rhs"))
    plain = lambda t: re.fullmatch(r"[A-Za-z0-9_*()]+", t) is not None
    left, right = factors(lhs), factors(rhs)
    return plain(lhs) and plain(rhs) and len(left) >= 2 and sorted(left) == sorted(right) \
        and left != right                 # the same factors in a different order


def _derivative_parameters(card: dict, symbols: list, functions, defs: dict) -> list[str]:
    """Symbols other than the variable inside a Diff(...): the derivative holds
    them fixed, which the paper need not mean (omega(t), mu(n))."""
    texts = [str(card[k]) for k in _EXPRESSION_KEYS if k in card]
    quotes = " ".join(str(v.get("quote") if isinstance(v, dict) else v) for v in (card.get("source") or {}).values())
    if not any("Diff(" in t for t in texts) or not re.search(r"\\partial|\\frac\s*\{\s*(?:d|\\mathrm\{d\})", quotes):
        return []                       # only a derivative read from the paper's LaTeX
    import sympy
    from .calculus import CalculusSpace
    try:
        space = CalculusSpace(symbols, functions, definitions=defs)
        exprs = [space.parse(t) for t in texts]
    except Exception:
        return []
    held: set[str] = set()
    for e in exprs:
        for call in e.atoms(sympy.Function):
            if type(call).__name__ == "Diff" and len(call.args) == 3:
                operand, variable = call.args[0], call.args[1]
                held |= {str(x) for x in space.expand(operand).free_symbols} - {str(variable)}
    return sorted(held)


def _arbitrary_functions(card: dict, functions, defs: dict) -> list[str]:
    """Declared functions without a definition that the card's expressions call."""
    declared = set(functions) - {k.split("(")[0].strip() for k in defs}
    if not declared:
        return []
    texts = " ".join(str(card[k]) for k in _EXPRESSION_KEYS if k in card)
    called = set(re.findall(r"(?<![A-Za-z0-9_])(?:DD_|D_)?([A-Za-z_][A-Za-z0-9_]*)\s*\(", texts))
    return sorted(called & declared)


def _valued_free_names(card: dict, defs: dict) -> list[str]:
    names = set(_names(card.get("valued_in_text"))) - {k.split("(")[0].strip() for k in defs}
    if not names:
        return []
    texts = " ".join(str(card[k]) for k in _EXPRESSION_KEYS if k in card)
    return sorted(names & set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", texts)))


def _singular_at_stated_values(card: dict, symbols: list, functions, defs: dict) -> list[str]:
    """Names the text sets to a number ($a = 0$) at which an expression of
    the card is undefined ((e^a - 1)/a): the generic identity says nothing
    there."""
    import sympy
    from .calculus import CalculusSpace
    stated = card.get("stated_values") or {}
    if not isinstance(stated, dict) or not stated:
        return []
    try:
        space = CalculusSpace(symbols, functions, definitions=defs)
        exprs = [space.parse_expanded(str(card[k])) for k in _EXPRESSION_KEYS if k in card]
    except Exception:                    # an unreadable card is not decided anyway
        return []
    hits = []
    for name, numbers in stated.items():
        symbol = next((x for e in exprs for x in e.free_symbols if str(x) == name), None)
        if symbol is None:
            continue
        for number in numbers if isinstance(numbers, list) else [numbers]:
            try:
                values = [sympy.simplify(e.subs(symbol, sympy.sympify(str(number)))) for e in exprs]
            except Exception:
                hits.append(name)
                break
            if any(v.has(sympy.zoo, sympy.nan, sympy.oo, -sympy.oo) for v in values):
                hits.append(name)
                break
    return sorted(set(hits))


# for each check: the fields on each side of the claimed equality, and the
# field naming a bound variable that belongs to neither side
_SIDES = {
    "identity": (("lhs",), ("rhs",), None),
    "coefficient": (("expr",), ("claim",), None),
    "remainder": (("function",), ("approximant",), None),
    "definite_integral": (("integrand", "lower_limit", "upper_limit"), ("claim",), "variable"),
    "fermi_integral": (("integrand",), ("claim",), "variable"),
    "series": (("summand",), ("claim",), "variable"),
    "numeric_integral": (("integrand",), ("claim",), "variable"),
}


def _one_sided(card: dict, symbols: list, functions, defs: dict, check: str) -> list[str]:
    """Symbols that occur on one side of the claimed equality only. Such a
    relation can be read as fixing that symbol (Gamma/(2 pi rho) = V^2,
    e^{iqL} = 1, cos(Omega t) = -1): it is a definition or a condition, not
    an identity, and refuting it as an identity would be wrong."""
    if check not in _SIDES:
        return []
    from .calculus import CalculusSpace
    left_keys, right_keys, bound_key = _SIDES[check]
    bound = {str(card[bound_key])} if bound_key and card.get(bound_key) else set()
    if check == "remainder":
        bound.add(str(card.get("variable", "")))
    beta = str(card.get("beta", "beta"))

    def side_symbols(keys, parse):
        found = set().union(*[{str(x) for x in parse(str(card[k])).free_symbols}
                              for k in keys if k in card] or [set()])
        if any(re.search(r"\bn[FB]\s*\(", str(card.get(k, ""))) for k in keys):
            found.add(beta)                                     # n_F(x) carries beta
        return found
    try:
        space = CalculusSpace(symbols, functions, definitions=defs)
        written = [side_symbols(keys, space.parse) for keys in (left_keys, right_keys)]
        expanded = [side_symbols(keys, space.parse_expanded) for keys in (left_keys, right_keys)]
    except Exception:                    # an unreadable card is not decided anyway
        return []
    # one-sided as written and after the definitions are used: a symbol hidden in
    # a definition on the other side (Gamma_R inside Sigma) is not a free choice
    return sorted(((written[0] ^ written[1]) & (expanded[0] ^ expanded[1])) - bound)


_APPROXIMATE = re.compile(r"(?<![A-Za-z_])\d+\.\d+")


def _lhs_is_a_name(card: dict, defs: dict) -> bool:
    lhs = str(card.get("lhs", ""))
    m = re.fullmatch(r"\(*\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)*", lhs)
    return bool(m) and m.group(1) not in {k.split("(")[0].strip() for k in defs}


def _realness_blockers(card: dict, raw_symbols: list, defs: dict | None = None) -> list[str]:
    names = {str(s["name"]) for s in raw_symbols      # real: true written by a person settles it
             if isinstance(s, dict) and s.get("realness") == "unstated" and not s.get("positive")
             and s.get("real") is not True}
    if not names:
        return []
    texts = " ".join(str(card[k]) for k in _EXPRESSION_KEYS if k in card)
    bodies = {k.split("(")[0].strip(): v for k, v in (defs or {}).items()}
    expanded, seen = texts, set()
    for _ in range(len(bodies)):          # names used through definitions count too
        called = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expanded)) & set(bodies) - seen
        if not called:
            break
        seen |= called
        expanded += " " + " ".join(bodies[n] for n in called)
    infinite = card.get("check") == "definite_integral" and any(
        "oo" in str(card.get(k, "")) for k in ("lower_limit", "upper_limit"))   # decay needs real parts
    if card.get("check") == "fermi_integral":
        # the shift c in n_F(w + c) must be real for the half-plane split
        shifts = " ".join(re.findall(r"\bn[FB]\s*\(([^()]*)\)", str(card.get("integrand", ""))))
        unstated = names & set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", shifts)) - {str(card.get("variable"))}
        if unstated:
            return sorted(unstated)
    if not infinite and not re.search(r"\b(?:re|im|conjugate|Abs)\s*\(", expanded):
        return []
    used = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expanded))
    return sorted(names & used)


def _used_symbols(symbols: list, card: dict, defs: dict) -> list:
    """Only the declared symbols a card actually uses: a shared conventions
    file may declare many more than one check can take."""
    texts = [str(card[k]) for k in _EXPRESSION_KEYS if k in card]
    texts += [*defs.values(), *defs.keys(), str(card.get("variable", "z")), str(card.get("beta", "beta")),
              str(card.get("infinitesimal", "")), *map(str, _names(card.get("labels")))]
    used = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", " ".join(texts)))
    kept = [s for s in symbols if (s if isinstance(s, str) else s.get("name")) in used]
    return kept or symbols[:1]


def _shared_definition_names(card: dict, base_dir: Path | None) -> set[str]:
    """Definitions that come from include files (shared conventions)."""
    includes = card.get("include") or []
    includes = [includes] if isinstance(includes, str) else list(includes)
    names: set[str] = set()
    for item in includes:
        path = Path(str(item))
        if not path.is_absolute() and base_dir is not None:
            path = base_dir / path
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        names |= {str(k).split("(")[0].strip() for k in (data.get("define") or {})}
        names |= {str(k).split(":", 1)[1].split("(")[0].strip()
                  for k in (data.get("source") or {}) if str(k).startswith("define:")}
    return names


_AMBIGUOUS = re.compile(r"SOURCE_APPLICATION_AMBIGUOUS:([A-Za-z_][A-Za-z0-9_]*)")
_NO_PRODUCT = re.compile(r"SOURCE_PRODUCT_WITH_COMMA:([A-Za-z_][A-Za-z0-9_]*)")
_BARE_CALL = re.compile(r"SOURCE_FUNCTION_WITHOUT_ARGUMENTS:([A-Za-z_][A-Za-z0-9_]*)")
_DECIDED = ("VALID", "INVALID")


def run_card(source: str | Path | dict, *, require_source: bool | None = None) -> dict[str, Any]:
    card = load_card(source)
    base_dir = None if isinstance(source, dict) else Path(source).resolve().parent
    shared_defs = _shared_definition_names(card, base_dir)
    card, conflicts = resolve_includes(card, base_dir)
    result = _run_resolved(dict(card), base_dir, shared_defs, conflicts, require_source)
    either = set(_names(card.get("either"))) - set(_names(card.get("functions"))) \
        - set(_names(card.get("multiply")))
    return _both_readings(card, result, either, base_dir, shared_defs, conflicts, require_source)


def _blockers(result: dict, pattern) -> set[str]:
    return {m.group(1) for r in result.get("decision_blocked_by") or [] for m in pattern.finditer(str(r))}


_MAX_READ_BOTH_WAYS = 3


def _reading(card, functions: set[str], products: set[str], base_dir, shared_defs, conflicts,
             require_source) -> dict:
    """Run the card with some ``either:`` names as functions, others as factors."""
    variant = dict(card)
    variant["functions"] = sorted(set(_names(card.get("functions"))) | functions)
    variant["multiply"] = sorted(set(_names(card.get("multiply"))) | products)
    # a function is not also a symbol; a factor must be one
    others = [s for s in card.get("symbols") or []
              if (s if isinstance(s, str) else s.get("name")) not in functions | products]
    variant["symbols"] = others + [{"name": n} for n in sorted(products)]
    return _run_resolved(variant, base_dir, shared_defs, conflicts, require_source)


def _both_readings(card, result, either, base_dir, shared_defs, conflicts, require_source) -> dict:
    """Names the paper writes right before '(' without saying whether they
    multiply or are functions (``either:``). The card is checked under every
    assignment of function/product to those names, and only VALID can come
    out of it: VALID needs every possible reading to be VALID. A reading
    that cannot exist (a product K(a, b) with a comma) drops out. An
    INVALID is never reported, because as a function the name stands for an
    arbitrary function, while the paper may mean a specific one (theta(t),
    the Fermi function, a delta function)."""
    from itertools import product as assignments
    applied: set[str] = set()
    for _ in range(len(either) + 1):
        new = (_blockers(result, _AMBIGUOUS) & either) - applied
        if not new:
            break
        applied |= new
        result = _reading(card, applied, set(), base_dir, shared_defs, conflicts, require_source)
    if not applied:
        return result
    names = sorted(applied)
    numbers = set(_names(card.get("stated_numbers")))
    out = dict(result)
    if len(names) > _MAX_READ_BOTH_WAYS:
        out["decision"] = "NOT_DECIDED"
        out["decision_blocked_by"] = list(result.get("decision_blocked_by") or []) + [
            f"FUNCTION_OR_PRODUCT:{','.join(names)} (too many names to read both ways)"]
        return out
    readings: dict[str, str] = {}
    for choice in assignments(("function", "product"), repeat=len(names)):
        functions = {n for n, c in zip(names, choice) if c == "function"}
        products = applied - functions
        run = result if not products else _reading(card, functions, products, base_dir,
                                                   shared_defs, conflicts, require_source)
        label = ", ".join(f"{n} as {c}" for n, c in zip(names, choice))
        if _blockers(run, _NO_PRODUCT) & products:
            readings[label] = "IMPOSSIBLE"
            continue
        if _blockers(run, _BARE_CALL) & functions & numbers:
            # written bare in this card too, and called a real/positive number in the text
            readings[label] = "IMPOSSIBLE"
            continue
        readings[label] = run["decision"] if not (_blockers(run, _AMBIGUOUS) & either - applied) \
            else "NOT_DECIDED"
    out["readings"] = {"names": names, **readings}
    possible = [d for d in readings.values() if d != "IMPOSSIBLE"]
    if possible and all(d == "VALID" for d in possible):
        out["decision"] = "VALID"
        out["decision_blocked_by"] = []
    else:
        out["decision"] = "NOT_DECIDED"
        out["decision_blocked_by"] = list(result.get("decision_blocked_by") or []) + [
            f"FUNCTION_OR_PRODUCT:{','.join(names)} (" + "; ".join(f"{k}: {v}" for k, v in readings.items()) + ")"]
    return out


def _run_resolved(card: dict, base_dir, shared_defs, conflicts, require_source) -> dict[str, Any]:
    raw = card.get("symbols") or []
    symbols = [{k: v for k, v in s.items() if k in ("name", "real", "nonzero")}
               if isinstance(s, dict) else s for s in raw]
    card["symbols"] = raw
    # a positive symbol is real; an explicit real: false is complex
    symbols = [{**s, "real": True} if isinstance(s, dict)
               and any(isinstance(r, dict) and r.get("name") == s["name"] and r.get("positive") for r in raw)
               else s for s in symbols]
    positive = tuple(s["name"] for s in raw if isinstance(s, dict) and s.get("positive")) \
        + _names(card.get("positive"))
    functions = _names(card.get("functions"))
    from .fidelity import fill_from_source, with_default_functions
    card, filled = fill_from_source(card, base_dir, symbols=symbols, functions=functions)
    defs = {str(k): str(v) for k, v in (card.get("define") or {}).items()}
    symbols = _used_symbols(symbols, card, defs) or [{"name": "unused_symbol"}]   # zeta(4) = pi^4/90 has none
    kept = {s if isinstance(s, str) else s["name"] for s in symbols}
    positive = tuple(n for n in positive if n in kept)
    defs = with_default_functions(
        defs, [str(card[k]) for k in _EXPRESSION_KEYS if k in card] + list(defs.values()),
        declared=[*(s if isinstance(s, str) else s["name"] for s in symbols), *functions])
    labels = _names(card.get("labels"))
    check = card["check"]
    failures = card.get("_source_failures") or {}
    try:
        out = _dispatch(card, check, symbols, positive, functions, defs, labels)
    except CardError:
        if not failures:
            raise
        from .fidelity import check_transcription
        needed = {k: v for k, v in failures.items() if not k.startswith("define:")}
        blocked = [f"SOURCE_UNREADABLE:{k}:{v}" for k, v in sorted((needed or failures).items())]
        return {"check": check, "decision": "NOT_DECIDED", "decision_blocked_by": blocked,
                "transcription_verified": False, "require_source": _require_source(require_source),
                "status": "UNKNOWN", "reasons": blocked,
                "transcription": check_transcription(card, symbols=symbols, functions=functions,
                                                     definitions=defs, positive=positive,
                                                     base_dir=base_dir, filled=filled),
                "unquoted_definitions": [], "notation_used": card.get("notation") or {},
                "convention_conflicts": conflicts, "built_from_source": filled}
    return _finish(card, check, out, symbols, positive, functions, defs, conflicts, filled,
                   base_dir, shared_defs, require_source)


def _dispatch(card, check, symbols, positive, functions, defs, labels) -> dict:
    from . import (certify_remainder, check_frequency_integral, verify_identity,
                   verify_langreth, verify_matsubara_sum, verify_operator_identity,
                   verify_series_coefficient)
    from .fermi_integral import verify_fermi_integral
    if check == "identity":
        lhs, rhs = _need(card, "lhs", "rhs")
        out = verify_identity(lhs, rhs, symbols=symbols, functions=functions, positive=positive,
                              definitions=defs, labels=labels)
    elif check == "coefficient":
        expr, claim, variable, order = _need(card, "expr", "claim", "variable", "order")
        out = verify_series_coefficient(expr, claim, variable=variable, order=int(order),
                                        symbols=symbols, functions=functions, positive=positive,
                                        definitions=defs, labels=labels)
    elif check == "remainder":
        f, P, variable, point, order = _need(card, "function", "approximant", "variable", "point", "order")
        if str(point) in ("unstated", "+-oo"):
            return _remainder_both(card, f, P, variable, int(order), symbols, functions,
                                   positive, defs,
                                   points=(("oo", "+-"), ("-oo", "+-")) if str(point) == "+-oo" else None)
        out = certify_remainder(f, P, variable=variable, point=point, order=int(order),
                                direction=str(card.get("direction", "+-")), symbols=symbols,
                                functions=functions, positive=positive, definitions=defs,
                                beta=_declared_beta(card, symbols)).to_dict()
    elif check == "fermi_integral":
        integrand, claim, variable, beta = _need(card, "integrand", "claim", "variable", "beta")
        out = verify_fermi_integral(integrand, claim, variable=variable, beta=beta, symbols=symbols,
                                    functions=functions, definitions=defs, positive=positive,
                                    infinitesimal=card.get("infinitesimal"))
    elif check == "series":
        from .series import verify_series_sum
        summand, claim, variable = _need(card, "summand", "claim", "variable")
        out = verify_series_sum(summand, claim, variable=variable, symbols=symbols,
                                lower=int(card.get("lower", 0)), functions=functions,
                                definitions=defs, positive=positive)
    elif check == "matsubara":
        summand, claim, statistics = _need(card, "summand", "claim", "statistics")
        out = verify_matsubara_sum(summand, claim, variable=str(card.get("variable", "z")),
                                   beta=str(card.get("beta", "beta")), statistics=statistics,
                                   convergence=str(card.get("convergence", "none")),
                                   symbols=symbols, functions=functions,
                                   declared_rules=_names(card.get("rules")),
                                   positive=positive).to_dict()
    elif check == "operator":
        lhs, rhs = _need(card, "lhs", "rhs")
        out = dict(verify_operator_identity(lhs, rhs, operators=_names(card.get("operators")),
                                            scalars=_names(card.get("scalars")),
                                            hermitian=_names(card.get("hermitian"))))
    elif check == "definite_integral":
        from .definite import verify_definite_integral
        integrand, claim, variable, lower, upper = _need(card, "integrand", "claim", "variable",
                                                         "lower_limit", "upper_limit")
        out = verify_definite_integral(integrand, claim, variable=variable, lower=lower,
                                       upper=upper, symbols=symbols, functions=functions,
                                       definitions=defs, positive=positive)
    elif check == "langreth":
        component, claim = _need(card, "component", "claim")
        out = dict(verify_langreth(_names(card.get("product")), component, claim))
    else:
        integrand, claim, variable = _need(card, "integrand", "claim", "variable")
        out = check_frequency_integral(integrand, claim, variable=variable, symbols=symbols,
                                       functions=functions, beta=card.get("beta"),
                                       positive=positive)
    return out


def _finish(card, check, out, symbols, positive, functions, defs, conflicts, filled,
            base_dir, shared_defs, require_source) -> dict:
    from .fidelity import ABSENT, check_transcription, decide
    try:
        transcription = check_transcription(card, symbols=symbols, functions=functions,
                                            definitions=defs, positive=positive,
                                            base_dir=base_dir, filled=filled)
    except AdapterError as exc:
        transcription = {"status": "UNCHECKED", "fields": {}, "reason": exc.code}
    verdict = out.get("status") or out.get("verdict")
    decision = decide(verdict, transcription["status"])
    why = []
    if conflicts:
        why.append("CONVENTION_CONFLICT")
    if transcription["status"] in ("MISMATCH", "NOT_IN_DOCUMENT"):
        why.append(f"TRANSCRIPTION_{transcription['status']}")
    strict = _require_source(require_source)
    missing = _missing_quotes(card, transcription) if strict else []
    if strict and missing:
        why.append("SOURCE_REQUIRED:" + ",".join(missing))
    if strict and not card.get("source_document"):
        why.append("SOURCE_DOCUMENT_REQUIRED")
    quoted = {k.split(":", 1)[1].split("(")[0].strip()
              for k, f in (transcription.get("fields") or {}).items()
              if k.startswith("define:") and f.get("status") == "MATCH"}
    from .fidelity import DEFAULT_FUNCTIONS
    builtin = {k.split("(")[0] for k in DEFAULT_FUNCTIONS}
    ad_hoc = sorted(k.split("(")[0].strip() for k in defs
                    if k.split("(")[0].strip() not in quoted | shared_defs | builtin)
    if strict and ad_hoc:                  # a card's own definitions must be quoted
        why.append("UNQUOTED_CARD_DEFINITION:" + ",".join(ad_hoc))
    texts_all = " ".join(str(card[k]) for k in _EXPRESSION_KEYS if k in card)
    if card.get("distribution_in_text") and (check in ("matsubara", "fermi_integral")
                                            or re.search(r"\bn[FB]\s*\(", texts_all)):
        why.append("DISTRIBUTION_IN_TEXT")     # the paper's n_F (with mu, say) may not be the built-in one
    if card.get("distribution_not_thermal") and re.search(
            r"\bn[FB]\s*\(", " ".join(str(card[k]) for k in _EXPRESSION_KEYS if k in card)) \
            or (card.get("distribution_not_thermal") and check in ("matsubara", "fermi_integral")):
        why.append("DISTRIBUTION_NOT_THERMAL")    # the text says n_F is not the Fermi function
    operators = set(_names(card.get("operators")))
    if operators and check not in ("langreth", "operator"):
        used = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*",
                              " ".join(str(card[k]) for k in _EXPRESSION_KEYS if k in card)))
        if used & operators:
            why.append("OPERATORS:" + ",".join(sorted(used & operators)))   # products need not commute
    if _reordering_only(card, check):
        # A B = B A or c_k c_q = -c_q c_k is a statement about operators, Grassmann
        # numbers or generators: as numbers it is trivially true or false
        why.append("REORDERING_ONLY")
    collided = set(_names(card.get("subscript_collisions"))) & set(re.findall(
        r"[A-Za-z_][A-Za-z0-9_]*", " ".join(str(card[k]) for k in _EXPRESSION_KEYS if k in card)))
    if collided:
        why.append("SUBSCRIPT_COLLISION:" + ",".join(sorted(collided)))
    if card.get("log_base") and re.search(r"\blog\s*\(", " ".join(str(card[k]) for k in _EXPRESSION_KEYS if k in card)):
        why.append("LOG_BASE_STATED")             # the text's log is to another base
    held = _derivative_parameters(card, symbols, functions, defs)
    if held:
        # d(omega t)/dt holds omega fixed; the paper may let it depend on t
        why.append("DERIVATIVE_HOLDS_FIXED:" + ",".join(held))
    redefined = set(_names(card.get("builtins_redefined"))) & set(re.findall(
        r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", " ".join(str(card[k]) for k in _EXPRESSION_KEYS if k in card)))
    if redefined:
        why.append("BUILTIN_REDEFINED:" + ",".join(sorted(redefined)))
    if card.get("trace") and check not in ("langreth", "operator"):
        why.append("TRACE_OF_MATRICES")        # Tr(ABC) = Tr(BAC) holds for numbers, not matrices
    if card.get("bold_symbols") and check not in ("langreth", "operator"):
        why.append("VECTOR_OR_MATRIX")         # bold k, q: dot products are not products of numbers
    if card.get("conditional"):
        # a second relation, a condition or words sit next to this one in the display
        why.append("CONDITION_IN_DISPLAY")
    if card.get("equiv_relation"):
        why.append("EQUIV_RELATION")          # 1/tau \equiv ...: a definition, not a claim
    if card.get("noncommuting") and check not in ("langreth", "operator"):
        # the text says its quantities are matrices: every check here is commutative
        why.append("NONCOMMUTING_STATED")
    named = _named_quantity_blockers(card, defs, check)
    if named:
        why.append("NAMED_QUANTITY_UNDEFINED:" + ",".join(named))
    if check == "identity" and _lhs_is_a_name(card, defs):
        # "A = ..." states the value of a named quantity: without A's own
        # definition the relation cannot be checked (A would be a free symbol)
        why.append("LHS_IS_A_NAMED_QUANTITY")
    unstated = _realness_blockers(card, card.get("symbols") or [], defs)
    if unstated:            # the claim takes Re/Im/conj/|.| of a symbol the paper never calls real
        why.append("REALNESS_UNSTATED:" + ",".join(unstated))
    errata = sorted(k for k, f in (transcription.get("fields") or {}).items() if f.get("erratum"))
    decision_with_errata = None
    if errata:                    # the printed formula is not what was checked
        decision_with_errata = decision
        why.append("ERRATUM_APPLIED:" + ",".join(errata))
    if decision == "INVALID" and not why:
        arbitrary = _arbitrary_functions(card, functions, defs)
        if arbitrary:
            # a declared function is arbitrary here; the paper's may be a specific one
            # (zeta(4) = pi^4/90 is false for an arbitrary zeta): never refuted
            why.append("ARBITRARY_FUNCTION:" + ",".join(arbitrary))
        one_sided = _one_sided(card, symbols, functions, defs, check)
        if one_sided:
            why.append("ONE_SIDED_SYMBOL:" + ",".join(one_sided))
        if any(_APPROXIMATE.search(str(card[k])) for k in _EXPRESSION_KEYS if k in card):
            # 0.7468 is a rounded value: 'approximately', not 'equal'
            why.append("APPROXIMATE_NUMBER")
        periodic = _periodic_blockers(card, symbols, functions, defs)
        if periodic:
            why.append("PERIODIC_IN_AN_INDEX:" + ",".join(periodic))
        branch = _branch_sensitive(card, symbols, functions, defs, positive)
        if branch:
            # sqrt(ab) = sqrt(a) sqrt(b) fails only for negative a, b: unless the text says
            # they are positive, the counterexample may lie outside what the paper means
            why.append("BRANCH_DEPENDS_ON_SIGN:" + ",".join(branch))
        if _holds_at_special_phases(card, symbols, functions, defs, check, out):
            # e^{i pi N} = 1 for even N, e^{iqL} = 1 for a lattice momentum: the claim may
            # be about such quantized values, which the generic counterexample misses
            why.append("HOLDS_AT_SPECIAL_PHASES")
        if card.get("approximation_stated") and check not in ("remainder", "coefficient"):
            why.append("APPROXIMATION_STATED")     # 'to first order in V': exact equality not claimed
        constrained = set(_names(card.get("constrained"))) & set(re.findall(
            r"[A-Za-z_][A-Za-z0-9_]*", " ".join(str(card[k]) for k in _EXPRESSION_KEYS if k in card)))
        if constrained:
            why.append("CONSTRAINED_IN_TEXT:" + ",".join(sorted(constrained)))
        valued = _valued_free_names(card, defs)
        if valued:
            # the text gives these a value; with them free, a refutation may be wrong
            why.append("VALUED_IN_TEXT:" + ",".join(valued))
    if decision == "VALID" and not why:
        singular = _singular_at_stated_values(card, symbols, functions, defs)
        if singular:
            # the text sets these names to a value where the claim is not defined
            why.append("SINGULAR_AT_STATED_VALUE:" + ",".join(singular))
    disagree = bool(card.get("consistency")) and decision == "INVALID" and not why
    if disagree:
        # A = C follows from two displays of the same quantity; they may hold
        # under different conditions, so a mismatch is flagged, not refuted
        why.append("DISPLAYS_DISAGREE")
    if why:
        decision = "NOT_DECIDED"
    unquoted = sorted(k for k in defs if k.split("(")[0].strip() not in quoted | builtin)
    return {"check": check, "decision": decision, "decision_blocked_by": why,
            "transcription_verified": transcription["status"] == "MATCH" and not missing,
            "require_source": strict, **out, "transcription": transcription,
            "unquoted_definitions": unquoted, "notation_used": card.get("notation") or {},
            "convention_conflicts": conflicts,
            "built_from_source": filled,
            **({"decision_with_errata": decision_with_errata} if errata else {}),
            **({"consistency": card["consistency"], "displays_disagree": disagree}
               if card.get("consistency") else {})}
