"""Order-of-limits auditor. Timeout/size-guard is UNKNOWN, never CONSISTENT_ZERO."""
from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

import pytest
import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.consistency import (  # noqa: E402
    CONSISTENT_ZERO,
    CONSISTENCY_UNKNOWN,
    INCONSISTENT_NONZERO,
    LIMIT_OPS_CAP,
    check_two_paths,
    family_zero_blocked,
)
from research.iterated_confluence.consistency import auditor as auditor_mod  # noqa: E402
from research.iterated_confluence.schema import (  # noqa: E402
    CONSISTENT_ZERO as SCHEMA_CONSISTENT_ZERO,
    CONSISTENCY_UNKNOWN as SCHEMA_CONSISTENCY_UNKNOWN,
    FAMILY_NONZERO,
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    INCONSISTENT_NONZERO as SCHEMA_INCONSISTENT_NONZERO,
    PATH_ZERO,
    PathConsistencyObligation,
    PathStep,
    compose_family_verdict,
)
from research.representation_invention.dd import newton_first  # noqa: E402
from research.representation_invention.labels import FORBIDDEN_GOLD_PATTERNS  # noqa: E402
from research.scalable_verification.confluence.engine import _count_ops  # noqa: E402
from symbolic_compactification.budgets import BudgetExceeded  # noqa: E402

CONS_DIR = ROOT / "research" / "iterated_confluence" / "consistency"


def _xy():
    return sympy.symbols("x y")


def test_public_api_and_schema_constants():
    assert CONSISTENT_ZERO == SCHEMA_CONSISTENT_ZERO == "CONSISTENT_ZERO"
    assert INCONSISTENT_NONZERO == SCHEMA_INCONSISTENT_NONZERO == "INCONSISTENT_NONZERO"
    assert CONSISTENCY_UNKNOWN == SCHEMA_CONSISTENCY_UNKNOWN == "UNKNOWN"
    assert CONSISTENCY_UNKNOWN != CONSISTENT_ZERO
    assert LIMIT_OPS_CAP == 80


def test_commuting_cubic_newton_second_dd_is_consistent_zero():
    z, x, y, w = sympy.symbols("z x y w")
    F = z**3
    nxy = newton_first(F, z, x, y)
    nyw = newton_first(F, z, y, w)
    expr = (nxy - nyw) / (x - w)
    assert nxy == (x**3 - y**3) / (x - y)
    path_a = [("y", x), ("w", x)]
    path_b = [("w", x), ("y", x)]
    result = check_two_paths(expr, path_a, path_b)
    assert isinstance(result, PathConsistencyObligation)
    assert result.verdict == CONSISTENT_ZERO, result.to_dict()
    assert result.verdict != CONSISTENCY_UNKNOWN
    assert result.verdict != INCONSISTENT_NONZERO
    assert result.provenance


def test_commuting_cubic_via_pathstep():
    z, x, y, w = sympy.symbols("z x y w")
    expr = (newton_first(z**3, z, x, y) - newton_first(z**3, z, y, w)) / (x - w)
    path_a = [
        PathStep(source="xyw", target="xxw", variable="y", target_value="x"),
        PathStep(source="xxw", target="xxx", variable="w", target_value="x"),
    ]
    path_b = [
        PathStep(source="xyw", target="xyx", variable="w", target_value="x"),
        PathStep(source="xyx", target="xxx", variable="y", target_value="x"),
    ]
    result = check_two_paths(expr, path_a, path_b, symbols={"x": x, "y": y, "w": w})
    assert result.verdict == CONSISTENT_ZERO, result.to_dict()
    assert result.start == "xyw"
    assert result.end == "xxx"


def test_order_swap_rational_is_inconsistent_nonzero():
    x, y = _xy()
    result = check_two_paths(x / (x + y), [("y", 0), ("x", 0)], [("x", 0), ("y", 0)])
    assert result.verdict == INCONSISTENT_NONZERO, result.to_dict()
    assert result.verdict != CONSISTENT_ZERO
    assert result.verdict != CONSISTENCY_UNKNOWN
    assert result.provenance
    as_text = check_two_paths("x / (x + y)", [("y", 0), ("x", 0)], [("x", 0), ("y", 0)])
    assert as_text.verdict == INCONSISTENT_NONZERO, as_text.to_dict()


def test_huge_kernel_is_unknown_not_consistent_zero():
    xs = sympy.symbols(f"s0:{LIMIT_OPS_CAP + 50}")
    expr = sum(xs)
    assert _count_ops(expr) > LIMIT_OPS_CAP
    path_a = [(xs[0], 0), (xs[1], 0)]
    path_b = [(xs[1], 0), (xs[0], 0)]
    result = check_two_paths(expr, path_a, path_b)
    assert result.verdict == CONSISTENCY_UNKNOWN, result.to_dict()
    assert result.verdict != CONSISTENT_ZERO
    assert "size_guard" in result.provenance


def test_huge_kernel_does_not_enter_limit_cascade(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("must not evaluate oversized kernels")

    monkeypatch.setattr(auditor_mod, "_limit_value", _boom)
    xs = sympy.symbols(f"s0:{LIMIT_OPS_CAP + 50}")
    expr = sum(xs)
    result = check_two_paths(expr, [(xs[0], 0)], [(xs[0], 0)])
    assert result.verdict == CONSISTENCY_UNKNOWN
    assert result.verdict != CONSISTENT_ZERO


def test_timeout_is_unknown_never_consistent_zero(monkeypatch):
    def _boom(*_a, **_k):
        raise BudgetExceeded("path_consistency", 8.0)

    monkeypatch.setattr(auditor_mod, "_limit_value", _boom)
    x, y = _xy()
    result = check_two_paths(x + y, [("y", 0)], [("x", 0)])
    assert result.verdict == CONSISTENCY_UNKNOWN, result.to_dict()
    assert result.verdict != CONSISTENT_ZERO
    assert "timeout" in result.provenance


def test_malformed_or_unparsable_is_unknown_not_consistent_zero():
    x, y = _xy()
    bad_step = check_two_paths(x + y, [("y",)], [("x", 0)])
    assert bad_step.verdict == CONSISTENCY_UNKNOWN, bad_step.to_dict()
    assert bad_step.verdict != CONSISTENT_ZERO
    bad_expr = check_two_paths("not a parseable expression ???", [("y", 0)], [("x", 0)])
    assert bad_expr.verdict == CONSISTENCY_UNKNOWN, bad_expr.to_dict()
    assert bad_expr.verdict != CONSISTENT_ZERO
    assert "parse" in bad_expr.provenance


def test_schema_unknown_consistency_blocks_family_zero():
    assert family_zero_blocked([CONSISTENCY_UNKNOWN], True) is True
    assert (
        compose_family_verdict(
            path_verdicts=[PATH_ZERO, PATH_ZERO],
            consistency_verdicts=[CONSISTENCY_UNKNOWN],
            reconstruction_verdicts=["ZERO"],
            require_path_independence=True,
        )
        == FAMILY_UNKNOWN
    )
    assert FAMILY_UNKNOWN != FAMILY_ZERO


def test_schema_inconsistent_is_family_nonzero():
    assert family_zero_blocked([INCONSISTENT_NONZERO], True) is True
    assert (
        compose_family_verdict(
            path_verdicts=[PATH_ZERO, PATH_ZERO],
            consistency_verdicts=[INCONSISTENT_NONZERO],
            reconstruction_verdicts=["ZERO"],
            require_path_independence=True,
        )
        == FAMILY_NONZERO
    )
    assert FAMILY_NONZERO != FAMILY_ZERO


def test_family_zero_blocked_requires_all_consistent_zero():
    assert family_zero_blocked([CONSISTENT_ZERO, CONSISTENT_ZERO], True) is False
    assert family_zero_blocked([CONSISTENT_ZERO, CONSISTENCY_UNKNOWN], True) is True
    assert family_zero_blocked([], True) is True
    assert family_zero_blocked([CONSISTENCY_UNKNOWN], False) is False
    assert family_zero_blocked([INCONSISTENT_NONZERO], False) is True
    assert (
        compose_family_verdict(
            path_verdicts=[PATH_ZERO, PATH_ZERO],
            consistency_verdicts=[CONSISTENT_ZERO],
            reconstruction_verdicts=["ZERO"],
            required_edge_verdicts=["ZERO", "ZERO"],
            require_path_independence=True,
        )
        == FAMILY_ZERO
    )


def test_source_ban_no_gold_identities():
    texts: list[str] = []
    for path in CONS_DIR.rglob("*.py"):
        texts.append(path.read_text(encoding="utf-8"))
    texts.append(inspect.getsource(auditor_mod))
    blob = "\n".join(texts)
    assert "Phi_Gamma" not in blob
    assert "phi_gamma" not in blob.lower()
    assert "guo_map" not in blob
    assert "GUO" not in blob
    for pat in FORBIDDEN_GOLD_PATTERNS:
        assert re.search(pat, blob) is None, pat
    src = inspect.getsource(check_two_paths)
    assert "FAMILY_ZERO" not in src
