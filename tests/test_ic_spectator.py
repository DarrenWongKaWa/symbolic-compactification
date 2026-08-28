"""Exact spectator split for V3 edges. False decomposition acceptance = 0.

Guo evaluation of 573-op five-branch kernels belongs to eval/;
do not gcd those here (Track V ops cap 80, gcd may hang).
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import pytest
import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.spectator import (  # noqa: E402
    count_ops,
    split_edge,
    split_report,
)
from research.iterated_confluence.spectator import split as split_mod  # noqa: E402
from research.scalable_verification.factor import (  # noqa: E402
    split_additive,
    split_multiplicative,
)

KEYS = {
    "certified",
    "mode",
    "S",
    "A_local",
    "B_local",
    "full_ops_A",
    "full_ops_B",
    "local_ops_A",
    "local_ops_B",
    "spectator_ops",
    "reduction_ratio_A",
    "reduction_ratio_B",
    "note",
    "reconstruction_ok",
}

x, y, z = sympy.symbols("x y z")
m, n = sympy.symbols("m n")
h1 = sympy.Function("h1")
h2 = sympy.Function("h2")


def _eq(a: sympy.Expr, b: sympy.Expr) -> bool:
    if a == b:
        return True
    try:
        return sympy.cancel(a - b) == 0
    except Exception:
        return False


def _assert_shape(out: dict) -> None:
    assert set(out) == KEYS
    assert isinstance(out["certified"], bool)
    assert out["mode"] in {"multiplicative", "additive", "none"}
    assert isinstance(out["note"], str) and out["note"]
    assert isinstance(out["reconstruction_ok"], bool)
    assert isinstance(out["S"], sympy.Expr)
    assert isinstance(out["A_local"], sympy.Expr)
    assert isinstance(out["B_local"], sympy.Expr)
    for key in (
        "full_ops_A",
        "full_ops_B",
        "local_ops_A",
        "local_ops_B",
        "spectator_ops",
    ):
        assert isinstance(out[key], int) and out[key] >= 0
    for key in ("reduction_ratio_A", "reduction_ratio_B"):
        assert out[key] is None or isinstance(out[key], float)


def _assert_no_proving_kernel(out: dict, A: sympy.Expr, B: sympy.Expr) -> None:
    _assert_shape(out)
    assert out["certified"] is False
    assert out["reconstruction_ok"] is False
    assert out["mode"] == "none"
    assert out["S"] == 1
    assert out["A_local"] == A
    assert out["B_local"] == B


def test_public_api_importable():
    from research.iterated_confluence.spectator import split_edge as se
    from research.iterated_confluence.spectator.split import split_edge as se_mod

    assert se is se_mod
    assert callable(count_ops)
    assert callable(split_report)


def test_wraps_track_v_not_a_copy():
    src = inspect.getsource(split_mod)
    assert "from research.scalable_verification.factor import" in src
    assert "split_multiplicative" in src
    assert "split_additive" in src
    assert "def split_multiplicative" not in src
    assert "def split_additive" not in src


# --------------------------------------------------------------------------- #
# Positives
# --------------------------------------------------------------------------- #


def test_cubic_common_linear_factor_splits_with_reconstruction():
    F = x**2 + x * y + y**2
    G = 3 * x**2
    A = (x - y) * F
    B = (x - y) * G
    out = split_edge(A, B)
    _assert_shape(out)
    assert out["certified"] is True
    assert out["reconstruction_ok"] is True
    assert out["mode"] == "multiplicative"
    assert _eq(out["S"], x - y)
    assert _eq(out["A_local"], F)
    assert _eq(out["B_local"], G)
    assert _eq(out["S"] * out["A_local"], A)
    assert _eq(out["S"] * out["B_local"], B)
    v = split_multiplicative(A, B)
    assert v["certified"] is True
    assert _eq(out["S"], v["S"])
    assert _eq(out["A_local"], v["A_local"])
    assert _eq(out["B_local"], v["B_local"])
    assert out["full_ops_A"] == count_ops(A)
    assert out["local_ops_A"] == count_ops(out["A_local"])
    if out["full_ops_A"] > 0:
        assert out["reduction_ratio_A"] == out["local_ops_A"] / out["full_ops_A"]
        assert out["reduction_ratio_A"] < 1.0


def test_spectator_depending_on_degeneration_is_not_peeled():
    A = y * (y + 3)
    B = 3 * y
    peeled = split_edge(A, B)
    assert peeled["certified"] is True
    blocked = split_edge(A, B, degeneration=y)
    assert blocked["certified"] is False
    assert blocked["note"] == "spectator_depends_on_degeneration"
    assert _eq(blocked["A_local"], A)
    assert _eq(blocked["B_local"], B)


def test_mul_args_peel_does_not_increase_ops():
    K = x + 1
    L = y + 2
    A = h1(m) * h2(n) * K
    B = h1(m) * h2(n) * L
    out = split_edge(A, B)
    assert out["certified"] is True
    assert out["note"] == "exact_applied_undef_mul_args"
    assert out["local_ops_A"] <= out["full_ops_A"]
    assert out["local_ops_B"] <= out["full_ops_B"]


def test_applied_undef_h1_h2_peels_with_reconstruction():
    K = x + 1
    L = y + 2
    A = h1(m) * h2(n) * K
    B = h1(m) * h2(n) * L
    out = split_edge(A, B)
    _assert_shape(out)
    assert out["certified"] is True
    assert out["reconstruction_ok"] is True
    assert out["mode"] == "multiplicative"
    assert set(sympy.Mul.make_args(out["S"])) == {h1(m), h2(n)}
    assert _eq(out["A_local"], K)
    assert _eq(out["B_local"], L)
    assert _eq(out["S"] * out["A_local"], A)
    assert _eq(out["S"] * out["B_local"], B)
    v = split_multiplicative(A, B)
    assert v["certified"] is True
    assert _eq(out["S"], v["S"])


def test_additive_common_term_splits_with_reconstruction():
    A = x + y
    B = x + z
    out = split_edge(A, B)
    _assert_shape(out)
    assert out["certified"] is True
    assert out["reconstruction_ok"] is True
    assert out["mode"] == "additive"
    assert _eq(out["S"], x)
    assert _eq(out["A_local"], y)
    assert _eq(out["B_local"], z)
    assert _eq(out["S"] + out["A_local"], A)
    assert _eq(out["S"] + out["B_local"], B)
    v = split_additive(A, B)
    assert v["certified"] is True
    assert _eq(out["S"], v["S"])


def test_multiplicative_preferred_when_both_modes_reconstruct():
    A = x + y
    out = split_edge(A, A)
    _assert_shape(out)
    assert out["certified"] is True
    assert out["mode"] == "multiplicative"
    assert _eq(out["S"] * out["A_local"], A)
    assert _eq(out["S"] * out["B_local"], A)


def test_partial_extra_factor_on_one_side_keeps_true_common():
    F = x + 3
    G = y + 4
    A = (x - y) * (x + 1) * F
    B = (x - y) * G
    out = split_edge(A, B)
    _assert_shape(out)
    assert out["certified"] is True
    assert out["reconstruction_ok"] is True
    assert _eq(out["S"], x - y)
    assert not _eq(out["S"], (x - y) * (x + 1))
    assert _eq(out["S"] * out["A_local"], A)
    assert _eq(out["S"] * out["B_local"], B)


# --------------------------------------------------------------------------- #
# Negatives — must not certify a false spectator
# --------------------------------------------------------------------------- #


def test_failed_reconstruction_is_not_certified(monkeypatch):
    def fake_mul(A, B):
        return {
            "S": x + 1,
            "A_local": y,
            "B_local": z,
            "certified": True,
            "note": "fake_mul",
        }

    def fake_add(A, B):
        return {
            "S": x + 1,
            "A_local": y,
            "B_local": z,
            "certified": True,
            "note": "fake_add",
        }

    monkeypatch.setattr(split_mod, "split_multiplicative", fake_mul)
    monkeypatch.setattr(split_mod, "split_additive", fake_add)
    A = x * y
    B = x * z
    out = split_edge(A, B)
    _assert_no_proving_kernel(out, A, B)
    assert out["note"] == "reconstruction_failed"
    assert not _eq(out["S"], x + 1)
    assert out["A_local"] != y
    assert out["B_local"] != z


def test_units_are_not_spectators():
    for A, B in (
        (x + 1, y + 1),
        (sympy.Integer(1), sympy.Integer(1)),
        (sympy.Integer(1), sympy.Integer(2)),
        (x, y),
    ):
        out = split_edge(A, B)
        _assert_shape(out)
        assert out["certified"] is False
        assert out["reconstruction_ok"] is False
        assert out["mode"] == "none"
        assert out["S"] == 1


def test_dropping_a_factor_without_reconstruction_must_not_certify():
    F = x + 3
    G = y + 4
    A = (x - y) * F
    B = G
    out = split_edge(A, B)
    _assert_no_proving_kernel(out, A, B)
    assert not _eq(out["S"], x - y)


def test_size_guard_does_not_invent_S():
    n = 8
    A = B = None
    while n <= 200:
        extras_a = sympy.Add(*[sympy.symbols(f"p{i}") for i in range(n)])
        extras_b = sympy.Add(*[sympy.symbols(f"q{i}") for i in range(n)])
        cand_a = (x + 1) * extras_a
        cand_b = (x + 1) * extras_b
        if count_ops(cand_a) + count_ops(cand_b) > 80:
            A, B = cand_a, cand_b
            break
        n += 8
    assert A is not None and B is not None
    assert count_ops(A) + count_ops(B) > 80
    v = split_multiplicative(A, B)
    assert v["certified"] is False
    out = split_edge(A, B)
    _assert_no_proving_kernel(out, A, B)
    assert not _eq(out["S"], x + 1)
    assert "too_large" in out["note"] or out["note"] in {
        "too_large_for_gcd",
        "no_exact_common_factor",
    }


def test_bad_input_not_certified():
    out = split_edge("not-an-expr", x)
    _assert_shape(out)
    assert out["certified"] is False
    assert out["reconstruction_ok"] is False
    assert out["mode"] == "none"
    assert out["note"].startswith("bad_input")


def test_source_ban_no_gold_pairing_or_simplify_proof():
    pkg = ROOT / "research" / "iterated_confluence" / "spectator"
    for path in sorted(pkg.glob("*.py")):
        src = path.read_text()
        assert "Phi_Gamma" not in src
        assert "guo_map" not in src
        assert "PAIRING" not in src
        assert "pairing_table" not in src
        assert "def L4" not in src
        assert "def L5" not in src
        assert "def L6" not in src
        assert "def L7" not in src
        assert "simplify(" not in src
        assert "sympy.simplify" not in src


# --------------------------------------------------------------------------- #
# Invariant: certified ⇔ reconstruction_ok; certified ⇒ exact rebuild
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "A,B",
    [
        ((x - y) * (x**2 + x * y + y**2), (x - y) * (3 * x**2)),
        (h1(m) * h2(n) * (x + 1), h1(m) * h2(n) * (y + 2)),
        (x + y, x + z),
        (x + 1, y + 1),
        ((x - y) * (x + 3), y + 4),
        (x * y, z),
        (2 * (x + 1), 3 * (x - 1)),
        (1 / (x - 1), 1 / (x + 1)),
        (sympy.Integer(1), sympy.Integer(1)),
        (x, -x),
    ],
)
def test_certified_iff_exact_reconstruction(A, B):
    out = split_edge(A, B)
    _assert_shape(out)
    assert out["certified"] == out["reconstruction_ok"]
    if out["certified"]:
        assert out["mode"] in {"multiplicative", "additive"}
        assert out["S"] not in (1, -1, sympy.Integer(1), sympy.Integer(-1))
        assert out["S"] != 0
        if out["mode"] == "multiplicative":
            assert _eq(out["S"] * out["A_local"], A)
            assert _eq(out["S"] * out["B_local"], B)
        else:
            assert _eq(out["S"] + out["A_local"], A)
            assert _eq(out["S"] + out["B_local"], B)
    else:
        assert out["mode"] == "none"
        assert out["S"] == 1
        assert out["A_local"] == A
        assert out["B_local"] == B


def test_split_report_is_json_serializable():
    A = (x - y) * (x + 1)
    B = (x - y) * (y + 2)
    report = split_report(A, B)
    blob = json.dumps(report)
    assert isinstance(blob, str)
    loaded = json.loads(blob)
    assert loaded["certified"] is True
    assert loaded["reconstruction_ok"] is True
    assert loaded["mode"] == "multiplicative"
    assert isinstance(loaded["S"], str)
    assert isinstance(loaded["A_local"], str)
    assert isinstance(loaded["B_local"], str)


def test_count_ops_matches_sympy():
    expr = (x - y) * (x**2 + x * y + y**2)
    assert count_ops(expr) == int(sympy.count_ops(expr, visual=False))
