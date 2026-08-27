"""Public observe() API. Read-only. No promotion authority."""
from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence, Union

import sympy

from symbolic_compactification.models import PACKAGE_VERSION, sha256_text
from symbolic_compactification.observations.backends import (
    cadabra_backend,
    egglog_backend,
    form_backend,
    lgg_backend,
    matchpy_backend,
    sympy_backend,
)
from symbolic_compactification.observations.discovery import (
    BACKEND_ORDER,
    backend_status,
    probe_backend,
    version_of,
)
from symbolic_compactification.observations.graph import merge_relations
from symbolic_compactification.observations.ir import ObservationBundle
from symbolic_compactification.observations.leak import assert_no_interpretation
from symbolic_compactification.observations.nodes import make_nodes
from symbolic_compactification.observations.packets import rank_packets
from symbolic_compactification.parser import parse_expression
from symbolic_compactification.structure import structure_summary
from symbolic_compactification.budgets import BudgetExceeded, run_with_budget

PRESETS = {
    "minimal": ("sympy",),
    "algebra": ("sympy", "matchpy"),
    "relations": ("sympy", "matchpy", "lgg", "egglog"),
    "physics": ("sympy", "matchpy", "lgg", "cadabra", "form"),
    "all_available": BACKEND_ORDER,
}

BackendSpec = Union[str, Sequence[str]]

_RUNNERS = {
    "sympy": sympy_backend.run,
    "matchpy": matchpy_backend.run,
    "egglog": egglog_backend.run,
    "lgg": lgg_backend.run,
    "cadabra": cadabra_backend.run,
    "form": form_backend.run,
}


def resolve_backends(spec: BackendSpec) -> list[str]:
    if spec == "auto":
        spec = "relations"
    if isinstance(spec, str) and spec in PRESETS:
        names = list(PRESETS[spec])
    elif isinstance(spec, str):
        names = [spec]
    else:
        names = list(spec)
    out = []
    for n in names:
        if n == "metatheory":
            continue  # optional, not implemented
        if n not in _RUNNERS:
            continue
        out.append(n)
    return out


def observe(
    expression: Union[str, sympy.Expr],
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
    *,
    context: Optional[dict] = None,
    backends: BackendSpec = "auto",
    timeout_s: float = 8.0,
) -> ObservationBundle:
    symbols = symbols or []
    functions = functions or []
    if isinstance(expression, str):
        expr = parse_expression(expression, symbols, functions=functions or None)
        raw = expression
    else:
        expr = expression
        raw = str(expression)
    names = resolve_backends(backends)
    status = backend_status()
    nodes = make_nodes(expr)
    fams, rels, variants = [], [], []
    ran = []
    for name in names:
        if not probe_backend(name).startswith("AVAILABLE"):
            continue
        fn = _RUNNERS[name]
        try:
            out = run_with_budget(
                fn, (expr, nodes),
                kwargs={"symbols": symbols, "functions": functions},
                seconds=timeout_s, operation=f"observe_{name}",
                mode="inline",
            )
        except (BudgetExceeded, Exception) as exc:
            out = {"unavailable": True, "backend": name,
                   "error": type(exc).__name__}
        if out.get("unavailable"):
            status[name] = f"OPTIONAL / failed ({out.get('error', 'unavailable')})"
            continue
        ran.append(name)
        fams.extend(out.get("families") or [])
        rels.extend(out.get("relations") or [])
        variants.extend(out.get("canonical_variants") or [])
    bundle = ObservationBundle(
        expression_summary={
            **structure_summary(expr),
            "raw_sha256": sha256_text(raw),
            "text": raw[:500],
        },
        nodes=nodes,
        families=fams,
        relations=merge_relations(rels),
        canonical_variants=variants,
        backend_status=status,
        provenance={
            "layer": "structural-observation-layer-v1",
            "package": PACKAGE_VERSION,
            "backends_run": ran,
            "context_keys": sorted((context or {}).keys()),
            "note": "observation only; no promotion; no scientific interpretation",
        },
    )
    bundle.packets = rank_packets(bundle)
    assert_no_interpretation(bundle.to_dict())
    return bundle
