"""Proposer-visible DEV items. No hidden target fields. Guo excluded."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
MANIFEST = HERE / "DEV_MANIFEST.json"

# Parseable residuals for frozen B9/LGG. Unparseable tasks are recorded
# as FAILED_OPERATIONAL for those baselines (not a method edit).
_PACK = {
    "thermal-01-fermi-im-digamma": {
        "current": "im(polygamma(0, Rational(1, 2) + I*y)) - (pi/2)*tanh(pi*y)",
        "symbols": [{"name": "y", "real": True}],
        "functions": ["im", "polygamma", "tanh"],
    },
    "thermal-03-digamma-reflection": {
        "current": "polygamma(0, z) - polygamma(0, 1 - z) + pi/tan(pi*z)",
        "symbols": [{"name": "z", "real": True}],
        "functions": ["polygamma", "tan"],
    },
    "thermal-05-trigamma-double-pole": {
        "current": "polygamma(1, z)",
        "symbols": [{"name": "z", "real": True}],
        "functions": ["polygamma"],
    },
    "mp-resolvent-dd-01": {
        "current": "(1/(lam - a) - 1/(mu - a))/(lam - mu) + 1/((lam - a)*(mu - a))",
        "symbols": [
            {"name": "lam", "real": True},
            {"name": "mu", "real": True},
            {"name": "a", "real": True},
        ],
        "functions": [],
    },
    "ac-r01-resolvent-hilbert-identity": {
        "current": "(1/(a - z) - 1/(a - w))/(z - w) - 1/((a - z)*(a - w))",
        "symbols": [
            {"name": "a", "real": True},
            {"name": "z", "real": True},
            {"name": "w", "real": True},
        ],
        "functions": [],
    },
    "sciml-phi-hermite-01": {
        "current": "(exp(z) - 1)/z",
        "symbols": [{"name": "z", "real": True}],
        "functions": ["exp"],
    },
}


def items() -> list[dict]:
    man = json.loads(MANIFEST.read_text())
    out = []
    for t in man["tasks"]:
        cid = t["case_id"]
        pack = _PACK.get(cid)
        item = {
            "id": cid,
            "split": "DEV",
            "task": "abstraction_invention",
            "family": t["domain"],
            "domain": t["domain"],
            "hidden_from_proposer": True,
            "assumptions": [],
            "scientific_context": [
                "Propose an operational representation with explicit members, F, operators, reconstruction.",
                "Do not invent physical names.",
            ],
            "tag": t["tag"],
            "ladder": t["ladder"],
            "operator_family": t["operator_family"],
            "parseable": pack is not None,
        }
        if pack:
            item.update(pack)
        else:
            item["current"] = ""
            item["symbols"] = []
            item["functions"] = []
            item["parseable"] = False
        out.append(item)
    return out
