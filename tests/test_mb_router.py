"""Frozen Track-V2 obligation router. Deterministic. No network. No verdicts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.multibranch_verification.router import (  # noqa: E402
    MEASURE_KEYS,
    STRATEGIES,
    THRESHOLDS,
    THRESHOLDS_PATH,
    VERDICTS,
    load_thresholds,
    measure,
    route,
    route_name,
)

KINDS = (
    "EQUALITY",
    "SUBSTITUTION",
    "DERIVATIVE",
    "IDENTITY",
    "LIMIT",
    "NEWTON_DD",
    "HERMITE_DD",
    "DIVIDED_DIFFERENCE",
    "DD_RECURRENCE",
    "HERMITE_RECURRENCE",
    "HERMITE_DD_RECURRENCE",
    "HERMITE_DIVIDED_DIFFERENCE",
    "ONE_PARAMETER_CONFLUENCE",
    "LOCAL_CONFLUENCE",
    "REPEATED_NODE_CONFLUENCE",
    "CONFLUENCE",
    "RECURRENCE",
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
    assert disk["track"] == "V2"
    assert disk["bounds"]["direct_ops_max"] == 40
    assert disk["bounds"]["special_function_ops_max"] == 80
    assert disk["bounds"]["recurrence_ops_max"] == 40
    assert disk["bounds"]["huge_ops"] == 400
    assert disk["bounds"]["huge_sum_ops"] == 400
    assert disk["bounds"]["huge_denom"] == 80
    assert disk["bounds"]["direct_symbols_max"] == 8
    assert disk["bounds"]["factor_denom_min"] == 2
    assert disk["mins"]["branch"] == 1
    assert disk["mins"]["sum"] == 1
    assert disk["mins"]["special_function"] == 1
    assert disk["mins"]["hermite_multiplicity"] == 2
    assert "polygamma" in disk["special_function_names"]
    assert disk["branch_limit"]["with_sum"] == "FACTOR"
    assert disk["branch_limit"]["without_sum"] == "SERIES"
    assert disk["denom_factor"] == "FACTOR"
    assert disk["policy_order"][0] == "HUGE_UNKNOWN"
    assert disk["policy_order"][-1] == "DEFAULT_UNKNOWN"


def test_strategies_exclude_verdicts():
    assert STRATEGIES == (
        "DIRECT",
        "FACTOR",
        "SERIES",
        "DD_RECURRENCE",
        "HERMITE_RECURRENCE",
        "SPECIAL_FUNCTION",
        "UNKNOWN",
    )
    for v in VERDICTS:
        assert v not in STRATEGIES
    assert route_name("ZERO") == "UNKNOWN"
    assert route_name("NONZERO") == "UNKNOWN"
    assert route_name("FAMILY_ZERO") == "UNKNOWN"
    assert route_name("FAMILY_NONZERO") == "UNKNOWN"
    assert route_name("DIRECT") == "DIRECT"
    assert route_name("FACTOR_LOCAL") == "UNKNOWN"


def test_measure_keys_types_and_json():
    x = sympy.symbols("x")
    got = measure(x + 1)
    assert tuple(got) == MEASURE_KEYS
    assert all(isinstance(got[k], int) and not isinstance(got[k], bool) for k in MEASURE_KEYS)
    assert json.loads(json.dumps(got)) == got


def test_measure_polynomial_ops_symbols_denom():
    x, y = sympy.symbols("x y")
    got = measure((x + y) ** 2)
    assert got["op_count"] == 2
    assert got["branch_count"] == 0
    assert got["sum_count"] == 0
    assert got["special_function_count"] == 0
    assert got["n_free_symbols"] == 2
    assert got["denom_complexity"] == 0
    assert got["multiplicity"] == 0


def test_measure_top_level_sum_and_piecewise_branches():
    n, n_max, x = sympy.symbols("n N x")
    f = sympy.Function("f")
    lone_sum = sympy.Sum(f(n), (n, 1, n_max))
    lone_pw = sympy.Piecewise((x, x > 0), (-x, True))
    five = sympy.Piecewise(
        (x, x > 4),
        (x - 1, x > 3),
        (x - 2, x > 2),
        (x - 3, x > 1),
        (0, True),
    )
    nested = sympy.Sum(sympy.Piecewise((f(n), n > 0), (0, True)), (n, 1, n_max))
    assert measure(lone_sum)["sum_count"] == 1
    assert measure(lone_pw)["branch_count"] == 2
    assert measure(five)["branch_count"] == 5
    both = measure(nested)
    assert both["sum_count"] == 1
    assert both["branch_count"] == 2
    assert both["n_free_symbols"] == 1


def test_measure_polygamma_denom_and_multiplicity():
    z, x, y = sympy.symbols("z x y")
    pg = measure(sympy.polygamma(1, z + 1) - sympy.polygamma(1, z))
    assert pg["special_function_count"] == 2
    elem = measure(sympy.exp(z) + sympy.sin(z) + sympy.log(z))
    assert elem["special_function_count"] == 0
    assert measure(sympy.polygamma(0, z))["special_function_count"] == 1
    newton = measure((x**2 - y**2) / (x - y))
    assert newton["denom_complexity"] == 1
    crowded = measure((x + y) / ((x - y) * (x - z)))
    assert crowded["denom_complexity"] >= 2
    f = sympy.Function("f")
    assert measure(sympy.Derivative(f(x), x))["multiplicity"] == 2
    assert measure(sympy.Derivative(f(x), (x, 2)))["multiplicity"] == 3
    assert measure(x + y)["multiplicity"] == 0


def test_measure_deterministic_and_integer_zero():
    x = sympy.symbols("x")
    expr = (x + 1) ** 2 + sympy.polygamma(0, x)
    assert measure(expr) == measure(expr)
    zeros = measure(0)
    assert zeros == {
        "op_count": 0,
        "branch_count": 0,
        "sum_count": 0,
        "n_free_symbols": 0,
        "special_function_count": 0,
        "denom_complexity": 0,
        "multiplicity": 0,
    }


def test_route_small_equality_direct_and_recurrences():
    x, y = sympy.symbols("x y")
    small = measure(x + y)
    assert small["op_count"] < 40
    assert route("EQUALITY", small) == "DIRECT"
    assert route("equality", small) == "DIRECT"
    assert route("IDENTITY", small) == "DIRECT"
    assert route("SUBSTITUTION", small) == "DIRECT"
    assert route("EQUALITY", {"op_count": small["op_count"]}) == "DIRECT"
    newton = measure((x**2 - y**2) / (x - y))
    assert newton["op_count"] < 40
    assert newton["multiplicity"] < 2
    assert route("NEWTON_DD", newton) == "DD_RECURRENCE"
    assert route("dd_recurrence", newton) == "DD_RECURRENCE"
    assert route("DIVIDED_DIFFERENCE", newton) == "DD_RECURRENCE"
    assert route("HERMITE_DD", newton) == "HERMITE_RECURRENCE"
    assert route("hermite_dd_recurrence", newton) == "HERMITE_RECURRENCE"
    assert route("hermite_divided_difference", newton) == "HERMITE_RECURRENCE"
    assert route("repeated_node_confluence", newton) == "HERMITE_RECURRENCE"
    assert route("NEWTON_DD", small) != "DIRECT"
    assert route("EQUALITY", small) != "DD_RECURRENCE"


def test_route_multiplicity_splits_dd_from_hermite():
    assert route("NEWTON_DD", _m(op_count=10, multiplicity=1)) == "DD_RECURRENCE"
    assert route("NEWTON_DD", _m(op_count=10, multiplicity=2)) == "HERMITE_RECURRENCE"
    assert route("DD_RECURRENCE", _m(op_count=10, multiplicity=3)) == "HERMITE_RECURRENCE"
    assert route("HERMITE_DD", _m(op_count=10, multiplicity=0)) == "HERMITE_RECURRENCE"
    assert route("EQUALITY", _m(op_count=10, multiplicity=3)) == "DIRECT"


def test_route_branch_limit_series_or_factor():
    n, n_max, x = sympy.symbols("n N x")
    f = sympy.Function("f")
    pw = sympy.Piecewise((x, x > 0), (-x, True))
    summed = sympy.Sum(sympy.Piecewise((f(n), n > 0), (0, True)), (n, 1, n_max))
    assert route("LIMIT", measure(pw)) == "SERIES"
    assert route("local_confluence", measure(pw)) == "SERIES"
    assert route("LIMIT", measure(summed)) == "FACTOR"
    assert route("one_parameter_confluence", measure(summed)) == "FACTOR"
    assert route("EQUALITY", measure(pw)) == "DIRECT"
    assert route("LIMIT", measure(x + 1)) == "UNKNOWN"


def test_route_denom_factor_and_free_symbol_cap():
    x, y, z = sympy.symbols("x y z")
    crowded = measure((x + y) / ((x - y) * (x - z)))
    assert crowded["denom_complexity"] >= 2
    assert crowded["op_count"] < 80
    assert route("EQUALITY", crowded) == "FACTOR"
    assert route("LIMIT", _m(op_count=20, denom_complexity=4)) == "FACTOR"
    assert route("EQUALITY", _m(op_count=10, n_free_symbols=8)) == "DIRECT"
    assert route("EQUALITY", _m(op_count=10, n_free_symbols=9)) == "UNKNOWN"


def test_route_polygamma_special_function():
    z = sympy.symbols("z")
    pg = measure(sympy.polygamma(0, z))
    assert pg["op_count"] < 80
    assert pg["special_function_count"] >= 1
    assert route("EQUALITY", pg) == "SPECIAL_FUNCTION"
    assert route("LIMIT", pg) == "SPECIAL_FUNCTION"
    assert route("NEWTON_DD", pg) == "SPECIAL_FUNCTION"
    assert route("HERMITE_DD", pg) == "SPECIAL_FUNCTION"


def test_route_huge_ops_sum_or_denom_unknown():
    assert route("EQUALITY", _m(op_count=401)) == "UNKNOWN"
    assert route("NEWTON_DD", _m(op_count=401)) == "UNKNOWN"
    assert route("LIMIT", _m(op_count=401, branch_count=5)) == "UNKNOWN"
    assert route("EQUALITY", _m(op_count=500, special_function_count=4)) == "UNKNOWN"
    assert route("EQUALITY", _m(op_count=401, sum_count=1)) == "UNKNOWN"
    assert route("LIMIT", _m(op_count=401, sum_count=3, branch_count=5)) == "UNKNOWN"
    assert route("EQUALITY", _m(op_count=50, denom_complexity=81)) == "UNKNOWN"
    assert route("HERMITE_DD", _m(op_count=50, denom_complexity=81)) == "UNKNOWN"


def test_route_exclusive_bounds():
    assert route("EQUALITY", _m(op_count=39)) == "DIRECT"
    assert route("EQUALITY", _m(op_count=40)) == "UNKNOWN"
    assert route("NEWTON_DD", _m(op_count=39)) == "DD_RECURRENCE"
    assert route("NEWTON_DD", _m(op_count=40)) == "UNKNOWN"
    assert route("HERMITE_DD", _m(op_count=39)) == "HERMITE_RECURRENCE"
    assert route("HERMITE_DD", _m(op_count=40)) == "UNKNOWN"
    assert route("EQUALITY", _m(op_count=79, special_function_count=1)) == "SPECIAL_FUNCTION"
    assert route("EQUALITY", _m(op_count=80, special_function_count=1)) == "UNKNOWN"
    assert route("EQUALITY", _m(op_count=400)) == "UNKNOWN"
    assert route("EQUALITY", _m(op_count=400, sum_count=1)) == "UNKNOWN"
    assert route("LIMIT", _m(op_count=400, branch_count=1)) == "SERIES"
    assert route("EQUALITY", _m(op_count=79, denom_complexity=80)) == "FACTOR"
    assert route("EQUALITY", _m(op_count=80, denom_complexity=80)) == "UNKNOWN"
    assert route("EQUALITY", _m(op_count=10, denom_complexity=80)) == "FACTOR"
    assert route("EQUALITY", _m(op_count=10, denom_complexity=81)) == "UNKNOWN"


def test_route_priority_special_over_hermite_branch_and_direct():
    assert route("EQUALITY", _m(op_count=10, special_function_count=1)) == "SPECIAL_FUNCTION"
    assert route(
        "LIMIT",
        _m(op_count=10, branch_count=1, special_function_count=1),
    ) == "SPECIAL_FUNCTION"
    assert route(
        "HERMITE_DD",
        _m(op_count=10, special_function_count=1, multiplicity=2),
    ) == "SPECIAL_FUNCTION"
    assert route("LIMIT", _m(op_count=10, branch_count=1)) == "SERIES"
    assert route("NEWTON_DD", _m(op_count=10, multiplicity=2, branch_count=1)) == "HERMITE_RECURRENCE"


def test_route_fail_closed_and_malformed_measures():
    assert route("RECURRENCE", _m(op_count=10)) == "UNKNOWN"
    assert route("PERMUTATION", _m(op_count=10)) == "UNKNOWN"
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
    bad2 = _m()
    bad2["multiplicity"] = -2
    assert route("HERMITE_DD", bad2) == "UNKNOWN"


def test_route_returns_only_strategies_never_verdicts():
    seen = set()
    grids = [
        _m(),
        _m(op_count=39),
        _m(op_count=40),
        _m(op_count=39, n_free_symbols=8),
        _m(op_count=39, n_free_symbols=9),
        _m(op_count=79, special_function_count=1),
        _m(op_count=80, special_function_count=1),
        _m(op_count=400, branch_count=5, sum_count=1),
        _m(op_count=401, sum_count=1, branch_count=5, special_function_count=2),
        _m(op_count=10, branch_count=1),
        _m(op_count=10, branch_count=1, sum_count=1),
        _m(op_count=10, multiplicity=2),
        _m(op_count=10, denom_complexity=4),
        _m(op_count=50, denom_complexity=81),
        _m(n_free_symbols=99, op_count=5),
    ]
    for kind in KINDS:
        for meas in grids:
            got = route(kind, meas)
            seen.add(got)
            assert got in STRATEGIES
            assert got not in VERDICTS
    assert "DIRECT" in seen
    assert "DD_RECURRENCE" in seen
    assert "HERMITE_RECURRENCE" in seen
    assert "SERIES" in seen
    assert "FACTOR" in seen
    assert "SPECIAL_FUNCTION" in seen
    assert "UNKNOWN" in seen


def test_router_does_not_import_engine_verifier():
    import research.multibranch_verification.router.complexity as mod

    banned = (
        "symbolic_compactification.verifier",
        "verify_equivalent",
        "verify_obligation",
        "compose_family_verdict",
    )
    src = Path(mod.__file__).read_text(encoding="utf-8")
    for needle in banned:
        assert needle not in src
    assert getattr(mod, "route")("EQUALITY", _m(op_count=1)) == "DIRECT"
    assert getattr(mod, "route")("FAMILY_ZERO", _m(op_count=1)) == "UNKNOWN"
