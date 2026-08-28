"""Frozen Track-V complexity router. Deterministic. No network. No verdicts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.scalable_verification.api import (  # noqa: E402
    NONZERO,
    STRATEGIES,
    ZERO,
    route_name,
)
from research.scalable_verification.router import (  # noqa: E402
    MEASURE_KEYS,
    THRESHOLDS,
    THRESHOLDS_PATH,
    load_thresholds,
    measure,
    route,
)

KINDS = (
    "EQUALITY",
    "SUBSTITUTION",
    "PERMUTATION",
    "DERIVATIVE",
    "LIMIT",
    "NEWTON_DD",
    "HERMITE_DD",
    "CONFLUENCE",
    "RECURRENCE",
    "MASTER_INSTANCE",
    "BASIS_RECONSTRUCTION",
    "DIVIDED_DIFFERENCE",
)


def _m(**over: int) -> dict[str, int]:
    base = {k: 0 for k in MEASURE_KEYS}
    base.update(over)
    return base


def test_thresholds_file_is_frozen_source_of_truth():
    disk = json.loads(THRESHOLDS_PATH.read_text(encoding="utf-8"))
    loaded = load_thresholds()
    assert disk == THRESHOLDS == loaded
    assert disk["does_not_decide_truth"] is True
    assert disk["bounds"]["direct_ops_max"] == 40
    assert disk["bounds"]["special_function_ops_max"] == 80
    assert disk["bounds"]["huge_ops"] == 400
    assert disk["bounds"]["huge_sum_ops"] == 400
    assert disk["mins"]["piecewise"] == 1
    assert disk["mins"]["sum"] == 1
    assert disk["mins"]["special_function"] == 1
    assert "polygamma" in disk["special_function_names"]
    assert disk["piecewise_limit"]["with_sum"] == "FACTOR_LOCAL"
    assert disk["piecewise_limit"]["without_sum"] == "SERIES_LOCAL"
    assert disk["policy_order"][0] == "HUGE_UNKNOWN"
    assert disk["policy_order"][-1] == "DEFAULT_UNKNOWN"


def test_strategies_come_from_shared_api():
    assert STRATEGIES == (
        "DIRECT",
        "FACTOR_LOCAL",
        "SERIES_LOCAL",
        "DD_CERTIFICATE",
        "SPECIAL_FUNCTION_LOCAL",
        "UNKNOWN",
    )
    assert ZERO not in STRATEGIES
    assert NONZERO not in STRATEGIES
    assert route_name("ZERO") == "UNKNOWN"
    assert route_name("DIRECT") == "DIRECT"


def test_measure_keys_types_and_json():
    x = sympy.symbols("x")
    got = measure(x + 1)
    assert tuple(got) == MEASURE_KEYS
    assert all(isinstance(got[k], int) and not isinstance(got[k], bool) for k in MEASURE_KEYS)
    assert json.loads(json.dumps(got)) == got


def test_measure_polynomial_ops_depth_symbols():
    x, y = sympy.symbols("x y")
    got = measure((x + y) ** 2)
    assert got["op_count"] == 2
    assert got["tree_depth"] == 2
    assert got["piecewise_count"] == 0
    assert got["sum_count"] == 0
    assert got["special_function_count"] == 0
    assert got["n_free_symbols"] == 2


def test_measure_top_level_sum_and_piecewise():
    n, n_max, x = sympy.symbols("n N x")
    f = sympy.Function("f")
    lone_sum = sympy.Sum(f(n), (n, 1, n_max))
    lone_pw = sympy.Piecewise((x, x > 0), (-x, True))
    nested = sympy.Sum(sympy.Piecewise((f(n), n > 0), (0, True)), (n, 1, n_max))
    assert measure(lone_sum)["sum_count"] == 1
    assert measure(lone_pw)["piecewise_count"] == 1
    both = measure(nested)
    assert both["sum_count"] == 1
    assert both["piecewise_count"] == 1
    assert both["n_free_symbols"] == 1


def test_measure_polygamma_not_elementary():
    z = sympy.symbols("z")
    pg = measure(sympy.polygamma(1, z + 1) - sympy.polygamma(1, z))
    assert pg["special_function_count"] == 2
    elem = measure(sympy.exp(z) + sympy.sin(z) + sympy.log(z))
    assert elem["special_function_count"] == 0
    assert measure(sympy.polygamma(0, z))["special_function_count"] == 1


def test_measure_deterministic_and_integer_zero():
    x = sympy.symbols("x")
    expr = (x + 1) ** 2 + sympy.polygamma(0, x)
    assert measure(expr) == measure(expr)
    zeros = measure(0)
    assert zeros == {
        "op_count": 0,
        "tree_depth": 0,
        "piecewise_count": 0,
        "sum_count": 0,
        "special_function_count": 0,
        "n_free_symbols": 0,
    }


def test_route_small_equality_direct_and_newton_dd():
    x, y = sympy.symbols("x y")
    small = measure(x + y)
    assert small["op_count"] < 40
    assert route("EQUALITY", small) == "DIRECT"
    assert route("equality", small) == "DIRECT"
    assert route("EQUALITY", {"op_count": small["op_count"]}) == "DIRECT"
    newton = measure((x**2 - y**2) / (x - y))
    assert newton["op_count"] < 40
    assert route("NEWTON_DD", newton) == "DD_CERTIFICATE"
    assert route("HERMITE_DD", newton) == "DD_CERTIFICATE"
    assert route("DIVIDED_DIFFERENCE", newton) == "DD_CERTIFICATE"
    assert route("NEWTON_DD", small) != "DIRECT"
    assert route("EQUALITY", small) != "DD_CERTIFICATE"


def test_route_piecewise_limit_series_or_factor():
    n, n_max, x = sympy.symbols("n N x")
    f = sympy.Function("f")
    pw = sympy.Piecewise((x, x > 0), (-x, True))
    summed = sympy.Sum(sympy.Piecewise((f(n), n > 0), (0, True)), (n, 1, n_max))
    assert route("LIMIT", measure(pw)) == "SERIES_LOCAL"
    assert route("LIMIT", measure(summed)) == "FACTOR_LOCAL"
    assert route("EQUALITY", measure(pw)) == "DIRECT"
    assert route("LIMIT", measure(x + 1)) == "UNKNOWN"


def test_route_polygamma_special_function_local():
    z = sympy.symbols("z")
    pg = measure(sympy.polygamma(0, z))
    assert pg["op_count"] < 80
    assert pg["special_function_count"] >= 1
    assert route("EQUALITY", pg) == "SPECIAL_FUNCTION_LOCAL"
    assert route("LIMIT", pg) == "SPECIAL_FUNCTION_LOCAL"
    assert route("NEWTON_DD", pg) == "SPECIAL_FUNCTION_LOCAL"


def test_route_huge_ops_or_huge_sum_unknown():
    assert route("EQUALITY", _m(op_count=401)) == "UNKNOWN"
    assert route("NEWTON_DD", _m(op_count=401)) == "UNKNOWN"
    assert route("LIMIT", _m(op_count=401, piecewise_count=1)) == "UNKNOWN"
    assert route("EQUALITY", _m(op_count=500, special_function_count=4)) == "UNKNOWN"
    assert route("EQUALITY", _m(op_count=401, sum_count=1)) == "UNKNOWN"
    assert route("LIMIT", _m(op_count=401, sum_count=3, piecewise_count=2)) == "UNKNOWN"


def test_route_exclusive_bounds():
    assert route("EQUALITY", _m(op_count=39)) == "DIRECT"
    assert route("EQUALITY", _m(op_count=40)) == "UNKNOWN"
    assert route("NEWTON_DD", _m(op_count=39)) == "DD_CERTIFICATE"
    assert route("NEWTON_DD", _m(op_count=40)) == "UNKNOWN"
    assert route("EQUALITY", _m(op_count=79, special_function_count=1)) == "SPECIAL_FUNCTION_LOCAL"
    assert route("EQUALITY", _m(op_count=80, special_function_count=1)) == "UNKNOWN"
    assert route("EQUALITY", _m(op_count=400)) == "UNKNOWN"
    assert route("EQUALITY", _m(op_count=400, sum_count=1)) == "UNKNOWN"
    assert route("LIMIT", _m(op_count=400, piecewise_count=1)) == "SERIES_LOCAL"


def test_route_priority_special_over_direct_and_piecewise():
    assert route("EQUALITY", _m(op_count=10, special_function_count=1)) == "SPECIAL_FUNCTION_LOCAL"
    assert route(
        "LIMIT",
        _m(op_count=10, piecewise_count=1, special_function_count=1),
    ) == "SPECIAL_FUNCTION_LOCAL"
    assert route("LIMIT", _m(op_count=10, piecewise_count=1)) == "SERIES_LOCAL"


def test_route_fail_closed_and_malformed_measures():
    assert route("CONFLUENCE", _m(op_count=10)) == "UNKNOWN"
    assert route("SUBSTITUTION", _m(op_count=10)) == "UNKNOWN"
    assert route("", _m(op_count=10)) == "UNKNOWN"
    assert route(None, _m(op_count=10)) == "UNKNOWN"
    assert route("EQUALITY", None) == "UNKNOWN"
    assert route("EQUALITY", "ops") == "UNKNOWN"
    assert route("EQUALITY", {**_m(), "op_count": True}) == "UNKNOWN"
    assert route("EQUALITY", {**_m(), "op_count": None}) == "UNKNOWN"
    assert route("EQUALITY", {**_m(), "op_count": "nope"}) == "UNKNOWN"


def test_route_negative_op_count_is_unknown():
    bad = _m()
    bad["op_count"] = -1
    assert route("EQUALITY", bad) == "UNKNOWN"


def test_route_returns_only_strategies_never_verdicts():
    seen = set()
    grids = [
        _m(),
        _m(op_count=39),
        _m(op_count=40),
        _m(op_count=79, special_function_count=1),
        _m(op_count=80, special_function_count=1),
        _m(op_count=400, piecewise_count=1, sum_count=1),
        _m(op_count=401, sum_count=1, piecewise_count=1, special_function_count=2),
        _m(op_count=10, piecewise_count=1),
        _m(op_count=10, piecewise_count=1, sum_count=1),
        _m(tree_depth=99, op_count=5),
    ]
    for kind in KINDS:
        for meas in grids:
            got = route(kind, meas)
            seen.add(got)
            assert got in STRATEGIES
            assert got not in {ZERO, NONZERO}
    assert "DIRECT" in seen
    assert "DD_CERTIFICATE" in seen
    assert "SERIES_LOCAL" in seen
    assert "FACTOR_LOCAL" in seen
    assert "SPECIAL_FUNCTION_LOCAL" in seen
    assert "UNKNOWN" in seen


def test_router_does_not_import_engine_verifier():
    import research.scalable_verification.router.complexity as mod

    banned = (
        "symbolic_compactification.verifier",
        "verify_equivalent",
        "verify_obligation",
    )
    src = Path(mod.__file__).read_text(encoding="utf-8")
    for needle in banned:
        assert needle not in src
    assert "symbolic_compactification.verifier" not in sys.modules
    assert getattr(mod, "route")("EQUALITY", _m(op_count=1)) == "DIRECT"
