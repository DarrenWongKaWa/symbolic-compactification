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
    own_source = dict(card.get("source") or {})
    for k, v in shared["source"].items():
        if k in own_source and own_source[k] != v:
            conflicts.append(f"card redefines shared quote {k}")
    if shared["source"]:
        merged["source"] = {**shared["source"], **own_source}
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
    fields = transcription.get("fields", {})
    return [k for k in _EXPRESSION_KEYS
            if k in card and fields.get(k, {}).get("status") != "MATCH"
            and not (k == "approximant" and re.fullmatch(r"\s*0\s*", str(card[k])))]


def _declared_beta(card: dict, symbols: list) -> str | None:
    """The inverse temperature, when the card declares it (for nF / nB)."""
    name = str(card.get("beta", "beta"))
    return name if any((s if isinstance(s, str) else s.get("name")) == name for s in symbols) else None


def _remainder_both(card, f, P, variable, order, symbols, functions, positive, defs) -> dict:
    """The text states no limit point: check x -> 0 and x -> oo, decide only
    when both agree (a remainder true at one point and false at the other
    means the claim depends on a point the paper did not state)."""
    from . import certify_remainder
    runs = {}
    for point, direction in (("0", str(card.get("direction", "+-"))), ("oo", "+-")):
        runs[point] = certify_remainder(
            f, P, variable=variable, point=point, order=order, direction=direction,
            symbols=symbols, functions=functions, positive=positive, definitions=defs,
            beta=_declared_beta(card, symbols)).to_dict()
    statuses = {r["status"] for r in runs.values()}
    if len(statuses) == 1 and statuses & {"CERTIFIED_BY_RULE", "NONZERO"}:
        out = dict(runs["0"])
        out["reasons"] = list(out.get("reasons", [])) + ["SAME_VERDICT_AT_0_AND_INFINITY"]
        return out
    return {**runs["0"], "status": "UNKNOWN",
            "reasons": ["LIMIT_POINT_UNSTATED: the verdict differs between x -> 0 and x -> oo"
                        if statuses >= {"CERTIFIED_BY_RULE", "NONZERO"} else "LIMIT_POINT_UNSTATED"],
            "at_0": runs["0"]["status"], "at_infinity": runs["oo"]["status"]}


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


def run_card(source: str | Path | dict, *, require_source: bool | None = None) -> dict[str, Any]:
    card = load_card(source)
    base_dir = None if isinstance(source, dict) else Path(source).resolve().parent
    shared_defs = _shared_definition_names(card, base_dir)
    card, conflicts = resolve_includes(card, base_dir)
    raw = card.get("symbols") or []
    symbols = [{k: v for k, v in s.items() if k in ("name", "real", "nonzero")}
               if isinstance(s, dict) else s for s in raw]
    # a positive symbol is real; an explicit real: false is complex
    symbols = [{**s, "real": True} if isinstance(s, dict) and s.get("real") is None
               and any(isinstance(r, dict) and r.get("name") == s["name"] and r.get("positive") for r in raw)
               else s for s in symbols]
    positive = tuple(s["name"] for s in raw if isinstance(s, dict) and s.get("positive")) \
        + _names(card.get("positive"))
    functions = _names(card.get("functions"))
    from .fidelity import fill_from_source, with_default_functions
    card, filled = fill_from_source(card, base_dir, symbols=symbols, functions=functions)
    defs = {str(k): str(v) for k, v in (card.get("define") or {}).items()}
    symbols = _used_symbols(symbols, card, defs)
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
        if str(point) == "unstated":
            return _remainder_both(card, f, P, variable, int(order), symbols, functions,
                                   positive, defs)
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
    errata = sorted(k for k, f in (transcription.get("fields") or {}).items() if f.get("erratum"))
    decision_with_errata = None
    if errata:                    # the printed formula is not what was checked
        decision_with_errata = decision
        why.append("ERRATUM_APPLIED:" + ",".join(errata))
    if why:
        decision = "NOT_DECIDED"
    unquoted = sorted(k for k in defs if k.split("(")[0].strip() not in quoted | builtin)
    return {"check": check, "decision": decision, "decision_blocked_by": why,
            "transcription_verified": transcription["status"] == "MATCH" and not missing,
            "require_source": strict, **out, "transcription": transcription,
            "unquoted_definitions": unquoted, "notation_used": card.get("notation") or {},
            "convention_conflicts": conflicts,
            "built_from_source": filled,
            **({"decision_with_errata": decision_with_errata} if errata else {})}
