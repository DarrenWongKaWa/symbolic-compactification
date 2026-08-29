"""Representation-program-search case-selection skeptic.

Negative controls must not enter DEV. No search is implemented here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.representation_program_search.cases.skeptic.check import (  # noqa: E402
    FABRICATED_TOY,
    FIRST_ORDER_LGG_ONLY,
    GRAMMAR_BAIT,
    GUO_SEALED,
    REASON_CODES,
    RENAMED_OLD_DEV_TEST,
    SYNTAX_REVEALS_TARGET,
    TRIVIAL_CSE,
    UNVERIFIABLE_DOMAIN,
    load_index,
    load_negative_controls,
    reject_reasons,
)

SKEPTIC = (
    ROOT
    / "research"
    / "representation_program_search"
    / "cases"
    / "skeptic"
)
TAXONOMY = SKEPTIC / "REJECTION_TAXONOMY.md"
NEGATIVE = SKEPTIC / "negative"

REQUIRED_TAXONOMY_NAMES = (
    "renamed old DEV/TEST",
    "syntax revealing target",
    "trivial CSE",
    "first-order LGG-only",
    "unverifiable domain",
    "fabricated toys",
    "NEWTON_DD",
    "HERMITE_DD",
    "RepresentationGrammarV1",
)

REQUIRED_NEGATIVE_IDS = (
    "nc-renamed-resolvent",
    "nc-leaked-hermite-sketch",
    "nc-trivial-cse",
    "nc-grammar-bait-hermite",
    "nc-guo-sigma-abc",
)


def _by_id() -> dict[str, dict]:
    return {d["case_id"]: d for _, d in load_negative_controls()}


def _well_formed() -> dict:
    return {
        "case_id": "fresh-stieltjes-transform-01",
        "title": "Stieltjes transform finite-difference kernel",
        "domain": "response",
        "expression_sketch": "(m(z)-m(w))/(z-w) with m the Stieltjes transform of a compactly supported measure",
        "latent_structure": "shared generating transform; generic quotient and diagonal derivative",
        "proposed_ladder": "R2_newton_dd",
        "assumption_contract": {
            "analytic_domains": [
                {
                    "statement": "z, w off the support of the measure",
                    "label": "DECLARED",
                    "source": "fresh public notes",
                }
            ],
            "positivity_conditions": [],
            "source_provenance": [
                "fresh public source, not an AC identity"
            ],
        },
        "is_guo": False,
        "grammar_bait": False,
        "synthetic": False,
        "notes": "Inline checker control; not an admitted DEV case.",
    }


def test_taxonomy_lists_every_reason():
    text = TAXONOMY.read_text(encoding="utf-8")
    for code in REASON_CODES:
        assert code in text, code
    for name in REQUIRED_TAXONOMY_NAMES:
        assert name in text, name
    assert "Guo" in text


def test_required_negative_controls_present():
    rows = load_negative_controls()
    ids = [d["case_id"] for _, d in rows]
    assert len(ids) == len(set(ids))
    for required in REQUIRED_NEGATIVE_IDS:
        assert required in ids, required
    guo_flags = [d["case_id"] for _, d in rows if d.get("is_guo") is True]
    assert guo_flags == ["nc-guo-sigma-abc"]
    for path, _d in rows:
        assert path.suffix == ".json"


def test_all_negative_controls_rejected():
    rows = load_negative_controls()
    assert rows, "missing negative control JSON"
    for path, d in rows:
        reasons = reject_reasons(d)
        assert reasons, f"{path.name} must be rejected"
        assert d.get("rejected") is True, path.name
        assert d.get("admitted") is False, path.name


def test_primary_reasons():
    ids = _by_id()
    assert RENAMED_OLD_DEV_TEST in reject_reasons(ids["nc-renamed-resolvent"])
    assert ids["nc-renamed-resolvent"]["historical_parent"] == "mp-resolvent-dd-01"
    leaked = reject_reasons(ids["nc-leaked-hermite-sketch"])
    assert SYNTAX_REVEALS_TARGET in leaked
    sketch = ids["nc-leaked-hermite-sketch"]["expression_sketch"]
    assert "HERMITE_DD" in sketch or "Hermite" in sketch
    assert TRIVIAL_CSE in reject_reasons(ids["nc-trivial-cse"])
    bait = reject_reasons(ids["nc-grammar-bait-hermite"])
    assert GRAMMAR_BAIT in bait
    assert ids["nc-grammar-bait-hermite"].get("grammar_bait") is True
    guo = reject_reasons(ids["nc-guo-sigma-abc"])
    assert GUO_SEALED in guo
    assert ids["nc-guo-sigma-abc"]["is_guo"] is True
    assert FIRST_ORDER_LGG_ONLY in reject_reasons(ids["nc-first-order-lgg"])
    assert UNVERIFIABLE_DOMAIN in reject_reasons(ids["nc-unverifiable-domain"])
    assert FABRICATED_TOY in reject_reasons(ids["nc-fabricated-toy"])


def test_guo_name_alone_is_sealed():
    named = _well_formed()
    named["case_id"] = "thermal-kernel-01"
    named["title"] = "Guo-like hop restated as a new case"
    named["is_guo"] = False
    assert GUO_SEALED in reject_reasons(named)


def test_index_matches_negative_dir():
    index = load_index()
    assert index["admitted"] is False
    assert index["must_reject"] is True
    assert index["search_implemented"] is False
    assert index["positive_cases"] is False
    assert index["contracts_sha"] == "5321eaa"
    listed = [row["case_id"] for row in index["dossiers"]]
    files = [d["case_id"] for _, d in load_negative_controls()]
    assert sorted(listed) == sorted(files)
    assert index["count"] == len(files)
    for row in index["dossiers"]:
        path = SKEPTIC / row["json"]
        assert path.is_file(), row["json"]
        assert row["admitted"] is False
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["case_id"] == row["case_id"]
        assert payload.get("rejected") is True


def test_well_formed_inline_control_not_flagged():
    assert reject_reasons(_well_formed()) == []


def test_remaining_taxonomy_hooks():
    renamed = _well_formed()
    renamed["historical_parent"] = "mp-kato-simple-ev-01"
    assert RENAMED_OLD_DEV_TEST in reject_reasons(renamed)
    leak = _well_formed()
    leak["expression_sketch"] = "apply HERMITE_DD to F"
    assert SYNTAX_REVEALS_TARGET in reject_reasons(leak)
    infix = _well_formed()
    infix["expression_sketch"] = "chi0 + chi0"
    assert TRIVIAL_CSE in reject_reasons(infix)
    lgg = _well_formed()
    lgg["latent_structure"] = "obvious LGG of f(x), f(x+a)"
    assert FIRST_ORDER_LGG_ONLY in reject_reasons(lgg)
    missing = _well_formed()
    missing["assumption_contract"] = {
        "analytic_domains": [
            {"statement": "z off poles", "label": "DECLARED", "source": "x"}
        ],
        "source_provenance": [],
    }
    assert UNVERIFIABLE_DOMAIN in reject_reasons(missing)
    unlabeled = _well_formed()
    unlabeled["assumption_contract"]["analytic_domains"] = [
        {"statement": "z not a pole"}
    ]
    assert UNVERIFIABLE_DOMAIN in reject_reasons(unlabeled)
    syn = _well_formed()
    syn["domain"] = "synthetic"
    assert FABRICATED_TOY in reject_reasons(syn)
    bait = _well_formed()
    bait["notes"] = "chosen specifically to fit RepresentationGrammarV1 HERMITE_DD bait"
    assert GRAMMAR_BAIT in reject_reasons(bait)


def test_negative_json_is_loadable():
    for path in sorted(NEGATIVE.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            payload = json.load(fh)
        assert isinstance(payload, dict)
        assert payload.get("case_id")
        assert "expression_sketch" in payload
        assert payload.get("rejected") is True
        assert payload.get("admitted") is False
