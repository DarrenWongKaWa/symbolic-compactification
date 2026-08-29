"""Case-selection skeptic. Negative controls must not enter DEV."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.assumption_complete_representation.cases.skeptic.check import (  # noqa: E402
    GUO_RESCUE,
    OBVIOUS_LGG,
    REASON_CODES,
    SELECTED_BECAUSE_METHOD_WORKS,
    SILENT_PHYSICS_POSITIVITY,
    SYNTHETIC_DISGUISED_AS_SCIENTIFIC,
    TARGET_LEAKED_BY_NOTATION,
    TRIVIAL_CSE,
    UNDER_SPECIFIED,
    UNVERIFIABLE,
    load_negative_controls,
    reject_reasons,
)
from research.assumption_complete_representation.schema import (  # noqa: E402
    NOT_DECLARED,
)

SKEPTIC = ROOT / "research" / "assumption_complete_representation" / "cases" / "skeptic"
TAXONOMY = SKEPTIC / "REJECTION_TAXONOMY.md"
NEGATIVE = SKEPTIC / "negative"

REQUIRED_TAXONOMY_NAMES = (
    "trivial CSE",
    "obvious LGG",
    "target leaked by notation",
    "unverifiable",
    "under-specified",
    "synthetic disguised as scientific",
    "selected because the method already works",
    "Guo rescue",
    "silent physics positivity",
)


def _by_id() -> dict[str, dict]:
    return {d["case_id"]: d for _, d in load_negative_controls()}


def _well_formed() -> dict:
    return {
        "case_id": "resolvent-dd-01",
        "title": "matrix resolvent divided difference",
        "domain": "mathphys",
        "expression_sketch": "(f(A)-f(B))/(A-B)",
        "latent_structure": "Newton DD of matrix function",
        "proposed_ladder": "R2_newton_dd",
        "assumption_contract": {
            "analytic_domains": [
                {
                    "statement": "spec(A), spec(B) in Omega",
                    "label": "DECLARED",
                    "source": "Kato §II.3",
                }
            ],
            "positivity_conditions": [],
            "source_provenance": [
                "Kato, Perturbation theory for linear operators, 1966"
            ],
        },
        "is_guo": False,
        "notes": "Inline checker control; not an admitted DEV case.",
    }


def test_taxonomy_lists_every_reason():
    text = TAXONOMY.read_text(encoding="utf-8")
    for code in REASON_CODES:
        assert code in text, code
    for name in REQUIRED_TAXONOMY_NAMES:
        assert name in text, name


def test_negative_control_count():
    rows = load_negative_controls()
    assert 4 <= len(rows) <= 6
    ids = [d["case_id"] for _, d in rows]
    assert len(ids) == len(set(ids))
    assert "nc-guo-sigma-abc" in ids
    guo_flags = [d["case_id"] for _, d in rows if d.get("is_guo") is True]
    assert guo_flags == ["nc-guo-sigma-abc"]
    for path, _d in rows:
        assert path.suffix == ".json"


def test_guo_rejected():
    d = _by_id()["nc-guo-sigma-abc"]
    assert d["is_guo"] is True
    reasons = reject_reasons(d)
    assert GUO_RESCUE in reasons
    named = {
        "case_id": "thermal-kernel-01",
        "title": "Guo-like hop restated as a new case",
        "domain": "thermal",
        "expression_sketch": "(f(A)-f(B))/(A-B)",
        "latent_structure": "Newton DD",
        "assumption_contract": {
            "analytic_domains": [
                {"statement": "A,B in Omega", "label": "DECLARED", "source": "x"}
            ],
            "source_provenance": ["frozen-hash"],
        },
        "is_guo": False,
    }
    assert GUO_RESCUE in reject_reasons(named)


def test_empty_provenance_rejected():
    d = _by_id()["nc-empty-provenance"]
    assert d["assumption_contract"]["source_provenance"] == []
    reasons = reject_reasons(d)
    assert UNVERIFIABLE in reasons
    missing = _well_formed()
    missing["assumption_contract"] = {
        "analytic_domains": [
            {"statement": "z off poles", "label": "DECLARED", "source": "x"}
        ],
        "source_provenance": [],
    }
    assert UNVERIFIABLE in reject_reasons(missing)
    absent = _well_formed()
    del absent["assumption_contract"]["source_provenance"]
    assert UNVERIFIABLE in reject_reasons(absent)


def test_not_declared_analytic_rejected():
    d = _by_id()["nc-not-declared-analytic"]
    labels = [p["label"] for p in d["assumption_contract"]["analytic_domains"]]
    assert NOT_DECLARED in labels
    reasons = reject_reasons(d)
    assert UNDER_SPECIFIED in reasons
    unlabeled = _well_formed()
    unlabeled["assumption_contract"]["analytic_domains"] = [
        {"statement": "z not a pole"}
    ]
    assert UNDER_SPECIFIED in reject_reasons(unlabeled)


def test_all_negative_controls_rejected():
    rows = load_negative_controls()
    assert rows, "missing negative control JSON"
    for path, d in rows:
        reasons = reject_reasons(d)
        assert reasons, f"{path.name} must be rejected"


def test_trivial_cse_and_leaks_and_positivity():
    ids = _by_id()
    assert TRIVIAL_CSE in reject_reasons(ids["nc-trivial-cse"])
    leaked = reject_reasons(ids["nc-leaked-master"])
    assert TARGET_LEAKED_BY_NOTATION in leaked
    assert SILENT_PHYSICS_POSITIVITY in reject_reasons(ids["nc-silent-positivity"])


def test_remaining_taxonomy_hooks():
    lgg = dict(_well_formed())
    lgg["latent_structure"] = "obvious LGG of f(x), f(x+a)"
    assert OBVIOUS_LGG in reject_reasons(lgg)
    syn = dict(_well_formed())
    syn["domain"] = "synthetic"
    assert SYNTHETIC_DISGUISED_AS_SCIENTIFIC in reject_reasons(syn)
    mw = dict(_well_formed())
    mw["notes"] = "selected because the method already works on Newton DD toys"
    assert SELECTED_BECAUSE_METHOD_WORKS in reject_reasons(mw)
    infix = dict(_well_formed())
    infix["expression_sketch"] = "chi0 + chi0"
    assert TRIVIAL_CSE in reject_reasons(infix)


def test_well_formed_inline_control_not_flagged():
    # Inline only: skeptic does not admit DEV files.
    assert reject_reasons(_well_formed()) == []


def test_negative_json_is_loadable():
    for path in sorted(NEGATIVE.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            payload = json.load(fh)
        assert isinstance(payload, dict)
        assert payload.get("case_id")
        assert "expression_sketch" in payload
