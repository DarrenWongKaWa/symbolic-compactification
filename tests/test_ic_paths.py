"""Track V3-B one-parameter path enumerator. Evaluation-only."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.paths import (  # noqa: E402
    OUT,
    dumps,
    enumerate_all,
    enumerate_family,
    write,
)
from research.iterated_confluence.schema import (  # noqa: E402
    PATH_UNKNOWN,
    UNKNOWN,
    PathCertificate,
    PathStep,
)
from research.multibranch_verification.graph.build import (  # noqa: E402
    _is_true,
    _parse_equalities,
)
from research.multibranch_verification.piecewise import (  # noqa: E402
    HIGHER_DEGENERACY,
    classify_condition,
)
from research.representation_invention.labels import FORBIDDEN_GOLD_PATTERNS  # noqa: E402

FROZEN_PATH = ROOT / "research" / "iterated_confluence" / "FROZEN_INPUTS_V3.json"
SRC_DIR = ROOT / "research" / "iterated_confluence" / "paths"
GID_RE = re.compile(r"^G\d{4}$")


@pytest.fixture(scope="module")
def frozen():
    return json.loads(FROZEN_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def blob():
    return enumerate_all()


@pytest.fixture(scope="module")
def families(blob):
    return {f["family_id"]: f for f in blob["families"]}


@pytest.fixture(scope="module")
def hyps(frozen):
    return {h["family_id"]: h for h in frozen["hypotheses"]}


def _eqset(cond: str) -> frozenset[frozenset[str]]:
    return frozenset(frozenset(p) for p in _parse_equalities(cond))


def _by_eq(hyp: dict) -> dict[frozenset[frozenset[str]], str]:
    out = {}
    for m in hyp["members"]:
        out[_eqset(str(m.get("cond") or ""))] = m["member_id"]
    return out


def _generic_ids(hyp: dict) -> list[str]:
    return [m["member_id"] for m in hyp["members"] if _is_true(str(m.get("cond") or ""))]


def _higher_ids(hyp: dict) -> list[str]:
    out = []
    for m in hyp["members"]:
        cond = str(m.get("cond") or "")
        if classify_condition(cond)["role"] == HIGHER_DEGENERACY:
            out.append(m["member_id"])
        elif len(_parse_equalities(cond)) >= 2:
            out.append(m["member_id"])
    return out


def _max_ops(path: dict, hyp: dict) -> int:
    ops = hyp["op_counts"]
    m = 0
    for step in path["steps"]:
        for mid in (step["source"], step["target"]):
            m = max(m, int(ops[mid]))
    return m


def _is_certified_shape(path: dict, hyp: dict) -> bool:
    if len(path["steps"]) != 1:
        return False
    by = {m["member_id"]: m for m in hyp["members"]}
    src = by[path["start_member"]]
    tgt = by[path["end_member"]]
    if not _is_true(str(src.get("cond") or "")):
        return False
    eqs = _parse_equalities(str(tgt.get("cond") or ""))
    return len(eqs) == 1 and set(eqs[0]) == {"m", "n"}


def _rank(path: dict, hyp: dict) -> tuple:
    certified = 0 if _is_certified_shape(path, hyp) else 1
    return (len(path["steps"]), _max_ops(path, hyp), certified, path["path_id"])


def test_public_api_and_seven_families(blob, frozen):
    assert callable(enumerate_family)
    assert callable(enumerate_all)
    assert callable(write)
    assert blob["n_families"] == 7
    assert blob["no_llm_calls"] is True
    assert blob["evaluation_only"] is True
    assert blob["does_not_adjudicate"] is True
    assert blob["family_ids"] == [h["family_id"] for h in frozen["hypotheses"]]
    assert len(blob["families"]) == 7


def test_five_branch_has_two_distinct_two_step_generic_to_higher(families, hyps):
    n5 = 0
    for fid, hyp in hyps.items():
        if len(hyp["member_ids"]) != 5:
            continue
        n5 += 1
        fam = families[fid]
        generic = set(_generic_ids(hyp))
        higher = set(_higher_ids(hyp))
        two = [
            p
            for p in fam["paths"]
            if len(p["steps"]) == 2
            and p["start_member"] in generic
            and p["end_member"] in higher
        ]
        ids = [p["path_id"] for p in two]
        assert len(two) >= 2, (fid, ids)
        assert len(set(ids)) == len(ids)
        for p in two:
            assert p["steps"][0]["source"] == p["start_member"]
            assert p["steps"][-1]["target"] == p["end_member"]
            assert p["steps"][0]["target"] == p["steps"][1]["source"]
    assert n5 == 6


def test_five_branch_expected_lattice_coordinates(families, hyps):
    mn = frozenset({frozenset({"m", "n"})})
    elln = frozenset({frozenset({"ell", "n"})})
    ellm = frozenset({frozenset({"ell", "m"})})
    for fid, hyp in hyps.items():
        if len(hyp["member_ids"]) != 5:
            continue
        fam = families[fid]
        by = _by_eq(hyp)
        g = by[frozenset()]
        m_n = by[mn]
        e_n = by[elln]
        e_m = by[ellm]
        trip = [mid for s, mid in by.items() if s != frozenset() and s not in {mn, elln, ellm}]
        assert len(trip) == 1
        t = trip[0]
        member_chains = {
            "->".join([p["start_member"], *[st["target"] for st in p["steps"]]])
            for p in fam["paths"]
        }
        assert f"{g}->{m_n}->{t}" in member_chains
        assert f"{g}->{e_n}->{t}" in member_chains
        assert f"{g}->{e_m}->{t}" in member_chains
        by_chain = {
            "->".join([p["start_member"], *[st["target"] for st in p["steps"]]]): p
            for p in fam["paths"]
        }
        p_mn = by_chain[f"{g}->{m_n}->{t}"]
        assert p_mn["steps"][0]["variable"] == "epsilon(m)"
        assert p_mn["steps"][0]["target_value"] == "epsilon(n)"
        assert p_mn["steps"][1]["variable"] == "epsilon(ell)"
        assert p_mn["steps"][1]["target_value"] == "epsilon(n)"
        p_en = by_chain[f"{g}->{e_n}->{t}"]
        assert p_en["steps"][0]["variable"] == "epsilon(ell)"
        assert p_en["steps"][0]["target_value"] == "epsilon(n)"
        assert p_en["steps"][1]["variable"] == "epsilon(m)"
        assert p_en["steps"][1]["target_value"] == "epsilon(n)"
        p_em = by_chain[f"{g}->{e_m}->{t}"]
        assert p_em["steps"][0]["variable"] == "epsilon(ell)"
        assert p_em["steps"][0]["target_value"] == "epsilon(m)"
        assert p_em["steps"][1]["variable"] == "epsilon(m)"
        assert p_em["steps"][1]["target_value"] == "epsilon(n)"
        one = {
            (p["start_member"], p["end_member"])
            for p in fam["paths"]
            if len(p["steps"]) == 1
        }
        for src, tgt in ((g, m_n), (g, e_n), (g, e_m), (m_n, t), (e_n, t), (e_m, t)):
            assert (src, tgt) in one


def test_every_step_has_exactly_one_variable(blob):
    n = 0
    for fam in blob["families"]:
        for p in fam["paths"]:
            assert p["path_verdict"] == PATH_UNKNOWN
            for step in p["steps"]:
                n += 1
                assert step["relation"] == "one_parameter_confluence"
                assert step["verdict"] == UNKNOWN
                var = step["variable"]
                val = step["target_value"]
                assert isinstance(var, str) and var
                assert isinstance(val, str) and val
                assert "," not in var
                assert "," not in val
                assert var.startswith("epsilon(")
                assert val.startswith("epsilon(")
    assert n >= 10


def test_no_path_uses_member_outside_family(families, hyps):
    for fid, fam in families.items():
        allowed = set(hyps[fid]["member_ids"])
        assert set(fam["member_ids"]) == allowed
        for p in fam["paths"]:
            assert GID_RE.match(p["start_member"])
            assert GID_RE.match(p["end_member"])
            assert p["start_member"] in allowed
            assert p["end_member"] in allowed
            for step in p["steps"]:
                assert step["source"] in allowed
                assert step["target"] in allowed
                assert GID_RE.match(step["source"])
                assert GID_RE.match(step["target"])
        for rec in fam["rejected_multi_parameter"]:
            assert rec["source"] in allowed
            assert rec["target"] in allowed


def test_rejected_includes_two_parameter_generic_to_triple(families, hyps):
    n = 0
    for fid, hyp in hyps.items():
        if len(hyp["member_ids"]) != 5:
            continue
        fam = families[fid]
        generic = set(_generic_ids(hyp))
        higher = set(_higher_ids(hyp))
        hits = [
            r
            for r in fam["rejected_multi_parameter"]
            if r.get("reason") == "not_one_parameter"
            and r["source"] in generic
            and r["target"] in higher
        ]
        assert hits, fid
        n += 1
        for r in hits:
            assert r.get("n_parameters", 2) >= 2
        one_step_pairs = {
            (p["start_member"], p["end_member"])
            for p in fam["paths"]
            if len(p["steps"]) == 1
        }
        for r in hits:
            assert (r["source"], r["target"]) not in one_step_pairs
    assert n == 6


def test_s2_i4_two_confluence_one_step_paths(families, hyps):
    hyp = hyps["guo-p2-s2-i4"]
    fam = families["guo-p2-s2-i4"]
    pairs = {(p["start_member"], p["end_member"]) for p in fam["paths"]}
    assert ("G0005", "G0004") in pairs
    assert ("G0009", "G0008") in pairs
    assert all(len(p["steps"]) == 1 for p in fam["paths"])
    for p in fam["paths"]:
        assert p["steps"][0]["relation"] == "one_parameter_confluence"
        assert p["steps"][0]["variable"] == "epsilon(m)"
        assert p["steps"][0]["target_value"] == "epsilon(n)"
    confluence_pairs = {
        (p["start_member"], p["end_member"])
        for p in fam["paths"]
        if p["steps"][0]["relation"] == "one_parameter_confluence"
    }
    assert confluence_pairs == {("G0005", "G0004"), ("G0009", "G0008")}
    assert ("G0005", "G0009") not in pairs
    assert ("G0005", "G0008") not in pairs
    subs = {(s["source"], s["target"], s["relation"]) for s in fam["substitutions"]}
    assert ("G0005", "G0009", "substitution") in subs
    for p in fam["paths"]:
        assert all(st["relation"] != "substitution" for st in p["steps"])
    assert fam["rejected_multi_parameter"] == []


def test_incomparable_diagonals_not_joined(families, hyps):
    for fid, hyp in hyps.items():
        fam = families[fid]
        diagonals = [
            m["member_id"]
            for m in hyp["members"]
            if len(_parse_equalities(str(m.get("cond") or ""))) == 1
        ]
        step_pairs = {
            (st["source"], st["target"])
            for p in fam["paths"]
            for st in p["steps"]
        }
        for i, a in enumerate(diagonals):
            for b in diagonals[i + 1 :]:
                assert (a, b) not in step_pairs
                assert (b, a) not in step_pairs


def test_ranking_deterministic(families, hyps):
    again = enumerate_all()
    first = enumerate_all()
    assert dumps(first) == dumps(again)
    for fid, fam in families.items():
        hyp = hyps[fid]
        keys = [_rank(p, hyp) for p in fam["paths"]]
        assert keys == sorted(keys)
        ids = [p["path_id"] for p in fam["paths"]]
        assert ids == sorted(ids, key=lambda i: keys[ids.index(i)])


def test_schema_objects_roundtrip_unknown_verdicts(hyps):
    hyp = next(h for h in hyps.values() if len(h["member_ids"]) == 5)
    fam = enumerate_family(hyp)
    assert fam["family_id"] == hyp["family_id"]
    assert fam["paths"]
    for raw in fam["paths"]:
        steps = [PathStep(**{k: s[k] for k in PathStep.__dataclass_fields__}) for s in raw["steps"]]
        cert = PathCertificate(
            path_id=raw["path_id"],
            start_member=raw["start_member"],
            end_member=raw["end_member"],
            steps=steps,
            path_verdict=raw["path_verdict"],
            provenance=list(raw["provenance"]),
        )
        assert cert.path_verdict == PATH_UNKNOWN
        assert all(s.verdict == UNKNOWN for s in cert.steps)
        assert cert.to_dict()["path_id"] == raw["path_id"]


def test_source_ban(blob):
    blob_text = dumps(blob)
    src_files = list(SRC_DIR.rglob("*"))
    texts = [blob_text]
    for path in src_files:
        if path.suffix in {".py", ".md", ".json"} and path.is_file():
            texts.append(path.read_text(encoding="utf-8"))
    joined = "\n".join(texts)
    assert "Phi_Gamma" not in joined
    assert "FAMILY_ZERO" not in joined
    for pat in FORBIDDEN_GOLD_PATTERNS:
        assert re.search(pat, joined) is None, pat


def test_committed_json_matches_builder(blob):
    assert OUT.is_file(), f"missing {OUT}"
    disk = json.loads(OUT.read_text(encoding="utf-8"))
    assert dumps(disk) == dumps(blob)
    assert disk["n_families"] == blob["n_families"] == 7
