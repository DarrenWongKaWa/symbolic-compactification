"""C1 response/Green dossiers: JSON loads; Guo is absent."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.assumption_complete_representation.schema import (  # noqa: E402
    DECLARED,
    DERIVED,
    NOT_DECLARED,
    CandidateDossier,
    Predicate,
    ScientificAssumptionContract,
    PREDICATE_LABELS,
    guo_is_not_admitted,
)

DOSSIER_DIR = (
    ROOT
    / "research"
    / "assumption_complete_representation"
    / "cases"
    / "response"
    / "dossiers"
)

PRED_KEYS = (
    "nonzero_conditions",
    "positivity_conditions",
    "analytic_domains",
    "limit_domains",
    "derived_conditions",
)

FORBIDDEN = ("phi_gamma", "phigamma", "hermite-on-guo", "hermite on guo")


def _pred_list(raw: list) -> list[Predicate]:
    out = []
    for p in raw:
        if isinstance(p, dict):
            out.append(
                Predicate(
                    statement=p["statement"],
                    label=p.get("label", NOT_DECLARED),
                    source=p.get("source", ""),
                )
            )
        else:
            out.append(p)
    return out


def load_dossier(path: Path) -> tuple[dict, CandidateDossier]:
    data = json.loads(path.read_text(encoding="utf-8"))
    ac_raw = data.get("assumption_contract") or {}
    ac = ScientificAssumptionContract(
        symbol_assumptions=ac_raw.get("symbol_assumptions") or {},
        function_domains=ac_raw.get("function_domains") or {},
        nonzero_conditions=_pred_list(ac_raw.get("nonzero_conditions") or []),
        positivity_conditions=_pred_list(ac_raw.get("positivity_conditions") or []),
        real_valued_functions=list(ac_raw.get("real_valued_functions") or []),
        analytic_domains=_pred_list(ac_raw.get("analytic_domains") or []),
        branch_conventions=list(ac_raw.get("branch_conventions") or []),
        limit_domains=_pred_list(ac_raw.get("limit_domains") or []),
        source_provenance=list(ac_raw.get("source_provenance") or []),
        derived_conditions=_pred_list(ac_raw.get("derived_conditions") or []),
    )
    dossier = CandidateDossier(
        case_id=data["case_id"],
        title=data["title"],
        domain=data["domain"],
        expression_sketch=data["expression_sketch"],
        latent_structure=data["latent_structure"],
        proposed_ladder=data.get("proposed_ladder", ""),
        assumption_contract=ac,
        public_source=data.get("public_source", ""),
        why_not_cse_lgg=data.get("why_not_cse_lgg", ""),
        proposer_leak_risk=data.get("proposer_leak_risk", ""),
        notes=data.get("notes", ""),
        rejected=bool(data.get("rejected", False)),
        reject_reason=data.get("reject_reason", ""),
        is_guo=bool(data.get("is_guo", False)),
    )
    return data, dossier


def json_paths() -> list[Path]:
    paths = sorted(DOSSIER_DIR.glob("*.json"))
    assert paths, f"no dossiers in {DOSSIER_DIR}"
    return paths


def test_dossier_count_in_range():
    n = len(json_paths())
    assert 3 <= n <= 8


def test_each_json_has_markdown():
    for path in json_paths():
        md = path.with_suffix(".md")
        assert md.is_file(), md


def test_is_guo_false_and_not_admitted_as_guo():
    for path in json_paths():
        data, dossier = load_dossier(path)
        assert data.get("is_guo") is False
        assert dossier.is_guo is False
        assert guo_is_not_admitted(dossier) is True
        blob = (dossier.case_id + dossier.title).lower()
        assert "guo" not in blob


def test_no_guo_gold_names():
    for path in json_paths():
        text = path.read_text(encoding="utf-8").lower()
        for tok in FORBIDDEN:
            assert tok not in text, f"{path} contains {tok}"


def test_predicate_labels_and_underspecified_policy():
    rejected = 0
    for path in json_paths():
        data, dossier = load_dossier(path)
        ac_raw = data["assumption_contract"]
        for key in PRED_KEYS:
            for p in ac_raw.get(key) or []:
                assert p["label"] in PREDICATE_LABELS
        ac = dossier.assumption_contract
        assert ac is not None
        if dossier.rejected:
            rejected += 1
            assert dossier.reject_reason == "PROBLEM_UNDERSPECIFIED"
            assert ac.has_not_declared_analytic() is True
        else:
            assert ac.has_not_declared_analytic() is False
            for pred in ac.analytic_domains + ac.limit_domains:
                assert pred.label in (DECLARED, DERIVED)
    assert rejected >= 1


def test_provenance_and_expression_present():
    for path in json_paths():
        data, dossier = load_dossier(path)
        ac = dossier.assumption_contract
        assert ac is not None
        assert ac.source_provenance
        assert dossier.expression_sketch
        assert dossier.public_source
        assert dossier.latent_structure
        assert dossier.why_not_cse_lgg
        assert data["case_id"] == path.stem
