#!/usr/bin/env python3
"""Verify a compactification candidate.

Two independent axes:

  relation     ZERO | NONZERO | UNKNOWN | ERROR
  improvement  IMPROVED | NO_IMPROVEMENT | DEPENDS

A new name that merely wraps the original expression can be ZERO and still
NO_IMPROVEMENT. ZERO does not mean the paper claim is proved.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _load_ledger():
    path = Path(__file__).resolve().parent / "ledger.py"
    spec = importlib.util.spec_from_file_location("ssc_skill_ledger", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _load_symbols(path: Path) -> list:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        return raw.get("symbols") or raw.get("assumptions") or []
    if isinstance(raw, list):
        return raw
    raise ValueError("symbols must be a list or {\"symbols\": [...]}")


def _count_ops(expr: str, symbols: list) -> int | None:
    try:
        from symbolic_compactification.parser import parse_expression
        import sympy
    except ImportError:
        return None
    parsed = parse_expression(expr, symbols)
    return int(sympy.count_ops(parsed, visual=False))


def _expand_definitions(expr: str, definitions: dict[str, str]) -> str:
    if expr.strip() in definitions:
        return definitions[expr.strip()]
    return expr


def _improvement(
    current: str,
    candidate: str,
    symbols: list,
    definitions: dict[str, str],
    verdict: str,
) -> dict[str, Any]:
    if _IDENT_RE.fullmatch(candidate.strip()) and candidate.strip() in definitions:
        return {
            "verdict": "NO_IMPROVEMENT",
            "reason_code": "DEFINITION_WRAP",
            "detail": "candidate is a new name; new definitions are not compactness",
        }
    if verdict != "ZERO":
        return {
            "verdict": "NO_IMPROVEMENT",
            "reason_code": "NOT_EQUIVALENT",
            "detail": "improvement is only scored after a ZERO residual",
        }
    before = _count_ops(current, symbols)
    after = _count_ops(candidate, symbols)
    extra_defs = len(definitions)
    if before is None or after is None:
        return {
            "verdict": "DEPENDS",
            "reason_code": "OPS_UNAVAILABLE",
            "ops_before": before,
            "ops_after": after,
            "new_definitions": extra_defs,
        }
    # New definitions are part of the complexity budget.
    penalized = after + extra_defs
    if penalized < before:
        verdict_i = "IMPROVED"
        code = "FEWER_OPS"
    elif penalized == before:
        verdict_i = "NO_IMPROVEMENT"
        code = "SAME_OPS"
    else:
        verdict_i = "NO_IMPROVEMENT"
        code = "MORE_OPS"
    return {
        "verdict": verdict_i,
        "reason_code": code,
        "ops_before": before,
        "ops_after": after,
        "new_definitions": extra_defs,
    }


def verify_candidate(
    current: str,
    candidate: str,
    symbols: list,
    *,
    definitions: dict[str, str] | None = None,
    assumptions: list | None = None,
    domain: str = "",
) -> dict[str, Any]:
    ledger = _load_ledger()
    definitions = definitions or {}
    expanded = _expand_definitions(candidate, definitions)
    verify = ledger.load_verify_equivalent()
    if verify is None:
        receipt = {
            "schema": ledger.RECEIPT_SCHEMA,
            "relation": {"verdict": "NOT_RUN", "reason": "engine missing"},
            "improvement": {
                "verdict": "DEPENDS",
                "reason_code": "ENGINE_MISSING",
            },
            "engine": ledger.engine_identity(),
        }
        return receipt
    result = verify(
        current,
        expanded,
        symbols,
        assumptions={"declared": assumptions or []},
    )
    relation = {
        "verdict": result.verdict,
        "residual": result.residual,
        "counterexample": result.counterexample,
        "lhs": current,
        "rhs": expanded,
        "candidate_as_submitted": candidate,
    }
    improvement = _improvement(
        current, candidate, symbols, definitions, result.verdict
    )
    bound = ledger.make_receipt(
        edge_id="compact-1",
        lhs=current,
        rhs=expanded,
        assumptions=assumptions or [],
        symbols=symbols,
        domain=domain,
        kind="ALGEBRAIC_EQUIVALENCE",
        verdict=result.verdict,
        residual=result.residual,
        counterexample=result.counterexample,
    )
    result_latex = ""
    if result.verdict == "ZERO":
        result_latex = _to_latex(candidate, symbols)
    return {
        "schema": ledger.RECEIPT_SCHEMA,
        "relation": relation,
        "improvement": improvement,
        "receipt": bound,
        "engine": bound["engine"],
        "definitions": definitions,
        "domain": domain,
        "result_latex": result_latex,
    }


def _to_latex(expr: str, symbols: list) -> str:
    try:
        from symbolic_compactification.parser import parse_expression
        import sympy
    except ImportError:
        return expr
    parsed = parse_expression(expr, symbols)
    return sympy.latex(parsed)


def _write_failure(out: Path, reason: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    stale = out / "result.tex"
    if stale.exists():
        stale.unlink()
    record = {
        "schema": "VerificationReceiptV1",
        "relation": {"verdict": "ERROR", "reason": reason},
        "improvement": {"verdict": "NO_IMPROVEMENT", "reason_code": "INPUT_ERROR"},
    }
    (out / "verification.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out / "unresolved.md").write_text(
        f"# Unresolved\n\n- {reason}\n", encoding="utf-8"
    )
    (out / "report.md").write_text(
        f"# Compactification report\n\nInput failed: {reason}\n", encoding="utf-8"
    )


def _write_outputs(out: Path, record: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    stale = out / "result.tex"
    if stale.exists():
        stale.unlink()
    (out / "verification.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    relation = record["relation"]
    improvement = record["improvement"]
    unresolved = []
    if relation.get("verdict") != "ZERO":
        unresolved.append(
            f"Relation is {relation.get('verdict')}, not ZERO. "
            "Do not present the candidate as verified."
        )
    if improvement.get("verdict") != "IMPROVED":
        unresolved.append(
            f"Improvement is {improvement.get('verdict')} "
            f"({improvement.get('reason_code')}). Equivalence is not compactness."
        )
    (out / "unresolved.md").write_text(
        "# Unresolved\n\n"
        + ("\n".join(f"- {item}" for item in unresolved) or "- None recorded.")
        + "\n",
        encoding="utf-8",
    )
    report = [
        "# Compactification report",
        "",
        f"- Relation: `{relation.get('verdict')}`",
        f"- Improvement: `{improvement.get('verdict')}` ({improvement.get('reason_code')})",
        f"- Engine: `{record.get('engine')}`",
        "",
        "ZERO means the encoded residual vanished under the declared symbols.",
        "It does not prove a paper-level claim, a limit, or an integral identity.",
        "",
    ]
    (out / "report.md").write_text("\n".join(report), encoding="utf-8")
    if relation.get("verdict") == "ZERO":
        submitted = relation.get("candidate_as_submitted") or relation.get("rhs") or ""
        latex = record.get("result_latex") or submitted
        (out / "result.tex").write_text(latex + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--symbols", required=True, type=Path)
    parser.add_argument("--definitions", type=Path, default=None)
    parser.add_argument("--domain", default="")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        definitions = {}
        if args.definitions:
            definitions = json.loads(args.definitions.read_text(encoding="utf-8"))
        record = verify_candidate(
            _read(args.current),
            _read(args.candidate),
            _load_symbols(args.symbols),
            definitions=definitions,
            domain=args.domain,
        )
    except Exception as exc:
        _write_failure(args.out, str(exc))
        print("ERROR", args.out)
        return 4
    _write_outputs(args.out, record)
    verdict = record["relation"].get("verdict")
    if verdict == "ZERO":
        print("ZERO", args.out)
        return 0
    print(verdict, args.out)
    return 2 if verdict == "NONZERO" else 3


if __name__ == "__main__":
    raise SystemExit(main())
