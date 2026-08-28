"""Exact intermediate builder. No heuristic interpolation. No gold names."""
from __future__ import annotations

import ast
import inspect
import json
import re
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.intermediates import (  # noqa: E402
    EQ_IMPOSITION,
    SUBSTITUTION,
    IntermediateBuild,
    build_intermediate,
    frozen_source_lattice_coverage,
    intermediates_required_for_frozen_families,
)
from research.iterated_confluence.schema import IntermediateExpression  # noqa: E402
import research.iterated_confluence.intermediates as inter_pkg  # noqa: E402
import research.iterated_confluence.intermediates.build as build_mod  # noqa: E402
import research.iterated_confluence.intermediates.lattice as lattice_mod  # noqa: E402

INTER_DIR = ROOT / "research" / "iterated_confluence" / "intermediates"
FROZEN_PATH = ROOT / "research" / "iterated_confluence" / "FROZEN_INPUTS_V3.json"
GID_RE = re.compile(r"^G\d{4}$")
GOLD = ("Phi_Gamma", "PhiGamma", "L4", "L5", "L6", "L7", "PRB master")


def _xy():
    return sympy.symbols("x y")


def _uneval_ratio(num, den):
    return sympy.Mul(num, sympy.Pow(den, -1, evaluate=False), evaluate=False)


def test_public_api_signature():
    assert callable(build_intermediate)
    sig = inspect.signature(build_intermediate)
    assert list(sig.parameters)[:5] == [
        "parent_expr",
        "variable",
        "target_value",
        "parent_id",
        "symbols",
    ]
    assert "IntermediateBuild" in inter_pkg.__all__
    assert "build_intermediate" in inter_pkg.__all__


def test_exact_subs_x_plus_y_at_y_zero():
    x, y = _xy()
    built = build_intermediate(x + y, y, 0, "P0")
    assert isinstance(built, IntermediateBuild)
    assert isinstance(built.record, IntermediateExpression)
    assert built.reconstruction_ok is True
    assert built.record.reconstruction_ok is True
    assert built.expr == x
    assert built.expr == (x + y).subs(y, 0)
    assert built.expr == (x + y).xreplace({y: 0})
    assert built.record.parent_id == "P0"
    assert built.record.transformation == SUBSTITUTION
    assert "xreplace" in built.record.provenance
    assert built.record.expr_sha256
    assert built.record.intermediate_id.startswith("P0|")


def test_eq_imposition_is_exact_substitution():
    x, y = _xy()
    built = build_intermediate(x + y, sympy.Eq(y, 0), None, "P0")
    assert built.reconstruction_ok is True
    assert built.expr == x
    assert built.record.transformation == EQ_IMPOSITION
    via_cond = build_intermediate(x + y, None, None, "P0", condition=sympy.Eq(y, 0))
    assert via_cond.reconstruction_ok is True
    assert via_cond.expr == x


def test_string_inputs_with_declared_symbols():
    x, y = _xy()
    built = build_intermediate("x+y", "y", "0", "P0", symbols=["x", "y"])
    assert built.reconstruction_ok is True
    assert built.expr == x


def test_limit_like_ratio_not_rewritten_to_one():
    x, y = _xy()
    parent = _uneval_ratio(x - y, x - y)
    assert parent != 1
    built = build_intermediate(parent, y, x, "P0")
    assert built.reconstruction_ok is False
    assert built.expr is None
    assert built.record.reconstruction_ok is False
    assert built.record.expr_sha256 == ""
    assert built.record.transformation != "limit"
    raw = parent.xreplace({y: x})
    assert raw.has(sympy.nan) or raw == 0 or not raw.is_finite
    assert built.expr != 1


def test_difference_of_squares_requires_limit_not_intermediate():
    x, y = _xy()
    parent = (x**2 - y**2) / (x - y)
    built = build_intermediate(parent, y, x, "P0")
    assert built.reconstruction_ok is False
    assert built.expr is None
    cancelled = sympy.cancel(parent).xreplace({y: x})
    assert cancelled == 2 * x
    assert built.record.provenance.startswith("refused:")
    assert "limit" in built.record.provenance or "not_finite" in built.record.provenance


def test_pole_is_not_an_intermediate():
    x, y = _xy()
    built = build_intermediate(1 / (x - y), y, x, "P0")
    assert built.reconstruction_ok is False
    assert built.expr is None


def test_missing_substitution_refuses():
    x, y = _xy()
    built = build_intermediate(x + y, None, None, "P0")
    assert built.reconstruction_ok is False
    assert built.expr is None


def test_no_heuristic_interpolation_of_missing_branches():
    for name in (
        "interpolate",
        "interpolate_branch",
        "invent_intermediate",
        "fill_missing",
        "guess_branch",
    ):
        assert not hasattr(inter_pkg, name)
        assert not hasattr(build_mod, name)
        assert not hasattr(lattice_mod, name)
    x, y = _xy()
    parent = (x**2 - y**2) / (x - y)
    built = build_intermediate(parent, y, x, "P0")
    assert built.reconstruction_ok is False
    assert built.expr is None
    src = inspect.getsource(build_mod) + inspect.getsource(lattice_mod)
    assert "def interpolate" not in src
    tree = ast.parse(inspect.getsource(build_mod))
    calls = [
        n.attr if isinstance(n, ast.Attribute) else n.id
        for n in ast.walk(tree)
        if isinstance(n, (ast.Attribute, ast.Name))
    ]
    assert "limit" not in calls
    assert "cancel" not in calls
    assert "simplify" not in calls
    assert "series" not in calls


def test_source_ban_phi_gamma():
    src = inspect.getsource(build_mod) + inspect.getsource(lattice_mod)
    src += inspect.getsource(inter_pkg)
    for token in GOLD:
        assert token not in src
    for path in INTER_DIR.rglob("*"):
        if path.suffix in {".py", ".md"} and path.is_file():
            text = path.read_text(encoding="utf-8")
            for token in GOLD:
                assert token not in text, (path.name, token)


def test_five_branch_guo_lattice_needs_no_intermediate():
    frozen = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))
    report = frozen_source_lattice_coverage(frozen)
    required = intermediates_required_for_frozen_families(frozen)
    five = [row for row in report if row["n_members"] == 5]
    assert len(five) == 6
    for row in five:
        assert row["intermediates_required"] is False
        assert row["missing_nodes"] == []
        assert row["constructed_intermediates"] == []
        assert row["unclassified_members"] == []
        assert set(row["index_names"]) == {"ell", "m", "n"}
        nodes = {tuple(n["indices"]) for n in row["present_nodes"]}
        assert nodes == {(), ("m", "n"), ("ell", "n"), ("ell", "m"), ("ell", "m", "n")} or nodes == {
            (),
            ("ell", "m"),
            ("ell", "n"),
            ("m", "n"),
            ("ell", "m", "n"),
        }
        for mid in row["member_ids"]:
            assert GID_RE.fullmatch(mid)
        assert required[row["family_id"]] is False
    assert all(v is False for v in required.values())
    for row in report:
        assert row["constructed_intermediates"] == []


def test_condition_mismatch_refuses():
    x, y = _xy()
    built = build_intermediate(
        x + y, y, 1, "P0", condition=sympy.Eq(y, 0)
    )
    assert built.reconstruction_ok is False
    assert built.expr is None
    assert "not_from_condition" in built.record.provenance
