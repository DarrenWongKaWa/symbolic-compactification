"""Call representation_invention.obligations compile/verify when present.

A missing package is not ZERO. Compile failures are COMPILE_FAILURE, not
UNKNOWN. A ZERO on an attack is a false certification and must be reported.
"""
from __future__ import annotations

import importlib
from typing import Any, Optional

from research.representation_invention.labels import (
    COMPILE_FAILURE,
    VERDICT_NONZERO,
    VERDICT_UNKNOWN,
    VERDICT_ZERO,
)
from research.representation_invention.schema import PARSE_FAILURE, parse_hypothesis_v2

_V2_COMPILE = "research.representation_invention.obligations.compile"
_V2_VERIFY = "research.representation_invention.obligations.verify"
_V2_PKG = "research.representation_invention.obligations"


def _load(name: str):
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def discover_obligations_api() -> dict[str, Any]:
    compile_mod = _load(_V2_COMPILE)
    verify_mod = _load(_V2_VERIFY)
    pkg = _load(_V2_PKG)
    compile_fn = None
    verify_fn = None
    for src in (compile_mod, pkg):
        if src is None:
            continue
        fn = getattr(src, "compile_hypothesis", None)
        if callable(fn):
            compile_fn = fn
            break
    for src in (verify_mod, pkg):
        if src is None:
            continue
        fn = getattr(src, "verify_obligation", None)
        if callable(fn):
            verify_fn = fn
            break
    return {
        "available": compile_fn is not None or verify_fn is not None,
        "compile": compile_fn,
        "verify": verify_fn,
        "compile_module": getattr(compile_fn, "__module__", None),
        "verify_module": getattr(verify_fn, "__module__", None),
    }


def _overall(parse_status: str, compile_status: Optional[str], verdicts: list[Optional[str]]) -> str:
    if parse_status == PARSE_FAILURE:
        return PARSE_FAILURE
    decided = [v for v in verdicts if v]
    if VERDICT_ZERO in decided:
        return VERDICT_ZERO
    if compile_status == COMPILE_FAILURE and not decided:
        return COMPILE_FAILURE
    if VERDICT_NONZERO in decided:
        return VERDICT_NONZERO
    if COMPILE_FAILURE in decided or compile_status == COMPILE_FAILURE:
        return COMPILE_FAILURE
    if decided:
        return decided[0]
    return VERDICT_UNKNOWN


def probe_case(case: dict[str, Any], api: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    api = api or discover_obligations_api()
    if not api.get("available"):
        return {
            "available": False,
            "case_id": case.get("id"),
            "verdict": None,
            "note": "obligations_package_empty",
        }
    catalog = {str(k): str(v) for k, v in (case.get("catalog") or {}).items()}
    hyp_raw = case.get("hypothesis") or {}
    parsed = parse_hypothesis_v2(hyp_raw, set(catalog))
    math = case.get("math") or {}
    symbols = list(math.get("symbols") or [])
    functions = list(math.get("functions") or [])
    compile_fn = api.get("compile")
    verify_fn = api.get("verify")
    compile_status = None
    rows: list[dict[str, Any]] = []
    notes: list[str] = []
    try:
        if compile_fn is None:
            return {
                "available": True,
                "case_id": case.get("id"),
                "verdict": VERDICT_UNKNOWN,
                "note": "compile_fn_missing",
                "parse_status": parsed.parse_status,
            }
        compiled = compile_fn(
            parsed,
            catalog,
            symbols=symbols,
            functions=functions,
        )
        compile_status = getattr(compiled, "compile_status", None)
        obligations = getattr(compiled, "obligations", None) or []
        notes.append("compiled")
        if verify_fn is None:
            verdicts = [COMPILE_FAILURE if compile_status == COMPILE_FAILURE else VERDICT_UNKNOWN]
            return {
                "available": True,
                "case_id": case.get("id"),
                "verdict": _overall(parsed.parse_status, compile_status, verdicts),
                "verdicts": verdicts,
                "note": "verify_fn_missing",
                "parse_status": parsed.parse_status,
                "compile_status": compile_status,
            }
        for obl in obligations:
            vr = verify_fn(obl, symbols=symbols, functions=functions)
            v = getattr(vr, "verdict", None)
            cstat = getattr(vr, "compile_status", None) or getattr(obl, "compile_status", None)
            rows.append(
                {
                    "kind": getattr(obl, "kind", None),
                    "compile_status": cstat,
                    "compile_error": getattr(obl, "compile_error", None),
                    "verdict": v,
                    "note": getattr(vr, "note", ""),
                }
            )
        notes.append("verified_rows")
    except TypeError:
        # Signature mismatch: do not launder into ZERO.
        return {
            "available": True,
            "case_id": case.get("id"),
            "verdict": VERDICT_UNKNOWN,
            "note": "signature_mismatch",
            "parse_status": parsed.parse_status,
        }
    except Exception as exc:
        return {
            "available": True,
            "case_id": case.get("id"),
            "verdict": VERDICT_UNKNOWN,
            "note": type(exc).__name__,
            "parse_status": parsed.parse_status,
        }
    verdicts = []
    for row in rows:
        if row.get("verdict"):
            verdicts.append(row["verdict"])
        elif row.get("compile_status") == COMPILE_FAILURE:
            verdicts.append(COMPILE_FAILURE)
    overall = _overall(parsed.parse_status, compile_status, verdicts)
    return {
        "available": True,
        "case_id": case.get("id"),
        "verdict": overall,
        "verdicts": verdicts,
        "rows": rows,
        "note": ",".join(notes) or "probed",
        "parse_status": parsed.parse_status,
        "compile_status": compile_status,
    }


def probe_all(cases: Optional[list] = None) -> dict[str, Any]:
    if cases is None:
        from research.representation_invention.falsifier.cases import ATTACK_CASES

        cases = ATTACK_CASES
    api = discover_obligations_api()
    rows = [probe_case(c, api) for c in cases]
    zeros = [r for r in rows if r.get("verdict") == VERDICT_ZERO]
    return {
        "available": bool(api.get("available")),
        "n": len(rows),
        "n_zero": len(zeros),
        "zero_ids": [r.get("case_id") for r in zeros],
        "rows": rows,
    }
