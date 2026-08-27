"""Grounded-Proposer-v2 harness. No live API."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.representation_invention.llm.catalog_render import catalog_ids, render_catalog
from research.representation_invention.llm.p1_baseline import (
    P1_RUNS_DIR,
    load_p1_runs,
    map_p1_type,
    summarize_p1,
)
from research.representation_invention.llm.parser import parse_p2
from research.representation_invention.llm.prompts import (
    SYSTEM_PROMPT,
    build_p2_user_prompt,
    include_sol_packets,
)
from research.representation_invention.llm.propose import propose_p2
from research.representation_invention.llm.score import COMPILE_NOT_WIRED, score_hypothesis
from research.representation_invention.schema import (
    OK,
    PARSE_FAILURE,
    REPRESENTATION_TYPES,
)
from research.structure_discovery.prototype.leakage import proposer_view

CAT = {"G0001", "G0002"}


def _ok_hyp(**over):
    raw = {
        "representation_type": "local_confluence",
        "member_ids": ["G0001", "G0002"],
        "member_roles": {"G0001": "generic", "G0002": "degenerate"},
        "latent_object": "F(z)",
        "latent_variables": ["z"],
        "nodes": [
            {"name": "x", "expression": "n", "multiplicity": 1},
            {"name": "y", "expression": "m", "multiplicity": 1},
        ],
        "operators": [{"member_id": "G0001", "kind": "limit", "args": {}}],
        "instance_maps": {},
        "reconstruction_rule": "limit F(x)->F(y)",
        "required_assumptions": [],
        "proof_obligations": [
            {
                "kind": "CONFLUENCE",
                "member_ids": ["G0001", "G0002"],
                "expected": "limit(G0001)==G0002",
            }
        ],
        "scientific_rationale": "branch limit",
        "confidence": 0.5,
    }
    raw.update(over)
    return raw


def _doc(*hyps, abstain: bool = False) -> dict:
    return {"abstain": abstain, "abstain_reason": "", "hypotheses": list(hyps)}


def _item() -> dict:
    return {
        "id": "toy-p2",
        "current": "K(n)+K(m)",
        "symbols": [{"name": "n", "real": True}, {"name": "m", "real": True}],
        "functions": ["K"],
        "scientific_context": ["Identify shared structure. Do not invent physics."],
        "gold_types": ["master_function"],
        "gold_members": ["Phi_Gamma"],
        "hidden_gold": {"aux_names": ["Phi_Gamma", "L4"]},
    }


def _entries() -> list[dict]:
    return [
        {
            "source_node_id": "G0001",
            "kind": "sum",
            "parent_gid": "",
            "text": "K(n)",
            "fingerprint": {"arity": 1, "branch_condition": "", "h_factors": ["K(n)"]},
        },
        {
            "source_node_id": "G0002",
            "kind": "sum",
            "parent_gid": "",
            "text": "K(m)",
            "fingerprint": {"arity": 1, "branch_condition": "", "h_factors": ["K(m)"]},
        },
    ]


def test_alias_parse_failure():
    raw = json.dumps(_doc(_ok_hyp(member_ids=["S1_True", "G0002"])))
    p = parse_p2(raw, CAT)
    assert p["n_ok"] == 0
    assert p["hypotheses"][0].parse_status == PARSE_FAILURE
    assert "alias" in (p["hypotheses"][0].parse_error or "")


def test_good_v2_json_parse():
    raw = json.dumps(_doc(_ok_hyp()))
    p = parse_p2(raw, CAT)
    assert p["parse_status"] == OK, p
    assert p["n_ok"] == 1
    h = p["hypotheses"][0]
    assert h.parse_status == OK
    assert h.member_ids == ["G0001", "G0002"]
    assert h.latent_object == "F(z)"
    assert h.reconstruction_rule.startswith("limit")
    assert h.operators[0].kind == "limit"


def test_p1_type_name_is_parse_failure_not_repaired():
    raw = json.dumps(_doc(_ok_hyp(representation_type="confluent_representation")))
    p = parse_p2(raw, CAT)
    assert p["hypotheses"][0].parse_status == PARSE_FAILURE
    assert "p1_type_not_accepted" in (p["hypotheses"][0].parse_error or "")


def test_system_lists_allowed_types_not_guo_instruction():
    for t in REPRESENTATION_TYPES:
        assert t in SYSTEM_PROMPT
    assert "You are NOT a verifier" in SYSTEM_PROMPT
    assert "member_ids" in SYSTEM_PROMPT
    assert "latent_object" in SYSTEM_PROMPT
    assert "reconstruction_rule" in SYSTEM_PROMPT
    assert "proof_obligations" in SYSTEM_PROMPT
    assert "confluent_representation" not in SYSTEM_PROMPT
    assert "use Hermite divided differences on Guo" not in SYSTEM_PROMPT
    assert "Guo" not in SYSTEM_PROMPT


def test_proposer_view_leakage():
    item = _item()
    pub = proposer_view(item)
    pub_blob = json.dumps(pub)
    assert "gold_types" not in pub_blob
    assert "Phi_Gamma" not in pub_blob
    assert "L4" not in pub_blob
    user = build_p2_user_prompt(
        condition="P3",
        expression=pub["current"],
        catalog_text=render_catalog(_entries()),
        packets_text="",
        scientific_context=pub.get("scientific_context") or [],
        symbols=pub.get("symbols") or [],
        functions=pub.get("functions") or [],
    )
    blob = SYSTEM_PROMPT + "\n" + user
    assert "Phi_Gamma" not in blob
    assert "L4" not in blob
    assert "gold_types" not in blob
    assert "STRUCTURAL OBSERVATION PACKETS" not in user


def test_p2_user_includes_injected_packets_p3_does_not():
    packets = "FAMILY F01\nmembers:\n  G0001: K(n)"
    p2 = build_p2_user_prompt(
        condition="P2",
        expression="K(n)+K(m)",
        catalog_text=render_catalog(_entries()),
        packets_text=packets,
    )
    p3 = build_p2_user_prompt(
        condition="P3",
        expression="K(n)+K(m)",
        catalog_text=render_catalog(_entries()),
        packets_text=packets,
    )
    assert include_sol_packets("P2") and include_sol_packets("P4")
    assert not include_sol_packets("P3")
    assert "STRUCTURAL OBSERVATION PACKETS" in p2
    assert "FAMILY F01" in p2
    assert "STRUCTURAL OBSERVATION PACKETS" not in p3
    assert "FAMILY F01" not in p3


def test_propose_p2_monkeypatched_chat_complete(monkeypatch):
    captured = {}

    def boom(*_a, **_k):
        raise AssertionError("packets_for_item must not run in unit tests")

    def fake_chat(messages, config=None):
        captured["messages"] = messages
        captured["config"] = config
        return {
            "blocked": False,
            "error": None,
            "content": json.dumps(_doc(_ok_hyp())),
            "api_key": "sk-abcdefghijklmnopqrstuvwxyz012345",
            "usage": {
                "prompt_tokens": 11,
                "completion_tokens": 7,
                "total_tokens": 18,
                "reasoning_tokens": 3,
            },
            "latency_s": 0.02,
            "model": "deepseek-v4-pro",
            "request_id": "test-req",
            "reasoning_len": 0,
            "reasoning_sha": None,
        }

    monkeypatch.setattr(
        "research.representation_invention.llm.propose.packets_for_item",
        boom,
    )
    monkeypatch.setattr(
        "research.representation_invention.llm.propose.chat_complete",
        fake_chat,
    )
    rec = propose_p2(_item(), _entries(), condition="P3", seed=0)
    assert rec["parse_status"] == OK, rec
    assert rec["n_ok"] == 1
    assert rec["n_hypotheses"] == 1
    assert rec["n_grounded"] == 1
    assert rec["condition"] == "P3"
    assert rec["usage"]["reasoning_tokens"] == 3
    assert rec["model"] == "deepseek-v4-pro"
    sys_msg, user_msg = captured["messages"]
    blob = sys_msg["content"] + "\n" + user_msg["content"]
    assert "Phi_Gamma" not in blob
    assert "L4" not in blob
    assert "gold_types" not in blob
    assert "STRUCTURAL OBSERVATION PACKETS" not in user_msg["content"]


def test_sanitize_fake_rec_must_not_include_api_key(monkeypatch):
    secret = "sk-abcdefghijklmnopqrstuvwxyz012345"

    def fake_chat(messages, config=None):
        return {
            "blocked": False,
            "error": None,
            "content": json.dumps(_doc(_ok_hyp())),
            "api_key": secret,
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            "latency_s": 0.01,
            "model": "deepseek-v4-pro",
        }

    monkeypatch.setattr(
        "research.representation_invention.llm.propose.packets_for_item",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no packetizer")),
    )
    monkeypatch.setattr(
        "research.representation_invention.llm.propose.chat_complete",
        fake_chat,
    )
    rec = propose_p2(_item(), _entries(), condition="P3")
    blob = json.dumps(rec)
    assert "api_key" not in blob
    assert secret not in blob
    assert ".env" not in blob


def test_propose_p2_p2_uses_injected_packets_not_packetizer(monkeypatch):
    captured = {}

    def fake_chat(messages, config=None):
        captured["user"] = messages[1]["content"]
        return {
            "blocked": False,
            "content": json.dumps(_doc(_ok_hyp())),
            "usage": {},
            "model": "deepseek-v4-pro",
        }

    monkeypatch.setattr(
        "research.representation_invention.llm.propose.packets_for_item",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no packetizer")),
    )
    monkeypatch.setattr(
        "research.representation_invention.llm.propose.chat_complete",
        fake_chat,
    )
    rec = propose_p2(
        _item(),
        _entries(),
        condition="P2",
        packets_text="FAMILY F01\nmembers:\n  G0001: K(n)",
    )
    assert rec["condition"] == "P2"
    assert rec["parse_status"] == OK
    assert "STRUCTURAL OBSERVATION PACKETS" in captured["user"]
    assert "FAMILY F01" in captured["user"]


def test_score_uses_compiler_fail_closed():
    scored = score_hypothesis(_ok_hyp() | {"parse_status": OK}, CAT)
    assert scored["grounded"] is True
    assert scored["compile_status"] in {COMPILE_NOT_WIRED, "COMPILE_OK", "COMPILE_FAILURE"}
    if scored["compile_status"] == "COMPILE_FAILURE":
        assert scored["layer"] == "C"
        assert scored["n_zero"] == 0


def test_p1_baseline_readonly_and_maps_type():
    assert map_p1_type("confluent_representation") == "local_confluence"
    paths = list(P1_RUNS_DIR.glob("*.json"))
    assert paths, "frozen P1 runs missing"
    before = {p: p.read_bytes() for p in paths}
    recs = load_p1_runs()
    summary = summarize_p1(recs)
    after = {p: p.read_bytes() for p in paths}
    assert before == after
    assert summary["n_records"] == len(paths)
    assert summary["type_counts"].get("confluent_representation", 0) >= 1
    assert summary["type_counts_v2"].get("local_confluence", 0) >= 1
    assert "confluent_representation" not in summary["type_counts_v2"]


def test_catalog_ids_from_entries():
    ids = catalog_ids(_entries())
    assert ids == CAT
    text = render_catalog(_entries())
    assert "G0001" in text and "G0002" in text
    assert "Phi_Gamma" not in text


def test_run_item_mocked(monkeypatch):
    from research.representation_invention.llm.run_p2 import run_item

    def fake_chat(messages, config=None):
        return {
            "blocked": False,
            "content": json.dumps(_doc(_ok_hyp())),
            "usage": {"reasoning_tokens": 2, "total_tokens": 9},
            "latency_s": 0.01,
            "model": "deepseek-v4-pro",
        }

    monkeypatch.setattr(
        "research.representation_invention.llm.propose.packets_for_item",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no packetizer")),
    )
    monkeypatch.setattr(
        "research.representation_invention.llm.propose.chat_complete",
        fake_chat,
    )
    rec = run_item(
        _item(),
        condition="P3",
        seed=4,
        catalog=_entries(),
    )
    assert rec["seed"] == 4
    assert rec["n_ok"] == 1
    assert rec["compile_status"] in {COMPILE_NOT_WIRED, "COMPILE_OK", "COMPILE_FAILURE", "skipped"}
    assert "api_key" not in json.dumps(rec)
