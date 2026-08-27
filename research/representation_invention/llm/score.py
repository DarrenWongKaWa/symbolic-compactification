"""Score P2 hypotheses: parse / ground / compile / verify.

If the V2 compiler (Subagent C) is not importable, compile is skipped
with compile_status="not_wired". COMPILE_FAILURE is never rewritten as UNKNOWN.
"""
from __future__ import annotations

import importlib
from typing import Any, Callable, Optional

from research.representation_invention.schema import (
    OK,
    PARSE_FAILURE,
    RepresentationHypothesisV2,
    is_catalog_id,
    parse_hypothesis_v2,
)

COMPILE_NOT_WIRED = "not_wired"
COMPILE_OK = "COMPILE_OK"
COMPILE_FAILURE = "COMPILE_FAILURE"
COMPILE_SKIPPED = "skipped"

_COMPILE_CANDIDATES = (
    ("research.representation_invention.obligations", "compile_hypothesis_v2"),
    ("research.representation_invention.obligations.compile", "compile_hypothesis"),
    ("research.representation_invention.obligations", "compile_hypothesis"),
)
_VERIFY_CANDIDATES = (
    ("research.representation_invention.obligations.verify", "verify_hypothesis_v2"),
    ("research.representation_invention.obligations", "verify_hypothesis_v2"),
    ("research.representation_invention.obligations.verify", "verify_compiled"),
)


def _load_optional(candidates: tuple[tuple[str, str], ...]) -> Optional[Callable]:
    for mod_name, attr in candidates:
        try:
            mod = importlib.import_module(mod_name)
        except ImportError:
            continue
        fn = getattr(mod, attr, None)
        if callable(fn):
            return fn
    return None


def catalog_texts(catalog: Any) -> dict[str, str]:
    """Normalize catalog to {G####: member_text}."""
    out: dict[str, str] = {}
    if catalog is None:
        return out
    if isinstance(catalog, dict):
        for k, v in catalog.items():
            gid = str(k)
            if isinstance(v, dict):
                out[gid] = str(v.get("text") or v.get("expression") or "")
            else:
                out[gid] = str(v)
        return out
    for e in catalog:
        if isinstance(e, dict):
            gid = str(e.get("source_node_id") or e.get("gid") or e.get("id") or "")
            if gid:
                out[gid] = str(e.get("text") or e.get("expression") or "")
        else:
            out[str(e)] = ""
    return out


def as_hyp_obj(hyp: Any, catalog: set[str]) -> RepresentationHypothesisV2:
    if isinstance(hyp, RepresentationHypothesisV2):
        return hyp
    d = as_hyp_dict(hyp)
    if d.get("parse_status") == PARSE_FAILURE:
        return parse_hypothesis_v2(d, catalog) if "member_ids" in d else RepresentationHypothesisV2(
            representation_type=str(d.get("representation_type") or "other_explicit"),
            member_ids=[],
            parse_status=PARSE_FAILURE,
            parse_error=str(d.get("parse_error") or "parse_failure"),
        )
    return parse_hypothesis_v2(d, catalog)


def as_hyp_dict(hyp: Any) -> dict[str, Any]:
    if hasattr(hyp, "to_dict"):
        return hyp.to_dict()
    return dict(hyp)


def member_ids_of(hyp: dict) -> list[str]:
    return [str(m) for m in (hyp.get("member_ids") or [])]


def is_grounded(hyp: dict, catalog: Any) -> bool:
    if hyp.get("parse_status") == PARSE_FAILURE:
        return False
    mids = member_ids_of(hyp)
    if not mids:
        return False
    ids = set(catalog_texts(catalog))
    if not ids and isinstance(catalog, (set, list, tuple)) and catalog and not isinstance(next(iter(catalog)), dict):
        ids = {str(x) for x in catalog}
    return all(is_catalog_id(m) and m in ids for m in mids)


def _count_verdicts(verdicts: list[str]) -> dict[str, int]:
    return {
        "n_zero": sum(1 for v in verdicts if v == "ZERO"),
        "n_nonzero": sum(1 for v in verdicts if v == "NONZERO"),
        "n_unknown": sum(1 for v in verdicts if v == "UNKNOWN"),
    }


def _verdicts_from(compiled: Any) -> list[str]:
    if compiled is None:
        return []
    if isinstance(compiled, dict):
        if isinstance(compiled.get("verdicts"), list):
            return [str(v) for v in compiled["verdicts"]]
        rows = compiled.get("obligations") or compiled.get("results") or []
        out = []
        for row in rows:
            if isinstance(row, dict) and row.get("verdict"):
                out.append(str(row["verdict"]))
            elif hasattr(row, "verdict"):
                out.append(str(row.verdict))
        return out
    if hasattr(compiled, "verdicts"):
        return [str(v) for v in (compiled.verdicts or [])]
    return []


def _compile_status_of(compiled: Any) -> Optional[str]:
    if compiled is None:
        return None
    if isinstance(compiled, dict):
        st = compiled.get("compile_status")
        return str(st) if st else None
    st = getattr(compiled, "compile_status", None)
    return str(st) if st else None


def score_hypothesis(
    hyp: Any,
    catalog: set[str],
    *,
    symbols: Any = None,
    functions: Any = None,
) -> dict[str, Any]:
    h = as_hyp_dict(hyp)
    parse_status = h.get("parse_status") or OK
    if parse_status == PARSE_FAILURE:
        return {
            "parse_status": PARSE_FAILURE,
            "grounded": False,
            "compile_status": COMPILE_SKIPPED,
            "verdicts": [],
            "n_zero": 0,
            "n_nonzero": 0,
            "n_unknown": 0,
            "layer": "G",
            "detail": h.get("parse_error") or "parse_failure",
        }
    grounded = is_grounded(h, catalog)
    if not grounded:
        return {
            "parse_status": parse_status,
            "grounded": False,
            "compile_status": COMPILE_SKIPPED,
            "verdicts": [],
            "n_zero": 0,
            "n_nonzero": 0,
            "n_unknown": 0,
            "layer": "G",
            "detail": "not_grounded",
        }

    texts = catalog_texts(catalog)
    ids = set(texts)
    if isinstance(catalog, (set, list, tuple)):
        for x in catalog:
            if isinstance(x, dict):
                gid = x.get("source_node_id") or x.get("gid") or x.get("id")
                if gid:
                    ids.add(str(gid))
            else:
                ids.add(str(x))
    ids = {str(x) for x in ids if is_catalog_id(str(x))} or set(member_ids_of(h))

    compile_fn = _load_optional(_COMPILE_CANDIDATES)
    if compile_fn is None:
        return {
            "parse_status": parse_status,
            "grounded": True,
            "compile_status": COMPILE_NOT_WIRED,
            "verdicts": [],
            "n_zero": 0,
            "n_nonzero": 0,
            "n_unknown": 0,
            "layer": "C",
            "detail": "compiler_not_wired",
        }

    hyp_obj = as_hyp_obj(h, ids if ids else set(texts))
    try:
        compiled = compile_fn(hyp_obj, texts, symbols, functions)
    except TypeError:
        try:
            compiled = compile_fn(
                hyp_obj, catalog=texts, symbols=symbols, functions=functions,
            )
        except Exception as exc:
            return {
                "parse_status": parse_status,
                "grounded": True,
                "compile_status": COMPILE_FAILURE,
                "verdicts": [],
                "n_zero": 0,
                "n_nonzero": 0,
                "n_unknown": 0,
                "layer": "C",
                "detail": f"compile_error:{type(exc).__name__}",
            }
    except Exception as exc:
        return {
            "parse_status": parse_status,
            "grounded": True,
            "compile_status": COMPILE_FAILURE,
            "verdicts": [],
            "n_zero": 0,
            "n_nonzero": 0,
            "n_unknown": 0,
            "layer": "C",
            "detail": f"compile_error:{type(exc).__name__}",
        }

    cstatus = _compile_status_of(compiled) or COMPILE_OK
    if cstatus == COMPILE_FAILURE:
        return {
            "parse_status": parse_status,
            "grounded": True,
            "compile_status": COMPILE_FAILURE,
            "verdicts": [],
            "n_zero": 0,
            "n_nonzero": 0,
            "n_unknown": 0,
            "layer": "C",
            "detail": "compile_failure",
        }

    verify_fn = _load_optional(_VERIFY_CANDIDATES)
    verdicts: list[str] = []
    if verify_fn is not None:
        try:
            verified = verify_fn(
                compiled, symbols=symbols, functions=functions,
            )
        except TypeError:
            try:
                verified = verify_fn(compiled)
            except Exception:
                verified = compiled
        except Exception:
            verified = compiled
        verdicts = _verdicts_from(verified) or _verdicts_from(compiled)
    else:
        verdicts = _verdicts_from(compiled)

    counts = _count_verdicts(verdicts)
    if not verdicts:
        layer, detail = "V", "compiled_unverified"
    elif counts["n_zero"] and not counts["n_nonzero"] and not counts["n_unknown"]:
        layer, detail = "OK", "certified"
    elif counts["n_nonzero"] and not counts["n_zero"]:
        layer, detail = "D", "wrong_structure"
    elif counts["n_unknown"]:
        layer, detail = "V", "unknown"
    else:
        layer, detail = "V", "mixed"
    return {
        "parse_status": parse_status,
        "grounded": True,
        "compile_status": cstatus,
        "verdicts": verdicts,
        "layer": layer,
        "detail": detail,
        **counts,
    }


def aggregate_scores(scores: list[dict]) -> dict[str, Any]:
    statuses = [s.get("compile_status") for s in scores]
    if scores and all(st == COMPILE_NOT_WIRED for st in statuses):
        compile_status = COMPILE_NOT_WIRED
    elif any(st == COMPILE_FAILURE for st in statuses):
        compile_status = COMPILE_FAILURE
    elif any(st == COMPILE_OK for st in statuses):
        compile_status = COMPILE_OK
    elif scores:
        compile_status = str(statuses[0] or COMPILE_NOT_WIRED)
    else:
        compile_status = COMPILE_NOT_WIRED
    return {
        "n_grounded": sum(1 for s in scores if s.get("grounded")),
        "n_zero": sum(int(s.get("n_zero") or 0) for s in scores),
        "n_nonzero": sum(int(s.get("n_nonzero") or 0) for s in scores),
        "n_unknown": sum(int(s.get("n_unknown") or 0) for s in scores),
        "n_compile_ok": sum(1 for s in scores if s.get("compile_status") == COMPILE_OK),
        "compile_status": compile_status,
    }
