"""Phase III freeze: strata, clusters, packs, P4 predeclaration. No Guo. No TEST."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.assumption_complete_representation.eval.ac_parser import parse_model_output
from research.assumption_complete_representation.eval.ac_prompts import (
    build_user_prompt,
    load_condition,
)
from research.assumption_complete_representation.eval.pack_data import (
    CORE,
    P4_ELIGIBLE,
    PACKAGING_GAP,
    PUBLIC_FORBIDDEN,
    PUBLIC_PACKS,
)
from research.llm_abstraction.leak import leak_hits

HERE = ROOT / "research" / "assumption_complete_representation"


def test_strata_partition_six_and_eight():
    strata = json.loads((HERE / "EVALUATION_STRATA.json").read_text())
    assert strata["n_core_comparable"] == 6
    assert strata["n_packaging_gap"] == 8
    assert strata["n_dev"] == 14
    ids_c = [x["case_id"] for x in strata["CORE_COMPARABLE"]]
    assert ids_c == CORE
    assert strata["PACKAGING_GAP"] == PACKAGING_GAP
    assert set(ids_c).isdisjoint(set(PACKAGING_GAP))
    assert strata["parser_extended"] is False
    assert strata["guo_in_dev_or_test"] is False
    assert strata["ai_unique_only_on"] == "CORE_COMPARABLE"


def test_clusters_keep_known_duplicates():
    cl = json.loads((HERE / "DEV_STRUCTURAL_CLUSTERS.json").read_text())
    by = {c["cluster_id"]: c for c in cl["clusters"]}
    assert set(by["RESOLVENT_CLUSTER"]["members"]) == {
        "mp-resolvent-dd-01", "ac-r01-resolvent-hilbert-identity",
    }
    assert set(by["DALECKII_KREIN_CLUSTER"]["members"]) == {
        "mp-daleckii-krein-01", "sciml-daleckii-krein-01",
    }
    members = [m for c in cl["clusters"] for m in c["members"]]
    assert len(members) == 14
    assert cl["keep_all_dev_tasks"] is True
    assert cl["task_weighted_n"] == 14
    assert cl["cluster_weighted_n"] == 12


def test_p4_predeclared_unlabeled():
    assert set(P4_ELIGIBLE) <= set(CORE)
    assert "thermal-01-fermi-im-digamma" not in P4_ELIGIBLE
    p4 = load_condition("P4").lower()
    assert "divided difference" not in p4
    assert "hermite" not in p4
    for cid in P4_ELIGIBLE:
        user = build_user_prompt(PUBLIC_PACKS[cid], "P4").lower()
        assert "divided difference" not in user
        assert "hermite" not in user
        assert PUBLIC_PACKS[cid]["case_id"] not in user


def test_public_packs_no_gold_tokens():
    for cid, pack in PUBLIC_PACKS.items():
        blob = {k: pack[k] for k in pack if k != "case_id"}
        hits = leak_hits(blob, PUBLIC_FORBIDDEN)
        assert hits == [], (cid, hits)


def test_parser_format_wrap_single_hypothesis():
    raw = json.dumps({
        "representation_type": "parameterized_family",
        "latent_object": "F(t)=1/(t-a)",
        "member_maps": [{"source_node_id": "G0001", "role": "instance"}],
        "operators": [{"member": "G0001", "O": "identity"}],
        "reconstruction_rule": "G0001 = F(lam)",
        "required_assumptions": ["lam != a"],
        "proof_obligations": ["G0001 - F(lam) = 0"],
    })
    p = parse_model_output(raw)
    assert p["format_wrap"] is True
    assert p["parse_status"] == "OK"
    assert p["hypotheses"][0]["parse_status"] == "OK"


def test_parser_missing_fields_is_parse_failure():
    raw = json.dumps({"abstain": False, "hypotheses": [{"representation_type": "x"}]})
    p = parse_model_output(raw)
    assert p["parse_status"] == "PARSE_FAILURE"
    assert "missing_fields" in (p["hypotheses"][0]["parse_error"] or "")


def test_no_guo_in_core():
    assert all("guo" not in i.lower() for i in CORE + PACKAGING_GAP)


def test_compiler_expands_catalog_and_F_calls():
    from research.assumption_complete_representation.eval.ac_compile import (
        COMPILER_VERSION,
        compile_and_verify,
    )
    from research.assumption_complete_representation.eval.pack_data import PUBLIC_PACKS
    pack = PUBLIC_PACKS["mp-resolvent-dd-01"]
    hyp = {
        "parse_status": "OK",
        "latent_object": "F(t)=1/(t-a)",
        "variables": ["t"],
        "nodes": [],
        "member_maps": [{"source_node_id": "G0001", "role": "instance"}],
        "operators": [{"member": "G0001", "O": "specialize"}],
        "reconstruction_rule": "G0001=F(lam)",
        "required_assumptions": [],
        "proof_obligations": [
            "G0001 - F(lam) = 0",
            "G0003 - ((F(lam)-F(mu))/(lam-mu)) = 0",
            "G0004 - (F(lam)*F(mu)) = 0",
        ],
    }
    c = compile_and_verify(hyp, pack)
    assert c["compiler_version"] == COMPILER_VERSION
    assert c["F_parsed"] is True
    verdicts = {o["text"]: o["verdict"] for o in c["obligations"]
                if o.get("note") == "parsed_eq"}
    assert verdicts["G0001 - F(lam) = 0"] == "ZERO"
    assert verdicts["G0003 - ((F(lam)-F(mu))/(lam-mu)) = 0"] == "ZERO"
    assert verdicts["G0004 - (F(lam)*F(mu)) = 0"] == "ZERO"


def test_execution_freeze_exists_and_locks_p4():
    freeze = json.loads((HERE / "DEV_EXECUTION_FREEZE.json").read_text())
    assert freeze["n_dev"] == 14
    assert freeze["P4_predeclared_before_P0P3"] is True
    assert freeze["P4_ELIGIBLE"] == P4_ELIGIBLE
    assert freeze["parser_extended"] is False
    assert freeze["guo_in_dev_or_test"] is False
    assert freeze["seeds"] == [0, 1, 2, 3, 4]
    assert freeze["model"] == "deepseek-v4-pro"
    assert freeze["retries_parse"] == 0
    pub = HERE / "packs" / "dev" / "public"
    hid = HERE / "packs" / "dev" / "hidden"
    for cid in CORE:
        assert (pub / f"{cid}.json").is_file()
        assert (hid / f"{cid}.json").is_file()
        pub_obj = json.loads((pub / f"{cid}.json").read_text())
        assert "case_id" not in pub_obj
        assert "hermite" not in json.dumps(pub_obj).lower()
