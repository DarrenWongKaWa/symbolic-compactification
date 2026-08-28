"""Track V3-A degeneracy coordinates. Evaluation-only; no family verdict."""
from __future__ import annotations

import inspect
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.coordinates import (  # noqa: E402
    OUT,
    analyze_all,
    analyze_family,
    dumps,
    write as write_coordinates,
)
from research.iterated_confluence.coordinates import analyze as coord_mod  # noqa: E402
from research.multibranch_verification.piecewise import (  # noqa: E402
    DIAGONAL,
    GENERIC,
    HIGHER_DEGENERACY,
)
from research.representation_invention.labels import (  # noqa: E402
    FORBIDDEN_GOLD_PATTERNS,
)

FROZEN = ROOT / "research" / "iterated_confluence" / "FROZEN_INPUTS_V3.json"
COORD_DIR = ROOT / "research" / "iterated_confluence" / "coordinates"
FIVE_PAIR = ["{ell,m}", "{ell,n}", "{m,n}"]
AND_RE = re.compile(r"^And\(")
EQ_MN = "{m,n}"
EQ_ELN = "{ell,n}"
EQ_ELM = "{ell,m}"
GID_RE = re.compile(r"^G\d{4}$")
BANNED_LLM = (
    "openai",
    "anthropic",
    "groq",
    "litellm",
    "httpx",
    "requests.get",
    "research.representation_invention.llm",
    "research.llm_abstraction",
)


def _frozen():
    return json.loads(FROZEN.read_text(encoding="utf-8"))


def _hyps():
    return {h["family_id"]: h for h in _frozen()["hypotheses"]}


def _pkg_py_text() -> str:
    parts: list[str] = []
    for path in sorted(COORD_DIR.glob("*.py")):
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _by_id(row: dict) -> dict[str, dict]:
    return {m["member_id"]: m for m in row["members"]}


def test_public_api():
    assert callable(analyze_family)
    assert callable(analyze_all)
    assert callable(write_coordinates)


def test_seven_families_present():
    frozen = _frozen()
    blob = analyze_all(frozen)
    assert frozen["n_hypotheses"] == 7
    assert blob["n_families"] == 7
    assert len(blob["families"]) == 7
    ids = [f["family_id"] for f in blob["families"]]
    assert ids == frozen["family_ids"]
    assert ids == [h["family_id"] for h in frozen["hypotheses"]]
    assert blob["no_llm_calls"] is True
    assert blob["does_not_adjudicate"] is True
    for row in blob["families"]:
        assert "family_id" in row
        assert "coordinates" in row
        assert "members" in row
        for m in row["members"]:
            assert set(m) >= {
                "member_id",
                "cond",
                "role",
                "active_equalities",
                "free_coordinates",
            }


def test_no_invented_members():
    frozen = _frozen()
    blob = analyze_all(frozen)
    by = {f["family_id"]: f for f in blob["families"]}
    for hyp in frozen["hypotheses"]:
        row = by[hyp["family_id"]]
        assert [m["member_id"] for m in row["members"]] == hyp["member_ids"]
        assert len(row["members"]) == hyp["n_members"] == len(hyp["members"])
        freeze_ids = {m["member_id"] for m in hyp["members"]}
        out_ids = {m["member_id"] for m in row["members"]}
        assert out_ids == freeze_ids
        for mid in out_ids:
            assert GID_RE.match(mid)
        for rec in row["members"]:
            assert rec["member_id"] in freeze_ids
            src = next(m for m in hyp["members"] if m["member_id"] == rec["member_id"])
            assert rec["cond"] == src["cond"]


def test_true_branch_empty_active_equalities():
    frozen = _frozen()
    blob = analyze_all(frozen)
    n_true = 0
    for hyp, row in zip(frozen["hypotheses"], blob["families"]):
        members = _by_id(row)
        for src in hyp["members"]:
            if str(src.get("cond") or "").strip() != "True":
                continue
            n_true += 1
            rec = members[src["member_id"]]
            assert rec["role"] == GENERIC
            assert rec["active_equalities"] == []
            assert rec["free_coordinates"] == row["coordinates"]
    assert n_true >= 7


def test_and_ell_m_m_n_is_higher_degeneracy_with_two_equalities():
    frozen = _frozen()
    blob = analyze_all(frozen)
    n_and = 0
    for hyp, row in zip(frozen["hypotheses"], blob["families"]):
        members = _by_id(row)
        for src in hyp["members"]:
            cond = str(src.get("cond") or "")
            if "And(" not in cond:
                continue
            n_and += 1
            rec = members[src["member_id"]]
            assert rec["role"] == HIGHER_DEGENERACY
            assert len(rec["active_equalities"]) == 2
            assert set(rec["active_equalities"]) == {EQ_ELM, EQ_MN}
            assert rec["free_coordinates"] == []
    assert n_and == 6


def test_five_branch_pairwise_table():
    frozen = _frozen()
    blob = analyze_all(frozen)
    n5 = 0
    for hyp, row in zip(frozen["hypotheses"], blob["families"]):
        if hyp["n_members"] != 5:
            continue
        n5 += 1
        assert row["coordinates"] == FIVE_PAIR
        assert row["linear_dependence"] is not None
        assert "(ell=m) follows from (ell=n and m=n)" in row["linear_dependence"]["note"]
        members = _by_id(row)
        for src in hyp["members"]:
            rec = members[src["member_id"]]
            cond = src["cond"]
            if cond == "True":
                assert rec["role"] == GENERIC
                assert rec["active_equalities"] == []
                assert rec["free_coordinates"] == FIVE_PAIR
            elif cond == "Equality(Symbol('m', real=True), Symbol('n', real=True))":
                assert rec["role"] == DIAGONAL
                assert rec["active_equalities"] == [EQ_MN]
                assert rec["free_coordinates"] == [EQ_ELM, EQ_ELN]
            elif cond == "Equality(Symbol('ell', real=True), Symbol('n', real=True))":
                assert rec["role"] == DIAGONAL
                assert rec["active_equalities"] == [EQ_ELN]
                assert rec["free_coordinates"] == [EQ_ELM, EQ_MN]
            elif cond == "Equality(Symbol('ell', real=True), Symbol('m', real=True))":
                assert rec["role"] == DIAGONAL
                assert rec["active_equalities"] == [EQ_ELM]
                assert rec["free_coordinates"] == [EQ_ELN, EQ_MN]
            elif AND_RE.match(cond):
                assert rec["role"] == HIGHER_DEGENERACY
                assert len(rec["active_equalities"]) == 2
            else:
                raise AssertionError((hyp["family_id"], src["member_id"], cond))
    assert n5 == 6


def test_s2_i4_substitution_is_not_a_degeneracy_coordinate():
    row = analyze_family(_hyps()["guo-p2-s2-i4"])
    assert row["coordinates"] == [EQ_MN]
    assert EQ_ELM not in row["coordinates"]
    assert EQ_ELN not in row["coordinates"]
    assert row["linear_dependence"] is None
    maps = [s["map"] for s in row["substitution_operators"]]
    assert maps
    for mp in maps:
        assert mp.get("b") == "c"
        assert "substitution is not a degeneracy coordinate" in (
            row["substitution_operators"][0]["note"]
        )
        assert "b" in mp and "c" in mp
    for rec in row["members"]:
        assert rec["member_id"] in {"G0004", "G0005", "G0008", "G0009"}
        if rec["cond"] == "True":
            assert rec["active_equalities"] == []
            assert rec["free_coordinates"] == [EQ_MN]
        else:
            assert rec["role"] == DIAGONAL
            assert rec["active_equalities"] == [EQ_MN]
            assert rec["free_coordinates"] == []
        joined = json.dumps(rec)
        assert "b" not in rec["active_equalities"]
        assert "c" not in rec["active_equalities"]
        assert "{b,c}" not in joined


def test_operator_epsilon_pairs_are_same_coordinates():
    frozen = _frozen()
    blob = analyze_all(frozen)
    for row in blob["families"]:
        index_ids = set(row["coordinates"])
        for form in row["operator_epsilon_pairs"]:
            assert form.startswith("epsilon(")
            left, right = form.split("-", 1)
            ia = left[len("epsilon(") : -1]
            ib = right[len("epsilon(") : -1]
            pid = "{" + ",".join(sorted((ia, ib))) + "}"
            assert pid in index_ids
        if row["family_id"] == "guo-p2-s2-i4":
            assert row["operator_epsilon_pairs"] == ["epsilon(m)-epsilon(n)"]


def test_analyze_family_does_not_call_an_llm():
    src = inspect.getsource(analyze_family)
    pkg = _pkg_py_text()
    for token in BANNED_LLM:
        assert token not in src
        assert token not in pkg
    hyp = _frozen()["hypotheses"][0]
    row = analyze_family(hyp)
    assert row["family_id"] == hyp["family_id"]
    assert len(row["members"]) == len(hyp["member_ids"])


def test_source_ban_coordinates_py():
    pkg = _pkg_py_text()
    for pat in FORBIDDEN_GOLD_PATTERNS:
        assert re.search(pat, pkg) is None, pat
    assert "Phi_Gamma" not in pkg
    assert "FAMILY_ZERO" not in pkg
    assert "FAMILY_NONZERO" not in pkg
    for path in COORD_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "Phi_Gamma" not in text
        assert "FAMILY_ZERO" not in text


def test_committed_json_matches_builder():
    blob = analyze_all()
    dest = write_coordinates(OUT)
    assert dest == OUT
    disk = json.loads(OUT.read_text(encoding="utf-8"))
    assert dumps(disk) == dumps(blob)
    assert disk["n_families"] == 7
