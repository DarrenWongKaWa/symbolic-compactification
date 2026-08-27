"""ssc-representation-bench-v0.1: schema, splits, no proposer leakage."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.representation_invention.bench.loader import (
    BENCH_ROOT,
    FREEZE_MANIFEST,
    HIDDEN_FIELDS,
    VERSION,
    assert_no_leakage,
    load_all,
    load_dev,
    load_test,
    proposer_view,
    validate_task,
)
from research.representation_invention.ladder import R_LEVELS
from research.representation_invention.schema import GID_RE, REPRESENTATION_TYPES
from symbolic_compactification import parse_expression

_R_RE = re.compile(r"\bR[0-8]\b")
_L_RE = re.compile(r"\bL[4-7]\b")
_GOLD_RE = re.compile(r"\bgold", re.I)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_counts_and_splits():
    dev = load_dev()
    test = load_test()
    assert len(dev) >= 12, len(dev)
    assert len(test) >= 8, len(test)
    assert all(it["split"] == "dev" for it in dev)
    assert all(it["split"] == "test" for it in test)
    ids = [it["id"] for it in dev + test]
    assert len(ids) == len(set(ids))
    assert all(it["version"] == VERSION for it in dev + test)


def test_files_live_under_owned_tree():
    for split, items in (("dev", load_dev()), ("test", load_test())):
        for it in items:
            path = BENCH_ROOT / "tasks" / split / f"{it['id']}.json"
            assert path.is_file(), path


def test_schema_on_disk():
    for it in load_all():
        validate_task(it, expected_split=it["split"])
        assert it["tier"] in ("A", "B", "C")
        assert it["task"] == "representation_invention"
        assert isinstance(it["catalog"], list)
        for entry in it["catalog"]:
            assert GID_RE.fullmatch(entry["id"])
            assert entry["text"].strip()


def test_tiers_cover_required_families():
    dev_ids = {it["id"] for it in load_dev()}
    test_ids = {it["id"] for it in load_test()}
    for required in (
        "dev-a-newton-first",
        "dev-a-repeated-node",
        "dev-a-hermite-two",
        "dev-a-deriv-family",
        "dev-a-recurrence-family",
        "dev-a-wrong-sign-dd",
        "dev-b-piecewise-dd",
        "dev-b-branch-degen",
        "dev-b-special-fn",
        "dev-b-master-induct",
        "dev-b-nonconfluent-pw",
        "dev-b-tautological-master",
        "dev-c-thermal-kernel",
        "dev-c-green-like",
        "dev-c-nl-response",
        "dev-c-pert-denom",
        "dev-c-tensor-family",
    ):
        assert required in dev_ids, required
    for required in (
        "test-a-newton-first",
        "test-a-repeated-node",
        "test-a-hermite-two",
        "test-a-wrong-sign-dd",
        "test-b-piecewise-dd",
        "test-b-nonconfluent-pw",
        "test-b-tautological-master",
        "test-c-thermal-kernel",
    ):
        assert required in test_ids, required
    assert {it["tier"] for it in load_dev()} >= {"A", "B", "C"}
    assert {it["tier"] for it in load_test()} >= {"A", "B", "C"}


def test_positive_and_adversarial_negatives():
    for split, items in (("dev", load_dev()), ("test", load_test())):
        polarities = {it["polarity"] for it in items}
        assert "positive" in polarities, split
        assert "negative" in polarities, split
        neg = [it for it in items if it["polarity"] == "negative"]
        assert any("divided_difference" in it["negative_tempting_structures"] for it in neg)
        assert any("master_function" in it["negative_tempting_structures"] for it in neg)


def test_hidden_eval_fields_present_on_disk():
    needed = (
        "target_type",
        "instance_maps",
        "r_level",
        "polarity",
        "negative_tempting_structures",
        "provenance_hidden",
        "difficulty",
    )
    for it in load_all():
        for key in needed:
            assert key in it, (it["id"], key)
        if it["polarity"] == "positive" and not it.get("catalog_external"):
            assert it["target_type"] in REPRESENTATION_TYPES
            assert it["r_level"] in R_LEVELS
        if it["polarity"] == "negative":
            assert it["target_type"] is None
            assert it["negative_tempting_structures"]


def test_proposer_view_strips_hidden_fields():
    items = load_all()
    assert items
    for it in items:
        view = proposer_view(it)
        blob = json.dumps(view)
        for key in HIDDEN_FIELDS:
            assert key not in view, (it["id"], key)
            assert f'"{key}"' not in blob, (it["id"], key)
        assert "catalog" in view or it.get("catalog_external")
        assert view.get("hidden_from_proposer") is True
        assert_no_leakage(view)
        tt = it.get("target_type")
        if tt:
            assert tt not in blob, (it["id"], tt)
        rlv = it.get("r_level")
        if rlv:
            assert rlv not in blob, (it["id"], rlv)
        assert "hermite_divided_difference" not in blob
        assert "Phi_Gamma" not in blob
        assert not _R_RE.search(blob), (it["id"], blob)
        assert not _GOLD_RE.search(blob), it["id"]
        assert not _L_RE.search(blob), it["id"]


def test_proposer_view_keeps_source_and_catalog():
    it = next(x for x in load_dev() if x["id"] == "dev-a-newton-first")
    view = proposer_view(it)
    assert view["current"] == it["current"]
    assert view["symbols"] == it["symbols"]
    assert view["functions"] == it["functions"]
    assert view["catalog"][0]["id"] == "G0001"
    assert "f(x)" in view["catalog"][0]["text"]
    assert set(view["catalog"][0]) <= {"id", "text", "kind"}
    assert "polarity" not in view
    assert "instance_maps" not in view


def test_no_guo_material_in_test():
    for it in load_test():
        blob = json.dumps(it).lower()
        assert "guo" not in blob
        assert "sigma_abc" not in blob
        assert "phi_gamma" not in blob
        assert it.get("catalog_external") is not True


def test_guo_pointer_is_dev_only_and_empty():
    ptr = next(x for x in load_dev() if x["id"] == "dev-guo-pointer")
    assert ptr["split"] == "dev"
    assert ptr.get("catalog_external") is True
    assert ptr["catalog"] == []
    view = proposer_view(ptr)
    assert_no_leakage(view)
    assert "Phi_Gamma" not in json.dumps(view)


def test_expressions_parse_short():
    for it in load_all():
        if it.get("catalog_external"):
            continue
        syms = it["symbols"]
        fns = it["functions"]
        texts = [it["current"]] + list(it["source_expressions"]) + [
            e["text"] for e in it["catalog"]
        ]
        for text in texts:
            if not text.strip():
                continue
            assert len(text) < 400, (it["id"], len(text))
            expr = parse_expression(text, syms, functions=fns or None)
            assert expr is not None


def test_freeze_manifest_matches_test_files():
    man = json.loads(FREEZE_MANIFEST.read_text())
    assert man["version"] == VERSION
    assert man["split"] == "test"
    files = man["files"]
    on_disk = sorted(p.name for p in (BENCH_ROOT / "tasks" / "test").glob("*.json"))
    assert on_disk == sorted(files)
    for name, digest in files.items():
        path = BENCH_ROOT / "tasks" / "test" / name
        assert _sha256(path) == digest, name


def test_leakage_helper_flags_hidden_keys():
    it = load_dev()[0]
    dirty = dict(proposer_view(it), target_type="divided_difference", r_level="R1")
    try:
        assert_no_leakage(dirty)
    except RuntimeError as exc:
        assert "F_LEAK" in str(exc)
    else:
        raise AssertionError("expected F_LEAK")
