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
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

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


def run_card(source: str | Path | dict) -> dict[str, Any]:
    card = load_card(source)
    raw = card.get("symbols") or []
    symbols = [{k: v for k, v in s.items() if k in ("name", "real", "nonzero")}
               if isinstance(s, dict) else s for s in raw]
    positive = tuple(s["name"] for s in raw if isinstance(s, dict) and s.get("positive")) \
        + _names(card.get("positive"))
    functions = _names(card.get("functions"))
    defs = {str(k): str(v) for k, v in (card.get("define") or {}).items()}
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
                                    functions=functions, definitions=defs, positive=positive)
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
    return {"check": check, **out}
