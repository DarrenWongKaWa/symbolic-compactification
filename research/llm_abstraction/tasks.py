"""Load calibration + frozen DEV items. Does not mutate frozen JSON on disk."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research.structure_discovery.prototype.leakage import proposer_view, assert_no_leakage

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CAL_DIR = HERE / "calibration"
BENCH_DIR = HERE / "bench"
V01 = ROOT / "benchmark_abstraction" / "ssc-abstraction-bench-v0.1" / "dev"
V02 = ROOT / "benchmark_abstraction" / "ssc-abstraction-bench-v0.2-beyond-lgg" / "dev"

GOLD_STRIP = (
    "gold_types", "gold_members", "gold_latent", "gold_operator",
    "forbidden_types", "hidden_gold", "gold_auxiliaries", "prefer_abstain",
    "requires_new_head", "gold_mode", "forbid_unnecessary", "shallow_ok",
    "polarity", "expected_lgg_fail", "lgg_expected", "note",
    "abstraction_depth", "hidden_from_proposer",
)

FROZEN_ANNOTATE = {
    "A-pos-born": {
        "category": "T1",
        "gold_types": ["parameterized_family"],
    },
    "A-neg-unrelated": {
        "category": "T1-neg",
        "gold_types": [],
        "forbidden_types": ["parameterized_family", "master_function"],
    },
    "B-pos-poly-deriv": {
        "category": "T4",
        "gold_types": ["derivative_family", "master_function", "recurrence_family"],
    },
    "T2-pos-distrib": {
        "category": "T2",
        "gold_types": ["parameterized_family", "other_structured"],
    },
    "T2-neg-not-distrib": {
        "category": "T2-neg",
        "gold_types": [],
        "forbidden_types": ["parameterized_family"],
    },
    "T4-pos-pg-deriv": {
        "category": "T3",
        "gold_types": ["derivative_family", "master_function", "recurrence_family"],
    },
    "T4-neg-indep": {
        "category": "T3-neg",
        "gold_types": [],
        "forbidden_types": ["derivative_family", "master_function"],
    },
    "T6-pos-specialize": {
        "category": "T5",
        "gold_types": ["confluent_representation", "parameterized_family"],
    },
    "T7-pos-swap": {
        "category": "T7",
        "gold_types": ["symmetry_invariant", "tensor_generator"],
    },
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def public_item(item: dict) -> dict:
    view = proposer_view(item)
    for k in GOLD_STRIP:
        view.pop(k, None)
    extra = tuple(GOLD_STRIP) + ("gold_template",)
    assert_no_leakage(view, extra_forbidden=extra)
    return view


def _load_dir(path: Path) -> list[dict]:
    if not path.is_dir():
        return []
    return [load_json(p) for p in sorted(path.glob("*.json"))]


def load_calibration() -> list[dict]:
    return _load_dir(CAL_DIR)


def _annotate_frozen(item: dict) -> dict:
    out = dict(item)
    extra = FROZEN_ANNOTATE.get(item.get("id") or "", {})
    for k, v in extra.items():
        out.setdefault(k, v)
    return out


def load_frozen_dev() -> list[dict]:
    names = [
        (V01, "A-pos-born.json"),
        (V01, "A-neg-unrelated.json"),
        (V01, "B-pos-poly-deriv.json"),
        (V02, "T2-pos-distrib.json"),
        (V02, "T2-neg-not-distrib.json"),
        (V02, "T4-pos-pg-deriv.json"),
        (V02, "T4-neg-indep.json"),
        (V02, "T6-pos-specialize.json"),
        (V02, "T7-pos-swap.json"),
    ]
    out = []
    for folder, name in names:
        p = folder / name
        if p.is_file():
            out.append(_annotate_frozen(load_json(p)))
    return out


def load_local_bench() -> list[dict]:
    return _load_dir(BENCH_DIR)


def load_dev_primary() -> list[dict]:
    seen = set()
    out = []
    for it in load_calibration() + load_local_bench() + load_frozen_dev():
        i = it.get("id")
        if i in seen:
            continue
        seen.add(i)
        out.append(it)
    return out


def load_guo_item() -> dict:
    from symbolic_compactification.adapters import (
        extract_expression_text,
        translate_wolfram_text,
    )
    raw = (ROOT / "examples" / "long" / "Guo_Sigma_abc_dc_exact.txt").read_text()
    tr = translate_wolfram_text(extract_expression_text(raw))
    # Bound indices appear in str(expr) but are not free; declare them so
    # parse_expression accepts the round-trip text. Do not declare reserved pi.
    symbols = list(tr.symbols)
    have = {s["name"] if isinstance(s, dict) else str(s) for s in symbols}
    for n in ("n", "m", "ell"):
        if n not in have:
            symbols.append({"name": n, "real": True})
    return {
        "id": "guo-sigma-abc",
        "split": "dev",
        "task": "abstraction_invention",
        "category": "GUO",
        "polarity": "positive",
        "current": str(tr.expr),
        "symbols": symbols,
        "functions": tr.functions,
        "source_format": "sympy",
        "scientific_context": [
            "Identify a small number of latent mathematical objects or representation changes that could explain multiple non-identical structural families.",
            "Do not simplify the full expression.",
            "Do not invent physical names. For each hypothesis: identify members; define latent object; specify operators/maps; provide a construction plan; list proof obligations.",
        ],
        "gold_types": [
            "master_function", "derivative_family", "confluent_representation",
            "divided_difference", "symmetry_invariant", "tensor_generator",
        ],
        "gold_members": [],
        "hidden_from_proposer": True,
        "hidden_gold": {"aux_names": ["Phi_Gamma", "PhiGamma"]},
    }
