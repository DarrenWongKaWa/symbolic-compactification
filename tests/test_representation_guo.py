"""Guo DEV catalog: G#### ids, 4/14 counts, gold-free proposer view."""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.representation_invention.labels import FORBIDDEN_GOLD_PATTERNS  # noqa: E402
from research.representation_invention.schema import is_catalog_id  # noqa: E402

GUO_DIR = ROOT / "research" / "representation_invention" / "guo"
PROPOSER_VISIBLE_PY = ("__init__.py", "catalog.py", "proposer_view.py")


@pytest.fixture(scope="module")
def guo_catalog():
    from research.representation_invention.guo.catalog import load_guo_catalog

    return load_guo_catalog()


def _import_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names.append(mod)
            prefix = f"{mod}." if mod else ""
            names.extend(f"{prefix}{alias.name}" for alias in node.names)
    return names


def test_catalog_ids_are_gxxxx(guo_catalog):
    from research.representation_invention.guo.catalog import (
        CATALOG_ENTRY_KEYS,
        assert_catalog_ids,
    )

    entries = guo_catalog.entries
    assert entries, "catalog must not be empty on the real Guo DEV expression"
    assert_catalog_ids(entries)
    for e in entries:
        assert is_catalog_id(e["source_node_id"])
        extra = set(e) - set(CATALOG_ENTRY_KEYS)
        assert not extra, extra
    assert all(is_catalog_id(i) for i in guo_catalog.ids)


def test_real_guo_n_sums_and_n_piecewise_branches(guo_catalog):
    from research.representation_invention.guo.catalog import (
        EXPECTED_N_PIECEWISE_BRANCHES,
        EXPECTED_N_SUMS,
        GUO_SOURCE,
        count_catalog_kinds,
    )

    assert GUO_SOURCE.is_file(), f"Guo DEV source missing: {GUO_SOURCE}"
    assert EXPECTED_N_SUMS == 4
    assert EXPECTED_N_PIECEWISE_BRANCHES == 14
    assert guo_catalog.n_sums == 4
    assert guo_catalog.n_piecewise_branches == 14
    kinds = count_catalog_kinds(guo_catalog.entries)
    assert kinds["n_sums"] == 4
    assert kinds["n_piecewise_branches"] == 14


def test_render_catalog_has_no_forbidden_gold(guo_catalog):
    from research.representation_invention.guo.catalog import render_catalog
    from research.representation_invention.guo.proposer_view import (
        render_proposer_view,
    )

    text = render_catalog(guo_catalog.entries)
    assert "SOURCE CATALOG" in text
    blob = text + "\n" + render_proposer_view(guo_catalog)
    for pat in FORBIDDEN_GOLD_PATTERNS:
        assert re.search(pat, blob) is None, pat
    for name in PROPOSER_VISIBLE_PY:
        src = (GUO_DIR / name).read_text(encoding="utf-8")
        for pat in FORBIDDEN_GOLD_PATTERNS:
            assert re.search(pat, src) is None, (name, pat)


def test_queries_module_not_imported_by_proposer_view():
    doomed = [
        m for m in sys.modules
        if m == "research.representation_invention.guo"
        or m.startswith("research.representation_invention.guo.")
    ]
    for m in doomed:
        del sys.modules[m]
    import importlib

    pv = importlib.import_module("research.representation_invention.guo.proposer_view")

    assert "research.representation_invention.guo.eval.queries" not in sys.modules
    assert "research.representation_invention.guo.eval" not in sys.modules
    for name in PROPOSER_VISIBLE_PY:
        imported = _import_names(GUO_DIR / name)
        blob = " ".join(imported)
        assert "queries" not in blob, (name, imported)
        assert not any(tok == "eval" or tok.startswith("eval.") for tok in imported)
    assert "COUNTS.md" in pv.HIDDEN_FROM_PROPOSER
    assert "eval/queries.py" in pv.HIDDEN_FROM_PROPOSER


def test_hidden_files_not_in_proposer_view(guo_catalog):
    from research.representation_invention.guo.eval.queries import QUERY_IDS
    from research.representation_invention.guo.proposer_view import (
        HIDDEN_FROM_PROPOSER,
        SCIENTIFIC_CONTEXT,
        proposer_view,
        render_proposer_view,
    )

    assert "COUNTS.md" in HIDDEN_FROM_PROPOSER
    assert "eval/queries.py" in HIDDEN_FROM_PROPOSER
    assert (GUO_DIR / "COUNTS.md").is_file()
    assert (GUO_DIR / "eval" / "queries.py").is_file()
    assert not (GUO_DIR / "queries.py").exists()

    view = proposer_view(guo_catalog)
    text = render_proposer_view(guo_catalog)
    for rel in HIDDEN_FROM_PROPOSER:
        assert rel not in view
        assert rel not in text
        assert rel not in view.get("catalog_text", "")
    for qid in QUERY_IDS:
        assert qid not in text
        assert qid not in view.get("catalog_text", "")
    assert view["scientific_context"] == list(SCIENTIFIC_CONTEXT)
    assert all(is_catalog_id(i) for i in view["catalog_ids"])


def test_eval_queries_cover_four_families(guo_catalog):
    from research.representation_invention.guo.eval.queries import (
        QUERY_IDS,
        instantiate_queries,
    )

    rows = instantiate_queries(guo_catalog.entries)
    families = {q["family"] for q in rows}
    assert families == {
        "local_confluence",
        "newton_dd_candidate",
        "repeated_node_dd",
        "possible_master_families",
    }
    assert QUERY_IDS == tuple(q["id"] for q in rows)
    by_id = {q["id"]: q for q in rows}
    assert by_id["Q-local-confluence"]["candidate_pairs"]
    assert by_id["Q-newton-dd-candidate"]["candidate_pairs"]
    assert by_id["Q-repeated-node-dd"]["candidate_members"]
    assert by_id["Q-possible-master-families"]["candidate_families"]
