"""Scan candidate contracts for parameter witnesses.

A witness satisfies DECLARED symbol/positivity/nonzero conditions and
still hits a required pole, cut, or division by zero. That disqualifies
the task until the problem statement is fixed.

Guo atoms are not loaded. No LLM.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import sympy

from research.assumption_complete_representation.audit.falsify.catalog import (
    CLEAN,
    CLEAN_PROBES,
    CLEAN_WHY,
    DISQUALIFIED,
    DISQUALIFIED_WITNESSES,
    GAP,
    GAPS,
    GUO_ANALOGUE,
    HEADLINE_CLEAN,
    SKIPPED_GUO,
    SKIPPED_REJECTED,
)
from research.assumption_complete_representation.schema import DECLARED, NOT_DECLARED

METHOD = "ac-a4-witness-1"
HERE = Path(__file__).resolve().parent
AC_ROOT = HERE.parents[1]
CASES_ROOT = AC_ROOT / "cases"
SCREENING_PATH = AC_ROOT / "SCREENING.json"
WITNESSES_PATH = HERE / "WITNESSES.json"

_PARSE = {
    "I": sympy.I,
    "pi": sympy.pi,
    "exp": sympy.exp,
    "polygamma": sympy.polygamma,
    "tanh": sympy.tanh,
    "tan": sympy.tan,
    "cosh": sympy.cosh,
    "sinh": sympy.sinh,
    "Rational": sympy.Rational,
    "oo": sympy.oo,
    "zoo": sympy.zoo,
    "nan": sympy.nan,
}
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

_NONFINITE = (
    sympy.zoo,
    sympy.nan,
    sympy.oo,
    -sympy.oo,
    sympy.S.NaN,
    sympy.S.ComplexInfinity,
    sympy.S.Infinity,
    sympy.S.NegativeInfinity,
)


def _locals_for(expr: str, assignment: dict[str, Any] | None = None) -> dict[str, Any]:
    """Bind identifiers to symbols so sympy.beta / sympy.zeta do not leak in."""
    local = dict(_PARSE)
    names = set(_IDENT.findall(expr))
    if assignment:
        names.update(str(k) for k in assignment)
        for raw in assignment.values():
            names.update(_IDENT.findall(str(raw)))
    for name in names:
        if name not in local:
            local[name] = sympy.Symbol(name)
    return local


def _sympify(text: Any, local: dict[str, Any] | None = None) -> sympy.Expr:
    return sympy.sympify(text, locals=local or dict(_PARSE))


def probe_is_singular(expr: str, assignment: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a restricted SymPy sketch at a concrete assignment."""
    local = _locals_for(expr, assignment)
    expr_s = _sympify(expr, local)
    subs: dict[sympy.Symbol, sympy.Expr] = {}
    for name, raw in assignment.items():
        subs[local[str(name)]] = _sympify(raw, local)
    val = expr_s.xreplace(subs)
    try:
        val = sympy.simplify(val)
    except Exception:
        pass
    singular = False
    if val in _NONFINITE:
        singular = True
    else:
        try:
            if val.has(*_NONFINITE):
                singular = True
        except Exception:
            pass
    if not singular:
        try:
            num = val.evalf()
            if num in _NONFINITE or (hasattr(num, "is_infinite") and num.is_infinite):
                singular = True
        except Exception:
            pass
    return {
        "expr": expr,
        "assignment": {str(k): str(v) for k, v in assignment.items()},
        "value": str(val),
        "singular": bool(singular),
    }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object: {path}")
    return payload


def load_screening() -> dict[str, Any]:
    return _load_json(SCREENING_PATH)


def _row_kind(bucket: str) -> str:
    if bucket == "keepers":
        return "keeper"
    if bucket == "flagged":
        return "flagged"
    if bucket == "miner_rejected":
        return "miner_rejected"
    return bucket


def iter_screening_rows(screening: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    blob = screening if screening is not None else load_screening()
    rows: list[dict[str, Any]] = []
    for bucket in ("keepers", "flagged", "miner_rejected"):
        for item in blob.get(bucket) or []:
            rec = dict(item)
            rec["_bucket"] = bucket
            rec["_kind"] = _row_kind(bucket)
            rows.append(rec)
    return rows


def load_dossier(rel_path: str) -> dict[str, Any]:
    path = CASES_ROOT / rel_path
    return _load_json(path)


def _pred_statements(items: Any, label: str | None = None) -> list[str]:
    out: list[str] = []
    if not isinstance(items, list):
        return out
    for item in items:
        if isinstance(item, dict):
            lab = str(item.get("label") or NOT_DECLARED).strip().upper()
            if label is not None and lab != label:
                continue
            stmt = str(item.get("statement") or "").strip()
            if stmt:
                out.append(stmt)
        elif item:
            out.append(str(item))
    return out


def _status_for(case_id: str, rejected: bool, is_guo: bool) -> str:
    if is_guo:
        return SKIPPED_GUO
    if rejected:
        return SKIPPED_REJECTED
    if case_id in DISQUALIFIED_WITNESSES:
        return DISQUALIFIED
    if case_id in GAPS and case_id not in CLEAN_WHY:
        return GAP
    return CLEAN


def _evaluate_witness(entry: dict[str, Any]) -> dict[str, Any]:
    probe = entry.get("probe") or {}
    expr = str(probe.get("expr") or "")
    assignment = dict(entry.get("assignment") or {})
    got = probe_is_singular(expr, assignment)
    expect = bool(probe.get("expect_singular", True))
    row = dict(entry)
    row["sympy"] = {
        "value": got["value"],
        "singular": got["singular"],
        "expect_singular": expect,
        "confirmed": got["singular"] is True if expect else got["singular"] is False,
    }
    return row


def _evaluate_clean_probes(case_id: str) -> dict[str, Any]:
    spec = CLEAN_PROBES.get(case_id) or {}
    finite_out = []
    for item in spec.get("finite") or []:
        probe = item.get("probe") or {}
        got = probe_is_singular(str(probe.get("expr") or ""), dict(item.get("assignment") or {}))
        finite_out.append(
            {
                **item,
                "sympy": {
                    "value": got["value"],
                    "singular": got["singular"],
                    "expect_singular": False,
                    "confirmed": got["singular"] is False,
                },
            }
        )
    blocked_out = []
    for item in spec.get("blocked") or []:
        probe = item.get("probe") or {}
        got = probe_is_singular(str(probe.get("expr") or ""), dict(item.get("assignment") or {}))
        blocked_out.append(
            {
                **item,
                "sympy": {
                    "value": got["value"],
                    "singular": got["singular"],
                    "expect_singular": True,
                    "confirmed": got["singular"] is True,
                },
            }
        )
    return {"finite": finite_out, "blocked": blocked_out}


def _case_record(row: dict[str, Any], dossier: dict[str, Any]) -> dict[str, Any]:
    case_id = str(dossier.get("case_id") or row.get("case_id") or "")
    rejected = bool(dossier.get("rejected") or row.get("rejected_flag"))
    is_guo = bool(dossier.get("is_guo") or row.get("is_guo"))
    ac = dossier.get("assumption_contract") if isinstance(dossier.get("assumption_contract"), dict) else {}
    status = _status_for(case_id, rejected, is_guo)
    rec: dict[str, Any] = {
        "case_id": case_id,
        "path": row.get("path"),
        "bucket": row.get("_bucket"),
        "title": dossier.get("title"),
        "domain": dossier.get("domain"),
        "rejected": rejected,
        "is_guo": is_guo,
        "skeptic": list(row.get("skeptic") or []),
        "status": status,
        "declared_positivity": _pred_statements(ac.get("positivity_conditions"), DECLARED),
        "declared_nonzero": _pred_statements(ac.get("nonzero_conditions"), DECLARED),
        "n_declared_analytic": len(_pred_statements(ac.get("analytic_domains"), DECLARED)),
        "n_derived": len(_pred_statements(ac.get("derived_conditions"), "DERIVED")),
        "symbol_assumptions": ac.get("symbol_assumptions") or {},
        "witnesses": [],
        "gaps": list(GAPS.get(case_id) or []),
        "why_clean": None,
        "probes": {},
        "disqualifies": status == DISQUALIFIED,
    }
    if status == DISQUALIFIED:
        rec["witnesses"] = [_evaluate_witness(w) for w in DISQUALIFIED_WITNESSES[case_id]]
        rec["why_clean"] = None
        rec["problem"] = "PROBLEM_UNDERSPECIFIED until the problem statement is fixed"
    elif status == CLEAN:
        rec["why_clean"] = CLEAN_WHY.get(case_id) or (
            "No pole/cut/division-by-zero witness found under DECLARED "
            "symbol/positivity/nonzero/analytic exclusions."
        )
        rec["probes"] = _evaluate_clean_probes(case_id)
    elif status == GAP:
        rec["why_clean"] = None
        rec["probes"] = _evaluate_clean_probes(case_id)
    if case_id in GAPS and status == DISQUALIFIED:
        rec["gaps"] = list(GAPS[case_id])
    if case_id in CLEAN_PROBES and status == DISQUALIFIED:
        rec["probes"] = _evaluate_clean_probes(case_id)
    return rec


def run_scan() -> dict[str, Any]:
    screening = load_screening()
    cases: list[dict[str, Any]] = []
    for row in iter_screening_rows(screening):
        dossier = load_dossier(str(row["path"]))
        cases.append(_case_record(row, dossier))

    n_clean = sum(1 for c in cases if c["status"] == CLEAN)
    n_disq = sum(1 for c in cases if c["status"] == DISQUALIFIED)
    n_gap_status = sum(1 for c in cases if c["status"] == GAP)
    n_skip_rej = sum(1 for c in cases if c["status"] == SKIPPED_REJECTED)
    n_skip_guo = sum(1 for c in cases if c["status"] == SKIPPED_GUO)
    n_scanned = sum(
        1
        for c in cases
        if c["status"] in {CLEAN, DISQUALIFIED, GAP}
    )
    failed_probes = []
    for rec in cases:
        for w in rec.get("witnesses") or []:
            sp = w.get("sympy") or {}
            if rec["status"] == DISQUALIFIED and not sp.get("confirmed"):
                failed_probes.append({"case_id": rec["case_id"], "witness_id": w.get("witness_id"), "sympy": sp})
        probes = rec.get("probes") or {}
        for item in (probes.get("finite") or []) + (probes.get("blocked") or []):
            sp = item.get("sympy") or {}
            if sp and not sp.get("confirmed"):
                failed_probes.append(
                    {
                        "case_id": rec["case_id"],
                        "assignment": item.get("assignment"),
                        "sympy": sp,
                    }
                )

    report = {
        "method": METHOD,
        "parent": "f987fcc",
        "branch": "work/ac-a-falsify",
        "headline_clean": HEADLINE_CLEAN,
        "guo_analogue": GUO_ANALOGUE,
        "pool": {
            "n_screening": int(screening.get("n_candidates") or 0),
            "n_scanned": n_scanned,
            "n_clean": n_clean,
            "n_disqualified": n_disq,
            "n_gap_only": n_gap_status,
            "n_skipped_rejected": n_skip_rej,
            "n_skipped_guo": n_skip_guo,
            "disqualified_ids": [c["case_id"] for c in cases if c["status"] == DISQUALIFIED],
            "gap_only_ids": [c["case_id"] for c in cases if c["status"] == GAP],
            "headline_clean_status": next(
                (c["status"] for c in cases if c["case_id"] == HEADLINE_CLEAN),
                None,
            ),
        },
        "probe_failures": failed_probes,
        "cases": cases,
    }
    return report


def write_witnesses(path: Path | None = None) -> dict[str, Any]:
    report = run_scan()
    out = path or WITNESSES_PATH
    out.write_text(json.dumps(report, indent=2, sort_keys=False, default=str) + "\n", encoding="utf-8")
    return report


def main() -> None:
    report = write_witnesses()
    pool = report["pool"]
    print(
        json.dumps(
            {
                "method": report["method"],
                "n_scanned": pool["n_scanned"],
                "n_clean": pool["n_clean"],
                "n_disqualified": pool["n_disqualified"],
                "disqualified_ids": pool["disqualified_ids"],
                "headline_clean": report["headline_clean"],
                "probe_failures": len(report["probe_failures"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
