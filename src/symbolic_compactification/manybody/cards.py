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
from pathlib import Path
from typing import Any

import yaml

from ..models import AdapterError

CHECKS = ("identity", "coefficient", "remainder", "fermi_integral", "matsubara",
          "operator", "langreth", "numeric_integral")


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
                    "approximant", "summand")


def _symbol_entries(value) -> dict[str, dict]:
    out = {}
    for s in value or []:
        entry = {"name": s} if isinstance(s, str) else dict(s)
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
    shared: dict[str, Any] = {"symbols": {}, "define": {}, "notation": {}, "functions": []}
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
    if "source_document" not in card and "source_document" in shared:
        merged["source_document"] = shared["source_document"]
    return merged, conflicts


def _require_source(flag: bool | None) -> bool:
    if flag is not None:
        return flag
    return os.environ.get(REQUIRE_SOURCE_ENV, "").strip().lower() in ("1", "true", "yes")


def _missing_quotes(card: dict, transcription: dict) -> list[str]:
    fields = transcription.get("fields", {})
    return [k for k in _EXPRESSION_KEYS
            if k in card and fields.get(k, {}).get("status") != "MATCH"]


def run_card(source: str | Path | dict, *, require_source: bool | None = None) -> dict[str, Any]:
    card = load_card(source)
    base_dir = None if isinstance(source, dict) else Path(source).resolve().parent
    card, conflicts = resolve_includes(card, base_dir)
    raw = card.get("symbols") or []
    symbols = [{k: v for k, v in s.items() if k in ("name", "real", "nonzero")}
               if isinstance(s, dict) else s for s in raw]
    positive = tuple(s["name"] for s in raw if isinstance(s, dict) and s.get("positive")) \
        + _names(card.get("positive"))
    functions = _names(card.get("functions"))
    from .fidelity import fill_from_source, with_default_functions
    card, filled = fill_from_source(card, base_dir, symbols=symbols, functions=functions)
    defs = {str(k): str(v) for k, v in (card.get("define") or {}).items()}
    defs = with_default_functions(
        defs, [str(card[k]) for k in _EXPRESSION_KEYS if k in card] + list(defs.values()),
        declared=[*(s if isinstance(s, str) else s["name"] for s in symbols), *functions])
    labels = _names(card.get("labels"))
    check = card["check"]
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
        out = certify_remainder(f, P, variable=variable, point=point, order=int(order),
                                direction=str(card.get("direction", "+-")), symbols=symbols,
                                functions=functions, positive=positive, definitions=defs).to_dict()
    elif check == "fermi_integral":
        integrand, claim, variable, beta = _need(card, "integrand", "claim", "variable", "beta")
        out = verify_fermi_integral(integrand, claim, variable=variable, beta=beta, symbols=symbols,
                                    functions=functions, definitions=defs, positive=positive,
                                    infinitesimal=card.get("infinitesimal"))
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
    elif check == "langreth":
        component, claim = _need(card, "component", "claim")
        out = dict(verify_langreth(_names(card.get("product")), component, claim))
    else:
        integrand, claim, variable = _need(card, "integrand", "claim", "variable")
        out = check_frequency_integral(integrand, claim, variable=variable, symbols=symbols,
                                       functions=functions, beta=card.get("beta"),
                                       positive=positive)
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
    if why:
        decision = "NOT_DECIDED"
    unquoted = sorted(k for k in defs
                      if f"define:{k}" not in transcription.get("fields", {})
                      and f"define:{k.split('(')[0]}" not in transcription.get("fields", {}))
    return {"check": check, "decision": decision, "decision_blocked_by": why,
            "transcription_verified": transcription["status"] == "MATCH" and not missing,
            "require_source": strict, **out, "transcription": transcription,
            "unquoted_definitions": unquoted, "convention_conflicts": conflicts,
            "built_from_source": filled}
